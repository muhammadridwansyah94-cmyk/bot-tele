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

# ------------------ CONFIG ------------------
APIS = [
    {"name": "TIMESMS", "url": "http://147.135.212.197/crapi/time/viewstats", "token": "Q1ZRNEVBYYpeild6RVSTh1SIT1tokHBBYnBWh0VykmhzUIZCclM"},
    {"name": "KONEKTA", "url": "http://51.77.216.195/crapi/konek/viewstats", "token": "RFNSSjRSQodDc2pmeYt5eESLYYhlgodCSHeFV2Joc0OCgWtyhJRj"},
    {"name": "ROXY", "url": "http://51.77.216.195/crapi/rx/viewstats", "token": "RU9RRTRSQmV7YYheVGqTVlNhckJhbJJci4pmU1ZRZWV_hIp3hm6G"},
    {"name": "Botsms", "url": "http://147.135.212.197/crapi/st/viewstats", "token": "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ"},
]

TELEGRAM_BOT_TOKEN = "8726837419:AAFGyBwcsH5uxEPWbTPFnRjKJrVqtAmcw9g"
TELEGRAM_GROUP_ID = -1003719397490
SMS_DELAY = 0.5
MAX_RETRY = 5
PERSIST_FILE = "sent_ids.json"

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ------------------ APP LOGO ------------------
app_logo_map = {"Gojek": "•", "Grab": "•", "Tokopedia": "•", "Shopee": "•", "WhatsApp": "•", "MyApp": "•"}

# ------------------ COUNTRY CODES ------------------
country_codes = {}  # (TETAP SAMA PERSIS SEPERTI PUNYA KAMU)

# ------------------ HELPERS ------------------
def mask_phone(phone):
    clean = phone.lstrip('+')
    return clean[:4] + "MNGL" + clean[-5:] if len(clean) > 7 else clean

def detect_country(phone):
    clean = phone.lstrip('+')
    for code in sorted(country_codes.keys(), key=len, reverse=True):
        if clean.startswith(code):
            return country_codes[code]
    return "Unknown", "🌍"

def format_sms(entry):
    app = entry["cli"]
    phone = entry["num"]
    message = entry["message"]

    country, flag = detect_country(phone)
    masked_phone = mask_phone(phone)
    otp_match = re.search(r'(\d[\d -]{2,12}\d)', message)
    otp = re.sub(r'[^0-9]', '', otp_match.group(1)) if otp_match else "N/A"

    app_logo = app_logo_map.get(app, "•")
    app_line = f"{app_logo}{app}{app_logo}".center(25)
    text = f"""<pre>
{app_line}
🌍 Country: {flag} {country}
📱 Phone: {masked_phone}
🔑 OTP: {otp}</pre>"""

    keyboard = [[InlineKeyboardButton("NUMBER FILE", url="https://t.me/Mangliotp")]]
    return text, InlineKeyboardMarkup(keyboard), masked_phone

def load_sent_ids():
    if os.path.exists(PERSIST_FILE):
        with open(PERSIST_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_ids(sent_ids):
    with open(PERSIST_FILE, "w") as f:
        json.dump(list(sent_ids), f)

async def send_sms_async(msg_text, reply_markup, phone):
    attempt = 0
    while attempt < MAX_RETRY:
        try:
            msg = await bot.send_message(
                chat_id=TELEGRAM_GROUP_ID,
                text=msg_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [✓] SMS terkirim: {phone}")

            async def delete_later(message_id):
                await asyncio.sleep(300)
                try:
                    await bot.delete_message(TELEGRAM_GROUP_ID, message_id)
                except:
                    pass

            asyncio.create_task(delete_later(msg.message_id))
            return
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramError:
            attempt += 1
            await asyncio.sleep(2)

# ===================== FIX STABIL =====================
async def fetch_api(session, api, sent_sms_ids):
    while True:
        try:
            params = {"token": api["token"], "records": ""}
            async with session.get(api["url"], params=params, timeout=40) as resp:
                
                raw = await resp.text()

                try:
                    data = json.loads(raw)
                except:
                    await asyncio.sleep(5)
                    continue

                # FORMAT 1 (3 API LAMA)
                if isinstance(data, dict) and "data" in data:
                    for entry in sorted(data.get("data", []), key=lambda x: x["dt"]):
                        sms_id = f"{entry['dt']}_{entry['num']}_{entry['cli']}"
                        if sms_id in sent_sms_ids:
                            continue

                        text, markup, masked_phone = format_sms(entry)
                        await send_sms_async(text, markup, masked_phone)
                        sent_sms_ids.add(sms_id)
                        save_sent_ids(sent_sms_ids)
                        await asyncio.sleep(SMS_DELAY)

                # FORMAT 2 (BOTSMS)
                elif isinstance(data, list):
                    for row in sorted(data, key=lambda x: x[3]):
                        cli, num, message, dt = row

                        sms_id = f"{dt}_{num}_{cli}"
                        if sms_id in sent_sms_ids:
                            continue

                        entry = {
                            "cli": cli,
                            "num": num,
                            "message": message,
                            "dt": dt
                        }

                        text, markup, masked_phone = format_sms(entry)
                        await send_sms_async(text, markup, masked_phone)
                        sent_sms_ids.add(sms_id)
                        save_sent_ids(sent_sms_ids)
                        await asyncio.sleep(SMS_DELAY)

        except Exception as e:
            print("Error di API:", api["name"], "|", e)
            await asyncio.sleep(5)
# ======================================================

async def main_loop():
    sent_sms_ids = load_sent_ids()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_api(session, api, sent_sms_ids) for api in APIS]
        await asyncio.gather(*tasks)

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

    print("✅ OTP Auto Forwarder Running (Persistent + Auto Retry + Keep-Alive)")
    asyncio.run(main_loop())
    flask_thread.join()
