import requests
import time
from datetime import datetime
import re
import telegram_send
import asyncio
import os

# ------------------ API DETAILS ------------------
API_URL = "http://147.135.212.197/crapi/st/viewstats"
TOKEN = "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ=="
params = {"token": TOKEN, "records": ""}

# ------------------ Telegram ENV ------------------
# Railway: Settings → Variables
# TELEGRAM_SEND_TOKEN = <bot token>
# TELEGRAM_SEND_CHAT_ID = <chat/group id>
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_SEND_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_SEND_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ ERROR: Telegram ENV variables not set!")
    exit(1)

# Gunakan conf "railway" untuk otomatis dari ENV
TELEGRAM_CONF = "railway"

last_seen_time = None

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

# ---------------- Country map minimal ----------------
country_map = {
    "1": ("United States", "🇺🇸"),
    "7": ("Russia", "🇷🇺"),
    "62": ("Indonesia", "🇮🇩"),
}

print("✅ OTP Auto Forwarder Started... Checking every 40 seconds.")

while True:
    entries = fetch_sms()
    if not entries:
        time.sleep(40)
        continue

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
            otp_match = re.search(r'\b(\d{4,8})\b', re.sub(r'[^0-9]', '', full_msg))
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

        # -------------------- Kirim Telegram (async-safe) --------------------
        try:
            asyncio.run(telegram_send.send(messages=[text], conf=TELEGRAM_CONF))
            print(f"Sent → {masked_phone} ({app}) | Country: {country} | OTP: {otp}")
        except Exception as e:
            print(f"Telegram send FAILED: {str(e)}")

    time.sleep(40)
