# 資安專案交付檢核

## 題目選擇

* **主題 CVE**：CVE-2024-23334
* **開源專案**：aiohttp
* **漏洞類型**：Path Traversal / Directory Traversal (CWE-22)
* **Lab 版本**：`site-c-mall/requirements.txt` 固定為 `aiohttp==3.9.1`
* **漏洞觸發點**：`site-c-mall/app.py` 的 `/assets-library/` 靜態路由啟用 `follow_symlinks=True`

## 對應作業要求

| 作業要求 | Repo 內對應內容 |
| --- | --- |
| 完成漏洞介紹簡報 | 可依本檔「簡報建議大綱」製作 |
| 錄製報告影片 | 可依本檔「影片展示流程」錄製 |
| 說明漏洞類型定義 | `writeup.md` 第 2 節 |
| 說明 CVE 影響 | `writeup.md` 第 2 節與第 7 階段 |
| 說明修補與預防 | `writeup.md` 第 4 節 |
| 搭建漏洞環境 | `docker-compose.yml`、各站台資料夾、`site-c-mall/Dockerfile` |
| 展示完整攻擊流程 | `exploit.sh` 與 `writeup.md` 第 3 節 |
| GitHub 上傳建置方式與自寫程式碼 | 上傳整個 `412630567-Lab-main` 目錄 |

## 簡報建議大綱

1. 專案主題與選題理由
2. aiohttp 與 CVE-2024-23334 背景
3. Path Traversal / CWE-22 漏洞類型定義
4. 受影響版本、修補版本與風險
5. Lab 架構圖：Gateway、aiohttp mall、status、dev、FTP
6. 核心漏洞程式碼：`follow_symlinks=True`
7. 攻擊流程：BOLA -> 弱口令 -> SSTI -> 賣家憑據 -> 上傳 -> FTP -> CVE -> PrivEsc/RCE
8. Demo 結果與取得的 flag
9. 修補方式與安全開發最佳實踐
10. 參考資料

## 影片展示流程

1. 執行 `docker compose up --build`
2. 開啟 `http://localhost:8080`，展示 NEO-MALL 入口
3. 讀取 `/api/products/0`，展示隱藏產品資訊
4. 使用 `guest/guest123` 登入
5. 在評論 API 送出 `{{ 7 * 7 }}`，展示 SSTI 回傳 `49`
6. 透過 SSTI 讀取 `config.VENDOR_CREDENTIALS`
7. 使用 `neo_vendor/VendorPass8899` 登入賣家中心
8. 偽造 `Content-Type: application/pdf` 上傳文字檔並取得絕對路徑
9. 讀取 FTP 備份提示 `backup_logs/server_migration.bak`
10. 對 `http://localhost:8081/assets-library/../../config/secret_flag.txt` 發送 `--path-as-is` 請求，展示 CVE-2024-23334 任意檔案讀取
11. 使用賣家診斷工具觸發 `/root/flag.sh` 指令注入，展示 user/root flag
12. 展示 `/api/debug-system` 的 Lua RCE 作為延伸風險

## 自動展示腳本

環境啟動後，可用下列指令跑完整展示：

```bash
chmod +x exploit.sh
./exploit.sh
```

可覆寫目標位址：

```bash
GATEWAY_URL=http://localhost:8080 AIOHTTP_URL=http://localhost:8081 FTP_URL=ftp://localhost ./exploit.sh
```

## 參考資料

* GitHub Security Advisory: https://github.com/aio-libs/aiohttp/security/advisories/GHSA-5h86-8mv2-jq9f
* CVE Record: https://www.cve.org/CVERecord?id=CVE-2024-23334
* aiohttp patch PR: https://github.com/aio-libs/aiohttp/pull/8079
* MITRE CWE-22: https://cwe.mitre.org/data/definitions/22.html
