import re
import asyncio
import aiohttp
import threading
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import ClientConnectionError, ClientPayloadError, ServerDisconnectedError

# ------------------ CONFIG ------------------
APIS = [
{"name": "TIMESMS", "url": "http://147.135.212.197/crapi/time/viewstats", "token": "Q1ZRNEVBYYpeild6RVSTh1SIT1tokHBBYnBWh0VykmhzUIZCclM"},
    {"name": "KONEKTA", "url": "http://51.77.216.195/crapi/konek/viewstats", "token": "RFNSSjRSQodDc2pmeYt5eESLYYhlgodCSHeFV2Joc0OCgWtyhJRj"},
    {"name": "ROXY", "url": "http://51.77.216.195/crapi/rx/viewstats", "token": "RU9RRTRSQmV7YYheVGqTVlNhckJhbJJci4pmU1ZRZWV_hIp3hm6G"},
]

TELEGRAM_BOT_TOKEN = "8629130600:AAGpqRe4ZypN1KwzrAGeHbUO11DuSlqSKJU"
TELEGRAM_GROUP_ID = -1003541370409

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ------------------ APP LOGO ------------------
app_logo_map = {"Gojek": "•", "Grab": "•", "Tokopedia": "•", "Shopee": "•", "WhatsApp": "•", "MyApp": "•"}

# ------------------ COUNTRY MAP ------------------
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
    "58": ("Venezuela", "🇻🇪"),
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
    "91": ("India", "🇮🇳"),
    "92": ("Pakistan", "🇵🇰"),
    "93": ("Afghanistan", "🇦🇫"),
    "94": ("Sri Lanka", "🇱🇰"),
    "95": ("Myanmar", "🇲🇲"),
    "98": ("Iran", "🇮🇷"),
    "211": ("South Sudan", "🇸🇸"),
    "212": ("Morocco", "🇲🇦"),
    "213": ("Algeria", "🇩🇿"),
    "216": ("Tunisia", "🇹🇳"),
    "218": ("Libya", "🇱🇾"),
    "220": ("Gambia", "🇬🇲"),
    "221": ("Senegal", "🇸🇳"),
    "222": ("Mauritania", "🇲🇷"),
    "223": ("Mali", "🇲🇱"),
    "224": ("Guinea", "🇬🇳"),
    "225": ("Ivory Coast", "🇨🇮"),
    "226": ("Burkina Faso", "🇧🇫"),
    "227": ("Niger", "🇳🇪"),
    "228": ("Togo", "🇹🇬"),
    "229": ("Benin", "🇧🇯"),
    "230": ("Mauritius", "🇲🇺"),
    "231": ("Liberia", "🇱🇷"),
    "232": ("Sierra Leone", "🇸🇱"),
    "233": ("Ghana", "🇬🇭"),
    "234": ("Nigeria", "🇳🇬"),
    "235": ("Chad", "🇹🇩"),
    "236": ("Central African Republic", "🇨🇫"),
    "237": ("Cameroon", "🇨🇲"),
    "238": ("Cape Verde", "🇨🇻"),
    "239": ("Sao Tome and Principe", "🇸🇹"),
    "240": ("Equatorial Guinea", "🇬🇶"),
    "241": ("Gabon", "🇬🇦"),
    "242": ("Congo", "🇨🇬"),
    "243": ("DR Congo", "🇨🇩"),
    "244": ("Angola", "🇦🇴"),
    "248": ("Seychelles", "🇸🇨"),
    "249": ("Sudan", "🇸🇩"),
    "250": ("Rwanda", "🇷🇼"),
    "251": ("Ethiopia", "🇪🇹"),
    "252": ("Somalia", "🇸🇴"),
    "253": ("Djibouti", "🇩🇯"),
    "254": ("Kenya", "🇰🇪"),
    "255": ("Tanzania", "🇹🇿"),
    "256": ("Uganda", "🇺🇬"),
    "257": ("Burundi", "🇧🇮"),
    "258": ("Mozambique", "🇲🇿"),
    "260": ("Zambia", "🇿🇲"),
    "261": ("Madagascar", "🇲🇬"),
    "262": ("Reunion", "🇷🇪"),
    "263": ("Zimbabwe", "🇿🇼"),
    "264": ("Namibia", "🇳🇦"),
    "265": ("Malawi", "🇲🇼"),
    "266": ("Lesotho", "🇱🇸"),
    "267": ("Botswana", "🇧🇼"),
    "268": ("Eswatini", "🇸🇿"),
    "269": ("Comoros", "🇰🇲"),
    "290": ("Saint Helena", "🇸🇭"),
    "291": ("Eritrea", "🇪🇷"),
    "297": ("Aruba", "🇦🇼"),
    "298": ("Faroe Islands", "🇫🇴"),
    "299": ("Greenland", "🇬🇱"),
    "350": ("Gibraltar", "🇬🇮"),
    "351": ("Portugal", "🇵🇹"),
    "352": ("Luxembourg", "🇱🇺"),
    "353": ("Ireland", "🇮🇪"),
    "354": ("Iceland", "🇮🇸"),
    "355": ("Albania", "🇦🇱"),
    "356": ("Malta", "🇲🇹"),
    "357": ("Cyprus", "🇨🇾"),
    "358": ("Finland", "🇫🇮"),
    "359": ("Bulgaria", "🇧🇬"),
    "370": ("Lithuania", "🇱🇹"),
    "371": ("Latvia", "🇱🇻"),
    "372": ("Estonia", "🇪🇪"),
    "373": ("Moldova", "🇲🇩"),
    "374": ("Armenia", "🇦🇲"),
    "375": ("Belarus", "🇧🇾"),
    "376": ("Andorra", "🇦🇩"),
    "377": ("Monaco", "🇲🇨"),
    "378": ("San Marino", "🇸🇲"),
    "380": ("Ukraine", "🇺🇦"),
    "381": ("Serbia", "🇷🇸"),
    "382": ("Montenegro", "🇲🇪"),
    "383": ("Kosovo", "🇽🇰"),
    "385": ("Croatia", "🇭🇷"),
    "386": ("Slovenia", "🇸🇮"),
    "387": ("Bosnia and Herzegovina", "🇧🇦"),
    "389": ("North Macedonia", "🇲🇰"),
    "420": ("Czech Republic", "🇨🇿"),
    "421": ("Slovakia", "🇸🇰"),
    "423": ("Liechtenstein", "🇱🇮"),
    "500": ("Falkland Islands", "🇫🇰"),
    "501": ("Belize", "🇧🇿"),
    "502": ("Guatemala", "🇬🇹"),
    "503": ("El Salvador", "🇸🇻"),
    "504": ("Honduras", "🇭🇳"),
    "505": ("Nicaragua", "🇳🇮"),
    "506": ("Costa Rica", "🇨🇷"),
    "507": ("Panama", "🇵🇦"),
    "509": ("Haiti", "🇭🇹"),
    "590": ("Guadeloupe", "🇬🇵"),
    "591": ("Bolivia", "🇧🇴"),
    "592": ("Guyana", "🇬🇾"),
    "593": ("Ecuador", "🇪🇨"),
    "594": ("French Guiana", "🇬🇫"),
    "595": ("Paraguay", "🇵🇾"),
    "596": ("Martinique", "🇲🇶"),
    "597": ("Suriname", "🇸🇷"),
    "598": ("Uruguay", "🇺🇾"),
    "599": ("Caribbean Netherlands", "🇧🇶"),
    "670": ("Timor-Leste", "🇹🇱"),
    "672": ("Norfolk Island", "🇳🇫"),  # Antarctica shared sometimes
    "673": ("Brunei", "🇧🇳"),
    "674": ("Nauru", "🇳🇷"),
    "675": ("Papua New Guinea", "🇵🇬"),
    "676": ("Tonga", "🇹🇴"),
    "677": ("Solomon Islands", "🇸🇧"),
    "678": ("Vanuatu", "🇻🇺"),
    "679": ("Fiji", "🇫🇯"),
    "680": ("Palau", "🇵🇼"),
    "681": ("Wallis and Futuna", "🇼🇫"),
    "682": ("Cook Islands", "🇨🇰"),
    "683": ("Niue", "🇳🇺"),
    "685": ("Samoa", "🇼🇸"),
    "686": ("Kiribati", "🇰🇮"),
    "687": ("New Caledonia", "🇳🇨"),
    "688": ("Tuvalu", "🇹🇻"),
    "689": ("French Polynesia", "🇵🇫"),
    "690": ("Tokelau", "🇹🇰"),
    "691": ("Micronesia", "🇫🇲"),
    "692": ("Marshall Islands", "🇲🇭"),
    "850": ("North Korea", "🇰🇵"),
    "852": ("Hong Kong", "🇭🇰"),
    "853": ("Macau", "🇲🇴"),
    "855": ("Cambodia", "🇰🇭"),
    "856": ("Laos", "🇱🇦"),
    "880": ("Bangladesh", "🇧🇩"),
    "886": ("Taiwan", "🇹🇼"),
    "960": ("Maldives", "🇲🇻"),
    "961": ("Lebanon", "🇱🇧"),
    "962": ("Jordan", "🇯🇴"),
    "963": ("Syria", "🇸🇾"),
    "964": ("Iraq", "🇮🇶"),
    "965": ("Kuwait", "🇰🇼"),
    "966": ("Saudi Arabia", "🇸🇦"),
    "967": ("Yemen", "🇾🇪"),
    "968": ("Oman", "🇴🇲"),
    "971": ("UAE", "🇦🇪"),
    "972": ("Israel", "🇮🇱"),
    "973": ("Bahrain", "🇧🇭"),
    "974": ("Qatar", "🇶🇦"),
    "975": ("Bhutan", "🇧🇹"),
    "976": ("Mongolia", "🇲🇳"),
    "977": ("Nepal", "🇳🇵"),
    "992": ("Tajikistan", "🇹🇯"),
    "993": ("Turkmenistan", "🇹🇲"),
    "994": ("Azerbaijan", "🇦🇿"),
    "995": ("Georgia", "🇬🇪"),
    "996": ("Kyrgyzstan", "🇰🇬"),
    "998": ("Uzbekistan", "🇺🇿"),
}

# ------------------ ANSI COLORS ------------------
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

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

def send_sms(msg_text, reply_markup, phone):
    try:
        msg = bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=msg_text, parse_mode="HTML", reply_markup=reply_markup)
        threading.Timer(300, lambda: bot.delete_message(chat_id=TELEGRAM_GROUP_ID, message_id=msg.message_id)).start()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [✓] SMS terkirim: {phone}")
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [!] Telegram send FAILED: {e}")

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

# ------------------ FETCH API ------------------
async def fetch_api(session, api, sent_sms_ids, status_dict, prev_status_dict, last_status_log_time, retry_delay=10, max_fail=5, status_log_interval=300):
    fail_count = 0
    while True:
        try:
            params = {"token": api["token"], "records": ""}
            async with session.get(api["url"], params=params, timeout=40) as resp:
                if resp.status != 200:
                    raise Exception(f"Status {resp.status}")

                data = await resp.json()
                entries = data.get("data", [])
                for entry in sorted(entries, key=lambda x: datetime.strptime(x["dt"], "%Y-%m-%d %H:%M:%S")):
                    sms_id = f"{entry['dt']}_{entry['num']}_{entry['cli']}"
                    if sms_id in sent_sms_ids:
                        continue
                    text, reply_markup, masked_phone = format_sms(entry)
                    threading.Thread(target=send_sms, args=(text, reply_markup, masked_phone)).start()
                    sent_sms_ids.add(sms_id)

                status_dict[api["name"]] = "active"
                fail_count = 0

        except (asyncio.TimeoutError, ClientConnectionError, ServerDisconnectedError, ClientPayloadError) as e:
            fail_count += 1
            status_dict[api["name"]] = "dead"
            if fail_count >= max_fail:
                await asyncio.sleep(60)
                fail_count = 0
            else:
                await asyncio.sleep(retry_delay)

        except Exception as e:
            fail_count += 1
            status_dict[api["name"]] = "error"
            await asyncio.sleep(retry_delay)

        # Cetak log status hanya jika berubah dan interval > status_log_interval
        now = asyncio.get_event_loop().time()
        status_changed = status_dict != prev_status_dict
        if status_changed or any(now - last_status_log_time[api_name] > status_log_interval for api_name in status_dict):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_parts = []
            for name, status in status_dict.items():
                if status == "active":
                    log_parts.append(f"{GREEN}{name}: ✅ aktif / menunggu SMS{RESET}")
                elif status == "dead":
                    log_parts.append(f"{YELLOW}{name}: ⚠ mati sementara{RESET}")
                elif status == "error":
                    log_parts.append(f"{RED}{name}: ❌ error{RESET}")
                last_status_log_time[name] = now
            print(f"[{timestamp}] [STATUS] " + " | ".join(log_parts))
            prev_status_dict.update(status_dict)

# ------------------ MAIN ------------------
async def main_loop():
    print("✅ OTP Auto Forwarder Started (log API max 5 menit, SMS real-time)")
    async with aiohttp.ClientSession() as session:
        status_dict = {api["name"]: "active" for api in APIS}
        prev_status_dict = status_dict.copy()
        last_status_log_time = {api["name"]: 0 for api in APIS}
        tasks = [fetch_api(session, api, set(), status_dict, prev_status_dict, last_status_log_time) for api in APIS]
        await asyncio.gather(*tasks)

asyncio.run(main_loop())