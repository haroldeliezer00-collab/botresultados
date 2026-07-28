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
    return "¡El bot de resultados de la Agencia Harold José está activo y funcionando al 100%!"

# Diccionario oficial de abreviaturas (Excluyendo Ruleta Royal)
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

# Estructura en memoria para la tabla acumulada
results_storage = {}
sent_individual_results = set()

# Encabezado corporativo oficial para la tabla
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

# ==========================================
# GENERADORES DE MENSAJES AUTOMÁTICOS
# ==========================================

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
        "⚡ ¡La precisión y los números hablan por sí solos! ¡Juega con confianza y gana con nosotros! 🍀 💰"
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

def format_individual_message(loteria, hora, num, animal):
    return (
        "🎯 AG HAROLD JOSE 🎯\n\n"
        f"🎰 {loteria.upper()}\n"
        f"🕒 {hora}  {num} - {animal.upper()}\n"
        "https://t.me/resultadosagharoldjose"
    )

# ==========================================
# SCRAPER DE RESULTADOS (PRINCIPAL Y OFICIALES)
# ==========================================
def scrape_and_notify(send_alerts=False):
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
    
    import re
    for url in sources:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for tag in soup.find_all(['h3', 'h4', 'strong', 'div', 'span', 'li']):
                t = tag.get_text(strip=True)
                if "ruleta royal" in t.lower():
                    continue # Excluir Ruleta Royal explícitamente
                
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
                            
                            key_unique = f"{hour_key}-{lot}-{num}"
                            if send_alerts and key_unique not in sent_individual_results:
                                sent_individual_results.add(key_unique)
                                msg = format_individual_message(lot, h_formatted, num, animal)
                                bot.send_message(CHANNEL_ID, msg)
        except Exception as e:
            print(f"Error escrapeando {url}: {e}")

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
# COMANDOS DE TEST INDIVIDUALES EN TELEGRAM
# ==========================================
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
    bot.reply_to(message, "🔄 Ejecutando revisión en páginas oficiales...")
    scrape_and_notify(send_alerts=True)
    bot.reply_to(message, "✅ ¡Scraping de prueba finalizado!")

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() == 'test_final')
def test_fin(message):
    bot.send_message(message.chat.id, get_final_text())

@bot.message_handler(func=lambda message: message.text and message.text.lower().strip() in ['probar', 'test'])
def test_general(message):
    bot.reply_to(message, "🛠️ Comandos de test disponibles:\n- test_buenos_dias\n- test_piramide\n- test_7am\n- test_bcv\n- test_anuncio\n- test_tabla\n- test_scraping\n- test_final")

# ==========================================
# PLANIFICADOR AUTOMÁTICO POR HORARIOS
# ==========================================
def background_scheduler():
    last_min = -1
    while True:
        now = datetime.now()
        current_hour = now.hour
        current_min = now.minute
        current_w_time = now.strftime("%H:%M")
        
        if current_min != last_min:
            last_min = current_min
            
            # 6:30 AM - Buenos días
            if current_w_time == "06:30":
                bot.send_message(CHANNEL_ID, get_morning_greeting_text())
                
            # 6:31 AM - Pirámide
            elif current_w_time == "06:31":
                bot.send_message(CHANNEL_ID, generate_pyramid_text())
                
            # 7:00 AM - Mensaje 7am
            elif current_w_time == "07:00":
                bot.send_message(CHANNEL_ID, get_7am_text())
                
            # 6:30 AM y 6:30 PM - Tasa BCV (18:30)
            elif current_w_time in ["06:30", "18:30"] and current_min == 30:
                # Evita duplicar a las 6:30 AM con el de buenos días o maneja separado
                pass
            
            # 6:30 AM / 6:30 PM BCV específico
            if (current_hour == 6 and current_min == 30) or (current_hour == 18 and current_min == 30):
                bot.send_message(CHANNEL_ID, get_bcv_text())

            # 10:00 AM, 2:00 PM (14:00), 5:00 PM (17:00) - Anuncios importantes
            elif current_w_time in ["10:00", "14:00", "17:00"]:
                bot.send_message(CHANNEL_ID, get_announcement_text())
                
            # Minuto 10 de cada hora - Tabla acumulada
            elif current_min == 10:
                scrape_and_notify(send_alerts=True)
                bot.send_message(CHANNEL_ID, build_table_message())
                time.sleep(65)
                
            # 9:10 PM (21:10) - Cierre de jornada
            elif current_w_time == "21:10":
                bot.send_message(CHANNEL_ID, get_final_text())

        # Revisión continua de resultados cada 2 minutos en segundo plano
        scrape_and_notify(send_alerts=True)
        time.sleep(45)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=background_scheduler, daemon=True).start()
    print("🤖 Bot completo de la Agencia Harold José iniciado correctamente...")
    bot.infinity_polling()
