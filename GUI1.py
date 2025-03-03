import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import requests

# Set the API URL (adjust if needed)

# API_URL = "http://localhost:5000"
API_URL = "http://54.85.106.111:5000"

def validate_time(time_str):
    """Ensure the time is between 09:30:00 and 16:00:00."""
    try:
        print("time_str: ", time_str)
        t = datetime.strptime(time_str, "%H:%M:%S").time()
        start_time = datetime.strptime("09:30:00", "%H:%M:%S").time()
        end_time = datetime.strptime("16:00:00", "%H:%M:%S").time()
        if t < start_time or t > end_time:
            return False
        return True
    except ValueError:
        return False

def submit_order():
    try:
        symbol = entry_symbol.get().strip()
        action = action_var.get()
        quantity_str = entry_quantity.get().strip()
        stop_loss_str = entry_stop_loss.get().strip()
        entry_time_str = entry_time_var.get().strip()
        exit_time_str = exit_time_var.get().strip()

        # Basic Validations
        if not symbol:
            messagebox.showerror("Error", "Symbol cannot be empty")
            return
        if not quantity_str.isdigit() or int(quantity_str) <= 0:
            messagebox.showerror("Error", "Invalid quantity")
            return
        if not stop_loss_str.isdigit() or int(stop_loss_str) < 0:
            messagebox.showerror("Error", "Invalid stop loss ticks")
            return
        if not validate_time(entry_time_str) or not validate_time(exit_time_str):
            messagebox.showerror("Error", "Time must be between 09:30:00 and 16:00:00")
            return

        # Get date values from calendars (format: yyyy-mm-dd)
        entry_date = entry_calendar.get_date()
        exit_date = exit_calendar.get_date()

        # Combine date and time strings
        entry_datetime_str = f"{entry_date} {entry_time_str}"
        exit_datetime_str = f"{exit_date} {exit_time_str}"
        try:
            entry_datetime = datetime.strptime(entry_datetime_str, '%Y-%m-%d %H:%M:%S')
            exit_datetime = datetime.strptime(exit_datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showerror("Error", "Invalid date/time format")
            return

        # Validate that entry and exit times are in the future and exit is after entry.
        current_dt = datetime.now()
        if entry_datetime <= current_dt:
            messagebox.showerror("Error", "Entry date and time must be in the future.")
            return
        if exit_datetime <= current_dt:
            messagebox.showerror("Error", "Exit date and time must be in the future.")
            return
        if exit_datetime <= entry_datetime:
            messagebox.showerror("Error", "Exit date and time must be after entry date and time.")
            return

        # Confirmation pop-up
        if not messagebox.askyesno("Confirm Order",
                                   f"Place order to {action} {quantity_str} shares of {symbol} at {entry_datetime_str}?"):
            return

        payload = {
            "symbol": symbol,
            "action": action,
            "quantity": int(quantity_str),
            "entry_time": entry_datetime_str,
            "exit_time": exit_datetime_str,
            "stop_loss_ticks": int(stop_loss_str)
        }
        response = requests.post(f"{API_URL}/place_order", json=payload)
        if response.status_code == 200:
            status_label.config(text="Order processing started!")
        else:
            status_label.config(text="Error: " + response.text)
    except Exception as e:
        status_label.config(text="Error: " + str(e))

def refresh_trade_activity():
    try:
        response = requests.get(f"{API_URL}/orders")
        if response.status_code == 200:
            orders = response.json()
            trade_treeview.delete(*trade_treeview.get_children())
            # Clear existing items in the treeview
            for item in trade_treeview.get_children():
                trade_treeview.delete(item)
            # Insert each order into the treeview with alternating row colors
            for idx, order in enumerate(orders):
                
                if order.get("stop_loss_price", "") is not None:
                    stop_loss_price = round(order.get("stop_loss_price", ""), 2)
                else:
                    stop_loss_price = ""
                    
                mongo_id = order.get("_id", "")
                symbol = order.get("symbol", "")
                act = order.get("action", "")
                entry_time = order.get("entry_time", "")
                exit_time = order.get("exit_time", "")
                StopLossExecuted = order.get("StopLossExecuted", False)
                quantity = order.get("quantity", "")
                entry_price = order.get("entry_price", "") or ""
                exit_price = order.get("exit_price", "") or ""
                status = order.get("status", "")
                tag = "evenrow" if idx % 2 == 0 else "oddrow"

                
                # trade_treeview.insert("", "end", values=(mongo_id, symbol, act, entry_time, exit_time,
                #                                           stop_loss_price, quantity, entry_price, exit_price, status),
                #                        tags=(tag,))

                # Insert a parent row (group header) with summary info
                parent_id = trade_treeview.insert("", "end",
                                                  text="Group",
                                                  values=(mongo_id, symbol, act, "", "", quantity, "", status))
                
                trade_treeview.insert(parent_id, "end",  text="Entry", values=(mongo_id, symbol, act, entry_time,
                                                                        "", "", entry_price),
                                       tags=(tag,))
                if act.upper() == "BUY":
                    act = "SELL"
                else: 
                     act = "BUY"

                trade_treeview.insert(parent_id, "end",  text="Exit", values=(mongo_id, symbol, act, exit_time, 
                                                        "", "", exit_price if not StopLossExecuted else ""),
                                       tags=(tag,))
                
                trade_treeview.insert(parent_id, "end",  text="Stop", values=(mongo_id, symbol, act, "",
                                                          stop_loss_price, "", stop_loss_price if StopLossExecuted else ""),
                                       tags=(tag,))
                
                

                
                
            status_label.config(text="Trade activity refreshed!")
        else:
            status_label.config(text="Error: " + response.text)
    except Exception as e:
        status_label.config(text="Error: " + str(e))

def cancel_order():
    try:
        selected_items = trade_treeview.selection()
        if not selected_items:
            status_label.config(text="Select an order to cancel.")
            return
        selected_item = selected_items[0]
        values = trade_treeview.item(selected_item, "values")
        mongo_id = values[0]
        if not mongo_id:
            status_label.config(text="No valid mongo_id found for selected order.")
            return
        if not messagebox.askyesno("Confirm Cancellation", "Are you sure you want to cancel this order?"):
            return
        payload = {"mongo_id": mongo_id}
        response = requests.post(f"{API_URL}/cancel_order", json=payload)
        if response.status_code == 200:
            status_label.config(text="Order cancelled successfully!")
        else:
            status_label.config(text="Error: " + response.text)
    except Exception as e:
        status_label.config(text="Error: " + str(e))

# -----------------------------
# GUI Setup with Overall Scrolling
# -----------------------------
root = tk.Tk()
root.title("IBKR Order Placement Client")
root.geometry("900x600")
root.configure(bg="#f0f0f0")

# Create a canvas for overall scrolling with both vertical and horizontal scrollbars.
canvas = tk.Canvas(root, bg="#f0f0f0")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
v_scrollbar.pack(side=tk.RIGHT, fill="y")
h_scrollbar = ttk.Scrollbar(root, orient="horizontal", command=canvas.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill="x")

canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Create a frame inside the canvas that holds the app content.
app_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=app_frame, anchor="nw")

# Configure ttk styling
style = ttk.Style()
style.configure("TLabel", font=("Arial", 9), padding=3)
style.configure("TButton", font=("Arial", 9), padding=3)
style.configure("TEntry", font=("Arial", 9), padding=3)
style.configure("TFrame", background="#f5f5f5")
style.configure("TLabelframe", font=("Arial", 9, "bold"), padding=8)
style.configure("TLabelframe.Label", font=("Arial", 12, "bold"), foreground="black")
style.configure("Treeview", font=("Arial", 9), rowheight=20)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#d9d9d9", foreground="black")
style.map("Treeview", background=[("selected", "#a6a6a6")])

# -----------------------------
# Order Placement Section
# -----------------------------
order_frame = ttk.LabelFrame(app_frame, text="Place Order", style="TLabelframe")
order_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
# (No column weight is set so entries keep fixed width)

ttk.Label(order_frame, text="Symbol:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_symbol = ttk.Entry(order_frame, width=15)
entry_symbol.grid(row=0, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Action:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
action_var = tk.StringVar(value="BUY")
action_frame = ttk.Frame(order_frame)
action_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
ttk.Radiobutton(action_frame, text="BUY", variable=action_var, value="BUY").pack(side="left", padx=5)
ttk.Radiobutton(action_frame, text="SELL", variable=action_var, value="SELL").pack(side="left", padx=5)

ttk.Label(order_frame, text="Entry Date:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
entry_calendar = Calendar(order_frame, date_pattern='yyyy-mm-dd')
entry_calendar.grid(row=2, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Entry Time (HH:MM:SS):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
entry_time_var = tk.StringVar(value="09:30:00")
ttk.Entry(order_frame, textvariable=entry_time_var, width=15).grid(row=3, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Exit Date:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
exit_calendar = Calendar(order_frame, date_pattern='yyyy-mm-dd')
exit_calendar.grid(row=4, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Exit Time (HH:MM:SS):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
exit_time_var = tk.StringVar(value="16:00:00")
ttk.Entry(order_frame, textvariable=exit_time_var, width=15).grid(row=5, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Stop Loss (Ticks):").grid(row=6, column=0, sticky="w", padx=5, pady=5)
entry_stop_loss = ttk.Entry(order_frame, width=15)
entry_stop_loss.grid(row=6, column=1, sticky="w", padx=5, pady=5)

ttk.Label(order_frame, text="Quantity:").grid(row=7, column=0, sticky="w", padx=5, pady=5)
entry_quantity = ttk.Entry(order_frame, width=15)
entry_quantity.grid(row=7, column=1, sticky="w", padx=5, pady=5)

submit_button = ttk.Button(order_frame, text="Submit Order", command=submit_order)
submit_button.grid(row=8, column=1, sticky="w", pady=10)

# -----------------------------
# Trade Activity Section
# -----------------------------
trade_frame = ttk.LabelFrame(app_frame, text="Trade Order Activity", style="TLabelframe")
trade_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
app_frame.rowconfigure(1, weight=1)

# Define your columns including "mongo_id" as the first column.
columns = ("mongo_id", "Symbol", "Action", "Time", "Stop Loss", "Quantity", "Price", "Status")

# Create the Treeview with show="tree headings" so the left (tree) column is displayed.
trade_treeview = ttk.Treeview(trade_frame, columns=columns, show="tree headings")

# Configure the left (tree) column with a header "Group"
trade_treeview.heading("#0", text="Group")
trade_treeview.column("#0", width=80, anchor="center")

# Configure the mongo_id column to be hidden
trade_treeview.heading("mongo_id", text="mongo_id")
trade_treeview.column("mongo_id", width=0, minwidth=0, stretch=False)


for col in columns[1:]:
    trade_treeview.heading(col, text=col)
    trade_treeview.column(col, width=90, anchor="center")
trade_treeview.grid(row=0, column=0, sticky="nsew")
trade_frame.rowconfigure(0, weight=1)
trade_frame.columnconfigure(0, weight=1)

# Add vertical scrollbar to the treeview
tree_v_scrollbar = ttk.Scrollbar(trade_frame, orient="vertical", command=trade_treeview.yview)
trade_treeview.configure(yscrollcommand=tree_v_scrollbar.set)
tree_v_scrollbar.grid(row=0, column=1, sticky="ns")

# Add horizontal scrollbar to the treeview
tree_h_scrollbar = ttk.Scrollbar(trade_frame, orient="horizontal", command=trade_treeview.xview)
trade_treeview.configure(xscrollcommand=tree_h_scrollbar.set)
tree_h_scrollbar.grid(row=1, column=0, sticky="ew")

# Configure alternating row colors for the treeview
trade_treeview.tag_configure("evenrow", background="#f2f2f2")
trade_treeview.tag_configure("oddrow", background="white")

# -----------------------------
# Control Buttons and Status Label
# -----------------------------
button_frame = ttk.Frame(app_frame)
button_frame.grid(row=2, column=0, pady=10)

refresh_button = ttk.Button(button_frame, text="Refresh Trade Activity", command=refresh_trade_activity)
refresh_button.pack(side="left", padx=5)

cancel_button = ttk.Button(button_frame, text="Cancel Order", command=cancel_order)
cancel_button.pack(side="left", padx=5)

status_label = ttk.Label(app_frame, text="", foreground="blue")
status_label.grid(row=3, column=0, pady=5)

root.mainloop()
