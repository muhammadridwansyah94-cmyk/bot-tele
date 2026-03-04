import requests
import time
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import re

# ------------------ تمہاری ڈیٹیلز ------------------
API_URL = "http://147.135.212.197/crapi/st/viewstats"
TOKEN = "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ=="
params = {"token": TOKEN, "records": ""}

TELEGRAM_BOT_TOKEN = "8726837419:AAFGyBwcsH5uxEPWbTPFnRjKJrVqtAmcw9g"
TELEGRAM_GROUP_ID = -1003719397490

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def escape_v2(text):
    chars_to_escape = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in chars_to_escape else c for c in str(text)])

def fetch_sms():
    try:
        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        print("API response type:", type(data))
        if data and isinstance(data, list) and data:
            print("First entry example:", data[0])
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"API fetch failed: {e}")
        return []

def parse_timestamp(ts_str):
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None

# ---------------- Country map fixed ----------------
country_map = {
    "1": ("United States", "🇺🇸"),
    "7": ("Russia", "🇷🇺"),
    "20": ("Egypt", "🇪🇬"),
    "27": ("South Africa", "🇿🇦"),
    "30": ("Greece", "🇬🇷"),
    "31": ("Netherlands", "🇳🇱"),
    "32": ("Belgium", "🇧🇪"),
    "33": ("France", "🇫🇷"),
    "34": ("Spain", "🇪🇸"),
    "36": ("Hungary", "🇭🇺"),
    "39": ("Italy", "🇮🇹"),
    "40": ("Romania", "🇷🇴"),
    "41": ("Switzerland", "🇨🇭"),
    "43": ("Austria", "🇦🇹"),
    "44": ("United Kingdom", "🇬🇧"),
    "45": ("Denmark", "🇩🇰"),
    "46": ("Sweden", "🇸🇪"),
    "47": ("Norway", "🇳🇴"),
    "48": ("Poland", "🇵🇱"),
    "49": ("Germany", "🇩🇪"),
    "62": ("Indonesia", "🇮🇩"),
    # ... tambahkan negara lain sesuai kebutuhan
}

last_seen_time = None

print("✅ OTP Auto Forwarder Started... Checking every 40 seconds.")

while True:
    entries = fetch_sms()
    if not entries:
        time.sleep(40)
        continue

    # Sort entries by timestamp (latest first)
    entries = sorted(entries, key=lambda x: parse_timestamp(x[3]) or datetime.min, reverse=True)

    new_entries = []

    if last_seen_time is None:
        new_entries = entries[:8]
        if new_entries:
            last_seen_time = parse_timestamp(new_entries[0][3])
    else:
        for entry in entries:
            ts = parse_timestamp(entry[3])
            if ts and ts > last_seen_time:
                new_entries.append(entry)

    if new_entries:
        latest_ts = parse_timestamp(new_entries[0][3])
        if latest_ts:
            last_seen_time = latest_ts
        print(f"Found {len(new_entries)} new OTP(s) | Latest: {new_entries[0][3]}")

    for entry in new_entries[::-1]:
        app       = entry[0].strip()
        phone     = entry[1].strip()
        full_msg  = entry[2].strip().replace('\n', ' ').replace('  ', ' ')
        timestamp = entry[3]

        # Country detection
        country_code = ""
        clean_phone = phone.lstrip('+')
        for code in sorted(country_map.keys(), key=len, reverse=True):
            if clean_phone.startswith(code):
                country_code = code
                break

        if country_code in country_map:
            country, flag = country_map[country_code]
        else:
            country = "Unknown"
            flag = "🌍"

        masked_phone = phone[:5] + "**" + phone[-5:] if len(phone) >= 10 else phone

        # OTP detect
        otp = "N/A"
        otp_match = re.search(
            r'(?:code|كود|رمز|كود التفعيل|رمز التحقق|código|куд|验证码|code de vérification|codice|verification code|Your .* code|Your .* código|Your .* код|imo verification code|WhatsApp code|code is|is)[\s\W:-]*(\d{3,8})',
            full_msg, re.IGNORECASE | re.UNICODE
        )
        if otp_match:
            otp = otp_match.group(1)
        else:
            otp_match = re.search(r'\b(\d{4,8})\b', full_msg)
            if otp_match:
                otp = otp_match.group(1)

        otp = re.sub(r'[- ]', '', otp)

        text = f"""✉️ *New {escape_v2(app)} OTP Received*

> *Time:* {escape_v2(timestamp)}
> *Country:* {escape_v2(country)}, {flag}
> *Service:* {escape_v2(app)}
> *Number:* `{escape_v2(masked_phone)}`
> *OTP:* ```{escape_v2(otp)}```
> *Message:*
> {escape_v2(full_msg)}

──────────────────────────────"""

        keyboard = [
            [InlineKeyboardButton("Main Channel", url="https://t.me/mrchd112")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            bot.send_message(
                chat_id=TELEGRAM_GROUP_ID,
                text=text,
                parse_mode="MarkdownV2",  # bisa diganti None jika masih error
                reply_markup=reply_markup,
                disable_notification=False
            )
            print(f"Sent → {masked_phone} ({app}) | Country: {country} | OTP: {otp}")
        except Exception as e:
            print(f"Telegram send FAILED: {str(e)}")

    time.sleep(40)
