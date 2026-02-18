import requests
from datetime import datetime

# --- تنظیمات اختصاصی ادمین ---
ADMIN_USER_ID = 12345678  # آیدی عددی اصلی خودت
SECRET_PASSWORD = "curtis_password" 

def check_admin_commands(bot_token, latest_data):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, params={'offset': -1, 'timeout': 1}, timeout=5).json()
        
        if not response.get("result"): 
            return None

        last_update = response["result"][0]
        if "message" not in last_update:
            return None
            
        message = last_update["message"]
        user_id = message["from"]["id"]
        text = message.get("text", "")

        # --- لایه امنیتی جدید ---
        # اول چک کن فرستنده حتما خودت باشی
        if user_id != ADMIN_USER_ID:
            return None # اگر غریبه بود، کلا نادیده بگیر

        # حالا که مطمئن شدیم خودتی، رمز رو چک کن
        if text.startswith(SECRET_PASSWORD):
            command = text.replace(SECRET_PASSWORD, "").strip().lower()
            
            if command == "status":
                u = latest_data['USDT']['price']
                status_msg = (
                    f"🕹 <b>Curtis Admin Dashboard</b>\n\n"
                    f"💵 تتر: {u:,}\n"
                    f"📊 تغییر ۲۴ ساعته: {latest_data['USDT']['change']}%\n"
                    f"💎 شاخص ۵۰ سنت: {round(u/2):,}\n\n"
                    f"✅ وضعیت: عملیاتی (Live)"
                )
                return status_msg
                
    except Exception:
        return None
    return None

def send_backdoor_response(bot_token, chat_id, text):
    # اینجا chat_id ورودی رو میگیره که همون ADMIN_USER_ID پاس داده شده هست
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}, timeout=5)
    except:
        pass