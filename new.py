import re
import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, RetryAfter

# ------------------ CONFIG ------------------
APIS = [
    {"name": "TIMESMS", "url": "http://147.135.212.197/crapi/time/viewstats", "token": "Q1ZRNEVBYYpeild6RVSTh1SIT1tokHBBYnBWh0VykmhzUIZCclM"},
    {"name": "KONEKTA", "url": "http://51.77.216.195/crapi/konek/viewstats", "token": "RFNSSjRSQodDc2pmeYt5eESLYYhlgodCSHeFV2Joc0OCgWtyhJRj"},
    {"name": "ROXY", "url": "http://51.77.216.195/crapi/rx/viewstats", "token": "RU9RRTRSQmV7YYheVGqTVlNhckJhbJJci4pmU1ZRZWV_hIp3hm6G"},
]

TELEGRAM_BOT_TOKEN = "8629130600:AAGpqRe4ZypN1KwzrAGeHbUO11DuSlqSKJU"
TELEGRAM_GROUP_ID = -1003541370409
SMS_DELAY = 0.5  # delay antar SMS untuk mencegah limit/flood
STATUS_LOG_INTERVAL = 300  # 5 menit

SMS_DELAY = 0.7
MAX_RETRY = 5

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ------------------ COUNTRY CODES (GLOBAL) ------------------
country_codes = {
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
    "51": ("Peru", "🇵🇪"),
    "52": ("Mexico", "🇲🇽"),
    "53": ("Cuba", "🇨🇺"),
    "54": ("Argentina", "🇦🇷"),
    "55": ("Brazil", "🇧🇷"),
    "56": ("Chile", "🇨🇱"),
    "57": ("Colombia", "🇨🇴"),
    "60": ("Malaysia", "🇲🇾"),
    "61": ("Australia", "🇦🇺"),
    "62": ("Indonesia", "🇮🇩"),
    "63": ("Philippines", "🇵🇭"),
    "64": ("New Zealand", "🇳🇿"),
    "65": ("Singapore", "🇸🇬"),
    "66": ("Thailand", "🇹🇭"),
    "81": ("Japan", "🇯🇵"),
    "82": ("South Korea", "🇰🇷"),
    "84": ("Vietnam", "🇻🇳"),
    "86": ("China", "🇨🇳"),
    "90": ("Turkey", "🇹🇷"),
    "91": ("India", "🇮🇳"),
    "92": ("Pakistan", "🇵🇰"),
    "93": ("Afghanistan", "🇦🇫"),
    "94": ("Sri Lanka", "🇱🇰"),
    "95": ("Myanmar", "🇲🇲"),
    "98": ("Iran", "🇮🇷"),
    "212": ("Morocco", "🇲🇦"),
    "213": ("Algeria", "🇩🇿"),
    "216": ("Tunisia", "🇹🇳"),
    "218": ("Libya", "🇱🇾"),
    "234": ("Nigeria", "🇳🇬"),
    "254": ("Kenya", "🇰🇪"),
    "255": ("Tanzania", "🇹🇿"),
    "351": ("Portugal", "🇵🇹"),
    "352": ("Luxembourg", "🇱🇺"),
    "353": ("Ireland", "🇮🇪"),
    "358": ("Finland", "🇫🇮"),
    "380": ("Ukraine", "🇺🇦"),
    "420": ("Czech Republic", "🇨🇿"),
    "421": ("Slovakia", "🇸🇰"),
    "971": ("UAE", "🇦🇪"),
    "972": ("Israel", "🇮🇱"),
    "974": ("Qatar", "🇶🇦"),
    "975": ("Bhutan", "🇧🇹"),
    "976": ("Mongolia", "🇲🇳"),
    "977": ("Nepal", "🇳🇵"),
    "998": ("Uzbekistan", "🇺🇿"),
}

# ------------------ HELPERS ------------------
def mask_phone(phone):
    clean = phone.lstrip('+')
    return clean[:4] + "MNGL" + clean[-5:] if len(clean) > 8 else clean

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

    text = f"""<pre>
{app}
🌍 Country: {flag} {country}
📱 Phone: {masked_phone}
🔑 OTP: {otp}</pre>"""

    keyboard = [[InlineKeyboardButton("SUPPORT", url="https://t.me/username_kamu")]]
    return text, InlineKeyboardMarkup(keyboard), masked_phone

# ------------------ AUTO RETRY SEND ------------------
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

            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ SMS terkirim: {phone}")

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

        except TelegramError as e:
            attempt += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Retry {attempt} gagal: {e}")
            await asyncio.sleep(2)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Gagal kirim setelah {MAX_RETRY}x: {phone}")

# ------------------ FETCH LOOP ------------------
async def fetch_api(session, api, sent_ids):
    while True:
        try:
            params = {"token": api["token"], "records": ""}
            async with session.get(api["url"], params=params, timeout=40) as resp:
                data = await resp.json()
                for entry in data.get("data", []):
                    sms_id = f"{entry['dt']}_{entry['num']}"
                    if sms_id in sent_ids:
                        continue
                    text, markup, masked = format_sms(entry)
                    await send_sms_async(text, markup, masked)
                    sent_ids.add(sms_id)
                    await asyncio.sleep(SMS_DELAY)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] API Error: {e}")
            await asyncio.sleep(10)

# ------------------ MAIN ------------------
async def main():
    print("🚀 OTP Forwarder Running (Auto Retry Enabled)")
    sent_ids = set()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_api(session, api, sent_ids) for api in APIS]
        await asyncio.gather(*tasks)

asyncio.run(main())
