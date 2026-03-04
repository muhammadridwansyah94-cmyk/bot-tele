import aiohttp
import asyncio
import re
from collections import deque

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # konsisten deteksi bahasa

# ================== KONFIG ==================
BOT_TOKEN = "8726837419:AAFmzoubZXF9TNgFQ1FSvVfcJLzudhV96Bc"
CHAT_ID = "-1003719397490"

MAIN_CHANNEL = "https://t.me/+rrb_zfoI63oyYzFl"
NUMBER_CHANNEL = "https://t.me/+hlWwgjlFHBNjM2M1"

# ===== MULTI API =====
API_LIST = [
    {"url": "http://147.135.212.197/crapi/st/viewstats", "token": "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ", "name": "BOTSMS"},
    {"url": "http://147.135.212.197/crapi/time/viewstats/crapi/st/viewstats", "token": "Q1ZRNEVBYYpeild6RVSTh1SIT1tokHBBYnBWh0VykmhzUIZCclM", "name": "TIMESMS"},
    {"url": "http://51.77.216.195/crapi/konek/viewstats", "token": "RFNSSjRSQodDc2pmeYt5eESLYYhlgodCSHeFV2Joc0OCgWtyhJRj", "name": "KONEKTA"},
]

INTERVAL = 20  # detik

bot = Bot(token=BOT_TOKEN)
sent_messages = deque(maxlen=1000)

# ===== COUNTRY MAP =====
country_map = {
    "1": ("US", "🇺🇸"),
    "1242": ("BS", "🇧🇸"),
    "1246": ("BB", "🇧🇧"),
    "1264": ("AI", "🇦🇮"),
    "1268": ("AG", "🇦🇬"),
    "1284": ("VG", "🇻🇬"),
    "1340": ("VI", "🇻🇮"),
    "1345": ("KY", "🇰🇾"),
    "1441": ("BM", "🇧🇲"),
    "1473": ("GD", "🇬🇩"),
    "1649": ("TC", "🇹🇨"),
    "1658": ("JM", "🇯🇲"),
    "1664": ("MS", "🇲🇸"),
    "1670": ("MP", "🇲🇵"),
    "1671": ("GU", "🇬🇺"),
    "1684": ("AS", "🇦🇸"),
    "1721": ("SX", "🇸🇽"),
    "1758": ("LC", "🇱🇨"),
    "1767": ("DM", "🇩🇲"),
    "1784": ("VC", "🇻🇨"),
    "1787": ("PR", "🇵🇷"),
    "1809": ("DO", "🇩🇴"),
    "1829": ("DO", "🇩🇴"),
    "1849": ("DO", "🇩🇴"),
    "1868": ("TT", "🇹🇹"),
    "1869": ("KN", "🇰🇳"),
    "1876": ("JM", "🇯🇲"),
    "1907": ("US", "🇺🇸"),
    "1939": ("PR", "🇵🇷"),
    "20": ("EG", "🇪🇬"),
    "211": ("SS", "🇸🇸"),
    "212": ("MA", "🇲🇦"),
    "213": ("DZ", "🇩🇿"),
    "216": ("TN", "🇹🇳"),
    "218": ("LY", "🇱🇾"),
    "220": ("GM", "🇬🇲"),
    "221": ("SN", "🇸🇳"),
    "222": ("MR", "🇲🇷"),
    "223": ("ML", "🇲🇱"),
    "224": ("GN", "🇬🇳"),
    "225": ("CI", "🇨🇮"),
    "226": ("BF", "🇧🇫"),
    "227": ("NE", "🇳🇪"),
    "228": ("TG", "🇹🇬"),
    "229": ("BJ", "🇧🇯"),
    "230": ("MU", "🇲🇺"),
    "231": ("LR", "🇱🇷"),
    "232": ("SL", "🇸🇱"),
    "233": ("GH", "🇬🇭"),
    "234": ("NG", "🇳🇬"),
    "235": ("TD", "🇹🇩"),
    "236": ("CF", "🇨🇫"),
    "237": ("CM", "🇨🇲"),
    "238": ("CV", "🇨🇻"),
    "239": ("ST", "🇸🇹"),
    "240": ("GQ", "🇬🇶"),
    "241": ("GA", "🇬🇦"),
    "242": ("CG", "🇨🇬"),
    "243": ("CD", "🇨🇩"),
    "244": ("AO", "🇦🇴"),
    "245": ("GW", "🇬🇼"),
    "246": ("IO", "🇮🇴"),
    "247": ("AC", "🇦🇨"),
    "248": ("SC", "🇸🇨"),
    "249": ("SD", "🇸🇩"),
    "250": ("RW", "🇷🇼"),
    "251": ("ET", "🇪🇹"),
    "252": ("SO", "🇸🇴"),
    "253": ("DJ", "🇩🇯"),
    "254": ("KE", "🇰🇪"),
    "255": ("TZ", "🇹🇿"),
    "256": ("UG", "🇺🇬"),
    "257": ("BI", "🇧🇮"),
    "258": ("MZ", "🇲🇿"),
    "260": ("ZM", "🇿🇲"),
    "261": ("MG", "🇲🇬"),
    "262": ("RE", "🇷🇪"),
    "263": ("ZW", "🇿🇼"),
    "264": ("NA", "🇳🇦"),
    "265": ("MW", "🇲🇼"),
    "266": ("LS", "🇱🇸"),
    "267": ("BW", "🇧🇼"),
    "268": ("SZ", "🇸🇿"),
    "269": ("KM", "🇰🇲"),
    "27": ("ZA", "🇿🇦"),
    "290": ("SH", "🇸🇭"),
    "291": ("ER", "🇪🇷"),
    "297": ("AW", "🇦🇼"),
    "298": ("FO", "🇫🇴"),
    "299": ("GL", "🇬🇱"),
    "30": ("GR", "🇬🇷"),
    "31": ("NL", "🇳🇱"),
    "32": ("BE", "🇧🇪"),
    "33": ("FR", "🇫🇷"),
    "34": ("ES", "🇪🇸"),
    "350": ("GI", "🇬🇮"),
    "351": ("PT", "🇵🇹"),
    "352": ("LU", "🇱🇺"),
    "353": ("IE", "🇮🇪"),
    "354": ("IS", "🇮🇸"),
    "355": ("AL", "🇦🇱"),
    "356": ("MT", "🇲🇹"),
    "357": ("CY", "🇨🇾"),
    "358": ("FI", "🇫🇮"),
    "359": ("BG", "🇧🇬"),
    "36": ("HU", "🇭🇺"),
    "370": ("LT", "🇱🇹"),
    "371": ("LV", "🇱🇻"),
    "372": ("EE", "🇪🇪"),
    "373": ("MD", "🇲🇩"),
    "374": ("AM", "🇦🇲"),
    "375": ("BY", "🇧🇾"),
    "376": ("AD", "🇦🇩"),
    "377": ("MC", "🇲🇨"),
    "378": ("SM", "🇸🇲"),
    "379": ("VA", "🇻🇦"),
    "380": ("UA", "🇺🇦"),
    "381": ("RS", "🇷🇸"),
    "382": ("ME", "🇲🇪"),
    "383": ("XK", "🇽🇰"),
    "385": ("HR", "🇭🇷"),
    "386": ("SI", "🇸🇮"),
    "387": ("BA", "🇧🇦"),
    "389": ("MK", "🇲🇰"),
    "39": ("IT", "🇮🇹"),
    "40": ("RO", "🇷🇴"),
    "41": ("CH", "🇨🇭"),
    "420": ("CZ", "🇨🇿"),
    "421": ("SK", "🇸🇰"),
    "423": ("LI", "🇱🇮"),
    "43": ("AT", "🇦🇹"),
    "44": ("UK", "🇬🇧"),
    "45": ("DK", "🇩🇰"),
    "46": ("SE", "🇸🇪"),
    "47": ("NO", "🇳🇴"),
    "48": ("PL", "🇵🇱"),
    "49": ("DE", "🇩🇪"),
    "500": ("FK", "🇫🇰"),
    "501": ("BZ", "🇧🇿"),
    "502": ("GT", "🇬🇹"),
    "503": ("SV", "🇸🇻"),
    "504": ("HN", "🇭🇳"),
    "505": ("NI", "🇳🇮"),
    "506": ("CR", "🇨🇷"),
    "507": ("PA", "🇵🇦"),
    "508": ("PM", "🇵🇲"),
    "509": ("HT", "🇭🇹"),
    "51": ("PE", "🇵🇪"),
    "52": ("MX", "🇲🇽"),
    "53": ("CU", "🇨🇺"),
    "54": ("AR", "🇦🇷"),
    "55": ("BR", "🇧🇷"),
    "56": ("CL", "🇨🇱"),
    "57": ("CO", "🇨🇴"),
    "58": ("VE", "🇻🇪"),
    "590": ("GP", "🇬🇵"),
    "591": ("BO", "🇧🇴"),
    "592": ("GY", "🇬🇾"),
    "593": ("EC", "🇪🇨"),
    "594": ("GF", "🇬🇫"),
    "595": ("PY", "🇵🇾"),
    "596": ("MQ", "🇲🇶"),
    "597": ("SR", "🇸🇷"),
    "598": ("UY", "🇺🇾"),
    "599": ("BQ", "🇧🇶"),
    "60": ("MY", "🇲🇾"),
    "61": ("AU", "🇦🇺"),
    "62": ("ID", "🇮🇩"),
    "63": ("PH", "🇵🇭"),
    "64": ("NZ", "🇳🇿"),
    "65": ("SG", "🇸🇬"),
    "66": ("TH", "🇹🇭"),
    "670": ("TL", "🇹🇱"),
    "672": ("AU", "🇦🇺"),
    "673": ("BN", "🇧🇳"),
    "674": ("NR", "🇳🇷"),
    "675": ("PG", "🇵🇬"),
    "676": ("TO", "🇹🇴"),
    "677": ("SB", "🇸🇧"),
    "678": ("VU", "🇻🇺"),
    "679": ("FJ", "🇫🇯"),
    "680": ("PW", "🇵🇼"),
    "681": ("WF", "🇼🇫"),
    "682": ("CK", "🇨🇰"),
    "683": ("NU", "🇳🇺"),
    "685": ("WS", "🇼🇸"),
    "686": ("KI", "🇰🇮"),
    "687": ("NC", "🇳🇨"),
    "688": ("TV", "🇹🇻"),
    "689": ("PF", "🇵🇫"),
    "690": ("TK", "🇹🇰"),
    "691": ("FM", "🇫🇲"),
    "692": ("MH", "🇲🇭"),
    "693": ("UM", "🇺🇲"),
    "694": ("UM", "🇺🇲"),
    "695": ("🌎", "🌎"),
    "696": ("PN", "🇵🇳"),
    "697": ("NF", "🇳🇫"),
    "698": ("CX", "🇨🇽"),
    "699": ("CC", "🇨🇨"),
    "7": ("RU", "🇷🇺"),
    "81": ("JP", "🇯🇵"),
    "82": ("KR", "🇰🇷"),
    "84": ("VN", "🇻🇳"),
    "850": ("KP", "🇰🇵"),
    "852": ("HK", "🇭🇰"),
    "853": ("MO", "🇲🇴"),
    "855": ("KH", "🇰🇭"),
    "856": ("LA", "🇱🇦"),
    "86": ("CN", "🇨🇳"),
    "870": ("🌎", "🌎"),
    "878": ("🌎", "🌎"),
    "880": ("BD", "🇧🇩"),
    "881": ("🌎", "🌎"),
    "882": ("🌎", "🌎"),
    "883": ("🌎", "🌎"),
    "886": ("TW", "🇹🇼"),
    "888": ("🌎", "🌎"),
    "89": ("🌎", "🌎"),
    "90": ("TR", "🇹🇷"),
    "91": ("IN", "🇮🇳"),
    "92": ("PK", "🇵🇰"),
    "93": ("AF", "🇦🇫"),
    "94": ("LK", "🇱🇰"),
    "95": ("MM", "🇲🇲"),
    "960": ("MV", "🇲🇻"),
    "961": ("LB", "🇱🇧"),
    "962": ("JO", "🇯🇴"),
    "963": ("SY", "🇸🇾"),
    "964": ("IQ", "🇮🇶"),
    "965": ("KW", "🇰🇼"),
    "966": ("SA", "🇸🇦"),
    "967": ("YE", "🇾🇪"),
    "968": ("OM", "🇴🇲"),
    "970": ("PS", "🇵🇸"),
    "971": ("AE", "🇦🇪"),
    "972": ("IL", "🇮🇱"),
    "973": ("BH", "🇧🇭"),
    "974": ("QA", "🇶🇦"),
    "975": ("BT", "🇧🇹"),
    "976": ("MN", "🇲🇳"),
    "977": ("NP", "🇳🇵"),
    "979": ("🌎", "🌎"),
    "98": ("IR", "🇮🇷"),
    "991": ("🌎", "🌎"),
    "992": ("TJ", "🇹🇯"),
    "993": ("TM", "🇹🇲"),
    "994": ("AZ", "🇦🇿"),
    "995": ("GE", "🇬🇪"),
    "996": ("KG", "🇰🇬"),
    "998": ("UZ", "🇺🇿")
}

# ===== LANG MAP =====
lang_map = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
    "pt": "Portuguese", "id": "Indonesian", "ms": "Malay", "vi": "Vietnamese",
    "ja": "Japanese", "ko": "Korean", "ru": "Russian", "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "af": "Afrikaans", "am": "Amharic", "az": "Azerbaijani", "be": "Belarusian",
    "bg": "Bulgarian", "bn": "Bengali", "bs": "Bosnian", "ca": "Catalan",
    "cs": "Czech", "cy": "Welsh", "da": "Danish", "el": "Greek", "eo": "Esperanto",
    "et": "Estonian", "eu": "Basque", "fa": "Persian", "fi": "Finnish",
    "ga": "Irish", "gl": "Galician", "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi",
    "hr": "Croatian", "ht": "Haitian Creole", "hu": "Hungarian", "hy": "Armenian",
    "is": "Icelandic", "jv": "Javanese", "ka": "Georgian", "kk": "Kazakh", "km": "Khmer",
    "kn": "Kannada", "ku": "Kurdish", "ky": "Kyrgyz", "la": "Latin", "lb": "Luxembourgish",
    "lo": "Lao", "lt": "Lithuanian", "lv": "Latvian", "mg": "Malagasy", "mi": "Maori",
    "mk": "Macedonian", "ml": "Malayalam", "mn": "Mongolian", "mr": "Marathi",
    "mt": "Maltese", "my": "Burmese", "ne": "Nepali", "nl": "Dutch", "no": "Norwegian",
    "pa": "Punjabi", "pl": "Polish", "ps": "Pashto", "ro": "Romanian", "sd": "Sindhi",
    "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian", "so": "Somali", "sq": "Albanian",
    "sr": "Serbian", "su": "Sundanese", "sv": "Swedish", "sw": "Swahili", "ta": "Tamil",
    "te": "Telugu", "tg": "Tajik", "th": "Thai", "tl": "Filipino", "tr": "Turkish",
    "uk": "Ukrainian", "ur": "Urdu", "xh": "Xhosa", "yi": "Yiddish", "zu": "Zulu"
}

# ===== ESCAPE =====
def escape_v2(text):
    if not text:
        return ""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in escape_chars else c for c in str(text))

def escape_header(text):
    return escape_v2(text).replace("#", "\\#")

# ===== OTP =====
def extract_otp(message):
    if not message:
        return "N/A"
    keywords = ["code", "codigo", "kode", "otp", "verification number"]
    for kw in keywords:
        pattern = re.compile(rf"(?i){kw}[:\s]*")
        match = pattern.search(message)
        if match:
            digits = re.findall(r'\d{2,8}', message[match.end():])
            if digits:
                return ''.join(digits)
    fallback = re.findall(r'\d{2,6}', message)
    return ''.join(fallback) if fallback else "N/A"

# ===== MASK PHONE =====
def mask_phone(phone):
    if len(phone) <= 8:
        return phone
    return phone[:4] + "MNGL" + phone[-4:]

# ===== DETEKSI BAHASA =====
def detect_language_full(text):
    if not text:
        return "unknown"
    try:
        code = detect(text)
        return lang_map.get(code, code)
    except:
        return "unknown"

# ===== AUTO DELETE =====
async def auto_delete(message_id):
    await asyncio.sleep(300)  # 5 menit
    try:
        await bot.delete_message(chat_id=CHAT_ID, message_id=message_id)
    except:
        pass

# ===== CHECK MULTI API =====
async def check_sms():
    async with aiohttp.ClientSession() as session:
        for api in API_LIST:
            try:
                async with session.get(api["url"], params={"token": api["token"], "records": ""}, timeout=15) as resp:
                    try:
                        data_json = await resp.json()
                        if data_json.get("status") != "success":
                            print(f"[{api['name']}] API status not success")
                            continue
                        data = data_json.get("data", [])
                    except:
                        text = await resp.text()
                        print(f"[{api['name']}] Invalid JSON, raw: {text[:200]}")
                        continue

                if not data:
                    continue

                for item in data:
                    app_name = item.get("cli", "UnknownApp")
                    phone = item.get("num", "UnknownNum")
                    message = item.get("message", "")
                    time = item.get("dt", "")

                    unique_id = f"{phone}-{message}-{time}-{api['name']}"
                    if unique_id in sent_messages:
                        continue
                    sent_messages.append(unique_id)

                    otp = extract_otp(message)
                    masked_phone = mask_phone(phone)
                    phone_clean = phone.replace("+", "")
                    country, flag = "Unknown", "🌍"
                    for code, (c, f) in country_map.items():
                        if phone_clean.startswith(code):
                            country, flag = c, f
                            break

                    header = f"{flag} \\#{escape_header(country)} \\#{escape_header(app_name)} {escape_v2(masked_phone)}"
                    lang_name = detect_language_full(message)
                    header_with_lang = f"{header}\n\\#{escape_v2(lang_name)}"

                    # keyboard tetap sama
                    keyboard = []
                    if otp != "N/A":
                        keyboard.append([InlineKeyboardButton(f"🔑 {otp}", callback_data=f"otp_{otp}")])
                    keyboard.append([
                        InlineKeyboardButton("Main Channel", url=MAIN_CHANNEL),
                        InlineKeyboardButton("Number Channel", url=NUMBER_CHANNEL)
                    ])
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    msg = await bot.send_message(
                        chat_id=CHAT_ID,
                        text=header_with_lang,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    asyncio.create_task(auto_delete(msg.message_id))
                    print(f"[{api['name']}] SMS from {phone_clean}, language: {lang_name}")

            except Exception as e:
                print(f"Error {api['name']}: {e}")

# ===== /stats COMMAND =====
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(sent_messages)
    await update.message.reply_text(
        f"📊 Total SMS tracked: {total}",
        parse_mode=ParseMode.MARKDOWN_V2
    )

# ===== MAIN LOOP =====
async def main_loop():
    while True:
        await check_sms()
        await asyncio.sleep(INTERVAL)

# ===== START BOT =====
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("stats", stats_command))
    asyncio.create_task(main_loop())
    print("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())