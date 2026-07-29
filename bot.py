import os
# Forzar la zona horaria de Venezuela para que el bot use la hora local exacta
os.environ['TZ'] = 'America/Caracas'
try:
    import time
    time.tzset()
except AttributeError:
    pass # Compatible por si se prueba en Windows local

import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask, render_template_string
import re
import urllib3
from datetime import datetime
import random
import telebot
import unicodedata

# Desactivar advertencias de certificados SSL por seguridad con páginas del Estado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Credenciales y canal principal actualizado
TOKEN = '8698848083:AAGa5S9cBp_E8UYSMskNDiC76P3qLY12HJA'
CANAL = '@pruebajsj'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

# --- FUNCIÓN PARA REMOVER ACENTOS Y NORMALIZAR TEXTO ---
def normalizar_cadena(texto):
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFD', str(texto))
    texto_sin_acentos = "".join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    return texto_sin_acentos.upper().strip()

# --- MAPA DE ALIAS PARA MAPEAR NOMBRES WEB A LA TABLA ---
ALIAS_LOTERIA = {
    "LA GRANJITA": "La Granjita",
    "GRANJITA": "La Granjita",
    "LOTTO ACTIVO": "Lotto Activo",
    "SELVA PLUS": "Selva Plus",
    "SELVA": "Selva Plus",
    "GUACHARO ACTIVO": "Guácharo Activo",
    "GUACHARO": "Guácharo Activo",
    "EL GUACHARO": "Guácharo Activo",
    "LOTO CHAIMA": "Loto Chaima",
    "CHAIMA": "Loto Chaima",
    "MONJE MILLONARIO": "Monje Millonario",
    "MONJE": "Monje Millonario",
    "EL MONJE": "Monje Millonario",
    "LOTTO ANIMALITO": "Lotto Animalito",
    "ANIMALITO": "Lotto Animalito",
    "LOTTO PANTERA": "Lotto Pantera",
    "PANTERA": "Lotto Pantera",
    "LOTTO REAL": "Lotto Real",
    "REAL": "Lotto Real",
    "LOTTO RD": "Lotto Rd",
    "CENTENA ANIMALITOS": "Centena Animalitos",
    "MEGA ANIMAL": "Mega Animal",
    "RULETON PERU": "Ruleton Perú",
    "RULETON COLOMBIA": "Ruleton Colombia",
    "RULETON VENEZUELA": "Ruleton Venezuela",
    "CONDOR GANA": "Cóndor Gana",
    "FRUTI GANA": "Fruti Gana",
    "TROPI GANA": "Tropi Gana",
    "GRANJA MILLONARIA": "Granja Millonaria",
    "ZOOLOGICO ACTIVO": "Zoológico Activo",
    "LOTTO MAX": "Lotto Max"
}

# --- DICCIONARIOS Y CONFIGURACIÓN PARA LA TABLA DE RESULTADOS ---
ABBR_MAP = {
    "La Granjita": "GRAJ",
    "Lotto Activo": "L.ACT",
    "Selva Plus": "SELV",
    "Guácharo Activo": "G.ARO",
    "Loto Chaima": "CHAIMA",
    "Monje Millonario": "MONJE",
    "Lotto Animalito": "L.ANI",
    "Lotto Pantera": "L.PAN",
    "Lotto Real": "L.REA",
    "Lotto Rd": "L.RD",
    "Centena Animalitos": "C.ANI",
    "Mega Animal": "MEGA",
    "Ruleton Perú": "R.PER",
    "Ruleton Colombia": "R.COL",
    "Ruleton Venezuela": "R.VEN",
    "Cóndor Gana": "COND",
    "Fruti Gana": "FRUT",
    "Tropi Gana": "TROP",
    "Granja Millonaria": "G.MIL",
    "Zoológico Activo": "ZOOL",
    "Lotto Max": "L.MAX"
}

def obtener_clave_estandar(nombre_raw):
    norm = normalizar_cadena(nombre_raw)
    if norm in ALIAS_LOTERIA:
        return ALIAS_LOTERIA[norm]
    for alias, key_std in ALIAS_LOTERIA.items():
        if alias in norm or norm in alias:
            return key_std
    for lot_key in ABBR_MAP.keys():
        if normalizar_cadena(lot_key) in norm or norm in normalizar_cadena(lot_key):
            return lot_key
    return nombre_raw

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

# --- ENCABEZADO SIMPLIFICADO Y LIMPIO ---
HEADER_TEXT = (
    "★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
    "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝙹𝙰 ⊱╮\n"
    "📲 JUEGA AQUI WHATSAPP: 04124489363\n\n"
    "📊 𝗥𝙴𝚂𝚄𝙻𝚃𝙰𝙳𝙾𝚂 𝙰𝙽𝙸𝙼𝙰𝙻𝙸𝚃𝙾𝚂 📊\n"
    "------------------------"
)

taquilla_activa_hoy = False
imagen_activa_id = None
ultimo_id_foto_canal = None

TEXTO_TAQUILLA = (
    "✅ AG HAROLD JOSÉ ACTIVA ✅\n"
    "Ya estamos operativos brindando la mejor atención. Calidad, respaldo y rapidez en cada una de todas tus solicitudes.\n\n"
    "📲 Envía tus jugadas:\n"
    "(Comprobante de pago / Lotería / monto / Hora)\n\n"
    "📖 Consulta nuestro reglamento aquí:\n"
    "https://wa.me/p/33319103291071105/584124489363\n"
    "🚀 Agiliza tu proceso aquí: https://wa.me/p/24724650613899486/584124489363\n\n"
    "RESULTADOS AUTOMÁTICOS\n"
    "https://t.me/pruebajsj\n\n"
    "¡Mucho éxito en la jornada de hoy! 🍀✨"
)

app = Flask('')

@app.route('/')
def home():
    estado_texto = "ACTIVA" if taquilla_activa_hoy else "INACTIVA"
    color_estado = "green" if taquilla_activa_hoy else "red"
    return (
        f"¡El bot de resultados AG HAROLD JOSE está activo en el canal @pruebajsj!<br>"
        f"Estado de la Taquilla Hoy: <b style='color: {color_estado};'>{estado_texto}</b>"
    )

resultados_enviados = set()
primera_ejecucion = True

def limpiar_texto(texto):
    return " ".join(texto.split())

def enviar_telegram(mensaje, disable_web_preview=True):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL, 
        "text": mensaje, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": disable_web_preview
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar al canal: {response.text}")
    except Exception as e:
        print(f"⚠️ Excepción de conexión con Telegram: {e}")

def limpiar_memoria_diaria():
    global resultados_enviados, primera_ejecucion, taquilla_activa_hoy, imagen_activa_id, ultimo_id_foto_canal, results_storage
    resultados_enviados.clear()
    results_storage.clear()
    primera_ejecucion = True
    taquilla_activa_hoy = False
    imagen_activa_id = None
    ultimo_id_foto_canal = None
    print("🧹 Memoria limpiada para el nuevo día.")

def activar_taquilla_proceso():
    global taquilla_activa_hoy, imagen_activa_id
    if not imagen_activa_id:
        return
    taquilla_activa_hoy = True
    try:
        bot.send_photo(chat_id=CANAL, photo=imagen_activa_id, caption=TEXTO_TAQUILLA)
    except Exception as e:
        print(f"Error al enviar taquilla: {e}")

@bot.channel_post_handler(content_types=['photo'])
def capturar_foto_canal(message):
    global ultimo_id_foto_canal, imagen_activa_id
    if message.photo:
        ultimo_id_foto_canal = message.photo[-1].file_id
    caption = message.caption if message.caption else ""
    if "taquilla activa" in caption.lower():
        imagen_activa_id = ultimo_id_foto_canal
        activar_taquilla_proceso()

@bot.channel_post_handler(content_types=['text'])
def capturar_texto_canal(message):
    global imagen_activa_id, ultimo_id_foto_canal
    text = message.text if message.text else ""
    if "taquilla activa" in text.lower():
        if ultimo_id_foto_canal:
            imagen_activa_id = ultimo_id_foto_canal
            activar_taquilla_proceso()

def enviar_saludo_madrugada():
    enviar_telegram("🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n\n🌅 ¡Despertando con la mejor energía y listos para ganar! 🌅\n\nComenzamos este nuevo día activos y con los mejores datos. ¡Que la suerte esté de nuestro lado! 🍀🔥", disable_web_preview=True)

def generar_piramide():
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d/%m/%Y")
    digitos = [int(c) for c in fecha_str if c.isdigit()]
    filas = [digitos]
    while len(filas[-1]) > 1:
        actual = filas[-1]
        siguiente = [(actual[i] + actual[i+1]) % 10 for i in range(len(actual) - 1)]
        filas.append(siguiente)
    lineas_formateadas = []
    for i, f in enumerate(filas):
        nums_str = "  ".join(str(d) for d in f)
        dots = "." * (3 + (i * 2))
        lineas_formateadas.append(f"{dots}   {nums_str}   {dots}")
    cuerpo_piramide = "\n".join(lineas_formateadas)
    seed_val = int(ahora.strftime("%Y%m%d"))
    rnd = random.Random(seed_val)
    candidates = []
    for f in filas:
        for idx in range(len(f) - 1):
            val = (f[idx] * 10 + f[idx+1]) % 37
            candidates.append(f"{val:02d}")
    unique_candidates = []
    for c in candidates:
        if c not in unique_candidates:
            unique_candidates.append(c)
    while len(unique_candidates) < 6:
        val_rand = rnd.randint(0, 36)
        c_rand = f"{val_rand:02d}"
        if c_rand not in unique_candidates:
            unique_candidates.append(c_rand)
    d1 = f"{unique_candidates[0]}-{unique_candidates[1]}-{unique_candidates[2]}"
    d2 = f"{unique_candidates[3]}-{unique_candidates[4]}-{unique_candidates[5]}"
    return (
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n"
        "📢 REPORTE TÁCTICO - LA PIRÁMIDE 📢\n\n"
        f"📅 Fecha: {fecha_str}\n\n"
        f"{cuerpo_piramide}\n\n"
        "🔥 DATOS CLAVES:\n"
        f"📌 {d1}\n"
        f"📌 {d2}\n"
    )

def enviar_piramide_diaria():
    enviar_telegram(generar_piramide(), disable_web_preview=True)

def enviar_tasa_dolar():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        precio_dolar = "No disponible"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            dolar_div = soup.find('div', id='dolar')
            if dolar_div and dolar_div.find('strong'):
                precio_dolar = dolar_div.find('strong').get_text(strip=True)
        enviar_telegram(f"💵 TASA OFICIAL BCV 💵\n\n🏦 Dólar Estadounidense\n📈 Bs. {precio_dolar}\n🔗 Fuente: BCV", disable_web_preview=True)
    except Exception as e:
        print(f"⚠️ Error BCV: {e}")

def enviar_saludo_matutino():
    enviar_telegram("🎯 AGENCIA HAROLD JOSE 🎯\n\n🌅 ¡Buenos días! Arrancamos la jornada con la mejor energía.\n\n🎟️ Catálogo: https://wa.me/c/584124489363\n📸 Instagram: https://www.instagram.com/agharold.jose", disable_web_preview=True)

def enviar_aviso_taquilla():
    enviar_telegram("🎯 AGENCIA HAROLD JOSE 🎯\n\n📢 ¡RECUERDA VERIFICAR NUESTRA TAQUILLA ACTIVA HOY EN NUESTRO CANAL DE WHATSAPP!\n👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T", disable_web_preview=True)

def enviar_mensaje_cierre():
    enviar_telegram("🎯 AGENCIA HAROLD JOSE 🎯\n\n🌙 ¡FINAL DE JORNADA! Gracias por jugar con nosotros. ¡Feliz noche! 🍀✨", disable_web_preview=True)

def normalizar_hora_tabla(hora_str):
    hora_str = hora_str.upper().strip()
    m = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', hora_str)
    if not m:
        return None
    h = int(m.group(1))
    ampm = m.group(3)
    if ampm == 'PM' and h < 12:
        h += 12
    elif ampm == 'AM' and h == 12:
        h = 0
    elif 1 <= h <= 7:
        h += 12
    if 8 <= h <= 19:
        return f"{h:02d}:00"
    return None

def formatear_hora_tabla(h_str):
    try:
        h_part = int(h_str.split(":")[0])
        if h_part == 0:
            return "12:00"
        elif h_part > 12:
            return f"{h_part - 12:02d}:00"
        return f"{h_part:02d}:00"
    except:
        return h_str

# --- CONSTRUCCIÓN DE TABLA COMPACTA (UNA SOLA LÍNEA POR GRUPO) ---
def build_table_message():
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

    text = HEADER_TEXT + "\n"

    for group in groups:
        abbrs = [ABBR_MAP.get(lot, lot[:4]) for lot in group]
        header_line = "HORA " + " . ".join(abbrs)
        text += header_line + "\n"

        for h in hours:
            h_display = formatear_hora_tabla(h)
            row_line = f"{h_display} "
            for lot in group:
                res = results_storage.get(h, {}).get(lot)
                if res:
                    num = res['num']
                    emoji = res['info'][1]
                    row_line += f" {num}{emoji} "
                else:
                    row_line += f" ....🚫"
            text += row_line.rstrip() + "\n"
        text += "\n"

    text += "MUCHA SUERTE EN SUS JUGADAS"
    return text

def enviar_tabla_resultados():
    # Solo enviar la tabla si estamos dentro del horario operativo (8 AM a 8 PM)
    hora_actual = datetime.now().hour
    if 8 <= hora_actual <= 20:
        try:
            enviar_telegram(build_table_message(), disable_web_preview=True)
        except Exception as e:
            print(f"⚠️ Error tabla: {e}")

# --- RASPADO AISLADO POR CADA CONTENEDOR DE LOTERÍA ---
def verificar_resultados():
    global resultados_enviados, primera_ejecucion, results_storage
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        resp = requests.get(URL_LOTERIA, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            return
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Buscar tarjetas o bloques individuales de cada lotería en la página
        contenedores = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'card|box|lottery|panel|content|item', re.IGNORECASE))
        if not contenedores:
            contenedores = [soup]

        for cont in contenedores:
            texto_cont = cont.get_text(" ", strip=True)
            
            # Identificar a qué lotería pertenece este bloque específico
            loteria_encontrada = None
            for key_oficial in ABBR_MAP.keys():
                if normalizar_cadena(key_oficial) in normalizar_cadena(texto_cont[:120]) or \
                   any(alias in normalizar_cadena(texto_cont[:120]) for alias, std in ALIAS_LOTERIA.items() if std == key_oficial):
                    loteria_encontrada = key_oficial
                    break
            
            if not loteria_encontrada:
                header_tag = cont.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                if header_tag:
                    loteria_encontrada = obtener_clave_estandar(header_tag.get_text())

            if loteria_encontrada and loteria_encontrada in ABBR_MAP:
                # Extraer filas o elementos de hora y número únicamente DENTRO de este bloque
                filas = cont.find_all(['div', 'li', 'tr', 'p', 'span'], class_=re.compile(r'item|row|slot|result|hora|data', re.IGNORECASE))
                if not filas:
                    filas = [cont]

                for fila in filas:
                    t_texto = fila.get_text(" ", strip=True).upper()
                    if "PENDIENTE" in t_texto:
                        continue
                    match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', t_texto)
                    match_res = re.search(r'\b(\d{1,2})\b', t_texto)
                    if match_h and match_res:
                        hora_norm = normalizar_hora_tabla(match_h.group(1))
                        num_val = match_res.group(1).zfill(2)
                        if hora_norm and int(num_val) <= 36:
                            animal_info = ANIMAL_DATA.get(num_val, ("ANIMAL", "🐾"))
                            if hora_norm not in results_storage:
                                results_storage[hora_norm] = {}
                            
                            # Guardado estricto e independiente por lotería
                            results_storage[hora_norm][loteria_encontrada] = {'num': num_val, 'info': animal_info}

    except Exception as e:
        print(f"⚠️ Error en raspado: {e}")

    if primera_ejecucion:
        primera_ejecucion = False
        print("🚀 Sincronización inicial completada.")

def loop_bot():
    verificar_resultados()

    schedule.every().day.at("00:00").do(limpiar_memoria_diaria)
    schedule.every().day.at("06:30").do(enviar_saludo_madrugada)
    schedule.every().day.at("06:31").do(enviar_piramide_diaria)
    schedule.every().day.at("06:30").do(enviar_tasa_dolar)
    schedule.every().day.at("07:00").do(enviar_saludo_matutino)
    schedule.every().day.at("10:00").do(enviar_aviso_taquilla)
    schedule.every().day.at("14:00").do(enviar_aviso_taquilla)
    schedule.every().day.at("17:00").do(enviar_aviso_taquilla)
    schedule.every().day.at("18:30").do(enviar_tasa_dolar)
    schedule.every().day.at("21:10").do(enviar_mensaje_cierre)

    # Envío automático de la tabla cada hora al minuto 10 (restringido de 8 AM a 8 PM)
    schedule.every().hour.at(":10").do(enviar_tabla_resultados)
    schedule.every(2).minutes.do(verificar_resultados)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    t_schedule = Thread(target=loop_bot)
    t_schedule.daemon = True
    t_schedule.start()

    t_bot = Thread(target=lambda: bot.infinity_polling(skip_pending=True))
    t_bot.daemon = True
    t_bot.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
