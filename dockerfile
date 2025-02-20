FROM debian:12 AS setup

ENV IBC_VERSION=3.20.0

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    ca-certificates git libxtst6 libgtk-3-0 openbox procps python3 socat tigervnc-standalone-server unzip wget2 xterm \
    # https://github.com/extrange/ibkr-docker/issues/74
    libasound2 \
    libnss3 \
    libgbm1 \
    libnspr4

# Create a directory for IBKR TWS
WORKDIR /opt/ibkr
RUN mkdir -p /opt/ibkr/tws

RUN wget2 https://github.com/IbcAlpha/IBC/releases/download/${IBC_VERSION}/IBCLinux-${IBC_VERSION}.zip -O ibc.zip \
    && unzip ibc.zip -d /opt/ibc \
    && rm ibc.zip

ENV INSTALL_FILENAME="ibgateway-10.30.1t-standalone-linux-x64.sh"

# Fetch hashes
RUN wget2 "https://github.com/extrange/ibkr-docker/releases/download/10.30.1t-stable/ibgateway-10.30.1t-standalone-linux-x64.sh.sha256" \
    -O hash

# Download IB Gateway (which contains TWS) and check hashes
RUN wget2 "https://github.com/extrange/ibkr-docker/releases/download/10.30.1t-stable/ibgateway-10.30.1t-standalone-linux-x64.sh" \
    -O "$INSTALL_FILENAME" \
    && sha256sum -c hash \
    && chmod +x "$INSTALL_FILENAME" \
    && yes '' | "./$INSTALL_FILENAME"  \
    && rm "$INSTALL_FILENAME"

# Set working directory
WORKDIR /opt/ibkr/tws

# Expose necessary ports for IBKR API
EXPOSE 7496 7497 4002 4001

RUN mkdir -p ~/ibc && mv /opt/ibc/config.ini ~/ibc/config.ini

RUN chmod a+x ./*.sh /opt/ibc/*.sh /opt/ibc/scripts/*.sh

CMD [ "/start.sh" ]