import os
import re
import time
import sqlite3
import logging
from threading import Thread, Lock

import requests
import schedule
from bs4 import BeautifulSoup
from flask import Flask


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")

CANAL_ID = os.environ.get(
    "CANAL_ID",
    "@pruebajsj"
)

URL_LOTERIA = os.environ.get(
    "URL_LOTERIA",
    "https://lotery.winbigvzla.com/resultados"
)

PORT = int(os.environ.get("PORT", 5000))

INTERVALO_MINUTOS = 2

# Tiempo máximo de espera para las peticiones HTTP
TIMEOUT_HTTP = 15

# Número máximo de intentos para enviar mensajes
MAX_REINTENTOS = 3


# ============================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "❌ Falta la variable de entorno TELEGRAM_TOKEN."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "¡El bot de resultados AG HAROLD JOSE está activo!"


@app.route("/health")
def health():
    return {
        "status": "ok",
        "bot": "AG HAROLD JOSE"
    }


# ============================================================
# VARIABLES GLOBALES
# ============================================================

primera_ejecucion = True

# Evita que dos verificaciones se ejecuten simultáneamente
lock_verificacion = Lock()


# ============================================================
# BASE DE DATOS SQLITE
# ============================================================

DB_NAME = "resultados.db"


def inicializar_base_datos():
    """
    Crea la tabla de resultados enviados si no existe.
    """

    conexion = sqlite3.connect(DB_NAME)

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados_enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loteria TEXT NOT NULL,
            hora TEXT NOT NULL,
            resultado TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(loteria, hora, resultado)
        )
    """)

    conexion.commit()
    conexion.close()

    logger.info("✅ Base de datos inicializada.")


def resultado_existe(loteria, hora, resultado):
    """
    Comprueba si un resultado ya fue registrado.
    """

    conexion = sqlite3.connect(DB_NAME)

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 1
        FROM resultados_enviados
        WHERE loteria = ?
        AND hora = ?
        AND resultado = ?
        LIMIT 1
    """, (
        loteria,
        hora,
        resultado
    ))

    existe = cursor.fetchone() is not None

    conexion.close()

    return existe


def guardar_resultado(loteria, hora, resultado):
    """
    Guarda un resultado después de confirmar
    que fue enviado correctamente a Telegram.
    """

    conexion = sqlite3.connect(DB_NAME)

    cursor = conexion.cursor()

    try:

        cursor.execute("""
            INSERT OR IGNORE INTO resultados_enviados
            (
                loteria,
                hora,
                resultado
            )
            VALUES (?, ?, ?)
        """, (
            loteria,
            hora,
            resultado
        ))

        conexion.commit()

        return True

    except Exception as e:

        logger.error(
            f"❌ Error guardando resultado en DB: {e}"
        )

        return False

    finally:

        conexion.close()


# ============================================================
# UTILIDADES
# ============================================================

def limpiar_texto(texto):
    """
    Limpia espacios y saltos de línea innecesarios.
    """

    return " ".join(texto.split())


# ============================================================
# TELEGRAM
# ============================================================

def enviar_mensaje_telegram(mensaje):
    """
    Envía un mensaje al canal de Telegram.

    Devuelve True si el envío fue exitoso.
    """

    url = (
        f"https://api.telegram.org/bot"
        f"{TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CANAL_ID,
        "text": mensaje
    }

    for intento in range(1, MAX_REINTENTOS + 1):

        try:

            respuesta = requests.post(
                url,
                json=payload,
                timeout=TIMEOUT_HTTP
            )

            if respuesta.status_code == 200:

                datos = respuesta.json()

                if datos.get("ok"):

                    logger.info(
                        "✅ Mensaje enviado correctamente."
                    )

                    return True

                logger.error(
                    f"❌ Telegram respondió con error: "
                    f"{datos}"
                )

            else:

                logger.error(
                    f"❌ Error HTTP Telegram: "
                    f"{respuesta.status_code} - "
                    f"{respuesta.text}"
                )

        except requests.RequestException as e:

            logger.error(
                f"⚠️ Error de conexión con Telegram "
                f"(intento {intento}/{MAX_REINTENTOS}): {e}"
            )

        except Exception as e:

            logger.error(
                f"⚠️ Error inesperado enviando Telegram: {e}"
            )

        if intento < MAX_REINTENTOS:

            espera = intento * 2

            logger.info(
                f"🔄 Reintentando en {espera} segundos..."
            )

            time.sleep(espera)

    logger.error(
        "❌ No fue posible enviar el mensaje "
        "después de varios intentos."
    )

    return False


# ============================================================
# SCRAPER
# ============================================================

def obtener_resultados():
    """
    Accede a la página de resultados y extrae
    los resultados encontrados.

    Devuelve una lista de diccionarios.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:

        with requests.Session() as session:

            respuesta = session.get(
                URL_LOTERIA,
                headers=headers,
                timeout=TIMEOUT_HTTP
            )

            if respuesta.status_code != 200:

                logger.error(
                    f"❌ Error accediendo a la página: "
                    f"{respuesta.status_code}"
                )

                return []

            soup = BeautifulSoup(
                respuesta.text,
                "html.parser"
            )

            tarjetas = soup.find_all(
                [
                    "div",
                    "article",
                    "section"
                ],
                class_=re.compile(
                    r"card|box|item|lotto|result",
                    re.IGNORECASE
                )
            )

            resultados = []

            for tarjeta in tarjetas:

                # ====================================================
                # BUSCAR NOMBRE DE LOTERÍA
                # ====================================================

                nombre_loteria = ""

                posibles_titulos = tarjeta.find_all(
                    [
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "span",
                        "div",
                        "strong",
                        "b"
                    ],
                    class_=re.compile(
                        r"title|header|name|lotto|text",
                        re.IGNORECASE
                    )
                )

                for pt in posibles_titulos:

                    texto = pt.get_text(
                        " ",
                        strip=True
                    ).upper()

                    if (
                        texto
                        and len(texto) > 2
                        and not re.search(
                            r"\d{1,2}:\d{2}",
                            texto
                        )
                        and "PENDIENTE" not in texto
                        and texto not in [
                            "WINBIG",
                            "RESULTADOS"
                        ]
                    ):

                        nombre_loteria = texto

                        break

                # ====================================================
                # SEGUNDO MÉTODO PARA ENCONTRAR NOMBRE
                # ====================================================

                if not nombre_loteria:

                    lineas = [
                        linea.strip().upper()
                        for linea in tarjeta.get_text(
                            "\n",
                            strip=True
                        ).split("\n")
                        if linea.strip()
                    ]

                    for linea in lineas:

                        if (
                            len(linea) > 2
                            and not re.search(
                                r"\d{1,2}:\d{2}",
                                linea
                            )
                            and "PENDIENTE" not in linea
                            and "-" not in linea
                        ):

                            nombre_loteria = linea

                            break

                if (
                    not nombre_loteria
                    or len(nombre_loteria) > 40
                ):
                    continue

                nombre_loteria = limpiar_texto(
                    nombre_loteria
                )

                # ====================================================
                # BUSCAR SORTEOS
                # ====================================================

                slots_sorteo = tarjeta.find_all(
                    [
                        "div",
                        "li",
                        "span",
                        "tr"
                    ],
                    class_=re.compile(
                        r"item|slot|draw|row|col",
                        re.IGNORECASE
                    )
                )

                if not slots_sorteo:

                    slots_sorteo = [tarjeta]

                for slot in slots_sorteo:

                    texto_slot = slot.get_text(
                        " ",
                        strip=True
                    ).upper()

                    if "PENDIENTE" in texto_slot:

                        continue

                    # ====================================================
                    # EXTRAER HORA
                    # ====================================================

                    match_hora = re.search(
                        r"(\d{1,2}:\d{2}\s*(?:AM|PM))",
                        texto_slot
                    )

                    if not match_hora:

                        continue

                    hora = match_hora.group(1).upper()

                    # ====================================================
                    # EXTRAER RESULTADO
                    # ====================================================

                    match_resultado = re.search(
                        r"(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)",
                        texto_slot
                    )

                    if not match_resultado:

                        continue

                    resultado_final = limpiar_texto(
                        match_resultado.group(1)
                    ).upper()

                    resultado = {
                        "loteria": nombre_loteria,
                        "hora": hora,
                        "resultado": resultado_final
                    }

                    # Evitar duplicados dentro
                    # de la misma consulta

                    if resultado not in resultados:

                        resultados.append(resultado)

            return resultados

    except requests.RequestException as e:

        logger.error(
            f"❌ Error de conexión con la página: {e}"
        )

        return []

    except Exception as e:

        logger.error(
            f"⚠️ Error procesando resultados: {e}"
        )

        return []


# ============================================================
# FORMATO DEL MENSAJE
# ============================================================

def construir_mensaje(resultado):
    """
    Construye el mensaje que será enviado al canal.
    """

    mensaje = (
        "🎯 AG HAROLD JOSE 🎯\n"
        f"🎰 {resultado['loteria']}\n"
        f"🕒 {resultado['hora']}  "
        f"{resultado['resultado']}"
    )

    return mensaje


# ============================================================
# VERIFICACIÓN PRINCIPAL
# ============================================================

def verificar_resultados():

    global primera_ejecucion

    # Evitar ejecuciones simultáneas

    if not lock_verificacion.acquire(
        blocking=False
    ):

        logger.warning(
            "⚠️ Ya existe una verificación en ejecución."
        )

        return

    try:

        logger.info(
            "🔍 Consultando nuevos resultados..."
        )

        resultados = obtener_resultados()

        if not resultados:

            logger.info(
                "ℹ️ No se encontraron resultados."
            )

            return

        logger.info(
            f"📊 Resultados encontrados: "
            f"{len(resultados)}"
        )

        # ========================================================
        # PRIMERA EJECUCIÓN
        # ========================================================

        if primera_ejecucion:

            nuevos_registros = 0

            for item in resultados:

                if not resultado_existe(
                    item["loteria"],
                    item["hora"],
                    item["resultado"]
                ):

                    guardar_resultado(
                        item["loteria"],
                        item["hora"],
                        item["resultado"]
                    )

                    nuevos_registros += 1

            primera_ejecucion = False

            logger.info(
                "🚀 Sincronización inicial completada."
            )

            logger.info(
                f"📦 Registros sincronizados: "
                f"{nuevos_registros}"
            )

            logger.info(
                "📢 A partir de ahora solo se "
                "enviarán resultados nuevos."
            )

            return

        # ========================================================
        # EJECUCIONES POSTERIORES
        # ========================================================

        nuevos_encontrados = 0

        for item in resultados:

            loteria = item["loteria"]
            hora = item["hora"]
            resultado = item["resultado"]

            # Ya existe en la base de datos

            if resultado_existe(
                loteria,
                hora,
                resultado
            ):

                continue

            mensaje = construir_mensaje(
                item
            )

            logger.info(
                f"📢 Nuevo resultado detectado: "
                f"{loteria} | "
                f"{hora} | "
                f"{resultado}"
            )

            # Enviar primero

            enviado = enviar_mensaje_telegram(
                mensaje
            )

            # Solo guardar si Telegram confirmó
            # el envío correctamente

            if enviado:

                guardado = guardar_resultado(
                    loteria,
                    hora,
                    resultado
                )

                if guardado:

                    nuevos_encontrados += 1

                    logger.info(
                        "💾 Resultado guardado correctamente."
                    )

            # Pausa para evitar enviar
            # demasiados mensajes rápidamente

            time.sleep(1)

        if nuevos_encontrados == 0:

            logger.info(
                "ℹ️ No hay resultados nuevos."
            )

        else:

            logger.info(
                f"🎉 Nuevos resultados enviados: "
                f"{nuevos_encontrados}"
            )

    except Exception as e:

        logger.error(
            f"⚠️ Error general verificando resultados: {e}"
        )

    finally:

        lock_verificacion.release()


# ============================================================
# LOOP DEL BOT
# ============================================================

def loop_bot():

    logger.info(
        "🤖 Iniciando sistema de monitoreo..."
    )

    # Primera sincronización

    verificar_resultados()

    # Programar revisiones

    schedule.every(
        INTERVALO_MINUTOS
    ).minutes.do(
        verificar_resultados
    )

    logger.info(
        f"⏱️ Verificación programada cada "
        f"{INTERVALO_MINUTOS} minutos."
    )

    while True:

        try:

            schedule.run_pending()

        except Exception as e:

            logger.error(
                f"⚠️ Error en el scheduler: {e}"
            )

        time.sleep(1)


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":

    logger.info(
        "🚀 Iniciando AG HAROLD JOSE..."
    )

    # Crear base de datos

    inicializar_base_datos()

    # Iniciar bot en segundo plano

    thread_bot = Thread(
        target=loop_bot,
        daemon=True
    )

    thread_bot.start()

    logger.info(
        "✅ Hilo del bot iniciado."
    )

    # Iniciar Flask

    logger.info(
        f"🌐 Servidor Flask iniciando en puerto {PORT}..."
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
