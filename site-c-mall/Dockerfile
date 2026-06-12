FROM python:3.10-alpine

# 安裝基礎工具 (包含 wget 用於下載)
RUN apk add --no-cache \
    curl \
    bash \
    procps \
    libffi-dev \
    openssl-dev \
    gcc \
    musl-dev \
    python3-dev \
    wget

# 強制安裝特定「脆弱版本」的 sudo (CVE-2019-14287)
# 直接從 Alpine 3.12 封存檔下載 apk 檔案，避開版本衝突
RUN wget http://dl-cdn.alpinelinux.org/alpine/v3.12/main/x86_64/sudo-1.9.0-r0.apk -O /tmp/sudo.apk && \
    apk add --no-cache --allow-untrusted /tmp/sudo.apk && \
    rm /tmp/sudo.apk

# 建立一般使用者 neo-user
RUN adduser -D -s /bin/bash neo-user

# 設定工作目錄
WORKDIR /app

# 複製依賴項並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY . .

# 設定屬主權限
RUN chown -R neo-user:neo-user /app

# 設定 flag.sh (放在 root 目錄)
RUN cp flag.sh /root/flag.sh && \
    chmod 755 /root/flag.sh && \
    mkdir -p /home/neo-user && \
    touch /home/neo-user/user_flag.txt && \
    chown neo-user:neo-user /home/neo-user/user_flag.txt

# 配置 Sudo 權限：模擬 CVE-2019-14287 脆弱配置
# 規則：允許 neo-user 以除了 root 以外的任何使用者身份執行 bash 與 flag.sh
# 漏洞利用點：sudo -u#-1 /bin/bash
RUN echo "Defaults:neo-user !requiretty" >> /etc/sudoers && \
    echo "neo-user ALL=(ALL, !root) NOPASSWD: /bin/bash, /root/flag.sh" >> /etc/sudoers

# 暴露埠號
EXPOSE 8080

# 以 neo-user 啟動
USER neo-user

# 啟動應用程式
CMD ["python", "app.py"]
