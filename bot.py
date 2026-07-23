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
    'CARNERO': '🐏', 
    'TORO': '🐂', 
    'CIEMPIÉS': '🐛', 
    'CIEMPIES': '🐛',
    'ALACRAN': '🦂',
    'LEÓN': '🦁', 
    'LEON': '🦁',
    'RANA': '🐸', 
    'PERICO': '🦜', 
    'CHIVO': '🐐',
    'COCHINO': '🐖', 
    'GALLO': '🐓', 
    'CARACOL': '🐌', 
    'CULEBRA': '🐍',
    'ZAMURO': '🐦‍⬛', 
    'GATO': '🐈', 
    'BALLENA': '🐋', 
    'CAIMAN': '🐊',
    'CAIMÁN': '🐊',
    'ÁGUILA': '🦅', 
    'AGUILA': '🦅',
    'TIGRE': '🐅', 
    'PAVO': '🦃', 
    'PAVITO': '🦃',
    'PAVO REAL': '🦚',
    'BURRO': '🫏', 
    'MONO': '🐵', 
    'IGUANA': '🦎', 
    'BUFALO': '🐃',
    'BÚFALO': '🐃',
    'GALLINA': '🐔', 
    'VACA': '🐄', 
    'PERRO': '🐶', 
    'ZORRO': '🦊',
    'OSO': '🐻', 
    'PESCADO': '🐟', 
    'CEBRA': '🦓', 
    'ZEBRA': '🦓',
    'VENADO': '🦌', 
    'CIERVO': '🦌',
    'CAMELLO': '🐫',
    'CAMELOS': '🐫',
    'DELFIN': '🐬',
    'DÉLFIN': '🐬',
    'BISONTE': '🦬', 
    'HORMIGA': '🐜', 
    'AVISPA': '🐝',
    'GRILLO': '🦗', 
    'PUERCOESPIN': '🦔',
    'PUERCOESPÍN': '🦔',
    'ELEFANTE': '🐘',
    'LECHUZA': '🦉',
    'PALOMA': '🐦',
    'JIRAFA': '🦒',
    'RATON': '🐭',
    'RATÓN': '🐭',
    'CISNE': '🦢',
    'PATO': '🦆',
    'CONEJO': '🐰',
    'CABALLO': '🐎',
    'PANTERA': '🐆',
    'PUMA': '🐆',
    'CUCARACHA': '🪳'
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.
  
