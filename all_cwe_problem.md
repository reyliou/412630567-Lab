

---

### 1. CWE-284 / CWE-639 — BOLA (Broken Object Level Authorization)
**位置：** `app.py` → `get_product_detail()`
```python
# 只要知道 id=0 就能存取隱藏商品，沒有權限檢查
product = next((p for p in PRODUCTS if p['id'] == product_id), None)
```

---

### 2. CWE-94 — SSTI (Server-Side Template Injection)
**位置：** `app.py` → `add_product_review()`
```python
template = jinja2.Template(comment)  # 直接把使用者輸入當 template 渲染
processed_comment = template.render(config=app_config)
```

---

### 3. CWE-22 — Path Traversal (CVE-2024-23334)
**位置：** `app.py` → `make_app()`
```python
app.router.add_static('/assets-library/', path='./static', follow_symlinks=True)
```
搭配直接暴露的 Port 8081 可繞過 Gateway。

---

### 4. CWE-78 — Command Injection
**位置：** `app.py` → `seller_diag_api()`
```python
process = subprocess.Popen(['/bin/bash', '-c', command], ...)
# command 直接來自使用者輸入，無任何過濾
```

---

### 5. CWE-269 — Improper Privilege Management (CVE-2019-14287)
**位置：** `Dockerfile`
```
neo-user ALL=(ALL, !root) NOPASSWD: /bin/bash, /root/flag.sh
# sudo -u#-1 可繞過 !root 限制
```

---

### 6. CWE-916 / CWE-256 — 密碼以 MD5 儲存 + 明文密碼
**位置：** `credentials.bak`
```
guest: FCF41657F02F88137A1BCF068A32C0A3  ← MD5，無 salt
```
`app.py` 的 `users.json` 則是**明文儲存**密碼（`"password": "password123"`）。

---

### 7. CWE-306 — 內網未授權存取
**位置：** `app.py` → `seller_diag_api()`
```python
if client_ip.startswith('172.') or client_ip.startswith('10.') ...
    is_internal = True
# 內網 IP 直接免登入使用 diag API
```

---

### 8. CWE-615 — 敏感資訊洩漏於 HTML 註解
**位置：** `site-a-status/index.html`
```html
<!-- Internal debug endpoint active at /api/debug-system -->
<!-- Required Header: X-NEO-DEBUG (Lua scripting enabled) -->
```

---

### 9. CWE-98 / CWE-200 — 絕對路徑洩漏
**位置：** `app.py` → `seller_upload_api()`
```python
abs_path = os.path.abspath(file_path)
return web.json_response({"message": f"File saved to {abs_path}"})
```

---

### 總覽

| # | CWE | 名稱 | 對應攻擊階段 |
|---|-----|------|------------|
| 1 | CWE-639 | BOLA | 第一階段 |
| 2 | CWE-94 | SSTI | 第二階段 |
| 3 | CWE-22 | Path Traversal | 第三階段 |
| 4 | CWE-78 | Command Injection | 第五階段 |
| 5 | CWE-269 | Privilege Mismanagement | 第五階段 |
| 6 | CWE-916/256 | 弱密碼儲存 | 第一階段 |
| 7 | CWE-306 | 缺少身份驗證 | 第五階段 |
| 8 | CWE-615 | 敏感資訊洩漏 | 第一階段 |
| 9 | CWE-200 | 路徑資訊洩漏 | 第三階段 |
