# 專業滲透測試報告：NEO-MALL 企業級環境 (SSTI 漏洞鏈版)

## 1. 執行摘要 (Executive Summary)
本報告詳述了針對 NEO-MALL 企業級電商系統進行的連鎖漏洞滲透測試。主題 CVE 為 **CVE-2024-23334**，漏洞類型為 **Path Traversal / Directory Traversal (CWE-22)**，目標開源專案為 Python 非同步 Web 框架 **aiohttp**。本 lab 以 `aiohttp==3.9.1` 和 `follow_symlinks=True` 的靜態檔案路由重現任意檔案讀取風險，並串聯弱口令、SSTI、不安全上傳、FTP 資訊外洩與偵錯介面 RCE，展示攻擊者如何逐步取得敏感資料與系統控制權。

## 2. CVE 與漏洞類型
*   **CVE 編號**：CVE-2024-23334
*   **受影響專案**：aiohttp，開源 Python HTTP client/server framework
*   **受影響版本**：aiohttp 3.9.1 與其他未修補版本；本環境固定使用 `aiohttp==3.9.1`
*   **修補版本**：3.9.2+
*   **漏洞類型定義**：Path Traversal 是指應用程式使用外部輸入組合檔案路徑時，沒有正確限制路徑必須留在預期根目錄內，導致攻擊者可用 `../` 等特殊路徑元素讀取根目錄外的檔案。
*   **本環境漏洞點**：`site-c-mall/app.py` 中 `app.router.add_static('/assets-library/', path='./static', follow_symlinks=True)`。
*   **影響**：未授權攻擊者可透過靜態檔案路由讀取應用程式目錄外的敏感檔案，例如設定檔、備份提示或 flag。

## 3. 漏洞鏈 (Attack Chain)

### 第一階段：BOLA 資訊外洩 (Broken Object Level Authorization - CWE-639)
*   **漏洞類型**：CWE-639 (失效的物件層級授權)
*   **動作**：嘗試存取前端介面未公開的產品 ID (`/api/products/0`)。
*   **發現內容**：獲取隱藏產品描述：「【內部組件】此模組僅供開發團隊進行壓力測試。如遇到連線問題，請開發人員前往 /system-status/ 檢查節點健康度。」
*   **目的**：挖掘系統隱藏路徑與開發者預留的監控接口。

### 第二階段：身分突破 (Initial Foothold)
*   **漏洞類型**：CWE-521 (弱口令)
*   **動作**：利用獲取的資訊與常見測試帳號進行登入。
*   **憑據**：`guest / guest123`。
*   **目的**：獲取基本的系統互動權限，以便存取產品評論功能並進行進一步攻擊。

### 第三階段：SSTI 模板注入 (Server-Side Template Injection - CWE-1336)
*   **位置**：產品詳情頁面 (`/product/{id}`) 的「產品評論」系統。
*   **漏洞原理**：伺服器使用 Jinja2 引擎來處理評論預覽。開發者為了提供動態排版功能，不安全地將用戶輸入直接傳入模板引擎的渲染函數：`jinja2.Template(user_input).render(config=app_config)`。
*   **測試 Payload**：`{{ 7 * 7 }}` -> 伺服器即時回傳 `49`，確認漏洞存在。

### 第四階段：資訊外洩 (Information Exfiltration)
*   **動作**：利用 SSTI 讀取伺服器配置 (`config`)。
*   **Payload**：`系統維護指令：{{ config['VENDOR_CREDENTIALS'] }}`
*   **即時收穫**：伺服器直接在評論頁面噴出賣家憑據：`{'username': 'neo_vendor', 'password': 'VendorPass8899'}`。
*   **結果**：攻擊者獲得了「賣家」(Seller) 權限。

### 第五階段：不安全的文件上傳 (Insecure File Upload - CWE-434)
*   **位置**：`/seller-portal` (賣家管理中心) 的手冊上傳功能。
*   **繞過手法**：使用 Burp Suite 攔截上傳請求，將檔案的 `Content-Type` 偽造為 `application/pdf`。
*   **關鍵情報**：成功上傳後，後端 API 為了方便開發者調試，在回應中洩漏了文件的**絕對路徑**：`/app/static/uploads/file.txt`。

### 第六階段：FTP 敏感資訊外洩 (FTP Sensitive Data Exposure)
*   **發現**：掃描發現內部測試環境開啟了匿名 FTP 服務 (`port 21`)。
*   **動作**：利用匿名登入 (`anonymous/anonymous`) 存取 `backup_logs` 資料夾。
*   **發現內容**：下載並閱讀 `server_migration.bak`，其中記錄了：「2024年系統安全審計：主要 flag 已移至 /app/config/secret_flag.txt，以避免透過通用靜態路由意外流出。請勿對此資料夾開放權限。」
*   **目的**：精確鎖定 Flag 的位置與檔名，避免在大規模檔案系統中盲目嘗試。

### 第七階段：路徑穿越致命打擊 (Path Traversal - CVE-2024-23334)
*   **核心漏洞**：`aiohttp 3.9.1` 在 `follow_symlinks=True` 的配置下存在路徑遍歷。
*   **滲透技巧**：由於 Port 8080 (Nginx) 網關具有嚴格的 URI 規範化檢查，會攔截 `..` 請求。攻擊者發現系統為了開發者便利，將後端服務直接暴露在 Port 8081 上，繞過了網關安全限制。
*   **利用方式**：結合前一階段獲得的絕對路徑與 FTP 洩漏的檔名，向 Port 8081 發送惡意請求。
*   **終極 Payload**：
    `curl --path-as-is http://localhost:8081/assets-library/../config/secret_flag.txt`
*   **結果**：成功獲取終極 Flag。


### 延伸攻擊一：指令注入與權限提升 (Command Injection & PrivEsc - CWE-78)
> 此段為非主 CVE 的延伸風險，用於展示任意檔案讀取取得情報後，如何串接其他設計失誤擴大影響。
*   **位置**：`/seller-portal` 的「系統診斷工具」。
*   **漏洞原理**：系統允許賣家以 `sudo` 權限執行 `/root/flag.sh`。該腳本在處理輸入參數時使用了危險的 `eval` 函數，且後端診斷工具被配置為使用 `/bin/bash` 執行指令。
*   **提權路徑**：攻擊者可以構造包含分號 (`;`) 的參數，利用 `eval` 的特性達成 RCE。
*   **利用方式**：在診斷工具中輸入：
    `sudo /root/flag.sh '412630567 ; id'`
*   **結果**：伺服器回傳 `uid=0(root)`，證實成功取得最高權限。

### 延伸攻擊二：讀取雙重動態 Flag (Flag Exfiltration)
*   **動作**：利用已取得的 Root 權限，讀取受系統保護的 Flag 檔案。
*   **讀取 User Flag**：
    `sudo /root/flag.sh '412630567 ; cat /home/neo-user/user_flag.txt'`
*   **讀取 Root Flag**：
    `sudo /root/flag.sh '412630567 ; cat /root/root_flag.txt'`
*   **技術亮點**：系統為不同權限等級的 Flag 設計了獨立的加鹽雜湊 (Salted Hash) 邏輯，確保 User Flag 與 Root Flag 內容完全不同，模擬真實 CTF 的多層次挑戰。

### 延伸攻擊三：Nginx/Lua 後門 RCE (CWE-94)
> 此段同樣不是 CVE-2024-23334 本身，而是透過前述資訊外洩找到的內部偵錯介面。
*   **漏洞類型**：CWE-94 (程式碼注入)
*   **發現方式**：透過 CVE-2024-23334 讀取 `site-b-dev` 的部署筆記，發現隱藏的偵錯介面。
*   **漏洞原理**：開發者在 OpenResty/Nginx 網關中留下了用於系統診斷的 Lua 後門。該介面直接將 HTTP 標頭 `X-NEO-DEBUG` 的內容傳入 `loadstring()` 並執行，導致嚴重的 RCE。
*   **利用方式**：
    `curl -H "X-NEO-DEBUG: ngx.say(os.execute('whoami'))" http://localhost:8080/api/debug-system`
*   **目的**：在網關層級獲取作業系統控制權，繞過應用程式邏輯。

## 4. 防禦修補建議 (Remediation)
1.  **SSTI**：絕對不可將用戶輸入直接作為模板字串傳入。應使用靜態模板並將用戶輸入作為變數傳遞。
2.  **檔案上傳**：應實施「白名單後綴檢查」與「魔法位元組 (Magic Bytes)」內容檢測，並避免洩漏伺服器內部路徑。
3.  **CVE-2024-23334**：更新 `aiohttp` 套件至 3.9.2+，並將 `follow_symlinks` 設為 `False`（除非絕對必要且路徑安全）。
4.  **Lua 注入**：嚴禁在生產環境中使用 `loadstring()` 執行來自用戶輸入或 HTTP 標頭的內容。應移除所有偵錯用的後門介面。
5.  **開發實務最佳實踐**：以反向代理伺服器處理靜態資源、在 CI 中加入 SCA 套件弱點掃描、避免將內部管理服務直接暴露到外部網路、所有測試帳密與維護介面都必須在部署前移除。

## 5. 參考資料
*   GitHub Security Advisory: https://github.com/aio-libs/aiohttp/security/advisories/GHSA-5h86-8mv2-jq9f
*   CVE Record: https://www.cve.org/CVERecord?id=CVE-2024-23334
*   aiohttp patch PR: https://github.com/aio-libs/aiohttp/pull/8079
*   MITRE CWE-22: https://cwe.mitre.org/data/definitions/22.html
