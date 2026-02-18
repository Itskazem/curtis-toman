import requests
import schedule
import time
import jdatetime
from datetime import datetime
import random
import json
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.live import Live

# ایمپورت فایل‌های جانبی
from backdoor import check_admin_commands, send_backdoor_response, ADMIN_USER_ID
from group_handler import process_group_messages

try:
    from messages import CURTIS_BRAIN
except ImportError:
    CURTIS_BRAIN = {
        "MORNING": ["سلام گنگستا! بازار باز شد."],
        "HOURLY": ["قیمت جدید رسید."],
        "NOON": ["ظهر بخیر، ناهار خوردی؟"],
        "EVENING": ["عصر شد و بازار هنوز داغه."],
        "CLOSING": ["کرکره‌ها پایین، شب خوش."],
        "ADVICE": ["پولت رو سفت بچسب."]
    }

# --- تنظیمات تلگرام ---
BOT_TOKEN = '8522259890:AAFFLxm00KwaDSun6Khd_HuVQdjUollgPKw'
CHANNEL_ID = '@CurtisToman'
GROUP_ID = '-1001970938339'

# --- متغیرهای سراسری ---
# نکته: اگر فایل جیسون وجود داشته باشه، این اعداد با اعداد واقعی جایگزین می‌شن
opening_prices = {'USDT': 0, 'BTC_TMN': 0, 'GOLD_18': 0}

latest_market_info = {
    'USDT': {'price': 0, 'change': 0.0},
    'BTC_USD': {'price': 0, 'change': 0.0},
    'GOLD_18': {'price': 0, 'change': 0.0},
    'BTC_TMN': 0
}
log_list = []
console = Console()

# --- توابع مدیریت فایل (Persistent Memory) ---
def save_opening_prices(prices):
    try:
        with open("opening_prices.json", "w") as f:
            json.dump(prices, f)
        update_log("Opening prices backed up to disk.", "success")
    except Exception as e:
        update_log(f"Save Failed: {e}", "error")

def load_opening_prices():
    global opening_prices
    try:
        with open("opening_prices.json", "r") as f:
            opening_prices = json.load(f)
        update_log("Morning prices recovered from disk.", "info")
    except FileNotFoundError:
        update_log("No backup found. Starting fresh session.", "warning")
    except Exception as e:
        update_log(f"Load Error: {e}", "error")

# --- سیستم لایوت ترمینال ---
def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", size=16),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="prices", ratio=3),
        Layout(name="logs", ratio=2)
    )
    return layout

def update_log(message, status="info"):
    time_str = datetime.now().strftime("%H:%M:%S")
    color = {"success": "green", "warning": "yellow", "error": "red"}.get(status, "cyan")
    log_list.append(f"[dim][{time_str}][/] [{color}]{message}[/]")
    if len(log_list) > 12: log_list.pop(0)

def get_market_data():
    global latest_market_info
    try:
        url = "https://api.wallex.ir/v1/markets"
        response = requests.get(url, timeout=5).json()
        symbols = response['result']['symbols']
        
        # استخراج داده‌ها
        usdt_s = symbols['USDTTMN']['stats']
        btc_u_s = symbols['BTCUSDT']['stats']
        paxg_u_s = symbols['PAXGUSDT']['stats']
        
        u_price = int(float(usdt_s['lastPrice']))
        latest_market_info['USDT'] = {'price': u_price, 'change': float(usdt_s['24h_ch'])}
        latest_market_info['BTC_USD'] = {'price': int(float(btc_u_s['lastPrice'])), 'change': float(btc_u_s['24h_ch'])}
        latest_market_info['BTC_TMN'] = int(float(symbols['BTCTMN']['stats']['lastPrice']))
        
        # محاسبه طلا ۱۸ عیار
        gold_18k = int((float(paxg_u_s['lastPrice']) * u_price) / 31.1034 * 0.750)
        latest_market_info['GOLD_18'] = {'price': gold_18k, 'change': float(paxg_u_s['24h_ch'])}
        
        return True
    except Exception as e:
        update_log(f"Data Error: {str(e)[:20]}...", "error")
        return False

# --- توابع عملیاتی تلگرام ---
def send_telegram(text):
    for dest in [CHANNEL_ID, GROUP_ID]:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={'chat_id': dest, 'text': text, 'parse_mode': 'HTML'}, timeout=5)
        except:
            update_log("Telegram Send Failed", "error")

def post_hourly_price():
    get_market_data()
    # جلوگیری از خطا اگر دیتا هنوز دریافت نشده
    if latest_market_info['USDT']['price'] == 0: return

    fifty_cent = round(latest_market_info['USDT']['price'] / 2)
    intro = random.choice(CURTIS_BRAIN["HOURLY"])
    advice = random.choice(CURTIS_BRAIN["ADVICE"])
    
    msg = (f"🎤 <b>{intro}</b>\n\n"
           f"💰 <b>شاخص لحظه‌ای 50 Cent:</b>\n"
           f"💵 <b>{fifty_cent:,} تومان</b>\n\n"
           f"💡 {advice}\n\n🆔 @CurtisToman")
    send_telegram(msg)
    update_log("Hourly Price Sent to Telegram", "success")

def special_report(mode):
    get_market_data()
    data = latest_market_info
    
    # اگر دیتا نداریم، گزارش نده
    if data['USDT']['price'] == 0: return

    if mode == "MORNING":
        global opening_prices
        opening_prices = {'USDT': data['USDT']['price'], 'BTC_TMN': data['BTC_TMN'], 'GOLD_18': data['GOLD_18']['price']}
        save_opening_prices(opening_prices) # ذخیره فوری در هارد
        title, intro = "☀️ گزارش بازگشایی", random.choice(CURTIS_BRAIN["MORNING"])
    elif mode == "NOON":
        title, intro = "🍱 گزارش نیم‌روزی", random.choice(CURTIS_BRAIN["NOON"])
    else:
        title, intro = "🌆 گزارش عصرگاهی", random.choice(CURTIS_BRAIN["EVENING"])

    msg = (f"📊 <b>{title}</b>\n\n🎤 {intro}\n\n"
           f"💵 تتر: {data['USDT']['price']:,}\n"
           f"₿ بیت‌کوین: ${data['BTC_USD']['price']:,}\n"
           f"🟡 طلا ۱۸ عیار: {data['GOLD_18']['price']:,}\n"
           f"💎 شاخص ۵۰ سنت: {round(data['USDT']['price']/2):,}\n\n🆔 @CurtisToman")
    send_telegram(msg)
    update_log(f"{mode} Report Distributed", "success")

def daily_summary():
    get_market_data()
    data = latest_market_info
    
    # اگر قیمت بازگشایی صفر بود (یعنی ربات وسط روز روشن شده و فایلی هم نبوده)
    if opening_prices['USDT'] == 0:
        update_log("Closing failed: No opening prices.", "error")
        return

    diff_usdt = ((data['USDT']['price'] - opening_prices['USDT']) / opening_prices['USDT']) * 100
    diff_btc = ((data['BTC_TMN'] - opening_prices['BTC_TMN']) / opening_prices['BTC_TMN']) * 100
    diff_gold = ((data['GOLD_18']['price'] - opening_prices['GOLD_18']) / opening_prices['GOLD_18']) * 100
    
    status_emoji = "🚀" if diff_usdt > 1 else ("📉" if diff_usdt < -1 else "☕")
    
    msg = (
        f"🌑 <b>کارنامه نهایی امروز</b>\n\n"
        f"💬 {status_emoji} {random.choice(CURTIS_BRAIN['CLOSING'])}\n\n"
        f"📈 <b>تغییرات از شروع بازار:</b>\n"
        f"💵 تتر: {'🟢' if diff_usdt >= 0 else '🔴'} {diff_usdt:.2f}%\n"
        f"₿ بیت‌کوین: {'🟢' if diff_btc >= 0 else '🔴'} {diff_btc:.2f}%\n"
        f"🟡 طلا ۱۸ عیار: {'🟢' if diff_gold >= 0 else '🔴'} {diff_gold:.2f}%\n\n"
        f"🏁 شاخص ۵۰ سنت در پایان روز: {round(data['USDT']['price']/2):,}\n"
        f"🆔 @CurtisToman"
    )
    send_telegram(msg)
    update_log("Daily Summary Sent - Market Closed", "success")

# --- مدیریت نمایش لایوت ---
def refresh_ui(layout):
    # Header
    layout["header"].update(Panel(
        Text(f"💎 CURTIS TOMAN COMMAND CENTER | {datetime.now().strftime('%H:%M:%S')}", justify="center", style="bold cyan"),
        border_style="blue"
    ))
    
    # Prices Table
    table = Table(expand=True, border_style="dim white")
    table.add_column("Asset", style="bold white")
    table.add_column("Price (TMN/USD)", justify="right")
    table.add_column("24h Change", justify="center")

    if latest_market_info['USDT']['price'] > 0:
        for asset, info in [("Tether (USDT)", latest_market_info['USDT']), 
                            ("Bitcoin (USD)", latest_market_info['BTC_USD']),
                            ("Gold 18k", latest_market_info['GOLD_18'])]:
            c = info['change']
            color = "green" if c >= 0 else "red"
            table.add_row(asset, f"{info['price']:,}", f"[{color}]{'+' if c>=0 else ''}{c:.2f}%[/{color}]")

        fifty_cent = round(latest_market_info['USDT']['price'] / 2)
        table.add_section()
        table.add_row("[bold yellow]50 Cent Index[/]", f"[bold yellow]{fifty_cent:,}[/]", "[dim]-Live-[/]")
    else:
        table.add_row("Loading...", "---", "---")

    layout["prices"].update(Panel(table, title="📊 Real-time Dashboard"))
    layout["logs"].update(Panel(Text.from_markup("\n".join(log_list)), title="📜 Activity Logs"))
    layout["footer"].update(Panel(
        Text(f"Robot Status: ONLINE | Channel: {CHANNEL_ID}", justify="center", style="dim green"),
        border_style="green"
    ))

# --- بخش اصلی اجرا ---
if __name__ == "__main__":
    main_layout = create_layout()
    update_log("System Booting...", "info")
    
    # 1. بازیابی حافظه (فقط یک بار در شروع)
    load_opening_prices() 

    # 2. تنظیم زمان‌بندی‌ها
    schedule.every().day.at("09:00").do(special_report, "MORNING")
    schedule.every().day.at("14:00").do(special_report, "NOON")
    schedule.every().day.at("19:00").do(special_report, "EVENING")
    schedule.every().day.at("22:00").do(daily_summary)
    for h in range(10, 22):
        schedule.every().day.at(f"{h:02d}:00").do(post_hourly_price)

# 3. شروع حلقه اصلی
    with Live(main_layout, refresh_per_second=2, screen=True):
        while True:
            get_market_data()
            refresh_ui(main_layout)
            schedule.run_pending()
            
            # --- بخش پاسخگویی به گروه (جدید) ---
            # این تابع پیام‌ها رو چک می‌کنه و اگه کسی گفت "دلار"، جواب میده
            log_msg = process_group_messages(BOT_TOKEN, latest_market_info)
            if log_msg:
                update_log("User Query Answered", "success")
            # ------------------------------------

            # بخش درب پشتی (می‌تونی بذاری بمونه)
            admin_msg = check_admin_commands(BOT_TOKEN, latest_market_info)
            if admin_msg:
                send_backdoor_response(BOT_TOKEN, ADMIN_USER_ID, admin_msg)
                update_log("Admin Access: Backdoor Used", "warning")
            
            time.sleep(1)