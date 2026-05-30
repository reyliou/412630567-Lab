import os
import sys
import json
import base64
import jinja2
from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

# 應用程式配置
app_config = {
    "VENDOR_CREDENTIALS": {"username": "neo_vendor", "password": "VendorPass8899"}
}

# 產品資料
PRODUCTS = [
    {
        "id": 0, 
        "name": "測試用-自動化報表系統", 
        "description": "【內部組件】此模組僅供開發團隊進行壓力測試。如遇到連線問題，請開發人員前往 /system-status/ 檢查節點健康度。", 
        "price": "0 元", 
        "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 1, 
        "name": "專業級網路交換器 Pro", 
        "description": "高效能 24 埠 GbE 管理型交換器，提供穩定的企業網路環境。", 
        "price": "12,500 元",
        "image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 2, 
        "name": "工業級安全監控攝影機", 
        "description": "配備 4K 高畫質與紅外線夜視功能，全天候守護企業安全。", 
        "price": "8,800 元",
        "image": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 3, 
        "name": "高效能伺服器主機殼", 
        "description": "採用超輕質鋁合金打造，具備優異的散熱與結構支撐能力。", 
        "price": "5,200 元",
        "image": "https://images.unsplash.com/photo-1591405351990-4726e331f141?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": 4, 
        "name": "企業級旗艦工作站", 
        "description": "搭載最新處理器，具備強大的運算與多工處理能力，適合專業人士。", 
        "price": "68,000 元",
        "image": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?auto=format&fit=crop&w=800&q=80"
    }
]

# 載入用戶資料
USERS_FILE = os.path.join(os.path.dirname(__file__), 'config', 'users.json')

def load_users():
    try:
        if not os.path.exists(USERS_FILE):
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            default_users = [
                {"id": 0, "username": "admin", "password": "password123", "role": "admin", "email": "admin@example.com"}
            ]
            save_users(default_users)
            return default_users
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving users: {e}")

REVIEWS = {}

# 頁面路由
async def index(request):
    return web.FileResponse('./static/index.html')

async def login_page(request):
    return web.FileResponse('./static/login.html')

async def register_page(request):
    return web.FileResponse('./static/register.html')

async def dashboard_page(request):
    session = await get_session(request)
    if 'username' not in session:
        return web.HTTPFound('/login')
    return web.FileResponse('./static/dashboard.html')

async def product_page(request):
    return web.FileResponse('./static/product.html')

async def cart_page(request):
    session = await get_session(request)
    if 'username' not in session:
        return web.HTTPFound('/login')
    return web.FileResponse('./static/cart.html')

async def privacy_page(request):
    return web.FileResponse('./static/privacy.html')

async def terms_page(request):
    return web.FileResponse('./static/terms.html')

async def admin_portal_page(request):
    session = await get_session(request)
    if session.get('role') != 'admin':
        return web.HTTPFound('/login')
    return web.FileResponse('./static/admin_panel.html')

async def seller_portal_page(request):
    session = await get_session(request)
    if session.get('role') not in ['seller', 'admin']:
        return web.HTTPFound('/login')
    return web.FileResponse('./static/seller_portal.html')

# API 路由
async def get_products(request):
    # 只返回 ID > 0 的產品，隱藏 ID 0
    visible_products = [p for p in PRODUCTS if p['id'] > 0]
    return web.json_response(visible_products)

async def get_product_detail(request):
    try:
        product_id = int(request.match_info['id'])
    except (ValueError, KeyError):
        return web.json_response({"error": "Invalid product ID"}, status=400)
    
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        return web.json_response(product)
    return web.json_response({"error": "Product not found"}, status=404)

async def login_api(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"success": False, "message": "無效的請求"}, status=400)
        
    username = data.get("username")
    password = data.get("password")
    
    users = load_users()
    user = next((u for u in users if u['username'] == username and u['password'] == password), None)
    
    if user:
        session = await get_session(request)
        session["username"] = username
        session["role"] = user.get("role", "user")
        return web.json_response({"success": True, "role": session["role"]})
    return web.json_response({"success": False, "message": "帳號或密碼錯誤"}, status=401)

async def register_api(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"success": False, "message": "無效的請求"}, status=400)
        
    username = data.get("username")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    email = data.get("email")
    
    if not username or not password or not email or not confirm_password:
        return web.json_response({"success": False, "message": "所有欄位均為必填"}, status=400)
    
    if password != confirm_password:
        return web.json_response({"success": False, "message": "兩次輸入的密碼不符"}, status=400)
    
    users = load_users()
    if any(u['username'] == username for u in users):
        return web.json_response({"success": False, "message": "此帳號已被註冊"}, status=400)
    
    new_user = {
        "id": len(users),
        "username": username,
        "password": password,
        "role": "user",
        "email": email
    }
    users.append(new_user)
    save_users(users)
    
    return web.json_response({"success": True, "message": "註冊成功"})

async def logout_api(request):
    session = await get_session(request)
    session.invalidate()
    return web.json_response({"success": True})

async def get_user_me(request):
    session = await get_session(request)
    if "username" in session:
        return web.json_response({"username": session["username"], "role": session.get("role")})
    return web.json_response({"error": "Unauthorized"}, status=401)

async def add_to_cart(request):
    session = await get_session(request)
    if "username" not in session:
        return web.json_response({"error": "請先登入"}, status=401)
        
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "無效的請求"}, status=400)
        
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1) # Get quantity, default to 1
    
    if product_id is None:
        return web.json_response({"error": "缺少產品 ID"}, status=400)
        
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return web.json_response({"error": "數量必須大於 0"}, status=400)
    except ValueError:
        return web.json_response({"error": "無效的數量"}, status=400)
    
    if "cart" not in session:
        session["cart"] = []
    
    # 確保 session 被標記為已修改
    cart = list(session["cart"])
    # Append the product ID 'quantity' times
    for _ in range(quantity):
        cart.append(product_id)
    session["cart"] = cart
    
    return web.json_response({"success": True, "cart_count": len(session["cart"])})

async def get_cart(request):
    session = await get_session(request)
    if "username" not in session:
        return web.json_response({"error": "Unauthorized"}, status=401)
        
    cart_ids = session.get("cart", [])
    cart_items = [p for p in PRODUCTS if p['id'] in cart_ids]
    return web.json_response(cart_items)

async def checkout_api(request):
    session = await get_session(request)
    if "username" not in session:
        return web.json_response({"error": "Unauthorized"}, status=401)
    
    session["cart"] = []
    return web.json_response({"success": True, "message": "訂單已成功送出"})

async def get_product_reviews(request):
    try:
        product_id = request.match_info['id']
    except KeyError:
        return web.json_response({"error": "Missing product ID"}, status=400)
    
    return web.json_response(REVIEWS.get(product_id, []))

async def add_product_review(request):
    session = await get_session(request)
    if "username" not in session:
        return web.json_response({"error": "請先登入"}, status=401)
        
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "無效的請求"}, status=400)
        
    product_id = data.get("product_id")
    comment = data.get("comment")
    if not product_id or not comment:
        return web.json_response({"error": "缺少產品 ID 或評論內容"}, status=400)
    
    product_id = str(product_id)
    
    # SSTI 漏洞點：使用 Jinja2 渲染評論，並傳入 app_config
    try:
        template = jinja2.Template(comment)
        processed_comment = template.render(config=app_config)
    except Exception as e:
        processed_comment = f"[Template Error]: {str(e)}"
    
    if product_id not in REVIEWS:
        REVIEWS[product_id] = []
    
    review_entry = {
        "username": session["username"],
        "comment": processed_comment
    }
    REVIEWS[product_id].append(review_entry)
    
    return web.json_response({"success": True, "review": review_entry})

async def seller_upload_api(request):
    session = await get_session(request)
    if session.get('role') not in ['seller', 'admin']:
        return web.json_response({"error": "Forbidden"}, status=403)
    
    reader = await request.multipart()
    field = await reader.next()
    if field.name != 'file':
        return web.json_response({"error": "Invalid field"}, status=400)
    
    filename = field.filename
    # Weak server-side validation: only check Content-Type
    content_type = field.headers.get('Content-Type')
    if content_type != 'application/pdf':
        return web.json_response({"error": "Only PDF files are allowed"}, status=400)
    
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)
            
    # Disclosure of absolute path
    abs_path = os.path.abspath(file_path)
    return web.json_response({
        "success": True, 
        "message": f"File saved to {abs_path}",
        "url": f"/assets-library/uploads/{filename}"
    })

async def seller_diag_api(request):
    session = await get_session(request)
    if session.get('role') not in ['seller', 'admin']:
        return web.json_response({"error": "Forbidden"}, status=403)
    
    try:
        data = await request.json()
        command = data.get("command")
        if not command:
            return web.json_response({"error": "缺少指令"}, status=400)
        
        # 漏洞點：指令注入 (Command Injection)
        import subprocess
        # 強制使用 /bin/bash 執行，以支援 <<< 和其他進階語法
        process = subprocess.Popen(['/bin/bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=5)
        
        output = stdout + stderr
        return web.json_response({"success": True, "output": output if output else "(無輸出內容)"})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def system_info(request):
    return web.json_response({
        "server_root": "/app/site-c-mall",
        "system_status": "active",
        "version": "2.4.1-enterprise",
        "internal_notes": "All systems operational. Seller maintenance account is managed via Admin Panel."
    })

def make_app():
    # 使用 Fernet.generate_key() 生成 32 位元金鑰並進行 urlsafe_b64encode
    # 這裡我們硬編碼一個合法的 32 位元金鑰（b64 格式）
    secret_key = b'p5H8_8m_G8v9_f8_W9-L1A_mN-0B1C2D3E4F5G6H7I8='
    
    app = web.Application()
    
    # 設定 Session
    setup(app, EncryptedCookieStorage(base64.urlsafe_b64decode(secret_key)))
    
    app.add_routes([
        web.get('/', index),
        web.get('/login', login_page),
        web.get('/register', register_page),
        web.get('/dashboard', dashboard_page),
        web.get('/product/{id}', product_page),
        web.get('/cart', cart_page),
        web.get('/privacy', privacy_page),
        web.get('/terms', terms_page),
        web.get('/admin-portal', admin_portal_page),
        web.get('/seller-portal', seller_portal_page),
        
        web.get('/api/products', get_products),
        web.get('/api/products/{id}', get_product_detail),
        web.get('/api/reviews/{id}', get_product_reviews),
        web.post('/api/reviews/add', add_product_review),
        web.post('/api/login', login_api),
        web.post('/api/register', register_api),
        web.post('/api/logout', logout_api),
        web.get('/api/user/me', get_user_me),
        web.post('/api/cart/add', add_to_cart),
        web.get('/api/cart', get_cart),
        web.post('/api/checkout', checkout_api),
        web.post('/api/seller/upload', seller_upload_api),
        web.post('/api/seller/diag', seller_diag_api),
        web.get('/api/system/info', system_info),
    ])
    
    # CVE-2024-23334 漏洞點 - 保持原樣
    app.router.add_static('/assets-library/', path='./static', follow_symlinks=True)
    
    return app

if __name__ == '__main__':
    print("\n🚀 NEO-MALL 線上商城：企業級版本已啟動")
    print("🌐 服務位址: http://localhost:8080")
    sys.stdout.flush()
    web.run_app(make_app(), host='0.0.0.0', port=8080)

