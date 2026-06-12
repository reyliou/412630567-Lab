FROM python:3.10-slim

# 安裝系統工具與特定的 sudo 版本 (或模擬 CVE-2019-14287 的環境)
# 註：在 Debian 11/12 中直接安裝 sudo 1.8.27 較困難，
# 我們這裡使用標準 sudo 並配合脆弱的 sudoers 設定來演示該 CVE 的核心邏輯。
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

# 設定屬主權限
RUN chown -R neo-user:neo-user /app

# 設定 flag.sh (放在 root 目錄，模擬高權限腳本)
RUN cp flag.sh /root/flag.sh && \
    chmod 755 /root/flag.sh && \
    # 建立 user_flag.txt 佔位並設定權限
    mkdir -p /home/neo-user && \
    touch /home/neo-user/user_flag.txt && \
    chown neo-user:neo-user /home/neo-user/user_flag.txt

# 配置 Sudo 權限：模擬 CVE-2019-14287 脆弱配置
# 規則：允許 neo-user 以除了 root 以外的任何使用者身份執行 /bin/bash (及 flag.sh)
# 漏洞利用點：sudo -u#-1 /bin/bash
RUN echo "neo-user ALL=(ALL, !root) NOPASSWD: /bin/bash, /root/flag.sh" >> /etc/sudoers

# 暴露埠號
EXPOSE 8080

# 切換到低權限使用者執行應用程式
USER neo-user

# 啟動應用程式
CMD ["python", "app.py"]
