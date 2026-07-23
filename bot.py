import os
import time
import threading
from datetime import datetime
import pytz
import requests
from flask import Flask

app = Flask(__name__)

# Configuración del Bot de Telegram (puedes usar variables de entorno en Render)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "TU_CHAT_ID_AQUI")

# Cabeceras con comillas cerradas correctamente
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.route('/')
def home():
    return "Bot de Resultados y Avisos Activo y Funcionando"

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

def loop_automatico():
    venezuela_tz = pytz.timezone('America/Caracas')
    enviado_manana = False
    enviado_tarde = False
    
    while True:
        try:
            ahora = datetime.now(venezuela_tz)
            hora_actual = ahora.strftime("%H:%M")
            
            # Reiniciar banderas a la medianoche para el día siguiente
            if hora_actual == "00:00":
                enviado_manana = False
                enviado_tarde = False
            
            # Aviso de la mañana: 7:40 AM (10 minutos antes del cierre de las 7:50 AM)
            if hora_actual == "07:40" and not enviado_manana:
                mensaje = (
                    "⚠️ *¡ATENCIÓN SEÑORES!* ⚠️\n"
                    "Quedan **10 minutos** para cerrar el horario de sellar las pollas:\n"
                    "• Mini Polla (8AM-10AM)\n"
                    "• Dupleta Guacharo (8AM-1PM)\n"
                    "• Polla Galaxy (8AM-12PM)\n"
                    "• Polla Animaniac (8AM-7PM)\n"
                    "⏰ *Cierre exacto a las 7:50 AM.*\n"
                    "¡Apuren sus jugadas y no se queden por fuera! 🏃‍♂️💨"
                )
                enviar_mensaje(mensaje)
                enviado_manana = True
            
            # Aviso de la tarde: 4:40 PM (10 minutos antes del cierre de las 4:50 PM)
            if hora_actual == "16:40" and not enviado_tarde:
                mensaje = (
                    "⚠️ *¡ATENCIÓN SEÑORES!* ⚠️\n"
                    "Quedan **10 minutos** para cerrar el horario de sellar:\n"
                    "• Dupleta Lotto Real (5PM-7PM)\n"
                    "⏰ *Cierre exacto a las 4:50 PM.*\n"
                    "¡Apuren sus jugadas! 🏃‍♂️💨"
                )
                enviar_mensaje(mensaje)
                enviado_tarde = True
                
        except Exception as e:
            print(f"Error en el loop de avisos: {e}")
            
        time.sleep(30) # Revisa el reloj cada 30 segundos

if __name__ == '__main__':
    # Iniciar el hilo en segundo plano para las tareas automatizadas y avisos
    hilo_automatizacion = threading.Thread(target=loop_automatico)
    hilo_automatizacion.daemon = True
    hilo_automatizacion.start()
    
    # Iniciar el servidor Flask requerido por Render usando el puerto dinámico
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                    
