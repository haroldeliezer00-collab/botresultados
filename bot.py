import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from datetime import datetime
from flask import Flask
import re

# Configuración principal
TOKEN = "8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk"
CHANNEL_ID = "@pruebajsj"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Bot activo y funcionando al 100%"

# Diccionario oficial de abreviaturas
ABBR_MAP = {
    "Lotto Activo": "L.ACT",
    "La Granjita": "GRAJ",
    "Selva Plus": "SELV",
    "Guácharo Activo": "G.ARO",
    "Loto Chaima": "CHAIMA",
    "Ruleton Perú": "R.PER",
    "Ruleton Colombia": "R.COL",
    "Ruleton Venezuela": "R.VEN",
    "Lotto Animalito": "L.ANIM",
    "Lotto Pantera": "L.PANT",
    "Monje Millonario": "MONJE",
    "Lotto Real": "L.REAL",
    "Lotto Inter": "L.INT",
    "Cazaloton": "CAZAL",
    "Mega Animal": "MEGA",
    "Centena Animalitos": "C.ANI",
    "Centena Plus": "C.PLUS",
    "Guacharito Millonario": "G.ITO",
    "Ruleta Activa": "R.ACT",
    "Granjita Plus": "G.PLUS",
    "La Ricachona": "RICAC",
    "Guaca Activa 37": "GUACA",
    "Lotto Max": "L.MAX",
    "Tropi Gana": "TROP",
    "Cóndor Gana": "COND",
    "Granja Millonaria": "G.MIL",
    "Fruti Gana": "FRUI",
    "Granjazo": "G.AZO",
    "Lotto Gato": "L.GATO",
    "Gatazo": "GATAZO",
    "Zoológico Activo": "ZOOL",
    "Lotto Rd": "L.RD",
    "MEGA GUACA": "M.GUAC",
    "PANDA PLUS": "P.PLUS"
}

# Diccionario Oficial de Animalitos con sus Emojis
ANIMAL_DATA = {
    "00": ("BALLENA", "🐳"), "0": ("DELFIN", "🐬"), "1": ("CARNERO", "🐏"), 
    "2": ("TORO", "🐂"), "3": ("CIEMPIES", "🐛"), "4": ("ALACRAN", "🦂"), 
    "5": ("LEON", "🦁"), "6": ("RATON", "🐭"), "7": ("CANARIO", "🐦"), 
    "8": ("TIBURON", "🦈"), "9": ("AGUILA", "🦅"), "10": ("TIGRE", "🐅"), 
    "11": ("GATO", "🐈"), "12": ("CABALLO", "🐎"), "13": ("MONO", "🐒"), 
    "14": ("PALOMA", "🕊️"), "15": ("ZORRO", "🦊"), "16": ("OSO", "🐻"), 
    "17": ("PAVO", "🦃"), "18": ("BURRO", "🫏"), "19": ("CHIVO", "🐐"), 
    "20": ("COCHINO", "🐖"), "21": ("GALLO", "🐓"), "22": ("CAMELLO", "🐪"), 
    "23": ("ZEBRA", "🦓"), "24": ("IGUANA", "🦎"), "25": ("GALLINA", "🐔"), 
    "26": ("VACA", "🐄"), "27": ("PERRO", "🐕"), "28": ("ZAMURO", "🦅"), 
    "29": ("ELEFANTE", "🐘"), "30": ("CAIMAN", "🐊"), "31": ("JIRAFA", "🦒"), 
    "32": ("CULEBRA", "🐍"), "33": ("PESCADO", "🐟"), "34": ("VENADO", "🦌"), 
    "35": ("JIBARO", "🐗"), "36": ("CULEBRA", "🐍")
}

results_storage = {}
sent_individual_results = set()
initial_load_done = False

HEADER_TEXT = (
    "★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
    "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝙹𝙰 ⊱╮\n"
    "      Mas de 6 años brindando\n"
    "          confianza y seguridad\n"
    "  en cada rincón de Venezuela\n"
    "       ʀᴇꜱᴜʟᴛ𝙰ᴅᴏꜱ ᴏꜰ𝙸ᴄ𝙸ᴀʟᴇꜱ\n"
    "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
    "📲JUEGA AQUI👇👇\n"
    "WHATSAPP: 04124489363\n\n"
    "📊 𝗥𝙴𝚂𝚄𝙻𝚃𝙰𝙳𝙾𝚂 𝙰𝙽𝙸𝙼𝙰𝙻𝙸𝚃𝙾𝚂 📊\n"
    "------------------------"
)

def get_morning_greeting_text():
    return (
        "🎯 AGENCIA HAROLD JOSÉ 🎯\n\n"
        "🌅 ¡Despierta con la mejor actitud y energía positiva! 🌟\n"
        "Que este nuevo día esté lleno de bendiciones, grandes jugadas y mucha prosperidad para todos. ¡Vamos con todo! 💪🍀"
    )

def generate_pyramid_text():
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    digits = [int(c) for c in now.strftime("%d%m%Y")]
    
    rows = [digits]
    while len(rows[-1]) > 1:
        prev = rows[-1]
        curr = [(prev[i] + prev[i+1]) % 10 for i in range(len(prev)-1)]
        rows.append(curr)
    
    pyramid_str = ""
    for idx, r in enumerate(rows):
        padding = "  " * idx
        row_nums = "   ".join(map(str, r))
        pyramid_str += f"{padding}... {row_nums} ...\n"
        
    return (
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n"
        "📢 REPORTE TÁCTICO - LA PIRÁMIDE 📢\n\n"
        f"📅 Fecha: {date_str}\n"
        "Análisis matemático actualizado y listo para la jugada. ¡A asegurar posición:\n\n"
        f"{pyramid_str}\n"
        "🔥 DATOS CLAVES PARA HOY:\n"
        "📌 25-13-07\n"
        "📌 35-20-02\n\n"
        "⚡ ¡La precisión y los números hablan por solos! ¡Juega con confianza y gana con nosotros! 🍀 💰"
    )

def get_7am_text():
    return (
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n"
        "🌅 ¡Buenos días a todos! 🌅\n\n"
        "Ya arrancamos un nuevo día con la mejor energía. Por aquí estaremos compartiendo todos los resultados de los animalitos a medida que vayan saliendo.\n\n"
        "📢 Nuestros canales oficiales:\n"
        "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
        "📸 Instagram: https://www.instagram.com/agharold.jose (@agharold.jose)\n"
        "💬 Canal de WhatsApp: https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
        "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
    )

def get_bcv_text():
    rate = "742,23"
    try:
        res = requests.get("https://www.bcv.org.ve/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            div = soup.find('div', id='field-dolar')
            if div:
                val = div.get_text(strip=True)
                if val:
                    rate = val
    except:
        pass
    return (
        "💵 TASA OFICIAL BCV 💵\n\n"
        "🏦 Moneda: Dólar Estadounidense\n"
        f"📈 Precio Oficial: Bs. {rate}\n\n"
        "🔗 Fuente: Banco Central de Venezuela\n"
        "La página para verificar el precio oficial del dólar es esta https://www.bcv.org.ve/"
    )

def get_announcement_text():
    return (
        "🎯 AGENCIA HAROLD JOSE 🎯\n"
        "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
        "📢 ¡AVISO IMPORTANTE PARA NUESTROS JUGADORES! 📢\n\n"
        "Recuerda que para jugar con nosotros debes acceder primero al Canal de WhatsApp para verificar si la taquilla se encuentra activa el día de hoy:\n"
        "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
        "📲 Si la taquilla está activa, puedes revisar nuestro catálogo y escribirnos directamente:\n"
        "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n\n"
        "💬 También estamos disponibles por Telegram:\n"
        "👉 t.me/ag_haroldjose\n\n"
        "¡Mucha suerte en sus jugadas! 🍀🔥"
    )

def get_final_text():
    return (
        "🎯 AGENCIA HAROLD JOSE 2 🎯\n\n"
        "🌙 ¡FINAL DE JORNADA! 🌙\n\n"
        "Estos fueron todos los resultados del día de hoy. ¡Gracias por jugar con nosotros! Los esperamos el día de mañana con mucha más suerte y energía. 🍀✨"
    )

def format_individual_message(loteria, hora, num, animal_info):
    name, emoji = animal_info
    return (
        "🎯 AG HAROLD JOSE 🎯\n\n"
        f"🎰 {loteria.upper()}\n"
        f"🕒 {hora}  {num} {emoji} - {name}\n"
        "https://t.me/resultadosagharoldjose"
    )

def scrape_and_notify(send_alerts=True):
    global initial_load_done
    sources = [
        "https://lotery.winbigvzla.com/resultados",
        "https://www.lottoactivo.com/resultados/lotto_activo/",
        "https://lagranjitaonline.com/",
        "https://www.selvaplus.com/resultados",
        "https://elguacharitomillonario.com/",
        "https://lotochaima.com/",
        "https://www.guacharoactivo.com.ve/resultados",
        "https://www.lottoactivo.com/resultados/lottoactivo2(monjemillonario)/",
        "https://www.lottoactivo.com/resultados/lotto_activo_internacional/",
        "https://www.guacaactiva.com/"
    ]
    
    for url in sources:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for tag in soup.find_all(['div', 'li', 'tr', 'article', 'section', 'span']):
                t = tag.get_text(separator=' ', strip=True)
                if not t or len(t) > 300:
                    continue
                if "ruleta royal" in t.lower():
                    continue
                
                for lot in ABBR_MAP.keys():
                    if lot.lower() in t.lower():
                        time_m = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', t, re.IGNORECASE)
                        num_m = re.search(r'\b(00|0?[0-9]|[1-3][0-5]|36)\b', t)
                        
                        if time_m and num_m:
                            h_raw = time_m.group(1).zfill(2)
                            hour_key = f"{h_raw}:00"
                            
                            # Normalizar a formato de horas en punto válidas (08:00 a 19:00)
                            if hour_key not in [f"{str(i).zfill(2)}:00" for i in range(8, 20)]:
                                continue
                                
                            num = num_m.group(1).zfill(2)
                            animal_info = ANIMAL_DATA.get(str(int(num)), ANIMAL_DATA.get(num, ("ANIMAL", "🎲")))

                            if hour_key not in results_storage:
                                results_storage[hour_key] = {}
                            
                            key_unique = f"{hour_key}-{lot}-{num}"
                            
                            # Si es la primera ejecución al encender el bot, marcamos todo lo existente como ya visto para no spamear
                            if not initial_load_done:
                                sent_individual_results.add(key_unique)
                                results_storage[hour_key][lot] = {"num": num, "info": animal_info}
                            else:
                                if lot not in results_storage[hour_key] or results_storage[hour_key][lot]["num"] != num:
                                    results_storage[hour_key][lot] = {"num": num, "info": animal_info}
                                    
                                    if send_alerts and key_unique not in sent_individual_results:
                                        sent_individual_results.add(key_unique)
                                        h_display = f"{h_raw}:00"
                                        msg = format_individual_message(lot, h_display, num, animal_info)
                                        bot.send_message(CHANNEL_ID, msg)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
    initial_load_done = True

def build_table_message():
    # Horarios fijos requeridos de 8:00 AM a 7:00 PM
    hours = [f"{str(i).zfill(2)}:00" for i in range(8, 20)]

    groups = [
        ["La Granjita", "Lotto Activo", "Selva Plus"],
        ["Guácharo Activo", "Loto Chaima", "Monje Millonario"],
        ["Lotto Animalito", "Lotto Pantera", "Lotto Real"],
        ["Lotto Rd", "Centena Animalitos", "Mega Animal"],
        ["Ruleton Perú", "Ruleton Colombia", "Ruleton Venezuela"],
        ["Cóndor Gana", "Fruti Gana", "Tropi Gana"],
        ["Granja Millonaria", "Zoológico Activo", "Lotto Max"]
    ]

    text = HEADER_TEXT + "\n\n"

    for group in groups:
        header_line = "HORA 🏛️"
        for lot in group:
            abbr = ABBR_MAP.get(lot, lot[:5])
            header_line += f" ⚪ {abbr}"
        text += header_line + "\n"

        for h in hours:
            row_line = f"⏰ {h}"
            for lot in group:
                res = results_storage.get(h, {}).get(lot)
                if res:
                    num = res['num']
                    emoji = res['info'][1]
                    row_line += f" {num} {emoji}"
                else:
                    row_line += " .... 🚫"
            text += row_line + "\n"
        text += "\n"

    text += "MUCHA SUERTE EN SUS JUGADAS"
    return text

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_buenos_dias')
def test_bd(message):
    bot.send_message(message.chat.id, get_morning_greeting_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_piramide')
def test_pir(message):
    bot.send_message(message.chat.id, generate_pyramid_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_7am')
def test_7(message):
    bot.send_message(message.chat.id, get_7am_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_bcv')
def test_b(message):
    bot.send_message(message.chat.id, get_bcv_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_anuncio')
def test_an(message):
    bot.send_message(message.chat.id, get_announcement_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_tabla')
def test_tab(message):
    scrape_and_notify(send_alerts=False)
    bot.send_message(message.chat.id, build_table_message())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_scraping')
def test_scr(message):
    bot.reply_to(message, "🔄 Ejecutando revisión...")
    scrape_and_notify(send_alerts=True)
    bot.reply_to(message, "✅ ¡Finalizado!")

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_final')
def test_fin(message):
    bot.send_message(message.chat.id, get_final_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() in ['probar', 'test'])
def test_general(message):
    bot.reply_to(message, "🛠️ Comandos:\n- test_buenos_dias\n- test_piramide\n- test_7am\n- test_bcv\n- test_anuncio\n- test_tabla\n- test_scraping\n- test_final")

def background_scheduler():
    last_min = -1
    # Carga inicial silenciosa para registrar lo que ya salió y evitar spam al encender
    scrape_and_notify(send_alerts=False)
    
    while True:
        now = datetime.now()
        current_hour = now.hour
        current_min = now.minute
        current_w_time = now.strftime("%H:%M")
        
        if current_min != last_min:
            last_min = current_min
            
            if current_w_time == "06:30":
                bot.send_message(CHANNEL_ID, get_morning_greeting_text())
            elif current_w_time == "06:31":
                bot.send_message(CHANNEL_ID, generate_pyramid_text())
            elif current_w_time == "07:00":
                bot.send_message(CHANNEL_ID, get_7am_text())
            
            if (current_hour == 6 and current_min == 30) or (current_hour == 18 and current_min == 30):
                bot.send_message(CHANNEL_ID, get_bcv_text())

            elif current_w_time in ["10:00", "14:00", "17:00"]:
                bot.send_message(CHANNEL_ID, get_announcement_text())
                
            # Envío automático de la tabla actualizada exactamente al minuto 10 de cada hora
            elif current_min == 10:
                scrape_and_notify(send_alerts=True)
                bot.send_message(CHANNEL_ID, build_table_message())
                time.sleep(65)
                
            elif current_w_time == "21:10":
                bot.send_message(CHANNEL_ID, get_final_text())

        # Revisión continua en segundo plano cada 45 segundos para detectar nuevos animalitos al instante
        scrape_and_notify(send_alerts=True)
        time.sleep(45)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=background_scheduler, daemon=True).start()
    print("🤖 Bot iniciado correctamente...")
    bot.infinity_polling()
