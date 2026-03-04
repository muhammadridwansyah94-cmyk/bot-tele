import re
import asyncio
import aiohttp
import json
import os
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, RetryAfter
from flask import Flask
import threading
from langdetect import detect

# ------------------ CONFIG ------------------
APIS = [
    {"name": "TIMESMS", "url": "http://147.135.212.197/crapi/time/viewstats", "token": "Q1ZRNEVBYYpeild6RVSTh1SIT1tokHBBYnBWh0VykmhzUIZCclM"},
    {"name": "KONEKTA", "url": "http://51.77.216.195/crapi/konek/viewstats", "token": "RFNSSjRSQodDc2pmeYt5eESLYYhlgodCSHeFV2Joc0OCgWtyhJRj"},
    {"name": "ROXY", "url": "http://51.77.216.195/crapi/rx/viewstats", "token": "RU9RRTRSQmV7YYheVGqTVlNhckJhbJJci4pmU1ZRZWV_hIp3hm6G"},
    {"name": "Botsms", "url": "http://147.135.212.197/crapi/st/viewstats", "token": "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ"},
]

TELEGRAM_BOT_TOKEN = "8629130600:AAGpqRe4ZypN1KwzrAGeHbUO11DuSlqSKJU"
TELEGRAM_GROUP_ID = -1003541370409

SMS_DELAY = 8
MAX_RETRY = 5
PERSIST_FILE = "sent_ids.json"
CLEANUP_HOURS = 24

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ------------------ COUNTRY DETECTION ------------------
def detect_country(phone):
    phone = phone.replace("+", "").strip()
    country_map = {
        "972": ("Israel", "🇮🇱"),
        "62": ("Indonesia", "🇮🇩"),
        "1": ("USA/Canada", "🇺🇸"),
        "91": ("India", "🇮🇳"),
        "44": ("UK", "🇬🇧"),
        "49": ("Germany", "🇩🇪"),
        "33": ("France", "🇫🇷"),
        "39": ("Italy", "🇮🇹"),
        "7": ("Russia", "🇷🇺"),
        "81": ("Japan", "🇯🇵"),
        "82": ("South Korea", "🇰🇷"),
        "84": ("Vietnam", "🇻🇳"),
        "63": ("Philippines", "🇵🇭"),
    }
    for code in sorted(country_map.keys(), key=len, reverse=True):
        if phone.startswith(code):
            return country_map[code]
    return "Unknown", "🌍"

# ------------------ HELPERS ------------------
def mask_phone(phone):
    clean = phone.lstrip('+')
    return clean[:4] + "MNGL" + clean[-5:] if len(clean) > 7 else clean

def detect_language(message):
    try:
        return detect(message).capitalize()
    except:
        return "Unknown"

def format_sms(entry):
    app = entry.get("cli", "Unknown")
    phone = entry.get("num", "")
    message = entry.get("message", "")

    masked_phone = mask_phone(phone)
    country_name, flag = detect_country(phone)

    otp_match = re.search(r'(\d[\d -]{2,12}\d)', message)
    otp = re.sub(r'[^0-9]', '', otp_match.group(1)) if otp_match else "N/A"

    lang_tag = detect_language(message)

    text = f"""<pre>
•{app}•
🌍 Country: {flag} {country_name}
📱 Phone: {masked_phone}
🔑 OTP: {otp}
#{lang_tag}</pre>"""

    keyboard = [[InlineKeyboardButton("NUMBER FILE", url="https://t.me/Mangliotp")]]
    return text, InlineKeyboardMarkup(keyboard), masked_phone, otp

# ------------------ SENT STORAGE ------------------
def load_sent_ids():
    now = datetime.utcnow().timestamp()
    if not os.path.exists(PERSIST_FILE):
        return {}
    try:
        with open(PERSIST_FILE, "r") as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if now - v < CLEANUP_HOURS * 3600}
    except:
        return {}

def save_sent_ids(sent_sms_ids):
    with open(PERSIST_FILE, "w") as f:
        json.dump(sent_sms_ids, f)

# ------------------ SEND ------------------
async def send_sms_async(msg_text, reply_markup, phone, otp, api_name, sent_sms_ids, sms_id):
    if sms_id in sent_sms_ids:
        print(f"[DEBUG] SMS {sms_id} already sent, skipping")
        return

    attempt = 0
    while attempt < MAX_RETRY:
        try:
            print(f"[DEBUG] Sending SMS {sms_id} to Telegram...")
            msg = await bot.send_message(
                chat_id=TELEGRAM_GROUP_ID,
                text=msg_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            sent_sms_ids[sms_id] = datetime.utcnow().timestamp()
            save_sent_ids(sent_sms_ids)

            async def delete_later(message_id):
                await asyncio.sleep(300)
                try:
                    await bot.delete_message(TELEGRAM_GROUP_ID, message_id)
                except Exception as e:
                    print(f"[WARNING] Failed to delete message {message_id} | {e}")

            asyncio.create_task(delete_later(msg.message_id))

            print(f"[✓] {api_name} | {phone} | OTP: {otp}")
            return

        except RetryAfter as e:
            print(f"[INFO] RetryAfter {e.retry_after}s for SMS {sms_id}")
            await asyncio.sleep(e.retry_after)
        except TelegramError as e:
            print(f"[ERROR] TelegramError on SMS {sms_id} | {e}")
            attempt += 1
            await asyncio.sleep(2)

# ------------------ FETCH ------------------
api_initialized = {}

async def fetch_api(session, api, sent_sms_ids):
    while True:
        try:
            headers = {"Authorization": api["token"]}
            async with session.get(api["url"], headers=headers, timeout=15) as response:
                print(f"[DEBUG] Fetched {api['name']} | status: {response.status}")
                if response.status != 200:
                    await asyncio.sleep(SMS_DELAY)
                    continue

                raw_data = await response.json()
                print(f"[DEBUG] {api['name']} raw response type: {type(raw_data)}")

                # --- WRAP RESPONSE JADI LIST ---
                if isinstance(raw_data, list):
                    data = raw_data
                elif isinstance(raw_data, dict):
                    data = next((v for v in raw_data.values() if isinstance(v, list)), [])
                    if not data:
                        print(f"[WARNING] {api['name']} dict response tapi tidak ada list, wrapping empty list")
                else:
                    data = []

        except Exception as e:
            print(f"[ERROR] API {api['name']} fetch failed | {e}")
            await asyncio.sleep(SMS_DELAY)
            continue

        entries = sorted(data, key=lambda x: x.get("id", 0), reverse=True)[:5]
        print(f"[DEBUG] {api['name']} processing {len(entries)} entries")

        if not api_initialized.get(api["name"]):
            api_initialized[api["name"]] = True
            print(f"[INFO] {api['name']} initialized (first run skipped)")
            await asyncio.sleep(SMS_DELAY)
            continue

        for entry in entries:
            sms_id = str(entry.get("id"))
            if sms_id in sent_sms_ids:
                print(f"[DEBUG] SMS ID {sms_id} already sent, skipping")
                continue

            print(f"[DEBUG] Processing SMS ID {sms_id} from {api['name']}")
            text, markup, masked_phone, otp = format_sms(entry)

            await send_sms_async(
                text,
                markup,
                masked_phone,
                otp,
                api["name"],
                sent_sms_ids,
                sms_id
            )

            await asyncio.sleep(12)  # dual bot pause

        await asyncio.sleep(SMS_DELAY)

# ------------------ MAIN ------------------
async def main_loop():
    sent_sms_ids = load_sent_ids()

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(fetch_api(session, api, sent_sms_ids))
            for api in APIS
        ]
        await asyncio.gather(*tasks)

# ------------------ KEEP ALIVE ------------------
app = Flask("KeepAlive")

@app.route("/")
def home():
    return "Server is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    print("✅ OTP Auto Forwarder Running (Dual Bot + Country Flag Active)")
    asyncio.run(main_loop())
    flask_thread.join()
