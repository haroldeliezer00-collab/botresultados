import os
import re
import threading
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask
import pytz
import requests

app = Flask(__name__)

# Configuración del Bot y Canal de Telegram (usando variables de entorno por seguridad)
TOKEN = os.environ.get("BOT_TOKEN", "TU_TOKEN_AQUI")
CHAT_ID = os.environ.get("CHAT_ID", "TU_CHAT_ID_AQUI")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Zona horaria de Venezuela
TZ_VENEZUELA = pytz.timezone("America/Caracas")


def enviar_telegram(mensaje):
  payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
  try:
    response = requests.post(TELEGRAM_API, data=payload, timeout=10)
    return response.json()
  except Exception as e:
    print(f"Error al enviar mensaje a Telegram: {e}")
    return None


@app.route("/")
def home():
  return "Bot de Resultados activo al pelo 🚀"


def tarea_automatica():
  while True:
    try:
      # Lógica de extracción de resultados
      ahora = datetime.now(TZ_VENEZUELA)
      url = "https://winbigvzla.com"  # Fuente configurada para los resultados
      headers = {"User-Agent": "Mozilla/5.0"}
      resp = requests.get(url, headers=headers, timeout=15)

      if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")

        # Línea corregida (con el cierre correcto de paréntesis y re.IGNORECASE)
        tarjetas = soup.find_all(
            ["div", "article", "section"],
            class_=re.compile(r"card|box|item|lotto|result", re.IGNORECASE),
        )

        # Procesamiento de resultados y envío a Telegram...
    except Exception as e:
      print(f"Error en tarea automática: {e}")

    time.sleep(3600)  # Espera el intervalo programado


if __name__ == "__main__":
  # Iniciar hilo en segundo plano para las tareas automatizadas
  hilo = threading.Thread(target=tarea_automatica, daemon=True)
  hilo.start()

  # Puerto dinámico para Render
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
