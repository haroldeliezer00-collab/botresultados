from datetime import datetime
import time
from bs4 import BeautifulSoup
import requests
from telegram import Bot
from telegram.error import TelegramError
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# ==========================================
# SERVIDOR WEB FALSO PARA RENDER (EVITA ERROR DE PUERTOS)
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
        
    def log_message(self, format, *args):
        return # Evita saturar los logs con cada ping

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Iniciar el servidor en segundo plano antes de arrancar el bot
threading.Thread(target=run_server, daemon=True).start()

# ==========================================
# CONFIGURACIÓN DEL BOT
# ==========================================
TOKEN = "8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk"
CHANNEL_ID = "@pruebajsj"
bot = Bot(token=TOKEN)

# Memoria temporal para control del día
processed_results = set()  # Evita repetir alertas de resultados ya enviados
pinned_summary_message_id = None  # ID del mensaje fijado con la tabla
daily_results_table = {}  # Almacena los resultados por hora y lotería para la tabla


def send_message(text, chat_id=CHANNEL_ID):
  try:
    res = bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
    return res.message_id
  except Exception as e:
    print(f"Error enviando mensaje: {e}")
    return None


# ==========================================
# 1. GENERADOR DE LA PIRÁMIDE TÁCTICA (6:31 AM)
# ==========================================


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

  pyramid_lines = []
  total_rows = len(rows)
  for i, row in enumerate(rows):
    spaces = "  " * (total_rows - i - 1)
    formatted_row = "  ".join(str(d) for d in row)
    pyramid_lines.append(f"{spaces}... {formatted_row} ...")
  return "\n".join(pyramid_lines)


# ==========================================
# 2. MENSAJES PROGRAMADOS FIJOS
# ==========================================


def job_good_morning():
  global processed_results, pinned_summary_message_id, daily_results_table
  processed_results.clear()
  pinned_summary_message_id = None
  daily_results_table.clear()

  text = (
      "🎯 <b>AGENCIA HAROLD JOSE</b> 🎯\n\n"
      "🌅 <b>¡Buenos días a todos!</b> 🌅\n\n"
      "Ya arrancamos un nuevo día con la mejor energía. Por aquí estaremos"
      " compartiendo todos los resultados de los animalitos a medida que vayan"
      " saliendo.\n\n"
      "📢 <b>Nuestros canales oficiales:</b>\n"
      "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
      "📸 Instagram: https://www.instagram.com/agharold.jose (@agharold.jose)\n"
      "💬 Canal de WhatsApp:"
      " https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
      "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
  )
  send_message(text)


def job_bcv():
  text = (
      "💵 <b>TASA OFICIAL BCV</b> 💵\n\n"
      "🏦 Moneda: Dólar Estadounidense\n"
      "📈 Precio Oficial: Bs. 742,23\n\n"
      "🔗 Fuente: Banco Central de Venezuela\n"
      "🌐 https://www.bcv.org.ve/"
  )
  send_message(text)


def job_pyramid():
  today = datetime.now().strftime("%d/%m/%Y")
  art = generate_pyramid(today)
  text = (
      "🎯 <b>CENTRO DE APUESTAS HAROLD JOSÉ</b> 🎯\n"
      "📢 <b>REPORTE TÁCTICO - LA PIRÁMIDE</b> 📢\n\n"
      f"📅 <b>Fecha:</b> {today}\n"
      "Análisis matemático actualizado y listo para la jugada. ¡A asegurar"
      " posición:\n\n"
      f"{art}\n\n"
      "🔥 <b>DATOS CLAVES PARA HOY:</b>\n"
      "📌 25-13-07\n"
      "📌 35-20-02\n\n"
      "⚡ ¡La precisión y los números hablan por sí solos! ¡Juega con confianza"
      " y gana con nosotros! 🍀 💰"
  )
  send_message(text)


def job_important_notice():
  text = (
      "🎯 <b>AGENCIA HAROLD JOSE</b> 🎯\n"
      "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
      "📢 <b>¡AVISO IMPORTANTE PARA NUESTROS JUGADORES!</b> 📢\n\n"
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
  send_message(text)


def job_polls():
  text = (
      "🔥 <b>¡Ya se subieron o ya se actualizó el canal con las pollas de este"
      " sorteo!</b> No te pierdas de los sorteos de las pollas, puedes verlo"
      " aquí 👇🏻\nhttps://t.me/pollasydupletas"
  )
  send_message(text)


def job_closing():
  text = (
      "🎯 <b>AGENCIA HAROLD JOSE</b> 🎯\n\n"
      "🌙 <b>¡FINAL DE JORNADA!</b> 🌙\n\n"
      "Estos fueron todos los resultados del día de hoy. ¡Gracias por jugar con"
      " nosotros! Los esperamos el día de mañana con mucha más suerte y"
      " energía. 🍀✨"
  )
  send_message(text)


# ==========================================
# 3. MONITOREO Y FASE DE RESUMEN ACUMULATIVO
# ==========================================


def check_and_process_results():
  global pinned_summary_message_id, daily_results_table
  url = "https://lotery.winbigvzla.com/resultados"

  try:
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
      print("[!] Error al conectar con la web de resultados principal.")
      return

    soup = BeautifulSoup(response.text, "html.parser")

    # --- SIMULACIÓN DE EXTRACCIÓN DE RESULTADOS DE LA PÁGINA ---
    nuevos_resultados_detectados = [
        # {"lottery": "LOTTO ACTIVO", "time": "09:00 AM", "number": "11", "animal": "GATO"}
    ]

    for item in nuevos_resultados_detectados:
      lottery_name = item["lottery"].strip().upper()

      # Excluir Ruleta Royal estrictamente
      if "RULETA ROYAL" in lottery_name:
        continue

      result_key = f"{item['time']}_{lottery_name}_{item['number']}"

      if result_key not in processed_results:
        processed_results.add(result_key)

        # FASE 1: Alerta Individual Instantánea al Canal
        individual_msg = (
            "🎯 <b>AG HAROLD JOSE</b> 🎯\n\n"
            f"🎰 <b>{lottery_name}</b>\n"
            f"🕒 {item['time']}  {item['number']} - {item['animal']}\n"
            "https://t.me/resultadosagharoldjose"
        )
        send_message(individual_msg)

        # FASE 2: Agregar a la estructura de la Tabla Acumulativa
        time_slot = item["time"]
        if time_slot not in daily_results_table:
          daily_results_table[time_slot] = {}
        daily_results_table[time_slot][lottery_name] = (
            f"{item['number']} {item['animal']}"
        )

        update_cumulative_dashboard_message()

  except Exception as e:
    print(f"[X] Excepción en scraping: {e}")


def update_cumulative_dashboard_message():
  global pinned_summary_message_id

  table_rows = ""
  for t_slot in sorted(daily_results_table.keys()):
    lotto_val = daily_results_table[t_slot].get("LOTTO ACTIVO", "---")
    guach_val = daily_results_table[t_slot].get("GUACHARO ACTIVO", "---")
    chaim_val = daily_results_table[t_slot].get("LOTO CHAIMA", "---")
    table_rows += f"<b>{t_slot}</b> | {lotto_val} | {guach_val} | {chaim_val}\n"

  dashboard_text = (
      "📊 <b>TABLA RESUMEN ACUMULATIVA - RESULTADOS DEL DÍA</b> 📊\n"
      "<i>Actualizándose automáticamente a medida que transcurre el"
      " día...</i>\n\n"
      "<b>HORA  | LOTTO ACTIVO | GUACHARO | CHAIMA</b>\n"
      "--------------------------------------------------\n"
      f"{table_rows if table_rows else 'Esperando primeros resultados...'}"
  )

  try:
    if pinned_summary_message_id is None:
      msg_id = send_message(dashboard_text)
      if msg_id:
        pinned_summary_message_id = msg_id
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
    print(f"[X] Error actualizando el mensaje fijado acumulativo: {e}")


# ==========================================
# 4. BUCLE PRINCIPAL (MANTIENE EL BOT ACTIVO)
# ==========================================
if __name__ == "__main__":
  print("[*] Bot iniciado correctamente. Manteniendo servicio activo...")
  while True:
    try:
      check_and_process_results()
      time.sleep(60)
    except KeyboardInterrupt:
      print("\n[!] Bot detenido manualmente.")
      break
    except Exception as e:
      print(f"[X] Error en el bucle principal: {e}")
      time.sleep(10)
  
