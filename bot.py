import os
import re
import time
from datetime import datetime
from threading import Thread

import requests
from bs4 import BeautifulSoup
from flask import Flask
import schedule

# Variables de configuración desde entorno o valores por defecto
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")
CANAL_ID = os.environ.get("CANAL_ID", "@pruebajsj")
URL_LOTERIA = "https://lotery.winbigvzla.com/resultados"

app = Flask(__name__)

# Conjunto global para evitar duplicados
resultados_enviados = set()


@app.route("/")
def home():
    return "¡El bot de resultados AG HAROLD JOSE está activo!"


def limpiar_texto(texto):
    return " ".join(texto.split())


def limpiar_memoria_diaria():
    """Limpia el conjunto de resultados a la medianoche."""
    global resultados_enviados
    resultados_enviados.clear()
    print("🧹 Memoria de resultados diaria limpiada.")


def verificar_resultados():
    global resultados_enviados
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            print(f"⚠️ Error al acceder a la página web: Estado {respuesta.status_code}")
            return

        soup = BeautifulSoup(respuesta.text, "html.parser")

        tarjetas = soup.find_all(
            ["div", "article", "section"],
            class_=re.compile(r"card|box|item|lotto|result", re.IGNORECASE),
        )

        for tarjeta in tarjetas:
            nombre_loteria = ""

            # Extraer el nombre de la lotería
            posibles_titulos = tarjeta.find_all(
                ["h1", "h2", "h3", "h4", "h5", "span", "div", "strong", "b"],
                class_=re.compile(r"title|header|name|lotto|text", re.IGNORECASE),
            )
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if (
                    t_text
                    and len(t_text) > 2
                    and not re.search(r"\d{1,2}:\d{2}", t_text)
                    and "PENDIENTE" not in t_text
                ):
                    if t_text not in ["WINBIG", "RESULTADOS"]:
                        nombre_loteria = t_text
                        break

            if not nombre_loteria:
                lineas = [
                    l.strip().upper()
                    for l in tarjeta.get_text("\n", strip=True).split("\n")
                    if l.strip()
                ]
                for linea in lineas:
                    if (
                        len(linea) > 2
                        and not re.search(r"\d{1,2}:\d{2}", linea)
                        and "PENDIENTE" not in linea
                        and "-" not in linea
                    ):
                        nombre_loteria = linea
                        break

            if not nombre_loteria or len(nombre_loteria) > 40:
                continue

            nombre_loteria = limpiar_texto(nombre_loteria)

            # Buscar slots de cada sorteo
            slots_sorteo = tarjeta.find_all(
                ["div", "li", "span", "tr"],
                class_=re.compile(r"item|slot|draw|row|col", re.IGNORECASE),
            )
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()

                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", texto_slot)
                if not match_h:
                    continue
                hora = match_h.group(1).upper()

                match_res = re.search(
                    r"(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)", texto_slot
                )
                if not match_res:
                    continue

                resultado_final = limpiar_texto(match_res.group(1)).upper()

                # Clave única incorporando la fecha
                clave = (fecha_hoy, nombre_loteria, hora, resultado_final)

                if clave not in resultados_enviados:
                    # Enviar mensaje inmediatamente al detectar un nuevo resultado
                    mensaje = (
                        "🎯 AG HAROLD JOSE 🎯\n\n"
                        f"🎰 *{nombre_loteria}*\n"
                        f"🕒 {hora}  {resultado_final}"
                    )

                    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    payload = {
                        "chat_id": CANAL_ID,
                        "text": mensaje,
                        "parse_mode": "Markdown",
                    }
                    
                    res_tg = requests.post(url, json=payload, timeout=10)
                    if res_tg.status_code == 200:
                        resultados_enviados.add(clave)
                        print(f"✅ Enviado: {nombre_loteria} ({hora}) -> {resultado_final}")
                    else:
                        print(f"❌ Error al enviar a Telegram: {res_tg.text}")

                    time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error general durante el scraping: {e}")


def loop_bot():
    # Programar la verificación cada 2 minutos
    schedule.every(2).minutes.do(verificar_resultados)
    
    # Programar la limpieza de memoria diaria a las 00:00
    schedule.every().day.at("00:00").do(limpiar_memoria_diaria)

    # Ejecución inicial al iniciar
    verificar_resultados()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # Iniciar el hilo del bot
    t = Thread(target=loop_bot)
    t.daemon = True
    t.start()

    # Iniciar servidor Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
