import os
import re
import time
import random
import logging
from datetime import datetime
from threading import Thread, Lock
from zoneinfo import ZoneInfo

import requests
import schedule
import urllib3
import telebot

from bs4 import BeautifulSoup
from flask import Flask

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

# Zona horaria
TIMEZONE_NAME = os.getenv("TZ", "America/Caracas")

try:
    TIMEZONE = ZoneInfo(TIMEZONE_NAME)
except Exception:
    print(
        f"⚠️ Zona horaria '{TIMEZONE_NAME}' no válida. "
        "Se utilizará America/Caracas."
    )
    TIMEZONE_NAME = "America/Caracas"
    TIMEZONE = ZoneInfo(TIMEZONE_NAME)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("AG_HAROLD_JOSE")


# ============================================================
# VARIABLES DE ENTORNO
# ============================================================

TOKEN = os.getenv("8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk", "").strip()

CANAL = os.getenv(
    "CANAL",
    "@pruebajsj"
).strip()

ENLACE_FIRMA_CANAL = os.getenv(
    "ENLACE_FIRMA_CANAL",
    "https://t.me/pruebajsj"
).strip()

URL_LOTERIA = os.getenv(
    "URL_LOTERIA",
    "https://lotery.winbigvzla.com/resultados"
).strip()

URL_BCV = os.getenv(
    "URL_BCV",
    "https://www.bcv.org.ve/"
).strip()


# ============================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "❌ ERROR: No se encontró la variable de entorno "
        "'TELEGRAM_TOKEN'. "
        "Configúrala en Render antes de iniciar el bot."
    )

if not CANAL:
    raise RuntimeError(
        "❌ ERROR: La variable 'CANAL' está vacía."
    )


# ============================================================
# CONFIGURACIÓN HTTP
# ============================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

HTTP_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 "
        "Safari/537.36"
    )
}

# Sesión HTTP reutilizable
session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# CONFIGURACIÓN DEL BOT DE TELEGRAM
# ============================================================

bot = telebot.TeleBot(
    TOKEN,
    parse_mode=None,
    threaded=True,
)


# ============================================================
# VARIABLES DE ESTADO
# ============================================================

taquilla_activa_hoy = False

imagen_activa_id = None

ultimo_id_foto_canal = None

resultados_enviados = set()

primera_ejecucion = True

# Lock para evitar problemas si varias tareas
# modifican el estado simultáneamente.
estado_lock = Lock()


# ============================================================
# LISTA DE ENLACES OFICIALES
# ============================================================

ENLACES_OFICIALES = {
    "LOTTO ACTIVO":
        "https://www.lottoactivo.com/resultados/lotto_activo/",

    "GUACHARO ACTIVO":
        "https://www.guacharoactivo.com.ve/resultados",

    "LOTO CHAIMA":
        "https://lotochaima.com/",

    "LA GRANJITA":
        "https://lagranjitaonline.com/",

    "SELVA PLUS":
        "https://www.selvaplus.com/resultados",

    "MONJE MILLONARIO":
        "https://www.lottoactivo.com/resultados/lottoactivo2(monjemillonario)/",

    "LOTTO ACTIVO RD INTERNACIONAL":
        "https://www.lottoactivo.com/resultados/lotto_activo_internacional/",

    "GUACA ACTIVA":
        "https://lotery.winbigvzla.com/resultados",

    "MEGA GUACA":
        "https://lotery.winbigvzla.com/resultados",

    "EL GUACHARITO MILLONARIO":
        "https://elguacharitomillonario.com/",

    "TRIO ACTIVO":
        "https://www.lottoactivo.com/resultados/trio_activo/",

    "TRIPLE GUACA37":
        "https://www.guacaactiva.com/",
}


# ============================================================
# TEXTOS DEL BOT
# ============================================================

TEXTO_TAQUILLA = f"""✅ AG HAROLD JOSÉ ACTIVA ✅
Ya estamos operativos brindando la mejor atención. Calidad, respaldo y rapidez en cada una de todas tus solicitudes.

📲 Envía tus jugadas:
(Comprobante de pago / Lotería / monto / Hora)

📖 Consulta nuestro reglamento aquí:
https://wa.me/p/33319103291071105/584124489363

🚀 Agiliza tu proceso aquí:
https://wa.me/p/24724650613899486/584124489363

RESULTADOS AUTOMÁTICOS
{ENLACE_FIRMA_CANAL}

¡Mucho éxito en la jornada de hoy! 🍀✨"""


BANNER_AGENCIA = """╔═══════ ⋆★⋆ ═══════╗
  ★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★
╚═══════ ⋆★⋆ ═══════╝
╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮
      Mas de 6 años brindando
        confianza y seguridad
en cada rincón de Venezuela
      ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰᛁᴄᠢᴀʟᴇꜱ
«La suerte es una flecha 🏹 lanzada que hace blanco 🎯 en el que menos la espera 🤑»
📲JUEGA AQUI👇👇
WHATSAPP: 04124489363"""


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    estado_texto = (
        "ACTIVA"
        if taquilla_activa_hoy
        else "INACTIVA (Esperando señal manual)"
    )

    color_estado = (
        "green"
        if taquilla_activa_hoy
        else "orange"
    )

    return (
        "<html>"
        "<head>"
        "<meta charset='UTF-8'>"
        "<title>AG HAROLD JOSE BOT</title>"
        "</head>"
        "<body>"
        f"<h2>🤖 Bot de resultados AG HAROLD JOSE</h2>"
        f"<p>Canal: {CANAL}</p>"
        f"<p>Estado de la Taquilla Hoy: "
        f"<b style='color:{color_estado};'>"
        f"{estado_texto}"
        f"</b></p>"
        "<hr>"
        "<h3>Enlaces de prueba rápida</h3>"
        "<p>"
        "<a href='/test/madrugada'>"
        "👉 Probar Saludo de Madrugada"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/piramide'>"
        "👉 Probar Pirámide Numérica"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/bcv'>"
        "👉 Probar Tasa BCV"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/saludo'>"
        "👉 Probar Saludo Matutino"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/taquilla'>"
        "👉 Probar Aviso de Taquilla"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/resultados'>"
        "👉 Forzar Revisión de Resultados"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/cierre'>"
        "👉 Probar Mensaje de Cierre"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test-refuerzo'>"
        "👉 Probar Refuerzo de Taquilla"
        "</a>"
        "</p>"
        "<p>"
        "<a href='/test/tabla'>"
        "👉 Probar Formato de Tabla"
        "</a>"
        "</p>"
        "</body>"
        "</html>"
    )


# ============================================================
# RUTAS DE PRUEBA
# ============================================================

@app.route("/test/madrugada")
def test_madrugada():
    enviar_saludo_madrugada()
    return "✅ Prueba ejecutada: saludo de madrugada."


@app.route("/test/piramide")
def test_piramide():
    enviar_piramide_diaria()
    return "✅ Prueba ejecutada: pirámide numérica."


@app.route("/test/bcv")
def test_bcv():
    enviar_tasa_dolar()
    return "✅ Prueba ejecutada: tasa BCV."


@app.route("/test/saludo")
def test_saludo():
    enviar_saludo_matutino()
    return "✅ Prueba ejecutada: saludo matutino."


@app.route("/test/taquilla")
def test_taquilla():
    enviar_aviso_taquilla()
    return "✅ Prueba ejecutada: aviso de taquilla."


@app.route("/test/resultados")
def test_resultados():
    verificar_resultados()
    return "✅ Prueba ejecutada: revisión de resultados."


@app.route("/test/cierre")
def test_cierre():
    enviar_mensaje_cierre()
    return "✅ Prueba ejecutada: mensaje de cierre."


@app.route("/test-refuerzo")
def test_refuerzo():
    tarea_refuerzo_tarde()
    return "✅ Prueba ejecutada: refuerzo de taquilla."


@app.route("/test/tabla")
def test_tabla():

    prueba_texto = (
        "📰RESULTADOS ANIMALITOS📰\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        " HORA🎰G.ITO🪙L.INT\n"
        "⏰08:30  29🐘    03🐛\n"
        "⏰09:30  44🐾    14🕊️\n"
        "⏰10:30  41🦘    32🐿️\n"
        "MUCHA SUERTE EN SUS JUGADAS"
    )

    enviar_mensaje_con_banner(prueba_texto)

    return "✅ Prueba de tabla con banner ejecutada."


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(texto):
    """
    Normaliza espacios y saltos de línea.
    """
    if not texto:
        return ""

    return " ".join(
        str(texto).split()
    )


def enviar_telegram(
    mensaje,
    disable_web_preview=True
):
    """
    Envía un mensaje al canal utilizando la API HTTP de Telegram.
    """

    if not mensaje:
        logger.warning(
            "Se intentó enviar un mensaje vacío."
        )
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CANAL,
        "text": mensaje,
        "disable_web_page_preview":
            disable_web_preview,
    }

    try:

        response = session.post(
            url,
            json=payload,
            timeout=HTTP_TIMEOUT,
        )

        if response.status_code != 200:

            logger.error(
                "Error de Telegram %s: %s",
                response.status_code,
                response.text,
            )

            return False

        return True

    except requests.RequestException as e:

        logger.error(
            "Error de conexión con Telegram: %s",
            e,
        )

        return False

    except Exception as e:

        logger.exception(
            "Error inesperado enviando Telegram: %s",
            e,
        )

        return False


def enviar_mensaje_con_banner(
    texto_original
):
    """
    Agrega el banner de la agencia
    antes del texto y lo publica.
    """

    mensaje_final = (
        BANNER_AGENCIA
        + "\n\n"
        + texto_original
    )

    return enviar_telegram(
        mensaje_final,
        disable_web_preview=True,
    )


# ============================================================
# LIMPIEZA DIARIA DE MEMORIA
# ============================================================

def limpiar_memoria_diaria():

    global resultados_enviados
    global primera_ejecucion
    global taquilla_activa_hoy
    global imagen_activa_id
    global ultimo_id_foto_canal

    with estado_lock:

        resultados_enviados.clear()

        primera_ejecucion = True

        taquilla_activa_hoy = False

        imagen_activa_id = None

        ultimo_id_foto_canal = None

    logger.info(
        "🧹 Memoria diaria limpiada correctamente."
    )


# ============================================================
# ACTIVACIÓN DE TAQUILLA
# ============================================================

def activar_taquilla_proceso():

    global taquilla_activa_hoy
    global imagen_activa_id

    with estado_lock:

        if not imagen_activa_id:

            logger.warning(
                "No se puede activar la taquilla: "
                "no existe imagen disponible."
            )

            return False

        taquilla_activa_hoy = True

        foto_id = imagen_activa_id

    logger.info(
        "✅ Taquilla activada manualmente."
    )

    try:

        bot.send_photo(
            chat_id=CANAL,
            photo=foto_id,
            caption=TEXTO_TAQUILLA,
        )

        logger.info(
            "Mensaje de taquilla activa enviado."
        )

        return True

    except Exception as e:

        logger.exception(
            "Error enviando taquilla activa: %s",
            e,
        )

        return False
# ============================================================
# CAPTURA DE FOTOS PUBLICADAS EN EL CANAL
# ============================================================

@bot.channel_post_handler(content_types=["photo"])
def capturar_foto_canal(message):

    global ultimo_id_foto_canal
    global imagen_activa_id

    try:

        if not message.photo:
            return

        # Guardamos la versión de mayor resolución
        ultimo_id_foto_canal = (
            message.photo[-1].file_id
        )

        caption = (
            message.caption
            if message.caption
            else ""
        )

        caption_lower = caption.lower()

        logger.info(
            "📷 Nueva foto detectada en el canal."
        )

        # Si la publicación contiene
        # "taquilla activa", se activa el proceso
        if "taquilla activa" in caption_lower:

            imagen_activa_id = (
                ultimo_id_foto_canal
            )

            activar_taquilla_proceso()

    except Exception as e:

        logger.exception(
            "Error procesando foto del canal: %s",
            e,
        )


# ============================================================
# CAPTURA DE TEXTOS PUBLICADOS EN EL CANAL
# ============================================================

@bot.channel_post_handler(content_types=["text"])
def capturar_texto_canal(message):

    global imagen_activa_id
    global ultimo_id_foto_canal

    try:

        text = (
            message.text
            if message.text
            else ""
        )

        if not text:
            return

        text_upper = text.upper()

        logger.info(
            "📝 Nuevo texto detectado en el canal."
        )

        # ----------------------------------------------------
        # ACTIVACIÓN DE TAQUILLA
        # ----------------------------------------------------

        if "TAQUILLA ACTIVA" in text_upper:

            if ultimo_id_foto_canal:

                imagen_activa_id = (
                    ultimo_id_foto_canal
                )

                activar_taquilla_proceso()

            else:

                logger.warning(
                    "Se detectó 'TAQUILLA ACTIVA', "
                    "pero no existe una foto previa."
                )

        # ----------------------------------------------------
        # DETECCIÓN DE TABLAS DE RESULTADOS
        # ----------------------------------------------------

        if "RESULTADOS ANIMALITOS" in text_upper:

            # Evitamos volver a procesar
            # publicaciones que ya tengan
            # nuestro propio banner.

            if "HAROLD JOSE" not in text_upper:

                enviar_mensaje_con_banner(
                    text
                )

                logger.info(
                    "📋 Tabla de resultados "
                    "detectada y reenviada."
                )

    except Exception as e:

        logger.exception(
            "Error procesando texto del canal: %s",
            e,
        )


# ============================================================
# REFUERZO DE TAQUILLA EN LA TARDE
# ============================================================

def tarea_refuerzo_tarde():

    global taquilla_activa_hoy
    global imagen_activa_id

    with estado_lock:

        activa = taquilla_activa_hoy
        foto_id = imagen_activa_id

    if not activa or not foto_id:

        logger.info(
            "⏭️ Refuerzo omitido: "
            "la taquilla no está activa."
        )

        return False

    logger.info(
        "🔄 Ejecutando refuerzo de taquilla "
        "de las 3:30 p.m."
    )

    try:

        bot.send_photo(

            chat_id=CANAL,

            photo=foto_id,

            caption=(
                TEXTO_TAQUILLA
                + "\n\n"
                + "🔄 *¡Seguimos activos con "
                "la jornada de la tarde!*"
            ),

            parse_mode="Markdown",
        )

        logger.info(
            "✅ Refuerzo de taquilla "
            "enviado correctamente."
        )

        return True

    except Exception as e:

        logger.exception(
            "Error enviando refuerzo "
            "de taquilla: %s",
            e,
        )

        return False


# ============================================================
# SALUDO DE MADRUGADA
# ============================================================

def enviar_saludo_madrugada():

    mensaje = (
        "AGENCIA HAROLD JOSE - "
        "SALUDO DE MADRUGADA\n\n"

        "¡Despertando con la mejor energía "
        "y listos para ganar!\n\n"

        "Comenzamos este nuevo día activos, "
        "enfocados y con los mejores datos "
        "para asegurar cada jugada. "
        "¡Que la suerte esté de nuestro lado "
        "desde temprano!"
    )

    resultado = enviar_telegram(
        mensaje,
        disable_web_preview=True,
    )

    if resultado:

        logger.info(
            "🌅 Saludo de madrugada enviado."
        )

    return resultado


# ============================================================
# GENERADOR DE PIRÁMIDE NUMÉRICA
# ============================================================

def generar_piramide():

    ahora = datetime.now(
        TIMEZONE
    )

    fecha_str = ahora.strftime(
        "%d/%m/%Y"
    )

    # Extraemos los dígitos de la fecha
    digitos = [
        int(c)
        for c in fecha_str
        if c.isdigit()
    ]

    filas = [
        digitos
    ]

    # Construimos la pirámide
    while len(filas[-1]) > 1:

        actual = filas[-1]

        siguiente = [

            (
                actual[i]
                + actual[i + 1]
            ) % 10

            for i in range(
                len(actual) - 1
            )
        ]

        filas.append(
            siguiente
        )

    # Formateamos visualmente
    lineas_formateadas = []

    for i, fila in enumerate(filas):

        nums_str = "  ".join(
            str(d)
            for d in fila
        )

        dots_count = (
            3 + (i * 2)
        )

        dots = (
            "."
            * dots_count
        )

        lineas_formateadas.append(
            f"{dots}  "
            f"{nums_str}  "
            f"{dots}"
        )

    cuerpo_piramide = (
        "\n".join(
            lineas_formateadas
        )
    )

    # Generador aleatorio determinista
    # basado en la fecha
    seed_val = int(
        ahora.strftime(
            "%Y%m%d"
        )
    )

    rnd = random.Random(
        seed_val
    )

    candidates = []

    # Generamos candidatos
    for fila in filas:

        if len(fila) >= 2:

            for idx in range(
                len(fila) - 1
            ):

                raw_val = (
                    fila[idx] * 10
                    + fila[idx + 1]
                )

                rem = (
                    raw_val % 38
                )

                if rem == 0:

                    candidates.append(
                        "00"
                    )

                elif rem == 1:

                    candidates.append(
                        "0"
                    )

                else:

                    candidates.append(
                        f"{rem - 1:02d}"
                    )

        elif len(fila) == 1:

            raw_val = (
                fila[0] * 11
            )

            rem = (
                raw_val % 38
            )

            if rem == 0:

                candidates.append(
                    "00"
                )

            elif rem == 1:

                candidates.append(
                    "0"
                )

            else:

                candidates.append(
                    f"{rem - 1:02d}"
                )

    # Eliminamos duplicados
    unique_candidates = []

    for candidato in candidates:

        valido = (

            candidato == "00"

            or candidato == "0"

            or (
                candidato.isdigit()
                and 1 <= int(candidato) <= 36
            )
        )

        if (

            valido
            and candidato
            not in unique_candidates

        ):

            unique_candidates.append(
                candidato
            )

    # Completamos hasta seis números
    while len(
        unique_candidates
    ) < 6:

        rand_rem = rnd.randint(
            0,
            37
        )

        if rand_rem == 0:

            c_rand = "00"

        elif rand_rem == 1:

            c_rand = "0"

        else:

            c_rand = (
                f"{rand_rem - 1:02d}"
            )

        if (
            c_rand
            not in unique_candidates
        ):

            unique_candidates.append(
                c_rand
            )

    seis_numeros = (
        unique_candidates[:6]
    )

    d1 = (
        f"{seis_numeros[0]}-"
        f"{seis_numeros[1]}-"
        f"{seis_numeros[2]}"
    )

    d2 = (
        f"{seis_numeros[3]}-"
        f"{seis_numeros[4]}-"
        f"{seis_numeros[5]}"
    )

    mensaje = f"""CENTRO DE APUESTAS HAROLD JOSE
REPORTE TACTICO - LA PIRAMIDE

Fecha: {fecha_str}
Analisis matematico actualizado y listo para la jugada.

{cuerpo_piramide}

DATOS CLAVES PARA HOY:
- {d1}
- {d2}

¡Juega con confianza y gana con nosotros!"""

    return mensaje


# ============================================================
# ENVÍO DE PIRÁMIDE DIARIA
# ============================================================

def enviar_piramide_diaria():

    mensaje = (
        generar_piramide()
    )

    resultado = enviar_telegram(
        mensaje,
        disable_web_preview=True,
    )

    if resultado:

        logger.info(
            "📐 Pirámide numérica enviada."
        )

    return resultado


# ============================================================
# CONSULTA Y ENVÍO DE TASA BCV
# ============================================================

def enviar_tasa_dolar():

    try:

        response = session.get(

            URL_BCV,

            timeout=HTTP_TIMEOUT,

            verify=False,
        )

        precio_dolar = (
            "No disponible"
        )

        if response.status_code == 200:

            soup = BeautifulSoup(

                response.text,

                "html.parser",
            )

            dolar_div = soup.find(

                "div",

                id="dolar",
            )

            if dolar_div:

                strong_elem = (
                    dolar_div.find(
                        "strong"
                    )
                )

                if strong_elem:

                    raw_precio = (
                        strong_elem
                        .get_text(
                            strip=True
                        )
                    )

                    val_limpio = (

                        raw_precio
                        .replace(
                            ".",
                            "",
                        )
                        .replace(
                            ",",
                            ".",
                        )
                    )

                    try:

                        precio_float = (
                            float(
                                val_limpio
                            )
                        )

                        precio_dolar = (

                            f"{precio_float:.2f}"
                            .replace(
                                ".",
                                ",",
                            )
                        )

                    except ValueError:

                        logger.warning(
                            "No se pudo "
                            "convertir el "
                            "valor BCV: %s",
                            raw_precio,
                        )

        else:

            logger.warning(
                "BCV respondió con "
                "HTTP %s",
                response.status_code,
            )

        mensaje = (

            "TASA OFICIAL BCV\n\n"

            "Moneda: Dolar Estadounidense\n"

            f"Precio Oficial: "
            f"Bs. {precio_dolar}\n\n"

            "Fuente: "
            "Banco Central de Venezuela"
        )

        resultado = enviar_telegram(

            mensaje,

            disable_web_preview=True,
        )

        if resultado:

            logger.info(
                "💵 Tasa BCV enviada."
            )

        return resultado

    except requests.RequestException as e:

        logger.error(
            "⚠️ Error de conexión "
            "con BCV: %s",
            e,
        )

        return False

    except Exception as e:

        logger.exception(
            "⚠️ Error inesperado "
            "en tasa BCV: %s",
            e,
        )

        return False


# ============================================================
# SALUDO MATUTINO
# ============================================================

def enviar_saludo_matutino():

    mensaje = (

        "AGENCIA HAROLD JOSE\n\n"

        "¡Buenos días a todos!\n\n"

        "Ya arrancamos un nuevo día "
        "con la mejor energía. "

        "Estaremos compartiendo todos "
        "los resultados de los animalitos "
        "a medida que vayan saliendo.\n\n"

        "Nuestros canales oficiales:\n"

        "Catálogo y WhatsApp: "
        "https://wa.me/c/584124489363\n"

        "Instagram: "
        "https://www.instagram.com/agharold_jose\n"

        "Canal de WhatsApp: "
        "https://whatsapp.com/channel/"
        "0029Vaza7YIGzzKJq7as7s1T\n\n"

        "¡Mucha suerte en sus jugadas "
        "el día de hoy y a ganar!"
    )

    resultado = enviar_telegram(

        mensaje,

        disable_web_preview=True,
    )

    if resultado:

        logger.info(
            "☀️ Saludo matutino enviado."
        )

    return resultado


# ============================================================
# AVISO DE TAQUILLA
# ============================================================

def enviar_aviso_taquilla():

    mensaje_promo = (

        "AGENCIA HAROLD JOSE\n"

        "Tu centro de apuestas de confianza. "
        "Atendemos vía WhatsApp y Telegram.\n\n"

        "AVISO IMPORTANTE PARA "
        "NUESTROS JUGADORES\n\n"

        "Recuerda que para jugar con nosotros "
        "debes acceder primero al Canal de "
        "WhatsApp para verificar si la taquilla "
        "se encuentra activa el día de hoy:\n"

        "https://whatsapp.com/channel/"
        "0029Vaza7YIGzzKJq7as7s1T\n\n"

        "Si la taquilla está activa, puedes "
        "revisar nuestro catálogo y escribirnos "
        "directamente:\n"

        "Catálogo y WhatsApp: "
        "https://wa.me/c/584124489363\n\n"

        "También estamos disponibles "
        "por Telegram:\n"

        "t.me/pruebajsj\n\n"

        "¡Mucha suerte en sus jugadas!"
    )

    resultado = enviar_telegram(

        mensaje_promo,

        disable_web_preview=True,
    )

    if resultado:

        logger.info(
            "📢 Aviso de taquilla enviado."
        )

    return resultado


# ============================================================
# MENSAJE DE CIERRE DE JORNADA
# ============================================================

def enviar_mensaje_cierre():

    mensaje = (

        "AGENCIA HAROLD JOSE\n\n"

        "FINAL DE JORNADA\n\n"

        "Estos fueron todos los resultados "
        "del día de hoy. "

        "¡Gracias por jugar con nosotros! "

        "Los esperamos el día de mañana "
        "con mucha más suerte y energía."
    )

    resultado = enviar_telegram(

        mensaje,

        disable_web_preview=True,
    )

    if resultado:

        logger.info(
            "🌙 Mensaje de cierre "
            "de jornada enviado."
        )

    return resultado
# ============================================================
# VERIFICACIÓN AUTOMÁTICA DE RESULTADOS
# ============================================================

def verificar_resultados():

    global resultados_enviados
    global primera_ejecucion

    try:

        logger.info(
            "🔎 Revisando resultados automáticos..."
        )

        # ----------------------------------------------------
        # CONSULTA DE LA PÁGINA
        # ----------------------------------------------------

        respuesta = session.get(

            URL_LOTERIA,

            timeout=HTTP_TIMEOUT,

            verify=False,
        )

        if respuesta.status_code != 200:

            logger.warning(

                "⚠️ La página de resultados "
                "respondió con HTTP %s",

                respuesta.status_code,
            )

            return False

        # ----------------------------------------------------
        # PARSEAR HTML
        # ----------------------------------------------------

        soup = BeautifulSoup(

            respuesta.text,

            "html.parser",
        )

        tarjetas = soup.find_all(

            [
                "div",
                "article",
                "section",
            ],

            class_=re.compile(

                r"card|box|item|lotto|result",

                re.IGNORECASE,
            ),
        )

        nuevos_encontrados = []

        # ----------------------------------------------------
        # RECORRER TARJETAS
        # ----------------------------------------------------

        for tarjeta in tarjetas:

            try:

                nombre_loteria = ""

                # ------------------------------------------------
                # BUSCAR POSIBLES TÍTULOS
                # ------------------------------------------------

                posibles_titulos = (

                    tarjeta.find_all(

                        [
                            "h1",
                            "h2",
                            "h3",
                            "h4",
                            "h5",
                            "span",
                            "div",
                            "strong",
                            "b",
                        ],

                        class_=re.compile(

                            r"title|header|name|lotto|text",

                            re.IGNORECASE,
                        ),
                    )
                )

                for pt in posibles_titulos:

                    t_text = (

                        pt.get_text(

                            " ",

                            strip=True,
                        )
                        .upper()
                    )

                    # Ignorar textos irrelevantes
                    if not t_text:

                        continue

                    if len(t_text) <= 2:

                        continue

                    if re.search(

                        r"\d{1,2}:\d{2}",

                        t_text,
                    ):

                        continue

                    if "PENDIENTE" in t_text:

                        continue

                    if t_text in [

                        "WINBIG",

                        "RESULTADOS",

                    ]:

                        continue

                    nombre_loteria = (
                        t_text
                    )

                    break

                # ------------------------------------------------
                # SI NO SE ENCONTRÓ TÍTULO
                # BUSCAR EN EL TEXTO DE LA TARJETA
                # ------------------------------------------------

                if not nombre_loteria:

                    lineas = [

                        linea.strip().upper()

                        for linea in (

                            tarjeta.get_text(

                                "\n",

                                strip=True,
                            )
                            .split("\n")
                        )

                        if linea.strip()
                    ]

                    for linea in lineas:

                        if len(linea) <= 2:

                            continue

                        if re.search(

                            r"\d{1,2}:\d{2}",

                            linea,
                        ):

                            continue

                        if (
                            "PENDIENTE"
                            in linea
                        ):

                            continue

                        if "-" in linea:

                            continue

                        nombre_loteria = (
                            linea
                        )

                        break

                # ------------------------------------------------
                # VALIDAR NOMBRE
                # ------------------------------------------------

                if not nombre_loteria:

                    continue

                if len(nombre_loteria) > 40:

                    continue

                nombre_loteria = (
                    limpiar_texto(
                        nombre_loteria
                    )
                )

                # ------------------------------------------------
                # IGNORAR RULETA ROYAL
                # ------------------------------------------------

                if (
                    "RULETA ROYAL"
                    in nombre_loteria
                ):

                    continue

                # ------------------------------------------------
                # BUSCAR SORTEOS
                # ------------------------------------------------

                slots_sorteo = (

                    tarjeta.find_all(

                        [
                            "div",
                            "li",
                            "span",
                            "tr",
                        ],

                        class_=re.compile(

                            r"item|slot|draw|row|col",

                            re.IGNORECASE,
                        ),
                    )
                )

                # Si no hay elementos internos,
                # utilizamos la tarjeta completa.

                if not slots_sorteo:

                    slots_sorteo = [
                        tarjeta
                    ]

                # ------------------------------------------------
                # RECORRER CADA SORTEO
                # ------------------------------------------------

                for slot in slots_sorteo:

                    try:

                        texto_slot = (

                            slot.get_text(

                                " ",

                                strip=True,
                            )
                            .upper()
                        )

                        if not texto_slot:

                            continue

                        if (
                            "PENDIENTE"
                            in texto_slot
                        ):

                            continue

                        # ------------------------------------------------
                        # BUSCAR HORA
                        # ------------------------------------------------

                        match_h = re.search(

                            r"(\d{1,2}:\d{2}\s*"
                            r"(?:AM|PM))",

                            texto_slot,
                        )

                        if not match_h:

                            continue

                        hora = (

                            match_h.group(
                                1
                            )
                            .upper()
                        )

                        # ------------------------------------------------
                        # DETECTAR TRIPLES
                        # ------------------------------------------------

                        es_triple = (

                            "TRIO ACTIVO"
                            in nombre_loteria

                            or

                            "TRÍO ACTIVO"
                            in nombre_loteria

                            or

                            "TRIPLE GUACA"
                            in nombre_loteria
                        )

                        # =================================================
                        # RESULTADOS DE TRES DÍGITOS
                        # =================================================

                        if es_triple:

                            match_num = re.search(

                                r"#?(\d{3})",

                                texto_slot,
                            )

                            if not match_num:

                                continue

                            num_triple = (

                                match_num.group(
                                    1
                                )
                            )

                            terminal = (

                                num_triple[-2:]
                            )

                            # Normalizamos nombre
                            # del Trío Activo

                            if (

                                "TRIO"
                                in nombre_loteria

                                or

                                "TRÍO"
                                in nombre_loteria
                            ):

                                loteria_nombre = (
                                    "TRÍO ACTIVO"
                                )

                            else:

                                loteria_nombre = (
                                    nombre_loteria
                                )

                            # Clave única
                            clave = (

                                nombre_loteria,

                                hora,

                                num_triple,
                            )

                            # ------------------------------------------------
                            # PRIMERA EJECUCIÓN
                            # ------------------------------------------------

                            if primera_ejecucion:

                                resultados_enviados.add(

                                    clave
                                )

                            # ------------------------------------------------
                            # RESULTADO NUEVO
                            # ------------------------------------------------

                            else:

                                if (

                                    clave
                                    not in
                                    resultados_enviados
                                ):

                                    item_dict = {

                                        "tipo":
                                            "triple",

                                        "loteria":
                                            loteria_nombre,

                                        "hora":
                                            hora,

                                        "numero":
                                            num_triple,

                                        "terminal":
                                            terminal,
                                    }

                                    if (

                                        item_dict
                                        not in
                                        nuevos_encontrados
                                    ):

                                        nuevos_encontrados.append(

                                            item_dict
                                        )

                                        resultados_enviados.add(

                                            clave
                                        )

                        # =================================================
                        # RESULTADOS DE ANIMALITOS
                        # =================================================

                        else:

                            match_res = re.search(

                                r"(\d{1,2}\s-\s"
                                r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+"
                                r"(?:\s+"
                                r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)",

                                texto_slot,
                            )

                            if not match_res:

                                continue

                            resultado_final = (

                                limpiar_texto(

                                    match_res.group(
                                        1
                                    )
                                )
                                .upper()
                            )

                            # Clave única
                            clave = (

                                nombre_loteria,

                                hora,

                                resultado_final,
                            )

                            # ------------------------------------------------
                            # PRIMERA EJECUCIÓN
                            # ------------------------------------------------

                            if primera_ejecucion:

                                resultados_enviados.add(

                                    clave
                                )

                            # ------------------------------------------------
                            # RESULTADO NUEVO
                            # ------------------------------------------------

                            else:

                                if (

                                    clave
                                    not in
                                    resultados_enviados
                                ):

                                    item_dict = {

                                        "tipo":
                                            "animalito",

                                        "loteria":
                                            nombre_loteria,

                                        "hora":
                                            hora,

                                        "resultado":
                                            resultado_final,
                                    }

                                    if (

                                        item_dict
                                        not in
                                        nuevos_encontrados
                                    ):

                                        nuevos_encontrados.append(

                                            item_dict
                                        )

                                        resultados_enviados.add(

                                            clave
                                        )

                    except Exception as e:

                        logger.exception(

                            "Error procesando "
                            "un sorteo individual: %s",

                            e,
                        )

                        continue

            except Exception as e:

                logger.exception(

                    "Error procesando "
                    "una tarjeta de resultados: %s",

                    e,
                )

                continue

        # ============================================================
        # PUBLICAR RESULTADOS NUEVOS
        # ============================================================

        if (

            nuevos_encontrados

            and

            not primera_ejecucion

        ):

            mensaje_lote = (

                "AGENCIA HAROLD JOSE "
                "- RESULTADOS\n\n"
            )

            for item in nuevos_encontrados:

                tipo = item.get(
                    "tipo"
                )

                loteria = item.get(
                    "loteria",
                    "Desconocida",
                )

                hora = item.get(
                    "hora",
                    "",
                )

                # ----------------------------------------------------
                # RESULTADO TRIPLE
                # ----------------------------------------------------

                if tipo == "triple":

                    numero = item.get(
                        "numero",
                        "",
                    )

                    terminal = item.get(
                        "terminal",
                        "",
                    )

                    mensaje_lote += (

                        f"*{loteria}* "
                        f"({hora})\n"

                        f"Num: {numero} "
                        f"(Terminal: "
                        f"{terminal})\n\n"
                    )

                # ----------------------------------------------------
                # RESULTADO ANIMALITO
                # ----------------------------------------------------

                else:

                    resultado = item.get(

                        "resultado",

                        "",
                    )

                    mensaje_lote += (

                        f"*{loteria}* "
                        f"({hora})\n"

                        f"Resultado: "
                        f"{resultado}\n\n"
                    )

            mensaje_lote += (

                f"Enlace: "
                f"{ENLACE_FIRMA_CANAL}"
            )

            # --------------------------------------------------------
            # Enviamos usando Markdown porque los nombres
            # de las loterías se formatean con *negrita*.
            # --------------------------------------------------------

            url = (

                f"https://api.telegram.org/"
                f"bot{TOKEN}/sendMessage"
            )

            payload = {

                "chat_id":
                    CANAL,

                "text":
                    mensaje_lote,

                "parse_mode":
                    "Markdown",

                "disable_web_page_preview":
                    True,
            }

            try:

                response = session.post(

                    url,

                    json=payload,

                    timeout=HTTP_TIMEOUT,
                )

                if response.status_code != 200:

                    logger.error(

                        "Error enviando lote "
                        "de resultados: %s",

                        response.text,
                    )

                else:

                    logger.info(

                        "🎰 Se enviaron %s "
                        "nuevos resultados.",

                        len(
                            nuevos_encontrados
                        ),
                    )

            except Exception as e:

                logger.exception(

                    "Error enviando resultados "
                    "a Telegram: %s",

                    e,
                )

        # ------------------------------------------------------------
        # Después de la primera revisión,
        # las siguientes revisiones buscarán
        # únicamente resultados 
