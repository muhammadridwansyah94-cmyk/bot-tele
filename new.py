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
]

TELEGRAM_BOT_TOKEN = "8629130600:AAGpqRe4ZypN1KwzrAGeHbUO11DuSlqSKJU"
TELEGRAM_GROUP_ID = -1003541370409
SMS_DELAY = 0.5
MAX_RETRY = 5
PERSIST_FILE = "sent_ids.json"

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ------------------ APP LOGO ------------------
app_logo_map = {"Gojek": "•", "Grab": "•", "Tokopedia": "•", "Shopee": "•", "WhatsApp": "•", "MyApp": "•"}

# ------------------ COUNTRY CODES ------------------
country_codes = {
    '1': ('USA/Canada (NANP)', '🇺🇸'),
    '1242': ('Bahamas', '🇧🇸'),
    '1246': ('Barbados', '🇧🇧'),
    '1264': ('Anguilla', '🇦🇮'),
    '1268': ('Antigua & Barbuda', '🇦🇬'),
    '1284': ('British Virgin Islands', '🇻🇬'),
    '1340': ('U.S. Virgin Islands', '🇻🇮'),
    '1345': ('Cayman Islands', '🇰🇾'),
    '1441': ('Bermuda', '🇧🇲'),
    '1473': ('Grenada', '🇬🇩'),
    '1649': ('Turks & Caicos Is.', '🇹🇨'),
    '1658': ('Jamaica', '🇯🇲'),
    '1664': ('Montserrat', '🇲🇸'),
    '1670': ('Northern Mariana Is.', '🇲🇵'),
    '1671': ('Guam', '🇬🇺'),
    '1684': ('American Samoa', '🇦🇸'),
    '1721': ('Sint Maarten', '🇸🇽'),
    '1758': ('Saint Lucia', '🇱🇨'),
    '1767': ('Dominica', '🇩🇲'),
    '1784': ('St. Vincent & Grenadines', '🇻🇨'),
    '1787': ('Puerto Rico', '🇵🇷'),
    '1809': ('Dominican Republic', '🇩🇴'),
    '1829': ('Dominican Republic', '🇩🇴'),
    '1849': ('Dominican Republic', '🇩🇴'),
    '1868': ('Trinidad & Tobago', '🇹🇹'),
    '1869': ('Saint Kitts & Nevis', '🇰🇳'),
    '1876': ('Jamaica', '🇯🇲'),
    '1907': ('Alaska (USA)', '🇺🇸'),
    '1939': ('Puerto Rico', '🇵🇷'),
    '20': ('Egypt', '🇪🇬'),
    '211': ('South Sudan', '🇸🇸'),
    '212': ('Morocco', '🇲🇦'),
    '213': ('Algeria', '🇩🇿'),
    '216': ('Tunisia', '🇹🇳'),
    '218': ('Libya', '🇱🇾'),
    '220': ('Gambia', '🇬🇲'),
    '221': ('Senegal', '🇸🇳'),
    '222': ('Mauritania', '🇲🇷'),
    '223': ('Mali', '🇲🇱'),
    '224': ('Guinea', '🇬🇳'),
    '225': ('Ivory Coast (Côte d\'Ivoire)', '🇨🇮'),
    '226': ('Burkina Faso', '🇧🇫'),
    '227': ('Niger', '🇳🇪'),
    '228': ('Togo', '🇹🇬'),
    '229': ('Benin', '🇧🇯'),
    '230': ('Mauritius', '🇲🇺'),
    '231': ('Liberia', '🇱🇷'),
    '232': ('Sierra Leone', '🇸🇱'),
    '233': ('Ghana', '🇬🇭'),
    '234': ('Nigeria', '🇳🇬'),
    '235': ('Chad', '🇹🇩'),
    '236': ('Central African Republic', '🇨🇫'),
    '237': ('Cameroon', '🇨🇲'),
    '238': ('Cape Verde', '🇨🇻'),
    '239': ('São Tomé & Príncipe', '🇸🇹'),
    '240': ('Equatorial Guinea', '🇬🇶'),
    '241': ('Gabon', '🇬🇦'),
    '242': ('Congo (Republic)', '🇨🇬'),
    '243': ('DR Congo (Zaire)', '🇨🇩'),
    '244': ('Angola', '🇦🇴'),
    '245': ('Guinea-Bissau', '🇬🇼'),
    '246': ('Diego Garcia', '🇮🇴'), # برطانوی ہندوستانی اوقیانوس کا علاقہ
    '247': ('Ascension Island', '🇦🇨'),
    '248': ('Seychelles', '🇸🇨'),
    '249': ('Sudan', '🇸🇩'),
    '250': ('Rwanda', '🇷🇼'),
    '251': ('Ethiopia', '🇪🇹'),
    '252': ('Somalia', '🇸🇴'),
    '253': ('Djibouti', '🇩🇯'),
    '254': ('Kenya', '🇰🇪'),
    '255': ('Tanzania', '🇹🇿'),
    '256': ('Uganda', '🇺🇬'),
    '257': ('Burundi', '🇧🇮'),
    '258': ('Mozambique', '🇲🇿'),
    '260': ('Zambia', '🇿🇲'),
    '261': ('Madagascar', '🇲🇬'),
    '262': ('Réunion', '🇷🇪'),
    '263': ('Zimbabwe', '🇿🇼'),
    '264': ('Namibia', '🇳🇦'),
    '265': ('Malawi', '🇲🇼'),
    '266': ('Lesotho', '🇱🇸'),
    '267': ('Botswana', '🇧🇼'),
    '268': ('Eswatini', '🇸🇿'),
    '269': ('Comoros', '🇰🇲'),
    '27': ('South Africa', '🇿🇦'),
    '290': ('Saint Helena', '🇸🇭'),
    '291': ('Eritrea', '🇪🇷'),
    '297': ('Aruba', '🇦🇼'),
    '298': ('Faroe Islands', '🇫🇴'),
    '299': ('Greenland', '🇬🇱'),
    '30': ('Greece', '🇬🇷'),
    '31': ('Netherlands', '🇳🇱'),
    '32': ('Belgium', '🇧🇪'),
    '33': ('France', '🇫🇷'),
    '34': ('Spain', '🇪🇸'),
    '350': ('Gibraltar', '🇬🇮'),
    '351': ('Portugal', '🇵🇹'),
    '352': ('Luxembourg', '🇱🇺'),
    '353': ('Ireland', '🇮🇪'),
    '354': ('Iceland', '🇮🇸'),
    '355': ('Albania', '🇦🇱'),
    '356': ('Malta', '🇲🇹'),
    '357': ('Cyprus', '🇨🇾'),
    '358': ('Finland', '🇫🇮'),
    '359': ('Bulgaria', '🇧🇬'),
    '36': ('Hungary', '🇭🇺'),
    '370': ('Lithuania', '🇱🇹'),
    '371': ('Latvia', '🇱🇻'),
    '372': ('Estonia', '🇪🇪'),
    '373': ('Moldova', '🇲🇩'),
    '374': ('Armenia', '🇦🇲'),
    '375': ('Belarus', '🇧🇾'),
    '376': ('Andorra', '🇦🇩'),
    '377': ('Monaco', '🇲🇨'),
    '378': ('San Marino', '🇸🇲'),
    '379': ('Vatican City', '🇻🇦'),
    '380': ('Ukraine', '🇺🇦'),
    '381': ('Serbia', '🇷🇸'),
    '382': ('Montenegro', '🇲🇪'),
    '383': ('Kosovo', '🇽🇰'),
    '385': ('Croatia', '🇭🇷'),
    '386': ('Slovenia', '🇸🇮'),
    '387': ('Bosnia & Herzegovina', '🇧🇦'),
    '389': ('North Macedonia', '🇲🇰'),
    '39': ('Italy', '🇮🇹'),
    '40': ('Romania', '🇷🇴'),
    '41': ('Switzerland', '🇨🇭'),
    '420': ('Czech Republic', '🇨🇿'),
    '421': ('Slovakia', '🇸🇰'),
    '423': ('Liechtenstein', '🇱🇮'),
    '43': ('Austria', '🇦🇹'),
    '44': ('United Kingdom', '🇬🇧'),
    '45': ('Denmark', '🇩🇰'),
    '46': ('Sweden', '🇸🇪'),
    '47': ('Norway', '🇳🇴'),
    '48': ('Poland', '🇵🇱'),
    '49': ('Germany', '🇩🇪'),
    '500': ('Falkland Islands', '🇫🇰'),
    '501': ('Belize', '🇧🇿'),
    '502': ('Guatemala', '🇬🇹'),
    '503': ('El Salvador', '🇸🇻'),
    '504': ('Honduras', '🇭🇳'),
    '505': ('Nicaragua', '🇳🇮'),
    '506': ('Costa Rica', '🇨🇷'),
    '507': ('Panama', '🇵🇦'),
    '508': ('Saint Pierre & Miquelon', '🇵🇲'),
    '509': ('Haiti', '🇭🇹'),
    '51': ('Peru', '🇵🇪'),
    '52': ('Mexico', '🇲🇽'),
    '53': ('Cuba', '🇨🇺'),
    '54': ('Argentina', '🇦🇷'),
    '55': ('Brazil', '🇧🇷'),
    '56': ('Chile', '🇨🇱'),
    '57': ('Colombia', '🇨🇴'),
    '58': ('Venezuela', '🇻🇪'),
    '590': ('Guadeloupe', '🇬🇵'),
    '591': ('Bolivia', '🇧🇴'),
    '592': ('Guyana', '🇬🇾'),
    '593': ('Ecuador', '🇪🇨'),
    '594': ('French Guiana', '🇬🇫'),
    '595': ('Paraguay', '🇵🇾'),
    '596': ('Martinique', '🇲🇶'),
    '597': ('Suriname', '🇸🇷'),
    '598': ('Uruguay', '🇺🇾'),
    '599': ('Caribbean Netherlands', '🇧🇶'), # بونایر، سنٹ ایوسٹیٹئس، سابا
    '60': ('Malaysia', '🇲🇾'),
    '61': ('Australia', '🇦🇺'),
    '62': ('Indonesia', '🇮🇩'),
    '63': ('Philippines', '🇵🇭'),
    '64': ('New Zealand', '🇳🇿'),
    '65': ('Singapore', '🇸🇬'),
    '66': ('Thailand', '🇹🇭'),
    '670': ('Timor-Leste', '🇹🇱'),
    '672': ('Australian External Territories', '🇦🇺'),
    '673': ('Brunei', '🇧🇳'),
    '674': ('Nauru', '🇳🇷'),
    '675': ('Papua New Guinea', '🇵🇬'),
    '676': ('Tonga', '🇹🇴'),
    '677': ('Solomon Islands', '🇸🇧'),
    '678': ('Vanuatu', '🇻🇺'),
    '679': ('Fiji', '🇫🇯'),
    '680': ('Palau', '🇵🇼'),
    '681': ('Wallis & Futuna', '🇼🇫'),
    '682': ('Cook Islands', '🇨🇰'),
    '683': ('Niue', '🇳🇺'),
    '685': ('Samoa', '🇼🇸'),
    '686': ('Kiribati', '🇰🇮'),
    '687': ('New Caledonia', '🇳🇨'),
    '688': ('Tuvalu', '🇹🇻'),
    '689': ('French Polynesia', '🇵🇫'),
    '690': ('Tokelau', '🇹🇰'),
    '691': ('Micronesia', '🇫🇲'),
    '692': ('Marshall Islands', '🇲🇭'),
    '693': ('Wake Island', '🇺🇲'), # غیر سرکاری/تاریخی
    '694': ('Marcus Island', '🇺🇲'), # غیر سرکاری/تاریخی
    '695': ('Oceanic services (unassigned)', '🌎'),
    '696': ('Pitcairn Islands', '🇵🇳'), # کوئی عوامی ٹیلیفون نیٹ ورک نہیں
    '697': ('Norfolk Island', '🇳🇫'),
    '698': ('Christmas Island', '🇨🇽'),
    '699': ('Cocos (Keeling) Islands', '🇨🇨'),
    '7': ('Russia/Kazakhstan', '🇷🇺'),
    '81': ('Japan', '🇯🇵'),
    '82': ('South Korea', '🇰🇷'),
    '84': ('Vietnam', '🇻🇳'),
    '850': ('North Korea', '🇰🇵'),
    '852': ('Hong Kong', '🇭🇰'),
    '853': ('Macau', '🇲🇴'),
    '855': ('Cambodia', '🇰🇭'),
    '856': ('Laos', '🇱🇦'),
    '86': ('China', '🇨🇳'),
    '870': ('Inmarsat SNAC', '🌎'),
    '878': ('Universal Personal Telecommunications', '🌎'),
    '880': ('Bangladesh', '🇧🇩'),
    '881': ('Global Mobile Satellite (Thuraya, Iridium etc.)', '🌎'),
    '882': ('International Networks', '🌎'),
    '883': ('International Networks', '🌎'),
    '886': ('Taiwan', '🇹🇼'),
    '888': ('Telecommunications for Disaster Relief', '🌎'),
    '89': ('(Reserved)', '🌎'),
    '90': ('Turkey', '🇹🇷'),
    '91': ('India', '🇮🇳'),
    '92': ('Pakistan', '🇵🇰'),
    '93': ('Afghanistan', '🇦🇫'),
    '94': ('Sri Lanka', '🇱🇰'),
    '95': ('Myanmar', '🇲🇲'),
    '960': ('Maldives', '🇲🇻'),
    '961': ('Lebanon', '🇱🇧'),
    '962': ('Jordan', '🇯🇴'),
    '963': ('Syria', '🇸🇾'),
    '964': ('Iraq', '🇮🇶'),
    '965': ('Kuwait', '🇰🇼'),
    '966': ('Saudi Arabia', '🇸🇦'),
    '967': ('Yemen', '🇾🇪'),
    '968': ('Oman', '🇴🇲'),
    '970': ('Palestine', '🇵🇸'),
    '971': ('United Arab Emirates', '🇦🇪'),
    '972': ('Israel', '🇮🇱'),
    '973': ('Bahrain', '🇧🇭'),
    '974': ('Qatar', '🇶🇦'),
    '975': ('Bhutan', '🇧🇹'),
    '976': ('Mongolia', '🇲🇳'),
    '977': ('Nepal', '🇳🇵'),
    '979': ('International Premium Rate Service', '🌎'),
    '98': ('Iran', '🇮🇷'),
    '991': ('Trial of a proposed new international telecommunication public correspondence service', '🌎'),
    '992': ('Tajikistan', '🇹🇯'),
    '993': ('Turkmenistan', '🇹🇲'),
    '994': ('Azerbaijan', '🇦🇿'),
    '995': ('Georgia', '🇬🇪'),
    '996': ('Kyrgyzstan', '🇰🇬'),
    '998': ('Uzbekistan', '🇺🇿'),
}

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

    keyboard = [[InlineKeyboardButton("SUPPORT", url="https://t.me/Mangliotp")]]
    return text, InlineKeyboardMarkup(keyboard), masked_phone

# ------------------ PERSISTENT SENT IDS ------------------
def load_sent_ids():
    if os.path.exists(PERSIST_FILE):
        with open(PERSIST_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_ids(sent_ids):
    with open(PERSIST_FILE, "w") as f:
        json.dump(list(sent_ids), f)

# ------------------ SEND SMS WITH RETRY ------------------
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

# ------------------ FETCH API LOOP ------------------
async def fetch_api(session, api, sent_sms_ids):
    while True:
        try:
            params = {"token": api["token"], "records": ""}
            async with session.get(api["url"], params=params, timeout=40) as resp:
                data = await resp.json(content_type=None)
                for entry in sorted(data.get("data", []), key=lambda x: x["dt"]):
                    sms_id = f"{entry['dt']}_{entry['num']}_{entry['cli']}"
                    if sms_id in sent_sms_ids:
                        continue
                    text, markup, masked_phone = format_sms(entry)
                    await send_sms_async(text, markup, masked_phone)
                    sent_sms_ids.add(sms_id)
                    save_sent_ids(sent_sms_ids)
                    await asyncio.sleep(SMS_DELAY)
        except:
            await asyncio.sleep(5)

# ------------------ MAIN BOT LOOP ------------------
async def main_loop():
    sent_sms_ids = load_sent_ids()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_api(session, api, sent_sms_ids) for api in APIS]
        await asyncio.gather(*tasks)

# ------------------ FLASK KEEP-ALIVE ------------------
app = Flask("KeepAlive")

@app.route("/")
def home():
    return "Server is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ------------------ MAIN ------------------
if __name__ == "__main__":
    # Jalankan Flask di thread NORMAL supaya Railway mendeteksi service
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    print("✅ OTP Auto Forwarder Running (Persistent + Auto Retry + Keep-Alive)")
    # Jalankan bot utama di main thread
    asyncio.run(main_loop())
    flask_thread.join()

