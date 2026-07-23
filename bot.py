import os
# Forzar la zona horaria de Venezuela para que el bot use tu hora local exacta
os.environ['TZ'] = 'America/Caracas'
try:
    import time
    time.tzset()
except AttributeError:
    pass # Compatible por si lo pruebas en Windows local

import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3

# Desactivar advertencias de certificados SSL por seguridad con páginas del Estado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = '8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk'
CANAL_ID = '@pruebajsj'
URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'
URL_POLLA_TARDE = 'https://srq.es/polla/superpollatarde'

app = Flask('')

@app.route('/')
def home():
    return (
        "¡El bot de resultados AG HAROLD JOSE está activo y blindado!<br><br>"
        "<b>Enlaces de prueba rápida:</b><br>"
        "👉 <a href='/test/saludo'>Probar Saludo Matutino</a><br>"
        "👉 <a href='/test/taquilla'>Probar Aviso de Taquilla</a><br>"
        "👉 <a href='/test/polla'>Probar Súper Polla Tarde (2:00 PM)</a><br>"
        "👉 <a href='/test/pozo'>Probar Pozo Millonario (2:00 PM)</a><br>"
        "👉 <a href='/test/recordatorio'>Probar Recordatorios Bloque 2:00 PM (Súper Polla + Pozo)</a><br>"
        "👉 <a href='/test/micro3pm'>Probar Micro Polla 3:00 PM</a><br>"
        "👉 <a href='/test/grandupleta'>Probar Gran Dupleta 4:00 PM</a><br>"
        "👉 <a href='/test/dupletamillonaria'>Probar Dupleta Millonaria 4:00 PM</a><br>"
        "👉 <a href='/test/minipolla'>Probar Mini Polla 4:00 PM</a><br>"
        "👉 <a href='/test/micro6pm'>Probar Micro Polla 5:00 PM</a><br>"
        "👉 <a href='/test/bcv'>Probar Tasa BCV</a><br>"
        "👉 <a href='/test/resultados'>Forzar Revisión de Resultados</a>"
    )

# --- RUTAS DE PRUEBA MANUAL ---
@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "¡Prueba ejecutada! Se envió el saludo matutino."

@app.route('/test/taquilla')
def test_taquilla():
    enviar_aviso_taquilla()
    return "¡Prueba ejecutada! Se envió el aviso de taquilla."

@app.route('/test/polla')
def test_polla():
    enviar_super_polla()
    return "¡Prueba ejecutada! Se envió la Súper Polla Tarde."

@app.route('/test/pozo')
def test_pozo():
    enviar_pozo_millonario()
    return "¡Prueba ejecutada! Se envió el Pozo Millonario."

@app.route('/test/recordatorio')
def test_recordatorio():
    enviar_lote_recordatorios_2pm()
    return "¡Prueba ejecutada! Se enviaron los recordatorios de Súper Polla y Pozo Millonario."

@app.route('/test/micro3pm')
def test_micro3pm():
    enviar_micro_polla_3pm()
    return "¡Prueba ejecutada! Micro Polla 3PM enviada."

@app.route('/test/grandupleta')
def test_grandupleta():
    enviar_gran_dupleta()
    return "¡Prueba ejecutada! Gran Dupleta enviada."

@app.route('/test/dupletamillonaria')
def test_dupletamillonaria():
    enviar_dupleta_millonaria()
    return "¡Prueba ejecutada! Dupleta Millonaria enviada."

@app.route('/test/minipolla')
def test_minipolla():
    enviar_mini_polla()
    return "¡Prueba ejecutada! Mini Polla enviada."

@app.route('/test/micro6pm')
def test_micro6pm():
    enviar_micro_polla_6pm()
    return "¡Prueba ejecutada! Micro Polla 6PM enviada."

@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "¡Prueba ejecutada! Se envió la tasa del BCV."

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "¡Prueba ejecutada! Se forzó la revisión de los resultados."
# -----------------------------

resultados_enviados = set()
primera_ejecucion = True

ANIMAL_EMOJIS = {
    'CARNERO': '🐏', 'TORO': '🐂', 'CIEMPIÉS': '🐛', 'CIEMPIES': '🐛',
    'ALACRAN': '🦂', 'LEÓN': '🦁', 'LEON': '🦁', 'RANA': '🐸', 
    'PERICO': '🦜', 'CHIVO': '🐐', 'COCHINO': '🐖', 'GALLO': '🐓', 
    'CARACOL': '🐌', 'CULEBRA': '🐍', 'ZAMURO': '🐦‍⬛', 'GATO': '🐈', 
    'BALLENA': '🐋', 'CAIMAN': '🐊', 'CAIMÁN': '🐊', 'ÁGUILA': '🦅', 
    'AGUILA': '🦅', 'TIGRE': '🐅', 'PAVO': '🦃', 'PAVITO': '🦃',
    'PAVO REAL': '🦚', 'BURRO': '🫏', 'MONO': '🐵', 'IGUANA': '🦎', 
    'BUFALO': '🐃', 'BÚFALO': '🐃', 'GALLINA': '🐔', 'VACA': '🐄', 
    'PERRO': '🐶', 'ZORRO': '🦊', 'OSO': '🐻', 'PESCADO': '🐟', 
    'CEBRA': '🦓', 'ZEBRA': '🦓', 'VENADO': '🦌', 'CIERVO': '🦌',
    'CAMELLO': '🐫', 'CAMELOS': '🐫', 'DELFIN': '🐬', 'DÉLFIN': '🐬',
    'BISONTE': '🦬', 'HORMIGA': '🐜', 'AVISPA': '🐝', 'GRILLO': '🦗', 
    'PUERCOESPIN': '🦔', 'PUERCOESPÍN': '🦔', 'ELEFANTE': '🐘',
    'LECHUZA': '🦉', 'PALOMA': '🐦', 'JIRAFA': '🦒', 'RATON': '🐭',
    'RATÓN': '🐭', 'CISNE': '🦢', 'PATO': '🦆', 'CONEJO': '🐰',
    'CABALLO': '🐎', 'PANTERA': '🐆', 'PUMA': '🐆', 'CUCARACHA': '🪳'
}

def limpiar_texto(texto):
    return " ".join(texto.split())

def obtener_emoji(resultado_texto):
    partes = resultado_texto.split('-')
    if len(partes) > 1:
        nombre_animal = partes[1].strip().upper()
        return ANIMAL_EMOJIS.get(nombre_animal, '')
    return ''

def limpiar_memoria_diaria():
    global resultados_enviados, primera_ejecucion
    resultados_enviados.clear()
    primera_ejecucion = True
    print("🧹 Memoria de resultados limpiada para arrancar el nuevo día.")

def enviar_saludo_matutino():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje = (
            "🎯 *AGENCIA HAROLD JOSE* 🎯\n\n"
            "🌅 *¡Buenos días a todos!* 🌅\n\n"
            "Ya arrancamos un nuevo día con la mejor energía. "
            "Por aquí estaremos compartiendo todos los resultados de los animalitos a medida que vayan saliendo.\n\n"
            "📢 *Nuestros canales oficiales:*\n"
            "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
            "📸 Instagram: https://www.instagram.com/agharold\\_jose (@agharold\\_jose)\n"
            "💬 Canal de WhatsApp: https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
            "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("☀️ Saludo matutino enviado.")
    except Exception as e:
        print(f"⚠️ Error en saludo matutino: {e}")

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

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje = (
            "💵 *TASA OFICIAL BCV* 💵\n\n"
            f"🏦 *Moneda:* Dólar Estadounidense\n"
            f"📈 *Precio Oficial:* Bs. *{precio_dolar}*\n\n"
            "🔗 Fuente: [Banco Central de Venezuela](https://www.bcv.org.ve/)"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("💵 Tasa BCV enviada.")
    except Exception as e:
        print(f"⚠️ Error en tasa BCV: {e}")

def enviar_aviso_taquilla():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje_promo = (
            "🎯 *AGENCIA HAROLD JOSE* 🎯\n"
            "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
            "📢 *¡AVISO IMPORTANTE PARA NUESTROS JUGADORES!* 📢\n\n"
            "Recuerda que para jugar con nosotros debes acceder primero a nuestro *Canal de WhatsApp* para verificar si la taquilla se encuentra activa el día de hoy:\n"
            "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
            "📲 *Si la taquilla está activa*, puedes revisar nuestro catálogo y escribirnos directamente:\n"
            "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n\n"
            "💬 También estamos disponibles por Telegram:\n"
            "👉 t.me/ag\\_haroldjose\n\n"
            "¡Mucha suerte en sus jugadas! 🍀🔥"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje_promo, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("📢 Aviso de taquilla enviado.")
    except Exception as e:
        print(f"⚠️ Error en aviso de taquilla: {e}")

# --- POLLAS DE LAS 2:00 PM ---
def enviar_super_polla():
    try:
        caption = (
            "🐔 *SÚPER POLLA MILLONARIA (TURNO TARDE)* 🐔\n\n"
            "🕒 *Horario del turno:* 3:00 PM - 7:00 PM\n"
            "🎟️ *Costo por puesto:* 200 Bs\n"
            "⏰ *Horario para sellar:* 2:00 PM - 2:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/25696750769917708/584124489363)\n"
            "📊 *Progreso en vivo:* https://srq.es/polla/superpollatarde\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("🐔 Súper Polla Tarde enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar la Súper Polla: {e}")

def enviar_pozo_millonario():
    try:
        caption = (
            "💰 *POZO MILLONARIO (3:00 PM - 7:00 PM)* 💰\n\n"
            "🎟️ *Costo por puesto:* 100 Bs\n"
            "⏰ *Horario para sellar:* 2:00 PM - 2:50 PM\n"
            "🏆 *Nota:* Premia segundo lugar sin haber ganador de primer lugar\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/25540557112229571/584124489363)\n"
            "📊 *Progreso en vivo:* https://tr.ee/pozo-millonario-tarde\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("💰 Pozo Millonario enviado con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar el Pozo Millonario: {e}")

def enviar_lote_pollas_2pm():
    enviar_super_polla()
    time.sleep(3)
    enviar_pozo_millonario()

# --- POLLA DE LAS 3:00 PM ---
def enviar_micro_polla_3pm():
    try:
        caption = (
            "🐔 *MICRO POLLA (4:00 PM - 7:00 PM)* 🐔\n\n"
            "🎟️ *Costo por puesto:* 80 Bs\n"
            "⏰ *Horario para sellar:* 3:00 PM - 3:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/32299623729684990/584124489363)\n"
            "📊 *Progreso en vivo:* https://pozomillonarioplus.com/pozos/micro-polla\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("🐔 Micro Polla 3PM enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar Micro Polla 3PM: {e}")

# --- POLLAS DE LAS 4:00 PM ---
def enviar_gran_dupleta():
    try:
        caption = (
            "🎯 *GRAN DUPLETA (5:00 PM - 7:00 PM)* 🎯\n\n"
            "🎟️ *Costo por puesto:* 80 Bs\n"
            "⏰ *Horario para sellar:* 4:00 PM - 4:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/33044876278437080/584124489363)\n"
            "📊 *Progreso en vivo:* https://tr.ee/gran-dupleta-luz-mar\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("🎯 Gran Dupleta enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar Gran Dupleta: {e}")

def enviar_dupleta_millonaria():
    try:
        caption = (
            "💰 *DUPLETA MILLONARIA (5:00 PM - 7:00 PM)* 💰\n\n"
            "🎟️ *Costo por puesto:* 80 Bs\n"
            "⏰ *Horario para sellar:* 4:00 PM - 4:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/25010694791923322/584124489363)\n"
            "📊 *Progreso en vivo:* https://srq.es/polla/duplemillonaria\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("💰 Dupleta Millonaria enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar Dupleta Millonaria: {e}")

def enviar_mini_polla():
    try:
        caption = (
            "⭐ *MINI POLLA (5:00 PM - 7:00 PM)* ⭐\n\n"
            "🎟️ *Costo por puesto:* 100 Bs\n"
            "⏰ *Horario para sellar:* 4:00 PM - 4:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/32977419918508878/584124489363)\n"
            "📊 *Progreso en vivo:* https://srq.es/polla/minipollanoche\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("⭐ Mini Polla enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar Mini Polla: {e}")

def enviar_lote_pollas_4pm():
    enviar_gran_dupleta()
    time.sleep(3)
    enviar_dupleta_millonaria()
    time.sleep(3)
    enviar_mini_polla()

# --- POLLA DE LAS 5:00 PM ---
def enviar_micro_polla_6pm():
    try:
        caption = (
            "🐔 *MICRO POLLA (6:00 PM - 7:00 PM)* 🐔\n\n"
            "🎟️ *Costo por puesto:* 80 Bs\n"
            "⏰ *Horario para sellar:* 5:00 PM - 5:50 PM\n\n"
            "📖 *¿Cómo se juega?:* [Ver información detallada](https://wa.me/p/32453161657664170/584124489363)\n"
            "📊 *Progreso en vivo:* https://srq.es/polla/micropolla\n\n"
            "📲 *Para jugar y asegurar tu puesto:* https://wa.link/uhefij\n\n"
            "¡No te quedes sin participar y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print("🐔 Micro Polla 6PM enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar Micro Polla 6PM: {e}")

# --- SCRAPER Y RECORDATORIOS DINÁMICOS ---
def obtener_monto_acumulado_web(url_destino):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        response = requests.get(url_destino, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            texto_completo = soup.get_text(" ", strip=True)
            match = re.search(r'([\d\.,]+\s*Bs\.?|Bs\.?\s*[\d\.,]+)', texto_completo, re.IGNORECASE)
            if match:
                return match.group(1)
        return "¡Revisa el enlace de progreso en vivo!"
    except Exception as e:
        print(f"⚠️ Error leyendo la web de la polla: {e}")
        return "¡Monto activo en la web!"

def enviar_recordatorio_generico(nombre_polla, url_progreso, url_enlace_jugada, hora_cierre):
    try:
        monto_actual = obtener_monto_acumulado_web(url_progreso)
        caption = (
            "⚠️ *¡ATENCIÓN JUGADORES! QUEDAN POCOS MINUTOS* ⚠️\n\n"
            f"🎰 *{nombre_polla}* 🎰\n\n"
            f"📈 *Monto / Acumulado actual en juego:* {monto_actual}\n"
            f"⏰ *Cierre de sellado:* ¡A las {hora_cierre} en punto!\n\n"
            f"📊 *Progreso en vivo:* {url_progreso}\n"
            f"📲 *Escríbenos ya para asegurar tu puesto:* {url_enlace_jugada}\n\n"
            "¡No te quedes fuera de este sorteo y a ganar! 🍀🔥"
        )
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CANAL_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False}
        requests.post(url, json=payload)
        print(f"📢 Recordatorio de {nombre_polla} enviado con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar recordatorio: {e}")

def enviar_recordatorio_super_polla():
    enviar_recordatorio_generico("SÚPER POLLA MILLONARIA (TURNO TARDE)", URL_POLLA_TARDE, "https://wa.link/uhefij", "2:50 PM")

def enviar_recordatorio_pozo_millonario():
    enviar_recordatorio_generico("POZO MILLONARIO (3:00 PM - 7:00 PM)", "https://tr.ee/pozo-millonario-tarde", "https://wa.link/uhefij", "2:50 PM")

def enviar_lote_recordatorios_2pm():
    enviar_recordatorio_super_polla()
    time.sleep(3)
    enviar_recordatorio_pozo_millonario()

def enviar_recordatorio_micro_3pm():
    enviar_recordatorio_generico("MICRO POLLA (4PM-7PM)", "https://pozomillonarioplus.com/pozos/micro-polla", "https://wa.link/uhefij", "3:50 PM")

def enviar_recordatorio_gran_dupleta():
    enviar_recordatorio_generico("GRAN DUPLETA (5PM-7PM)", "https://tr.ee/gran-dupleta-luz-mar", "https://wa.link/uhefij", "4:50 PM")

def enviar_recordatorio_dupleta_millonaria():
    enviar_recordatorio_generico("DUPLETA MILLONARIA (5PM-7PM)", "https://srq.es/polla/duplemillonaria", "https://wa.link/uhefij", "4:50 PM")

def enviar_recordatorio_mini_polla():
    enviar_recordatorio_generico("MINI POLLA (5PM-7PM)", "https://srq.es/polla/minipollanoche", "https://wa.link/uhefij", "4:50 PM")

def enviar_lote_recordatorios_4pm():
    enviar_recordatorio_gran_dupleta()
    time.sleep(3)
    enviar_recordatorio_dupleta_millonaria()
    time.sleep(3)
    enviar_recordatorio_mini_polla()

def enviar_recordatorio_micro_6pm():
    enviar_recordatorio_generico("MICRO POLLA (6PM-7PM)", "https://srq.es/polla/micropolla", "https://wa.link/uhefij", "5:50 PM")

# --- VERIFICADOR DE RESULTADOS CORREGIDO Y COMPLETO ---
def verificar_resultados():
    global primera_ejecucion, resultados_enviados
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        # Búsqueda robusta de tarjetas o contenedores de resultados en la página
        tarjetas = soup.find_all(['div', 'article', 'section', 'li'], class_=re.compile(r'(result|item|card|loteria|sorteo|box|animal)', re.I))
        
        nuevos_resultados = []
        for tarjeta in tarjetas:
            texto_tarjeta = limpiar_texto
