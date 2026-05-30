#!/bin/bash
# 直接從參數讀取學號 (漏洞點)
STUDENT_ID=$1

if [ -z "$STUDENT_ID" ]; then
    echo "錯誤：請提供學號作為參數。"
    exit 1
fi

# 故意設計的漏洞點：使用 eval 處理參數，允許指令拼接
eval "STUDENT_INPUT=$STUDENT_ID"

echo "正在為學號 $STUDENT_INPUT 生成安全識別碼..."

# 為 User 和 Root 生成不同的雜湊值
USER_HASH=$(echo -n "USER_$STUDENT_INPUT" | md5sum | cut -d" " -f1)
ROOT_HASH=$(echo -n "ROOT_$STUDENT_INPUT" | md5sum | cut -d" " -f1)

USER_FLAG="FLAG{$USER_HASH}"
ROOT_FLAG="ROOT_FLAG{$ROOT_HASH}"

# 寫入 Flag 檔案
echo -n "$USER_FLAG" > /home/neo-user/user_flag.txt
echo -n "$ROOT_FLAG" > /root/root_flag.txt

# 確保權限正確
chown neo-user:neo-user /home/neo-user/user_flag.txt
chmod 644 /home/neo-user/user_flag.txt
chmod 600 /root/root_flag.txt

echo "Flag 生成成功！"
