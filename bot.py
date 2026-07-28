import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from datetime import datetime
from flask import Flask

# Configuración con tu token y tu canal oficial de Telegram
TOKEN = "8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk"
CHANNEL_ID = "@pruebajsj"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "¡El bot de resultados de la Agencia Harold José está activo y funcionando!"

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

# Estructura en memoria
results_storage = {}
sent_individual_results = set()

# Encabezado corporativo oficial
HEADER_TEXT = (
    "★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
    "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝙹𝙰 ⊱╮\n"
    "      Mas de 6 años brindando\n"
    "          confianza y seguridad\n"
    "  en cada rincón de Venezuela\n"
    "       ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰɪᴄɪᴀʟᴇꜱ\n"
    "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
    "📲JUEGA AQUI👇👇\n"
    "WHATSAPP: 04124489363\n\n"
    "📊 𝗥𝙴𝚂𝚄𝙻𝚃𝙰𝙳𝙾𝚂 𝙰𝙽𝙸𝙼𝙰𝙻𝙸𝚃𝙾𝚂 📊\n"
    "------------------------"
)

def scrape_results(send_telegram_alerts=False):
    """Entra a winbigvzla.com, extrae los resultados y los organiza en memoria."""
    try:
        url = "https://winbigvzla.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Búsqueda y extracción en la página
        import re
        for tag in soup.find_all(['h3', 'h4', 'strong', 'div', 'span']):
            t = tag.get_text(strip=True)
            for lot in ABBR_MAP.keys():
                if lot.lower() in t.lower():
                    parent_text = tag.parent.get_text(separator=' ', strip=True) if tag.parent else t
                    time_m = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)?', parent_text, re.IGNORECASE)
                    num_m = re.search(r'\b(0?[0-9]|[1-3][0-5]|36)\b', parent_text)
                    
                    if time_m and num_m:
                        h_raw = time_m.group(1)
                        ampm = time_m.group(2) if time_m.group(2) else ""
                        h_formatted = f"{h_raw} {ampm}".strip().upper()
                        
                        hour_key = h_raw if ":" in h_raw else "09:00"
                        if len(hour_key) == 4:
                            hour_key = "0" + hour_key
                            
                        num = num_m.group(1).zfill(2)
                        
                        parts = parent_text.split(num)
                        animal = "ANIMAL"
                        if len(parts) > 1:
                            words = parts[1].strip().split()
                            if words:
                                animal = words[0].upper()

                        if hour_key not in results_storage:
                            results_storage[hour_key] = {}
                        
                        results_storage[hour_key][lot] = {"num": num, "animal": animal}
                        
                        clave_unica = f"{hour_key}-{lot}-{num}"
                        if send_telegram_alerts and clave_unica not in sent_individual_results:
                            sent_individual_results.add(clave_unica)
                            msg_ind = (
                                f"AG HAROLD JOSE RESULTADOS\n"
                                f"AGENCIA HAROLD JOSE - RESULTADOS\n\n"
                                f"🏛️ {lot.upper()} ({h_formatted})\n"
                                f"Resultado: {num} - {animal}\n\n"
                                f"Enlace: {CHANNEL_ID}"
                            )
                            bot.send_message(CHANNEL_ID, msg_ind)
        return True
    except Exception as e:
        print(f"Error en scraping: {e}")
        return False

def build_table_message():
    hours = sorted(list(results_storage.keys()))
    if not hours:
        hours = ["08:00", "09:00", "10:00", "11:00", "12:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00"]

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
                    row_line += f" {res['num']} {res['animal']}"
                else:
                    row_line += " .... 🚫"
            text += row_line + "\n"
        text += "\n"

    text += "MUCHA SUERTE EN SUS JUGADAS"
    return text

# ==========================================
# COMANDO DE PRUEBA INSTANTÁNEA EN TELEGRAM
# ==========================================
@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() in ['probar', 'test', 'actualizar'])
def cmd_probar(message):
    bot.reply_to(message, "🔄 Extrayendo resultados de la web y generando la tabla...")
    scrape_results(send_telegram_alerts=False)
    tabla_generada = build_table_message()
    bot.send_message(message.chat.id, tabla_generada)

# ==========================================
# AUTOMATIZACIÓN POR HORARIOS (MINUTO 10)
# ==========================================
def background_scheduler():
    while True:
        now = datetime.now()
        if now.minute == 10:
            scrape_results(send_telegram_alerts=True)
            tabla_auto = build_table_message()
            bot.send_message(CHANNEL_ID, tabla_auto)
            time.sleep(65)
        time.sleep(15)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=background_scheduler, daemon=True).start()
    print("🤖 Bot y servidor web iniciados correctamente...")
    bot.infinity_polling()
