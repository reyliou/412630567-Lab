FROM ubuntu:18.04

# 設定非互動模式避免安裝時卡住
ENV DEBIAN_FRONTEND=noninteractive

# 安裝 Python 3.10 (使用 deadsnakes PPA) 與必要工具
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.10 \
    python3.10-distutils \
    python3.10-dev \
    sudo \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 安裝與配置 pip for Python 3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# 建立一般使用者 neo-user
RUN useradd -m -s /bin/bash neo-user

# 設定工作目錄
WORKDIR /app

# 複製依賴項並安裝
COPY requirements.txt .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

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

# 啟動應用程式 (使用新安裝的 python3.10)
CMD ["python3.10", "app.py"]
