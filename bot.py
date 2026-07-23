import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

# Configuración del Bot de Telegram (puedes usar variables de entorno o definirlo aquí)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "TU_CHAT_ID_AQUI")

# Cabeceras corregidas (comillas cerradas correctamente para evitar errores de sintaxis)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.route('/')
def home():
    return "Bot de Resultados Activo y Funcionando"

def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

def consultar_resultados():
    try:
        # Aquí va la lógica de Web Scraping para obtener los resultados de las loterías
        # Ejemplo:
        # url = "URL_DE_RESULTADOS"
        # response = requests.get(url, headers=headers)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # ... extraes los datos y llamas a enviar_mensaje() ...
        print("Ciclo de verificación ejecutado correctamente.")
    except Exception as e:
        print(f"Error en la consulta: {e}")

def loop_automatico():
    while True:
        consultar_resultados()
        # Espera el tiempo necesario entre consultas (ej. cada hora = 3600 segundos)
        time.sleep(3600)

if __name__ == '__main__':
    # Iniciar el hilo en segundo plano para las tareas automatizadas
    hilo_automatizacion = threading.Thread(target=loop_automatico)
    hilo_automatizacion.daemon = True
    hilo_automatizacion.start()
    
    # Iniciar el servidor Flask requerido por Render usando el puerto dinámico
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
