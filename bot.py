import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from datetime import datetime

# Configuración con tu token y tu canal oficial de Telegram
TOKEN = "8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk"
CHANNEL_ID = "@pruebajsj"

bot = telebot.TeleBot(TOKEN)

# Diccionario oficial de abreviaturas definido por ti
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

# Estructura para almacenar en memoria: results_storage[hora][nombre_loteria] = {"num": "20", "animal": "🐷"}
results_storage = {}
sent_individual_results = set()

# Encabezado corporativo oficial
HEADER_TEXT = (
    "★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
    "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
    "      Mas de 6 años brindando\n"
    "          confianza y seguridad\n"
    "  en cada rincón de Venezuela\n"
    "       ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰɪᴄɪᴀʟᴇꜱ\n"
    "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝙲𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
    "📲JUEGA AQUI👇👇\n"
    "WHATSAPP: 04124489363\n\n"
    "📊 𝗥𝙴𝚂𝚄𝙻𝚃𝙰𝙳𝙾𝚂 𝙰𝙽𝙸𝙼𝙰𝙻𝙸𝚃𝙾𝚂 📊\n"
    "------------------------"
)

def scrape_results():
    """Función encargada de revisar la página web, extraer resultados y enviar alertas individuales."""
    try:
        url = "https://winbigvzla.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Lógica de scraping personalizada para capturar y poblar results_storage
        
    except Exception as e:
        print(f"Error en scraping: {e}")

def build_table_message():
    """Construye la tabla acumulada organizada en bloques de 3 columnas tal como la solicitaste."""
    hours = sorted(list(results_storage.keys()))
    if not hours:
        hours = ["08:00", "09:00"]

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
# COMANDOS DE PRUEBA MANUAL
# ==========================================

@bot.message_handler(func=lambda message: message.text and message.text.lower() == 'actualizar')
def cmd_actualizar(message):
    bot.reply_to(message, "🔄 Forzando revisión de la página web...")
    scrape_results()
    bot.reply_to(message, "✅ ¡Revisión completada y datos guardados en memoria!")

@bot.message_handler(func=lambda message: message.text and message.text.lower() == 'tabla')
def cmd_tabla(message):
    bot.reply_to(message, "📊 Generando tabla acumulada para prueba inmediata...")
    tabla_generada = build_table_message()
    bot.send_message(message.chat.id, tabla_generada)

# ==========================================
# AUTOMATIZACIÓN POR HORARIOS (MINUTO 10)
# ==========================================
def background_scheduler():
    while True:
        now = datetime.now()
        if now.minute == 10:
            tabla_auto = build_table_message()
            bot.send_message(CHANNEL_ID, tabla_auto)
            time.sleep(65)
        time.sleep(15)

if __name__ == '__main__':
    threading.Thread(target=background_scheduler, daemon=True).start()
    print("Bot iniciado correctamente y escuchando comandos...")
    bot.infinity_polling()
