import os
# Forzar la zona horaria de Venezuela para que el bot use la hora local exacta
os.environ['TZ'] = 'America/Caracas'
try:
    import time
    time.tzset()
except AttributeError:
    pass

import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3
from datetime import datetime
import random
import telebot
import traceback

# Desactivar advertencias de certificados SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Credenciales y canal principal
TOKEN = '8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk'
CANAL = '@pruebajsj'
ENLACE_CANAL = 'https://t.me/pruebajsj'

bot = telebot.TeleBot(TOKEN)

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

taquilla_activa_hoy = False
imagen_activa_id = None
ultimo_id_foto_canal = None

# Almacén de resultados del día para armar la tabla acumulativa estructurada
resultados_tabla_dia = {}
resumen_message_id = None

TEXTO_TAQUILLA = (
    "✅ AG HAROLD JOSÉ ACTIVA ✅\n"
    "Ya estamos operativos brindando la mejor atención. Calidad, respaldo y rapidez en cada una de todas tus solicitudes.\n\n"
    "📲 Envía tus jugadas:\n"
    "(Comprobante de pago / Lotería / monto / Hora)\n\n"
    "📖 Consulta nuestro reglamento aquí:\n"
    "https://wa.me/p/33319103291071105/584124489363\n"
    "🚀 Agiliza tu proceso aquí: https://wa.me/p/24724650613899486/584124489363\n\n"
    "RESULTADOS AUTOMÁTICOS\n"
    f"{ENLACE_CANAL}\n\n"
    "¡Mucho éxito en la jornada de hoy! 🍀✨"
)

app = Flask('')

@app.route('/')
def home():
    estado_texto = "ACTIVA" if taquilla_activa_hoy else "INACTIVA"
    color_estado = "green" if taquilla_activa_hoy else "red"
    return (
        f"¡El bot de resultados AG HAROLD JOSE está activo en el canal {CANAL}!<br>"
        f"Estado de la Taquilla Hoy: <b style='color: {color_estado};'>{estado_texto}</b><br>"
        f"Horas registradas en la tabla hoy: <b>{len(resultados_tabla_dia)}</b><br><br>"
        "<b>Enlaces de prueba rápida (Test):</b><br>"
        "👉 <a href='/test/madrugada'>Probar Saludo de Madrugada</a><br>"
        "👉 <a href='/test/piramide'>Probar Pirámide Numérica</a><br>"
        "👉 <a href='/test/bcv'>Probar Tasa BCV</a><br>"
        "👉 <a href='/test/saludo'>Probar Saludo Matutino</a><br>"
        "👉 <a href='/test/taquilla'>Probar Aviso de Taquilla</a><br>"
        "👉 <a href='/test/pollas'>Probar Aviso de Pollas y Resumen</a><br>"
        "👉 <a href='/test/resultados'>Forzar Revisión de Resultados</a><br>"
        "👉 <a href='/test/cierre'>Probar Mensaje de Cierre</a><br>"
        "👉 <a href='/test-refuerzo'>Probar Refuerzo de Taquilla</a>"
    )

# --- RUTAS DE PRUEBA MANUAL ---
@app.route('/test/madrugada')
def test_madrugada():
    enviar_saludo_madrugada()
    return "Prueba ejecutada."

@app.route('/test/piramide')
def test_piramide():
    enviar_piramide_diaria()
    return "Prueba ejecutada."

@app.route('/test/bcv')
def test_bcv():
    enviar_tasa_dolar()
    return "Prueba ejecutada."

@app.route('/test/saludo')
def test_saludo():
    enviar_saludo_matutino()
    return "Prueba ejecutada."

@app.route('/test/taquilla')
def test_taquilla():
    enviar_aviso_taquilla()
    return "Prueba ejecutada."

@app.route('/test/pollas')
def test_pollas():
    tarea_minuto_diez()
    return "Prueba ejecutada (Pollas + Resumen Acumulativo)."

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "Prueba ejecutada."

@app.route('/test/cierre')
def test_cierre():
    enviar_mensaje_cierre()
    return "Prueba ejecutada."

@app.route('/test-refuerzo')
def test_refuerzo():
    tarea_refuerzo_tarde()
    return "Prueba ejecutada."
# -----------------------------

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
    global resultados_enviados, primera_ejecucion, taquilla_activa_hoy, imagen_activa_id, ultimo_id_foto_canal, resultados_tabla_dia, resumen_message_id
    resultados_enviados.clear()
    primera_ejecucion = True
    taquilla_activa_hoy = False
    imagen_activa_id = None
    ultimo_id_foto_canal = None
    resultados_tabla_dia.clear()
    resumen_message_id = None
    print("🧹 Memoria y tabla acumulativa limpiadas para el nuevo día.")

def activar_taquilla_proceso():
    global taquilla_activa_hoy, imagen_activa_id
    if not imagen_activa_id:
        return
    taquilla_activa_hoy = True
    try:
        bot.send_photo(chat_id=CANAL, photo=imagen_activa_id, caption=TEXTO_TAQUILLA)
        print("Taquilla activada correctamente.")
    except Exception as e:
        print(f"Error al enviar taquilla: {e}")

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
            print(f"Error en refuerzo: {e}")

def enviar_saludo_madrugada():
    enviar_telegram(
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n\n"
        "🌅 ¡Despertando con la mejor energía y listos para ganar! 🌅\n\n"
        "Comenzamos este nuevo día activos y enfocados. ¡Que la suerte esté de nuestro lado! 🍀🔥",
        disable_web_preview=True
    )

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
        lineas_formateadas.append(f"{'.' * dots_count}  {nums_str}  {'.' * dots_count}")
    
    cuerpo_piramide = "\n".join(lineas_formateadas)
    seed_val = int(ahora.strftime("%Y%m%d"))
    rnd = random.Random(seed_val)
    
    candidates = []
    for f in filas:
        for idx in range(len(f) - 1):
            candidates.append(f"{(f[idx] * 10 + f[idx+1]) % 37:02d}")
        for num in f:
            candidates.append(f"{(num * 7) % 37:02d}")
            
    unique_candidates = []
    for c in candidates:
        if c not in unique_candidates:
            unique_candidates.append(c)
            
    while len(unique_candidates) < 6:
        c_rand = f"{rnd.randint(0, 36):02d}"
        if c_rand not in unique_candidates:
            unique_candidates.append(c_rand)
            
    d1 = f"{unique_candidates[0]}-{unique_candidates[1]}-{unique_candidates[2]}"
    d2 = f"{unique_candidates[3]}-{unique_candidates[4]}-{unique_candidates[5]}"
    
    return (
        "🎯 CENTRO DE APUESTAS HAROLD JOSÉ 🎯\n"
        "📢 REPORTE TÁCTICO - LA PIRÁMIDE 📢\n\n"
        f"📅 Fecha: {fecha_str}\n\n"
        f"{cuerpo_piramide}\n\n"
        "🔥 DATOS CLAVES:\n"
        f"📌 {d1}\n"
        f"📌 {d2}\n\n"
        "⚡ ¡A jugar con confianza! 🍀 💰"
    )

def enviar_piramide_diaria():
    enviar_telegram(generar_piramide(), disable_web_preview=True)

def enviar_tasa_dolar():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        precio_dolar = "No disponible"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            dolar_div = soup.find('div', id='dolar')
            if dolar_div and dolar_div.find('strong'):
                precio_dolar = dolar_div.find('strong').get_text(strip=True)
        enviar_telegram(
            f"💵 TASA OFICIAL BCV 💵\n\n🏦 Dólar Estadounidense\n📈 Precio: Bs. {precio_dolar}\n\n🔗 Fuente: BCV",
            disable_web_preview=True
        )
    except Exception as e:
        print(f"Error BCV: {e}")

def enviar_saludo_matutino():
    enviar_telegram(
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n🌅 ¡Buenos días a todos! Listos compartiendo resultados.\n\n"
        "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
        "📸 Instagram: https://www.instagram.com/agharold.jose\n"
        "💬 Canal WhatsApp: https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n¡A ganar! 🍀🔥",
        disable_web_preview=True
    )

def enviar_aviso_taquilla():
    enviar_telegram(
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n📢 ¡AVISO IMPORTANTE!\n"
        "Verifica si la taquilla está activa en nuestro Canal de WhatsApp:\n"
        "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
        f"📲 Escríbenos y consulta nuestro canal: {ENLACE_CANAL}",
        disable_web_preview=True
    )

def obtener_abreviatura(nombre_lotto):
    n = nombre_lotto.upper()
    if "GRANJITA" in n or "GRAJ" in n:
        return "GRAJ"
    elif "LOTTO ACTIVO" in n and "INTERNACIONAL" not in n:
        return "L.ACT"
    elif "SELVA" in n:
        return "SELV"
    elif "GUACHARO" in n:
        return "G.ARO"
    elif "CHAIMA" in n:
        return "CHAIM"
    elif "MONJE" in n:
        return "MONJE"
    elif "ANIMALITOS" in n or "L.ANIM" in n:
        return "L.ANIM"
    elif "PANTERA" in n:
        return "L.PANT"
    elif "REAL" in n:
        return "L.REAL"
    elif "RD" in n:
        return "L.RD"
    elif "CENTRO" in n or "CEN" in n:
        return "CEN.A"
    elif "MEGA" in n:
        return "MEGA"
    elif "PARLEY" in n:
        return "R.PER"
    elif "COLOMBIA" in n:
        return "R.COL"
    elif "VENEZUELA" in n:
        return "R.VEN"
    elif "CONDE" in n:
        return "COND"
    elif "FRUTA" in n:
        return "FRUI"
    elif "TROPICAL" in n:
        return "TROP"
    elif "MILLONARIO" in n:
        return "G.MIL"
    elif "ZODIACAL" in n or "ZOOL" in n:
        return "ZOOL"
    elif "MAX" in n:
        return "L.MAX"
    return n[:4]

def actualizar_mensaje_resumen():
    global resumen_message_id, resultados_tabla_dia
    if not resultados_tabla_dia:
        return

    texto = (
        "╔═══════ ⋆★⋆ ═══════╗\n"
        "   ★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
        "╚═══════ ⋆★⋆ ═══════╝\n"
        "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
        "      Mas de 6 años brindando\n"
        "         confianza y seguridad\n"
        "    en cada rincón de Venezuela\n"
        "      ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰɪᴄɪᴀʟᴇꜱ\n"
        "📲JUEGA AQUI👇👇\n"
        "WHATSAPP: 04124489363\n"
        "📰RESULTADOS ANIMALITOS📰\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
    )

    bloques = [
        ["GRAJ", "L.ACT", "SELV"],
        ["G.ARO", "CHAIM", "MONJE"],
        ["L.ANIM", "L.PANT", "L.REAL"],
        ["L.RD", "CEN.A", "MEGA"],
        ["R.PER", "R.COL", "R.VEN"],
        ["COND", "FRUI", "TROP"],
        ["G.MIL", "ZOOL", "L.MAX"]
    ]

    horas_ordenadas = sorted(resultados_tabla_dia.keys())

    for b_idx, bloque in enumerate(bloques):
        c1, c2, c3 = bloque[0], bloque[1], bloque[2]
        texto += f" HORA🎰{c1[:4]}🪙{c2[:4]}🪙{c3[:4]}\n"
        texto += "➖➖➖➖➖➖➖➖➖➖\n"

        for hora in horas_ordenadas:
            datos_hora = resultados_tabla_dia[hora]
            r1 = datos_hora.get(c1, "....🚫")
            r2 = datos_hora.get(c2, "....🚫")
            r3 = datos_hora.get(c3, "....🚫")
            texto += f"⏰{hora[:5]}  {r1:<6} {r2:<6} {r3:<6}\n"

        if b_idx < len(bloques) - 1:
            texto += "\n"

    texto += "\nMUCHA SUERTE EN SUS JUGADAS"

    try:
        if resumen_message_id:
            bot.edit_message_text(
                chat_id=CANAL,
                message_id=resumen_message_id,
                text=texto,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            print("📝 Tabla resumen acumulativa actualizada con éxito en el canal.")
        else:
            msg = bot.send_message(
                chat_id=CANAL,
                text=texto,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            resumen_message_id = msg.message_id
            try:
                bot.pin_chat_message(chat_id=CANAL, message_id=resumen_message_id)
                print("📌 Nueva tabla resumen enviada y fijada con éxito.")
            except Exception as pin_err:
                print(f"⚠️ No se pudo fijar la tabla resumen: {pin_err}")
    except Exception as e:
        print(f"⚠️ Error al actualizar tabla resumen: {e}")
        try:
            msg = bot.send_message(
                chat_id=CANAL,
                text=texto,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            resumen_message_id = msg.message_id
            bot.pin_chat_message(chat_id=CANAL, message_id=resumen_message_id)
        except Exception as e2:
            print(f"⚠️ Error crítico al recrear la tabla: {e2}")

def tarea_minuto_diez():
    enviar_telegram(
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n📢 ¡Pollas actualizadas!\n"
        "Puedes verlas aquí 👇🏻\nhttps://t.me/pollasydupletas\n\n¡Mucho éxito! 🍀",
        disable_web_preview=False
    )
    if resultados_tabla_dia:
        actualizar_mensaje_resumen()
    print("⏰ Tarea del minuto 10 ejecutada (Pollas + Tabla Resumen).")

def enviar_aviso_pollas():
    enviar_telegram(
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n📢 ¡Pollas actualizadas!\n"
        "Puedes verlas aquí 👇🏻\nhttps://t.me/pollasydupletas\n\n¡Mucho éxito! 🍀",
        disable_web_preview=False
    )

def enviar_mensaje_cierre():
    enviar_telegram(
        "🎯 AGENCIA HAROLD JOSE 🎯\n\n🌙 ¡FINAL DE JORNADA!\n"
        "Gracias por jugar con nosotros. ¡Los esperamos mañana con más energía! 🍀✨",
        disable_web_preview=True
    )

def verificar_resultados():
    global resultados_enviados, primera_ejecucion, resultados_tabla_dia
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
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
            if "RULETA ROYAL" in nombre_loteria.upper():
                continue

            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_slot)
                if not match_h:
                    continue
                hora = match_h.group(1).upper()

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado_crudo = limpiar_texto(match_res.group(1)).upper()
                clave = (nombre_loteria, hora, resultado_crudo)

                partes_res = resultado_crudo.split(" - ")
                if len(partes_res) == 2:
                    num_res = partes_res[0].strip()
                    anim_res = partes_res[1].strip()
                    resultado_formateado = f"{num_res}{anim_res[:2]}"
                else:
                    resultado_formateado = resultado_crudo

                abrev = obtener_abreviatura(nombre_loteria)

                if hora not in resultados_tabla_dia:
                    resultados_tabla_dia[hora] = {}

                if primera_ejecucion:
                    resultados_enviados.add(clave)
                    resultados_tabla_dia[hora][abrev] = resultado_formateado
                else:
                    if clave not in resultados_enviados:
                        item_dict = {'loteria': nombre_loteria, 'hora': hora, 'resultado': resultado_crudo}
                        if item_dict not in nuevos_encontrados:
                            nuevos_encontrados.append(item_dict)
                            resultados_enviados.add(clave)
                            resultados_tabla_dia[hora][abrev] = resultado_formateado

        if primera_ejecucion:
            primera_ejecucion = False
            if resultados_tabla_dia:
                actualizar_mensaje_resumen()
            return

        if nuevos_encontrados:
            for item_nuevo in nuevos_encontrados:
                mensaje = (
                    "🎯 AG HAROLD JOSE 🎯\n\n"
                    f"🎰 {item_nuevo['loteria']}\n"
                    f"🕒 {item_nuevo['hora']}  {item_nuevo['resultado']}\n"
                    f"{ENLACE_CANAL}"
                )
                enviar_telegram(mensaje, disable_web_preview=True)
                time.sleep(3)
            
            actualizar_mensaje_resumen()

    except Exception as e:
        print(f"Error en resultados: {e}")

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
    
    schedule.every().hour.at(":10").do(tarea_minuto_diez)

    schedule.every().day.at("15:30").do(tarea_refuerzo_tarde)
    schedule.every().day.at("18:30").do(enviar_tasa_dolar)
    schedule.every().day.at("21:10").do(enviar_mensaje_cierre)
    schedule.every(1).minute.do(verificar_resultados)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Error en schedule: {e}")
        time.sleep(1)

def iniciar_polling_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True, interval=3, timeout=20)
        except Exception as e:
            print(f"⚠️ Error en polling de Telegram: {e}")
            traceback.print_exc()
            time.sleep(5)

if __name__ == '__main__':
    t_schedule = Thread(target=loop_bot)
    t_schedule.daemon = True
    t_schedule.start()

    t_bot = Thread(target=iniciar_polling_bot)
    t_bot.daemon = True
    t_bot.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
