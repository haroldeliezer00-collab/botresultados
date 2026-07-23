import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
import schedule
import urllib3

# Desactivar advertencias de certificados si las hubiera
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Configuración del Bot de Telegram y Canales
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")
CANALES = ['@resultadosagharoldjose', '@pruebajsj']

def enviar_telegram(mensaje):
    """Envía un mensaje a todos los canales configurados."""
    exito_total = True
    for canal in CANALES:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': canal,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code != 200:
                print(f"Error al enviar a {canal}: {response.text}")
                exito_total = False
        except Exception as e:
            print(f"Excepción al conectar con Telegram para {canal}: {e}")
            exito_total = False
    return exito_total

# --- Funciones de Mensajes y Tareas ---

def enviar_saludo():
    mensaje = "🌅 *¡Buenos días a todos los miembros del canal!*\n\nQue tengan excelente energía y mucha suerte hoy. ¡Comenzamos la jornada con todo! 🎯"
    enviar_telegram(mensaje)

def enviar_taquilla():
    mensaje = "⚠️ *AVISO IMPORTANTE DE TAQUILLA*\n\nRecuerden verificar sus operaciones a tiempo. ¡Evitemos contratiempos! 🏦✨"
    enviar_telegram(mensaje)

def enviar_bcv():
    # Aquí puedes integrar tu consulta de BCV/Binance real si la tienes
    mensaje = "📊 *TASA OFICIAL / BINANCE*\n\nConsulta los valores actualizados del día en nuestros grupos y canales asociados. 💵📈"
    enviar_telegram(mensaje)

def verificar_resultados():
    # Lógica de ejemplo o scraping para verificar resultados de lotería
    mensaje = "🎯 *AG HAROLD JOSE* 🎯\n\n🎰🎰 *LOTTO ACTIVO / RULETA*\n⏰ *Actualización de Resultados en curso...*"
    enviar_telegram(mensaje)

# --- Rutas de Flask y Pruebas Manuales ---

@app.route('/')
def home():
    return "¡El Bot de Resultados AG Harold Jose está activo y funcionando perfectamente! 🚀"

@app.route('/test/saludo')
def test_saludo():
    enviar_saludo()
    return "¡Mensaje de prueba de saludo enviado a los canales!"

@app.route('/test/taquilla')
def test_taquilla():
    enviar_taquilla()
    return "¡Aviso de taquilla enviado a los canales!"

@app.route('/test/bcv')
def test_bcv():
    enviar_bcv()
    return "¡Mensaje de tasa BCV enviado a los canales!"

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "¡Prueba de resultados enviada a los canales!"

# --- Programador de Tareas (Schedule) ---

def ejecutar_programacion():
    # Configura tus horarios automáticos aquí si lo deseas
    # Ejemplo: schedule.every().day.at("08:00").do(enviar_saludo)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar el hilo del programador en segundo plano
hilo_scheduler = threading.Thread(target=ejecutar_programacion, daemon=True)
hilo_scheduler.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
