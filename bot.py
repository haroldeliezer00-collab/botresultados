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

# Enlaces oficiales adicionales para respaldo/verificación
ENLACES_OFICIALES = {
    "LOTTO ACTIVO": "https://www.lottoactivo.com/resultados/lotto_activo/",
    "GUACHARO ACTIVO": "https://www.guacharoactivo.com.ve/resultados",
    "LOTO CHAIMA": "https://lotochaima.com/",
    "LA GRANJITA": "https://lagranjitaonline.com/",
    "SELVA PLUS": "https://www.selvaplus.com/resultados",
    "MONJE MILLONARIO": "https://www.lottoactivo.com/resultados/lottoactivo2(monjemillonario)/",
    "LOTTO ACTIVO RD INTERNACIONAL": "https://www.lottoactivo.com/resultados/lotto_activo_internacional/",
    "GUACA ACTIVA": "https://lotery.winbigvzla.com/resultados",
    "MEGA GUACA": "https://lotery.winbigvzla.com/resultados",
    "EL GUACHARITO MILLONARIO": "https://elguacharitomillonario.com/"
}

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
    "LOTTO RD INTERNACIONAL": "Lotto Rd",
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

HEADER_TEXT = (
    "★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
    "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝙹𝙰 ⊱╮\n"
    "      Mas de 6 años brindando\n"
    "          confianza y seguridad\n"
    "  en cada rincón de Venezuela\n"
    "       ʀᴇꜱ𝚄𝙻𝚃𝙰ᴅᴏꜱ ᴏꜰ𝙸ᴄ𝙸ᴀʟᴇꜱ\n"
    "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
    "📲JUEGA AQUI👇👇\n"
    "WHATSAPP: 04124489363\n\n"
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
        f"Estado de la Taquilla Hoy: <b style='color: {color_estado};'>{estado_texto}</b><br><br>"
        "<b>Enlaces de prueba rápida (Test):</b><br>"
        "👉 <a href='/test/madrugada'>Probar Saludo de Madrugada (6:30 AM)</a><br>"
        "👉 <a href='/test/piramide'>Probar Pirámide Numérica (6:31 AM)</a><br>"
        "👉 <a href='/test/bcv'>Probar Tasa BCV (6:30 AM / 6:30 PM)</a><br>"
        "👉 <a href='/test/saludo'>Probar Saludo Matutino (7:00 AM)</a><br>"
        "👉 <a href='/test/taquilla'>Probar Aviso de Taquilla (10 AM, 2 PM, 5 PM)</a><br>"
        "👉 <a href='/test/resultados'>Forzar Revisión de Resultados</a><br>"
        "👉 <a href='/test/tabla'>Probar Tabla de Resultados (Minuto 10)</a><br>"
        "👉 <a href='/test/cierre'>Probar Mensaje de Cierre (9:10 PM)</a><br>"
        "👉 <a href='/test-refuerzo'>Probar Refuerzo de Taquilla (Tarde)</a>"
    )

@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "¡Prueba ejecutada! Se envió el saludo de madrugada al canal."

@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "¡Prueba ejecutada! Se envió la pirámide numérica al canal."

@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "¡Prueba ejecutada! Se envió la tasa del BCV al canal."

@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "¡Prueba ejecutada! Se envió el saludo matutino al canal."

@app.route('/test/taquilla')
def test_taquilla():
    enviar_aviso_taquilla()
    return "¡Prueba ejecutada! Se envió el aviso de taquilla al canal."

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "¡Prueba ejecutada! Se forzó la revisión de resultados."

@app.route('/test/tabla')
def test_tabla():
    verificar_resultados()
    enviar_tabla_resultados()
    return "¡Prueba ejecutada! Se actualizó y envió la tabla de resultados al canal."

@app.route('/test/cierre')
def test_cierre():
    enviar_mensaje_cierre()
    return "¡Prueba ejecutada! Se envió el mensaje de cierre al canal."

@app.route('/test-refuerzo')
def test_refuerzo():
    tarea_refuerzo_tarde()
    return "Prueba de refuerzo ejecutada manualmente."

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
    print("🧹 Memoria de resultados y estado de taquilla limpiados para arrancar el nuevo día.")

def activar_taquilla_proceso():
    global taquilla_activa_hoy, imagen_activa_id
    if not imagen_activa_id:
        return
    taquilla_activa_hoy = True
    print(f"¡Taquilla activada manualmente desde el canal!")
    try:
        bot.send_photo(
            chat_id=CANAL,
            photo=imagen_activa_id,
            caption=TEXTO_TAQUILLA
        )
        print("Mensaje de taquilla activa enviado al canal con éxito.")
    except Exception as e:
        print(f"Error al enviar la taquilla al canal: {e}")

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

def tarea_refuerzo_tarde():
    global taquilla_activa_hoy, imagen_activa_id
    if taquilla_activa_hoy and imagen_activa_id:
        try:
            bot.send_photo(
                chat_id=CANAL,
                photo=imagen_activa_id,
                caption=TEXTO_TAQUILLA + "\n\n🔄 *¡Seguimos activos con la jornada de la tarde!*",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error al enviar refuerzo de tarde: {e}")

def enviar_saludo_madrugada():
    mensaje = (
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n\n"
        "🌅 ¡Despertando con la mejor energía y listos para ganar! 🌅\n\n"
        "Comenzamos este nuevo día activos, enfocados y con los mejores datos para asegurar cada jugada. ¡Que la suerte esté de nuestro lado desde temprano! 🍀🔥"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

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
        dots_count = 3 + (i * 2)
        dots = "." * dots_count
        lineas_formateadas.append(f"{dots}   {nums_str}   {dots}")
    
    cuerpo_piramide = "\n".join(lineas_formateadas)
    
    seed_val = int(ahora.strftime("%Y%m%d"))
    rnd = random.Random(seed_val)
    
    candidates = []
    for f in filas:
        for idx in range(len(f) - 1):
            val = (f[idx] * 10 + f[idx+1]) % 37
            candidates.append(f"{val:02d}")
        for num in f:
            val2 = (num * 7 + idx) % 37
            candidates.append(f"{val2:02d}")
            
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
    
    mensaje = (
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n"
        "📢 REPORTE TÁCTICO - LA PIRÁMIDE 📢\n\n"
        f"📅 Fecha: {fecha_str}\n"
        "Análisis matemático actualizado y listo para la jugada. ¡A asegurar posición:\n\n"
        f"{cuerpo_piramide}\n\n"
        "🔥 DATOS CLAVES PARA HOY:\n"
        f"📌 {d1}\n"
        f"📌 {d2}\n\n"
        "⚡ ¡La precisión y los números hablan por sí solos! ¡Juega con confianza y gana con nosotros! 🍀 💰"
    )
    return mensaje

def enviar_piramide_diaria():
    mensaje = generar_piramide()
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_tasa_dolar():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        precio_dolar = "No disponible"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            dolar_div = soup.find('div', id='dolar')
            if dolar_div:
                strong_elem = dolar_div.find('strong')
                if strong_elem:
                    precio_dolar = strong_elem.get_text(strip=True)

        mensaje = (
            "💵 TASA OFICIAL BCV 💵\n\n"
            "🏦 Moneda: Dólar Estadounidense\n"
            f"📈 Precio Oficial: Bs. {precio_dolar}\n\n"
            "🔗 Fuente: Banco Central de Venezuela"
        )
        enviar_telegram(mensaje, disable_web_preview=True)
    except Exception as e:
        print(f"⚠️ Error en tasa BCV: {e}")

def enviar_saludo_matutino():
    mensaje = (
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n"
        "🌅 ¡Buenos días a todos! 🌅\n\n"
        "Ya arrancamos un nuevo día con la mejor energía. "
        "Por aquí estaremos compartiendo todos los resultados de los animalitos a medida que vayan saliendo.\n\n"
        "📢 Nuestros canales oficiales:\n"
        "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
        "📸 Instagram: https://www.instagram.com/agharold.jose (@agharold.jose)\n"
        "💬 Canal de WhatsApp: https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
        "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

def enviar_aviso_taquilla():
    mensaje_promo = (
        "🎯 AGENCIA HAROLD JOSE 🎯\n"
        "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
        "📢 ¡AVISO IMPORTANTE PARA NUESTROS JUGADORES! 📢\n\n"
        "Recuerda que para jugar con nosotros debes acceder primero al Canal de WhatsApp para verificar si la taquilla se encuentra activa el día de hoy:\n"
        "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
        "📲 Si la taquilla está activa, puedes revisar nuestro catálogo y escribirnos directamente:\n"
        "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n\n"
        "💬 También estamos disponibles por Telegram:\n"
        "👉 t.me/pruebajsj\n\n"
        "¡Mucha suerte en sus jugadas! 🍀🔥"
    )
    enviar_telegram(mensaje_promo, disable_web_preview=True)

def enviar_mensaje_cierre():
    mensaje = (
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n"
        "🌙 ¡FINAL DE JORNADA! 🌙\n\n"
        "Estos fueron todos los resultados del día de hoy. ¡Gracias por jugar con nosotros! Los esperamos el día de mañana con mucha más suerte y energía. 🍀✨"
    )
    enviar_telegram(mensaje, disable_web_preview=True)

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
    if not ampm:
        if 1 <= h <= 7:
            h += 12
    if 8 <= h <= 19:
        return f"{h:02d}:00"
    return None

def formatear_hora_tabla(h_str):
    try:
        h_part = int(h_str.split(":")[0])
        if h_part == 0:
            h_12 = 12
        elif h_part > 12:
            h_12 = h_part - 12
        else:
            h_12 = h_part
        return f"{h_12:02d}:00"
    except:
        return h_str

# --- CONSTRUCCIÓN DE LA TABLA DE RESULTADOS (DISEÑO COMPACTO Y ALINEADO) ---
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
        header_line = "HORA🏛️"
        for lot in group:
            abbr = ABBR_MAP.get(lot, lot[:5])
            header_line += f"⚪{abbr}" # Sin espacio antes del círculo blanco
        text += header_line + "\n"

        for h in hours:
            h_display = formatear_hora_tabla(h) # "08:00"
            row_line = f"⏰{h_display}  " # Hora pegada al reloj, seguida de 2 espacios de separación
            for lot in group:
                res = results_storage.get(h, {}).get(lot)
                if res:
                    num = res['num']
                    emoji = res['info'][1]
                    # Número y animalito completamente pegados, seguidos de 3 espacios hacia la siguiente columna
                    row_line += f"{num}{emoji}   "
                else:
                    # Sin resultado, con el mismo espaciado uniforme
                    row_line += f"....🚫   "
            text += row_line.rstrip() + "\n" # Limpiar espacios sobrantes al final de cada fila
        text += "\n"

    text += "MUCHA SUERTE EN SUS JUGADAS"
    return text

def enviar_tabla_resultados():
    try:
        tabla_msg = build_table_message()
        enviar_telegram(tabla_msg, disable_web_preview=True)
        print("📊 Tabla horaria de resultados enviada al canal.")
    except Exception as e:
        print(f"⚠️ Error al enviar tabla de resultados: {e}")

# --- RASPADO WEB Y ACTUALIZACIÓN EN TIEMPO REAL ---
def verificar_resultados():
    global resultados_enviados, primera_ejecucion, results_storage
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            for nombre_ofi, url_ofi in ENLACES_OFICIALES.items():
                try:
                    res_ofi = requests.get(url_ofi, headers=headers, timeout=10, verify=False)
                    if res_ofi.status_code == 200:
                        pass
                except:
                    pass
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))

        nuevos_encontrados = []

        for tarjeta in tarjetas:
            nombre_loteria = ""
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
                    if t_text not in ["WINBIG", "RESULTADOS"]:
                        nombre_loteria = t_text
                        break

            if not nombre_loteria:
                lineas = [l.strip().upper() for l in tarjeta.get_text("\n", strip=True).split("\n") if l.strip()]
                for linea in lineas:
                    if len(linea) > 2 and not re.search(r'\d{1,2}:\d{2}', linea) and "PENDIENTE" not in linea and "-" not in linea:
                        nombre_loteria = linea
                        break

            if not nombre_loteria or len(nombre_loteria) > 40:
                continue

            nombre_loteria = limpiar_texto(nombre_loteria)
            matched_key_lot = obtener_clave_estandar(nombre_loteria)

            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', texto_slot)
                if not match_h:
                    continue
                hora_cruda = match_h.group(1).upper()
                hora_normalizada = normalizar_hora_tabla(hora_cruda)
                if not hora_normalizada:
                    continue

                match_res = re.search(r'(\d{1,2}\s*[-–—]\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado_final = limpiar_texto(match_res.group(1)).upper()
                
                # Aceptar números de 1 o 2 dígitos (Soporta Guácharo Activo y otros rangos)
                num_m = re.search(r'\b(\d{1,2})\b', resultado_final)
                if num_m:
                    num_val = num_m.group(1).zfill(2)
                    # Buscar animalito o asignar un icono por defecto si el número es superior a 36
                    animal_info = ANIMAL_DATA.get(num_val, ("ANIMAL", "🐾"))
                    
                    if hora_normalizada not in results_storage:
                        results_storage[hora_normalizada] = {}
                    
                    results_storage[hora_normalizada][matched_key_lot] = {'num': num_val, 'info': animal_info}

                clave = (nombre_loteria, hora_cruda, resultado_final)

                if primera_ejecucion:
                    resultados_enviados.add(clave)
                else:
                    if clave not in resultados_enviados:
                        item_dict = {'loteria': nombre_loteria, 'hora': hora_cruda, 'resultado': resultado_final}
                        if item_dict not in nuevos_encontrados:
                            nuevos_encontrados.append(item_dict)
                            resultados_enviados.add(clave)

        if primera_ejecucion:
            primera_ejecucion = False
            print(f"🚀 Sincronización inicial lista. Total registros base: {len(resultados_enviados)}")
            return

        for item_nuevo in nuevos_encontrados:
            mensaje = (
                "🎯 AG HAROLD JOSE 🎯\n\n"
                f"🎰 {item_nuevo['loteria']}\n"
                f"🕒 {item_nuevo['hora']}  {item_nuevo['resultado']}"
            )
            enviar_telegram(mensaje, disable_web_preview=True)
            time.sleep(3)

    except Exception as e:
        print(f"⚠️ Error general en resultados: {e}")

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
    
    schedule.every().day.at("15:30").do(tarea_refuerzo_tarde)
    schedule.every().day.at("18:30").do(enviar_tasa_dolar)
    schedule.every().day.at("21:10").do(enviar_mensaje_cierre)

    schedule.every().hour.at(":10").do(enviar_tabla_resultados)
    schedule.every(1).minute.do(verificar_resultados)

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
