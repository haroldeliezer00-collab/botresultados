from threading import Thread
import time
from datetime import datetime
from flask import Flask
import schedule
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError

# Mini servidor Flask para mantener el bot activo en Render
app = Flask('')


@app.route('/')
def home():
  return "Bot de Agencia Harold José activo 🚀"


def run_flask():
  app.run(host='0.0.0.0', port=10000)


# Configuración del Bot de Telegram
TOKEN = "8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk"
CHANNEL_ID = "@pruebajsj"
bot = Bot(token=TOKEN)

pinned_summary_message_id = None


# 1. TASA BCV (6:30 AM y 6:30 PM)
def send_bcv_rate():
  try:
    mensaje = (
        "💵 TASA OFICIAL BCV 💵\n\n"
        "🏦 Moneda: Dólar Estadounidense\n"
        "📈 Precio Oficial: Bs. 742,23\n\n"
        "🔗 Fuente: Banco Central de Venezuela\n"
        "🌐 https://www.bcv.org.ve/"
    )
    bot.send_message(chat_id=CHANNEL_ID, text=mensaje)
  except Exception as e:
    print(f"Error BCV: {e}")


# 2. PIRÁMIDE TÁCTICA (6:31 AM)
def generate_pyramid(date_str):
  digits = [int(c) for c in date_str if c.isdigit()]
  rows = [digits]
  while len(rows[-1]) > 1:
    current_row = rows[-1]
    next_row = [
        (current_row[i] + current_row[i + 1]) % 10
        for i in range(len(current_row) - 1)
    ]
    rows.append(next_row)

  pyramid_text = ""
  for idx, row in enumerate(rows):
    indent = "  " * idx
    row_str = "  ".join(str(n) for n in row)
    pyramid_text += f"{indent}{row_str}\n"
  return pyramid_text


def send_tactical_pyramid():
  today_str = datetime.now().strftime("%d/%m/%Y")
  pyramid_art = generate_pyramid(today_str)
  mensaje = (
      "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n"
      "📢 REPORTE TÁCTICO - LA PIRÁMIDE 📢\n\n"
      f"📅 Fecha: {today_str}\n"
      "Análisis matemático actualizado y listo para la jugada. ¡A asegurar"
      " posición:\n\n"
      f"{pyramid_art}\n"
      "🔥 DATOS CLAVES PARA HOY:\n"
      "📌 25-13-07\n"
      "📌 35-20-02\n\n"
      "⚡ ¡La precisión y los números hablan por sí solos! ¡Juega con confianza"
      " y gana con nosotros! 🍀 💰"
  )
  bot.send_message(chat_id=CHANNEL_ID, text=mensaje)


# 3. BUENOS DÍAS (7:00 AM)
def send_good_morning():
  mensaje = (
      "🎯 AGENCIA HAROLD JOSE 🎯\n\n"
      "🌅 ¡Buenos días a todos! 🌅\n\n"
      "Ya arrancamos un nuevo día con la mejor energía. Por aquí estaremos"
      " compartiendo todos los resultados de los animalitos a medida que vayan"
      " saliendo.\n\n"
      "📢 Nuestros canales oficiales:\n"
      "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
      "📸 Instagram: https://www.instagram.com/agharold.jose (@agharold.jose)\n"
      "💬 Canal de WhatsApp:"
      " https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
      "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
  )
  bot.send_message(chat_id=CHANNEL_ID, text=mensaje)


# 4. AVISO IMPORTANTE (10:00 AM, 2:00 PM, 5:00 PM)
def send_important_notice():
  mensaje = (
      "🎯 AGENCIA HAROLD JOSE 🎯\n"
      "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
      "📢 ¡AVISO IMPORTANTE PARA NUESTROS JUGADORES! 📢\n\n"
      "Recuerda que para jugar con nosotros debes acceder primero al Canal de"
      " WhatsApp para verificar si la taquilla se encuentra activa el día de"
      " hoy:\n"
      "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
      "📲 Si la taquilla está activa, puedes revisar nuestro catálogo y"
      " escribirnos directamente:\n"
      "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n\n"
      "💬 También estamos disponibles por Telegram:\n"
      "👉 t.me/ag_haroldjose\n\n"
      "¡Mucha suerte en sus jugadas! 🍀🔥"
  )
  bot.send_message(chat_id=CHANNEL_ID, text=mensaje)


# 5. AVISO DE POLLAS (Minuto 10 de cada hora)
def send_pollas_notice():
  mensaje = (
      "🔥 ¡Ya se subieron o ya se actualizó el canal con las pollas de este"
      " sorteo! No te pierdas de los sorteos de las pollas, puedes verlo aquí"
      " 👇🏻\nhttps://t.me/pollasydupletas"
  )
  bot.send_message(chat_id=CHANNEL_ID, text=mensaje)


# 6. CIERRE DE JORNADA (9:10 PM)
def send_night_closing():
  mensaje = (
      "🎯 AGENCIA HAROLD JOSE 🎯\n\n"
      "🌙 ¡FINAL DE JORNADA! 🌙\n\n"
      "Estos fueron todos los resultados del día de hoy. ¡Gracias por jugar con"
      " nosotros! Los esperamos el día de mañana con mucha más suerte y"
      " energía. 🍀✨"
  )
  bot.send_message(chat_id=CHANNEL_ID, text=mensaje)


# 7. SCRAPING Y RESULTADOS (Minuto 10 de cada hora)
def fetch_and_post_results():
  global pinned_summary_message_id
  url_principal = "https://lotery.winbigvzla.com/resultados"
  try:
    response = requests.get(url_principal, timeout=10)
    if response.status_code != 200:
      return

    soup = BeautifulSoup(response.text, "html.parser")
    resultados_detectados = []

    for res in resultados_detectados:
      if "RULETA ROYAL" in res["lottery"].upper():
        continue

      mensaje_individual = (
          "🎯 AG HAROLD JOSE 🎯\n\n"
          f"🎰 {res['lottery']}\n"
          f"🕒 {res['time']}  {res['number']} - {res['animal']}\n"
          "https://t.me/resultadosagharoldjose"
      )
      bot.send_message(chat_id=CHANNEL_ID, text=mensaje_individual)
      update_cumulative_dashboard(res)

  except Exception as e:
    print(f"Error scraping: {e}")


def update_cumulative_dashboard(new_result):
  global pinned_summary_message_id
  dashboard_text = (
      "📊 <b>TABLA RESUMEN ACUMULATIVA - RESULTADOS DEL DÍA</b> 📊\n\n"
      "HORA  | LOTTO ACTIVO | GUACHARO | CHAIMA\n"
      "------------------------------------------\n"
      "08:00 | 20 🐷        | 10 🐅    | 09 🦅\n"
      f"<i>Actualizado: {new_result['lottery']} ({new_result['time']}) ->"
      f" {new_result['number']} {new_result['animal']}</i>"
  )
  try:
    if pinned_summary_message_id is None:
      sent_msg = bot.send_message(
          chat_id=CHANNEL_ID, text=dashboard_text, parse_mode="HTML"
      )
      pinned_summary_message_id = sent_msg.message_id
      bot.pin_chat_message(
          chat_id=CHANNEL_ID, message_id=pinned_summary_message_id
      )
    else:
      bot.edit_message_text(
          chat_id=CHANNEL_ID,
          message_id=pinned_summary_message_id,
          text=dashboard_text,
          parse_mode="HTML",
      )
  except TelegramError as e:
    print(f"Error dashboard: {e}")


# ==========================================
# PLANIFICADOR Y EJECUCIÓN
# ==========================================
if __name__ == "__main__":
  # Iniciar Flask en un hilo secundario para Render
  t = Thread(target=run_flask)
  t.start()

  # Configurar horarios
  schedule.every().day.at("06:30").do(send_bcv_rate)
  schedule.every().day.at("06:31").do(send_tactical_pyramid)
  schedule.every().day.at("07:00").do(send_good_morning)

  schedule.every().day.at("10:00").do(send_important_notice)
  schedule.every().day.at("14:00").do(send_important_notice)
  schedule.every().day.at("17:00").do(send_important_notice)

  schedule.every().day.at("18:30").do(send_bcv_rate)
  schedule.every().day.at("21:10").do(send_night_closing)

  schedule.every().hour.at(":10").do(fetch_and_post_results)
  schedule.every().hour.at(":10").do(send_pollas_notice)

  print("Bot en marcha en Render...")
  while True:
    schedule.run_pending()
    time.sleep(1)
    
