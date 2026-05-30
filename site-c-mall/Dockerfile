FROM python:3.11-slim

WORKDIR /app

# 安裝必要套件
RUN apt-get update && apt-get install -y sudo coreutils && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 建立 neo-user 並設定家目錄
RUN useradd -m neo-user

COPY . .

# 設定 Flag 生成腳本
RUN mv /app/flag.sh /root/flag.sh && \
    chmod +x /root/flag.sh

# 設定 Sudo 權限：允許 neo-user 免密碼執行 flag.sh (故意留下指令拼接漏洞的空間)
RUN echo "neo-user ALL=(ALL) NOPASSWD: /root/flag.sh" >> /etc/sudoers

# 確保 /app 目錄權限
RUN mkdir -p /app/config && chown -R neo-user:neo-user /app

# 切換到 neo-user 執行
USER neo-user

EXPOSE 8080

CMD ["python", "app.py"]
