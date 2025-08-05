FROM python:3.10-slim

# Install Chrome and dependencies for Selenium/Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg unzip xvfb libglib2.0-0 libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libxss1 libxtst6 fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libx11-6 libxext6 libxinerama1 libxkbcommon0 libxrender1 libxv1

# Install Chrome
RUN wget -qO- https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the sandbox server code
COPY server.py /app/server.py
WORKDIR /app

# Expose a port for RPC
EXPOSE 8000

# Run headless Xvfb and the server
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & DISPLAY=:99 python server.py"]
