# Canva 簡報內容稿：CVE-2024-23334 aiohttp Path Traversal

## Canva 生成 Prompt

請建立一份 16:9、約 12 頁的資安課堂報告簡報，主題是「CVE-2024-23334：aiohttp 靜態路由 Path Traversal 漏洞分析與 Lab 展示」。視覺風格使用深色科技感背景、青綠色與橘色作為重點色、簡潔的攻擊鏈流程圖、程式碼片段、風險矩陣與修補檢核表。受眾是資安課程老師與同學。內容要包含漏洞類型定義、CVE 影響、攻擊流程、修補與預防方式、開發實務最佳實踐、參考資料。不要使用過度花俏的裝飾，重點放在清楚、專業、可展示。

---

## Slide 1：封面

**標題**：CVE-2024-23334：aiohttp Path Traversal 漏洞分析  
**副標題**：以 NEO-MALL CTF Lab 展示任意檔案讀取攻擊鏈  
**頁面重點**：

* 開源專案：aiohttp
* 漏洞類型：Path Traversal / Directory Traversal
* CWE：CWE-22
* Lab 版本：aiohttp 3.9.1

**視覺建議**：深色背景，中央放 CVE 編號，右側放簡化架構圖：User -> Gateway -> aiohttp app -> sensitive files。

**講稿提示**：本次報告選擇 2024 年公開的 aiohttp CVE-2024-23334，透過自建 CTF lab 重現靜態路由設定錯誤導致的任意檔案讀取。

---

## Slide 2：專案目標與報告範圍

**標題**：本專案要回答三個問題

**頁面重點**：

* 這個漏洞類型是什麼？
* CVE-2024-23334 對 aiohttp 造成什麼影響？
* 開發者應如何修補、預防並建立更安全的實務流程？

**視覺建議**：三欄式，每欄用簡短問句與圖示：Definition、Impact、Defense。

**講稿提示**：簡報會先介紹 Path Traversal 的定義，再說明 aiohttp 的 CVE 細節，最後透過 lab 攻擊流程與修補建議收束。

---

## Slide 3：漏洞類型定義：Path Traversal / CWE-22

**標題**：Path Traversal 讓攻擊者走出預期目錄

**頁面重點**：

* 應用程式使用外部輸入組合檔案路徑
* 未限制路徑必須留在指定根目錄內
* 攻擊者可用 `../` 或特殊路徑繞過限制
* 結果可能是讀取設定檔、金鑰、備份、原始碼或 flag

**視覺建議**：左側放「合法路徑」資料夾圖，右側放「../../config/secret_flag.txt」穿越到敏感目錄的路徑箭頭。

**講稿提示**：這類漏洞的核心不是單純有 `../`，而是伺服器沒有確認最後解析出的檔案仍在允許目錄內。

---

## Slide 4：CVE-2024-23334 背景

**標題**：aiohttp 靜態路由設定錯誤導致任意檔案讀取

**頁面重點**：

* aiohttp 是 Python 非同步 HTTP client/server framework
* 當作 Web server 並設定 static routes 時，需要指定靜態檔案根目錄
* 若啟用 `follow_symlinks=True`，未正確驗證讀取路徑是否仍位於根目錄內
* 修補版本：aiohttp 3.9.2+

**程式碼片段**：

```python
app.router.add_static(
    "/assets-library/",
    path="./static",
    follow_symlinks=True
)
```

**視覺建議**：程式碼片段放中央，`follow_symlinks=True` 用橘色框標記。

**講稿提示**：本 lab 固定使用 aiohttp 3.9.1，並保留 `follow_symlinks=True`，讓漏洞可被穩定展示。

---

## Slide 5：CVE 影響與風險

**標題**：攻擊者不需要登入即可讀取敏感檔案

**頁面重點**：

* NVD CVSS v3.1：7.5 HIGH
* 攻擊向量：Network
* 權限需求：None
* 使用者互動：None
* 主要衝擊：Confidentiality High

**風險說明**：

* 可能讀取應用程式設定檔
* 可能取得憑據、token、備份提示
* 可能作為後續 RCE 或提權的情報來源

**視覺建議**：做一個 2x3 風險矩陣或 KPI rail，顯示 AV:N、PR:N、UI:N、C:H。

**講稿提示**：這個 CVE 的直接影響是資料機密性破壞，但在真實攻擊鏈中，外洩資訊常常會成為下一階段攻擊的跳板。

---

## Slide 6：Lab 環境架構

**標題**：NEO-MALL Lab 模擬多服務企業環境

**頁面重點**：

* `nginx-gateway`：主要入口，對外 port 8080
* `neo-mall`：aiohttp 電商服務，後端 port 8081
* `neo-status`：狀態頁
* `neo-dev`：開發者入口與部署筆記
* `neo-ftp`：匿名 FTP 備份服務

**視覺建議**：畫一張架構圖：Attacker -> Gateway -> Mall / Status / Dev / FTP，並標註 CVE 目標在 Mall 的 `/assets-library/`。

**講稿提示**：Lab 不是單點漏洞展示，而是模擬真實攻擊中，攻擊者會從一個小資訊外洩逐步串接到核心漏洞。

---

## Slide 7：攻擊鏈總覽

**標題**：從低權限資訊收集到敏感檔案讀取

**攻擊流程**：

1. BOLA 讀取隱藏產品 ID
2. 弱口令登入 `guest/guest123`
3. SSTI 測試 `{{ 7 * 7 }}`
4. SSTI 讀取 `config.VENDOR_CREDENTIALS`
5. 賣家登入 `neo_vendor/VendorPass8899`
6. 不安全上傳洩漏絕對路徑
7. FTP 備份提示洩漏 flag 位置
8. CVE-2024-23334 讀取 `secret_flag.txt`

**視覺建議**：水平攻擊鏈 timeline，每一步用不同顏色標示：Recon、Foothold、Exfiltration、CVE、Impact。

**講稿提示**：這頁先讓觀眾知道完整故事線，後面再拆解關鍵技術點。

---

## Slide 8：核心利用方式

**標題**：`--path-as-is` 保留惡意路徑並直打 aiohttp

**Payload**：

```bash
curl --path-as-is \
  http://localhost:8081/assets-library/../../config/secret_flag.txt
```

**頁面重點**：

* `assets-library` 是 aiohttp 靜態路由
* `../../config/secret_flag.txt` 嘗試離開 `static` 目錄
* 直連 port 8081 可避開 gateway 對 URI 的規範化處理
* 成功後可讀取 `FLAG{cve_2024_23334_path_traversal_mastered}`

**視覺建議**：左側放 terminal command，右側放「static -> config」的穿越箭頭圖。

**講稿提示**：這裡是本報告的主 CVE 展示。攻擊的關鍵是讓後端實際收到包含 `../` 的路徑，並利用 vulnerable static route 解析到敏感檔案。

---

## Slide 9：延伸攻擊與風險放大

**標題**：任意檔案讀取常是攻擊鏈的情報入口

**頁面重點**：

* SSTI 外洩賣家憑據
* FTP 洩漏部署與檔案位置提示
* 賣家診斷工具存在 command injection
* Gateway 偵錯介面存在 Lua `loadstring()` RCE

**風險總結**：

* 單一 CVE 可造成敏感資料外洩
* 多個低/中風險弱點串接後，可升級成完整入侵
* 內部測試功能與 debug 後門是常見放大器

**視覺建議**：中心放 CVE-2024-23334，周圍放四個風險節點：SSTI、FTP、Command Injection、Lua RCE。

**講稿提示**：安全評估不能只看單一漏洞，要看它是否能和其他設計失誤串聯。

---

## Slide 10：修補與預防方式

**標題**：修補不只升級版本，也要移除危險配置

**修補清單**：

* 升級 aiohttp 至 3.9.2 或更新版本
* 停用 `follow_symlinks=True`
* 靜態資源交給 Nginx 等 reverse proxy 處理
* 路徑解析後檢查 realpath 是否仍在允許根目錄
* 避免將後端服務直接暴露在外部網路
* 不在回應中洩漏伺服器絕對路徑

**視覺建議**：Checklist 形式，前三項用最醒目的顏色標記為「必做」。

**講稿提示**：官方 advisory 也提醒，即使升級後仍建議避免在對外服務使用 `follow_symlinks=True`，因為它本身容易造成危險設定。

---

## Slide 11：開發實務最佳實踐

**標題**：把防線放進開發流程，而不是只靠事後修補

**最佳實踐**：

* 使用 SCA 工具掃描依賴套件 CVE
* CI/CD 中加入 dependency check 與版本鎖定
* 建立安全預設值：debug off、least privilege、deny by default
* 測試帳號、維護 API、診斷工具不得進入正式環境
* 對所有檔案存取做 allowlist 與 canonical path 檢查
* 使用 secret manager 管理密鑰，不放在 repo 或靜態目錄附近
* 定期做 threat modeling，檢查多弱點串接風險

**視覺建議**：流程圖：Design -> Code -> CI -> Deploy -> Monitor，每階段放一個安全控制。

**講稿提示**：這個 lab 裡的問題橫跨依賴版本、危險設定、憑據管理、debug 介面與網路暴露，因此修補也必須是流程化的。

---

## Slide 12：結論與參考資料

**標題**：CVE-2024-23334 的核心教訓

**結論**：

* Path Traversal 的本質是「未限制解析後路徑」
* aiohttp 在 `follow_symlinks=True` 靜態路由設定下曾存在任意檔案讀取風險
* CVE 的直接影響是機密性破壞，但可能串接成完整攻擊鏈
* 修補策略要同時包含升級、移除危險設定、網路隔離與安全開發流程

**參考資料**：

* GitHub Security Advisory: https://github.com/aio-libs/aiohttp/security/advisories/GHSA-5h86-8mv2-jq9f
* NVD CVE Detail: https://nvd.nist.gov/vuln/detail/CVE-2024-23334
* aiohttp Patch PR: https://github.com/aio-libs/aiohttp/pull/8079
* MITRE CWE-22: https://cwe.mitre.org/data/definitions/22.html

**視覺建議**：左側放 4 句 takeaways，右側放 QR code 區塊或參考資料清單。

**講稿提示**：最後強調這不是單純版本問題，而是危險設定和缺少安全邊界檢查共同造成的漏洞。

