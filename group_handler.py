import requests

# متغیر برای ذخیره آخرین پیامی که پردازش کردیم (جلوگیری از پاسخ تکراری)
last_processed_update_id = 0

def process_group_messages(bot_token, latest_data):
    global last_processed_update_id
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    # اگر اولین بار است، فقط آخرین پیام را بگیر، در غیر این صورت پیام‌های جدیدتر از آخرین بار را بگیر
    params = {'timeout': 1}
    if last_processed_update_id != 0:
        params['offset'] = last_processed_update_id + 1
    else:
        params['offset'] = -1 # فقط آخرین پیام برای شروع

    try:
        response = requests.get(url, params=params, timeout=5).json()
        
        if not response.get("result"):
            return

        for update in response["result"]:
            update_id = update["update_id"]
            
            # آپدیت کردن آخرین شناسه پیام
            if update_id > last_processed_update_id:
                last_processed_update_id = update_id
            
            # بررسی اینکه پیام متنی باشد
            if "message" not in update: continue
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip() # متن پیام
            
            # --- منطق پاسخگویی به کلمات کلیدی ---
            response_text = None
            
            # ۱. دلار یا تتر
            if any(k in text for k in ["دلار", "تتر", "usdt", "USDT"]):
                p = latest_data['USDT']['price']
                c = latest_data['USDT']['change']
                icon = "🟢" if c >= 0 else "🔴"
                response_text = f"💵 <b>قیمت لحظه‌ای تتر:</b>\n\n💰 {p:,} تومان\n{icon} تغییر ۲۴ ساعته: {c}%"

            # ۲. طلا یا سکه
            elif any(k in text for k in ["طلا", "سکه", "gold"]):
                p = latest_data['GOLD_18']['price']
                c = latest_data['GOLD_18']['change']
                response_text = f"🟡 <b>طلای ۱۸ عیار (گرم):</b>\n\n💰 {p:,} تومان\n⚖️ انس جهانی: {c}% تغییر"

            # ۳. بیت کوین
            elif any(k in text for k in ["بیت", "btc", "BTC", "bitcoin"]):
                usd = latest_data['BTC_USD']['price']
                tmn = latest_data['BTC_TMN']
                c = latest_data['BTC_USD']['change']
                icon = "🟢" if c >= 0 else "🔴"
                response_text = f"₿ <b>بیت‌کوین (Bitcoin):</b>\n\n🇺🇸 ${usd:,}\n🇮🇷 {tmn:,} تومان\n{icon} تغییر: {c}%"

            # ارسال پاسخ اگر کلمه کلیدی پیدا شد
            if response_text:
                send_reply(bot_token, chat_id, response_text, message["message_id"])
                return f"Replied to keyword in chat {chat_id}"

    except Exception:
        pass
    return None

def send_reply(bot_token, chat_id, text, reply_to_msg_id):
    """ارسال پاسخ به صورت Reply روی پیام کاربر"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'reply_to_message_id': reply_to_msg_id # این خط باعث میشه روی پیام طرف ریپلای کنه
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass