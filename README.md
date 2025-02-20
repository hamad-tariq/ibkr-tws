# IBKR TWS Deployment on Render

This repository provides a **Dockerized** setup for deploying **Interactive Brokers' TWS** on **Render.com**.

## 🔹 How It Works
- Uses **Xvfb** to create a virtual display.
- Runs **IBKR TWS** in headless mode.
- Exposes an **API port (7497)** to allow automated trading bots.

## 🚀 Deployment Instructions
1. **Fork this repository**.
2. **Connect it to Render.com** (as a **Background Worker**).
3. **Deploy** using the provided `Dockerfile`.

## ⚠️ Limitations
- **IBKR TWS auto-logs out after 24 hours**. Use **IB Gateway** instead.
- **No GPU acceleration** available on Render.

## 📞 Connecting Your Script
Once deployed, connect using Python:

```python
from ib_insync import *

ib = IB()
ib.connect('your-render-instance.com', 7497, clientId=1)
print("Connected to IBKR TWS")
```