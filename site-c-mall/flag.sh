#!/bin/bash
# 讀取學號
read -r STUDENT_ID

# 故意設計的漏洞點：使用 eval 或不安全的變數引用，允許指令拼接
# 玩家可以輸入 "412630567 ; cat /root/root_flag.txt"
eval "STUDENT_INPUT=$STUDENT_ID"

if [ -z "$STUDENT_INPUT" ]; then
    echo "請提供學號"
    exit 1
fi

# 計算 Hash
HASH=$(echo -n "NEO_$STUDENT_INPUT" | md5sum | cut -d" " -f1)
USER_FLAG="FLAG{$HASH}"
ROOT_FLAG="ROOT_FLAG{$HASH}"

# 寫入 Flag 檔案
echo -n "$USER_FLAG" > /home/neo-user/user_flag.txt
echo -n "$ROOT_FLAG" > /root/root_flag.txt

# 確保權限正確
chown neo-user:neo-user /home/neo-user/user_flag.txt
chmod 644 /home/neo-user/user_flag.txt
chmod 600 /root/root_flag.txt
