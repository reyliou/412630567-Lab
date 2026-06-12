FROM python:3.10-alpine

# 安裝系統工具與特定的「脆弱版本」sudo (CVE-2019-14287)
# 透過指定 Alpine v3.12 的存儲庫安裝 sudo 1.9.0-r0
RUN apk add --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/v3.12/main \
    sudo=1.9.0-r0 && \
    apk add --no-cache \
    curl \
    bash \
    procps \
    libffi-dev \
    openssl-dev \
    gcc \
    musl-dev \
    python3-dev

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
