FROM python:3.10-slim

# 安裝系統工具與 sudo
RUN apt-get update && apt-get install -y \
    sudo \
    curl \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# 建立一般使用者 neo-user
RUN useradd -m -s /bin/bash neo-user

# 設定工作目錄
WORKDIR /app

# 複製依賴項並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY . .

# 設定 flag.sh
RUN cp flag.sh /root/flag.sh && \
    chmod +x /root/flag.sh && \
    # 建立 user_flag.txt 佔位並設定權限
    mkdir -p /home/neo-user && \
    touch /home/neo-user/user_flag.txt && \
    chown neo-user:neo-user /home/neo-user/user_flag.txt

# 配置 Sudo 權限：允許所有使用者 (包含執行 app 的使用者) 免密碼執行 flag.sh
RUN echo "ALL ALL=(ALL) NOPASSWD: /root/flag.sh" >> /etc/sudoers

# 暴露埠號
EXPOSE 8080

# 啟動應用程式 (以 root 執行以確保能讀取配置，但在真實環境建議降權)
CMD ["python", "app.py"]
