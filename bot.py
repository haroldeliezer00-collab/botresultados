```python
import os
import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3

# ============================================================
# CONFIGURACIÓN DE ZONA HORARIA
# ============================================================

# Zona horaria de Venezuela
os.environ["TZ"] = "America/Caracas"

try:
    time.tzset()
except AttributeError:
    # Compatible con Windows
    pass


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

# Desactivar advertencias SSL
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# ============================================================
# CONFIGURACIÓN DEL BOT
# ============================================================

TOKEN = "TU_TOKEN_AQUI"

# Canal oficial
CANAL = "@resultadosagharoldjose"

# URL de resultados
URL_LOTERIA = "https://lotery.winbigvzla.com/resultados"

# URL del BCV
URL_BCV = "https://www.bcv.org.ve/"


# ============================================================
# FLASK
# ============================================================

app = Flask("")


# ============================================================
# MEMORIA DE RESULTADOS
# ============================================================

resultados_enviados = set()

primera_ejecucion = True


# ============================================================
# FUNCIÓN PARA LIMPIAR TEXTO
# ============================================================

def limpiar_texto(texto):
    return " ".join(texto.split())


# ============================================================
# ENVÍO A TELEGRAM
# ============================================================

def enviar_telegram(
    mensaje,
    disable_web_preview=True
):

    """
    Función centralizada para enviar mensajes
    al canal oficial.
    """

    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CANAL,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": (
            disable_web_preview
        )
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        if response.status_code != 200:

            print(
                "⚠️ Error al enviar al canal:"
            )

            print(
                response.text
            )

            return False

        print(
            "✅ Mensaje enviado correctamente."
        )

        return True

    except requests.exceptions.Timeout:

        print(
            "⚠️ Tiempo de espera agotado "
            "al enviar mensaje."
        )

        return False

    except requests.exceptions.RequestException as e:

        print(
            f"⚠️ Error de conexión con Telegram: {e}"
        )

        return False

    except Exception as e:

        print(
            f"⚠️ Excepción inesperada "
            f"con Telegram: {e}"
        )

        return False


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def home():

    return (
        "¡El bot de resultados AG HAROLD JOSE "
        "está activo y blindado!"
        "<br><br>"
        "<b>Enlaces de prueba rápida:</b><br>"
        "👉 <a href='/test/saludo'>"
        "Probar Saludo Matutino</a><br>"
        "👉 <a href='/test/taquilla'>"
        "Probar Aviso de Taquilla</a><br>"
        "👉 <a href='/test/bcv'>"
        "Probar Tasa BCV</a><br>"
        "👉 <a href='/test/resultados'>"
        "Forzar Revisión de Resultados</a>"
    )


# ============================================================
# RUTAS DE PRUEBA
# ============================================================

@app.route("/test/saludo")
def test_saludo():

    try:

        enviar_saludo_matutino()

        return (
            "¡Prueba ejecutada! "
            "Se envió el saludo matutino al canal."
        )

    except Exception as e:

        print(
            f"⚠️ Error en prueba de saludo: {e}"
        )

        return (
            f"Error ejecutando prueba: {e}"
        ), 500


@app.route("/test/taquilla")
def test_taquilla():

    try:

        enviar_aviso_taquilla()

        return (
            "¡Prueba ejecutada! "
            "Se envió el aviso de taquilla al canal."
        )

    except Exception as e:

        print(
            f"⚠️ Error en prueba de taquilla: {e}"
        )

        return (
            f"Error ejecutando prueba: {e}"
        ), 500


@app.route("/test/bcv")
def test_bcv():

    try:

        enviar_tasa_dolar()

        return (
            "¡Prueba ejecutada! "
            "Se envió la tasa del BCV al canal."
        )

    except Exception as e:

        print(
            f"⚠️ Error en prueba BCV: {e}"
        )

        return (
            f"Error ejecutando prueba: {e}"
        ), 500


@app.route("/test/resultados")
def test_resultados():

    try:

        verificar_resultados()

        return (
            "¡Prueba ejecutada! "
            "Se forzó la revisión de los resultados."
        )

    except Exception as e:

        print(
            f"⚠️ Error en prueba de resultados: {e}"
        )

        return (
            f"Error ejecutando prueba: {e}"
        ), 500


# ============================================================
# LIMPIAR MEMORIA DIARIA
# ============================================================

def limpiar_memoria_diaria():

    global resultados_enviados
    global primera_ejecucion

    resultados_enviados.clear()

    primera_ejecucion = True

    print(
        "🧹 Memoria de resultados limpiada "
        "para arrancar el nuevo día."
    )


# ============================================================
# SALUDO MATUTINO
# ============================================================

def enviar_saludo_matutino():

    mensaje = (

        "🎯 *AGENCIA HAROLD JOSE* 🎯\n\n"

        "🌅 *¡Buenos días a todos!* 🌅\n\n"

        "Ya arrancamos un nuevo día "
        "con la mejor energía. "

        "Por aquí estaremos compartiendo "
        "todos los resultados de los animalitos "
        "a medida que vayan saliendo.\n\n"

        "📢 *Nuestros canales oficiales:*\n"

        "🎟️ Catálogo y WhatsApp: "
        "https://wa.me/c/584124489363\n"

        "📸 Instagram: "
        "https://www.instagram.com/"
        "agharold\\_jose "
        "(@agharold\\_jose)\n"

        "💬 Canal de WhatsApp: "
        "https://whatsapp.com/channel/"
        "0029Vaza7YIGzzKJq7as7s1T\n\n"

        "¡Mucha suerte en sus jugadas "
        "el día de hoy y a ganar! 🍀🔥"
    )

    enviar_telegram(
        mensaje,
        disable_web_preview=True
    )

    print(
        "☀️ Saludo matutino enviado."
    )


# ============================================================
# TASA DEL BCV
# ============================================================

def enviar_tasa_dolar():

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 "
            "Safari/537.36"
        }

        response = requests.get(
            URL_BCV,
            headers=headers,
            timeout=20,
            verify=False
        )

        precio_dolar = "No disponible"

        if response.status_code == 200:

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            dolar_div = soup.find(
                "div",
                id="dolar"
            )

            if dolar_div:

                strong_elem = (
                    dolar_div.find(
                        "strong"
                    )
                )

                if strong_elem:

                    precio_dolar = (
                        strong_elem.get_text(
                            strip=True
                        )
                    )

        mensaje = (

            "💵 *TASA OFICIAL BCV* 💵\n\n"

            "🏦 *Moneda:* "
            "Dólar Estadounidense\n"

            f"📈 *Precio Oficial:* "
            f"Bs. *{precio_dolar}*\n\n"

            "🔗 Fuente: "
            "[Banco Central de Venezuela]"
            "(https://www.bcv.org.ve/)"
        )

        enviar_telegram(
            mensaje,
            disable_web_preview=True
        )

        print(
            f"💵 Tasa BCV enviada: "
            f"{precio_dolar}"
        )

    except requests.exceptions.RequestException as e:

        print(
            f"⚠️ Error de conexión con BCV: {e}"
        )

    except Exception as e:

        print(
            f"⚠️ Error en tasa BCV: {e}"
        )


# ============================================================
# AVISO DE TAQUILLA
# ============================================================

def enviar_aviso_taquilla():

    mensaje_promo = (

        "🎯 *AGENCIA HAROLD JOSE* 🎯\n"

        "Tu centro de apuestas de confianza. "
        "Atendemos vía WhatsApp y Telegram.\n\n"

        "📢 *¡AVISO IMPORTANTE "
        "PARA NUESTROS JUGADORES!* 📢\n\n"

        "Recuerda que para jugar con nosotros "
        "debes acceder primero a nuestro "
        "*Canal de WhatsApp* para verificar "
        "si la taquilla se encuentra activa "
        "el día de hoy:\n"

        "👉 "
        "https://whatsapp.com/channel/"
        "0029Vaza7YIGzzKJq7as7s1T\n\n"

        "📲 *Si la taquilla está activa*, "
        "puedes revisar nuestro catálogo "
        "y escribirnos directamente:\n"

        "🎟️ Catálogo y WhatsApp: "
        "https://wa.me/c/584124489363\n\n"

        "💬 También estamos disponibles "
        "por Telegram:\n"

        "👉 t.me/ag\\_haroldjose\n\n"

        "¡Mucha suerte en sus jugadas! 🍀🔥"
    )

    enviar_telegram(
        mensaje_promo,
        disable_web_preview=True
    )

    print(
        "📢 Aviso de taquilla enviado."
    )


# ============================================================
# VERIFICAR RESULTADOS
# ============================================================

def verificar_resultados():

    global primera_ejecucion

    try:

        headers = {

            "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 "
            "Safari/537.36"
        }

        respuesta = requests.get(

            URL_LOTERIA,

            headers=headers,

            timeout=20
        )

        if respuesta.status_code != 200:

            print(

                "⚠️ La página de resultados "
                "respondió con código: "
                f"{respuesta.status_code}"
            )

            return


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


        nuevos_encontrados = []


        # ====================================================
        # RECORRER TARJETAS
        # ====================================================

        for tarjeta in tarjetas:

            nombre_loteria = ""


            # -----------------------------------------------
            # BUSCAR POSIBLES TÍTULOS
            # -----------------------------------------------

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
                        "b"
                    ],

                    class_=re.compile(

                        r"title|header|name|lotto|text",

                        re.IGNORECASE
                    )
                )
            )


            for pt in posibles_titulos:

                t_text = (

                    pt.get_text(

                        " ",

                        strip=True
                    )
                    .upper()
                )


                if (

                    t_text

                    and len(t_text) > 2

                    and not re.search(

                        r"\d{1,2}:\d{2}",

                        t_text
                    )

                    and "PENDIENTE"
                    not in t_text
                ):

                    if t_text not in [

                        "WINBIG",

                        "RESULTADOS"
                    ]:

                        nombre_loteria = (
                            t_text
                        )

                        break


            # -----------------------------------------------
            # MÉTODO ALTERNATIVO
            # -----------------------------------------------

            if not nombre_loteria:

                lineas = [

                    l.strip().upper()

                    for l in tarjeta.get_text(

                        "\n",

                        strip=True
                    ).split("\n")

                    if l.strip()
                ]


                for linea in lineas:

                    if (

                        len(linea) > 2

                        and not re.search(

                            r"\d{1,2}:\d{2}",

                            linea
                        )

                        and "PENDIENTE"
                        not in linea

                        and "-"
                        not in linea
                    ):

                        nombre_loteria = (
                            linea
                        )

                        break


            # -----------------------------------------------
            # VALIDAR NOMBRE
            # -----------------------------------------------

            if (

                not nombre_loteria

                or len(nombre_loteria) > 40
            ):

                continue


            nombre_loteria = (
                limpiar_texto(
                    nombre_loteria
                )
            )


            # -----------------------------------------------
            # BUSCAR SLOTS
            # -----------------------------------------------

            slots_sorteo = (

                tarjeta.find_all(

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
            )


            if not slots_sorteo:

                slots_sorteo = [
                    tarjeta
                ]


            # -----------------------------------------------
            # RECORRER SLOTS
            # -----------------------------------------------

            for slot in slots_sorteo:

                texto_slot = (

                    slot.get_text(

                        " ",

                        strip=True
                    )
                    .upper()
                )


                if "PENDIENTE" in texto_slot:

                    continue


                # -------------------------------------------
                # BUSCAR HORA
                # -------------------------------------------

                match_h = re.search(

                    r"(\d{1,2}:\d{2}\s*"
                    r"(?:AM|PM))",

                    texto_slot
                )


                if not match_h:

                    continue


                hora = (

                    match_h.group(
                        1
                    )
                    .upper()
                )


                # -------------------------------------------
                # BUSCAR RESULTADO
                # -------------------------------------------

                match_res = re.search(

                    r"(\d{1,2}\s*-\s*"
                    r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+"
                    r"(?:\s+"
                    r"[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)",

                    texto_slot
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


                # -------------------------------------------
                # CLAVE ÚNICA
                # -------------------------------------------

                clave = (

                    nombre_loteria,

                    hora,

                    resultado_final
                )


                # -------------------------------------------
                # PRIMERA EJECUCIÓN
                # -------------------------------------------

                if primera_ejecucion:

                    resultados_enviados.add(
                        clave
                    )

                    continue


                # -------------------------------------------
                # EVITAR DUPLICADOS
                # -------------------------------------------

                if clave in resultados_enviados:

                    continue


                # -------------------------------------------
                # REGISTRAR RESULTADO NUEVO
                # -------------------------------------------

                item_dict = {

                    "loteria":
                    nombre_loteria,

                    "hora":
                    hora,

                    "resultado":
                    resultado_final
                }


                if (

                    item_dict

                    not in nuevos_encontrados
                ):

                    nuevos_encontrados.append(

                        item_dict
                    )

                    resultados_enviados.add(

                        clave
                    )


        # ====================================================
        # SINCRONIZACIÓN INICIAL
        # ====================================================

        if primera_ejecucion:

            primera_ejecucion = False

            print(

                "🚀 Sincronización inicial "
                "lista."

            )

            print(

                "📊 Total registros base: "

                f"{len(resultados_enviados)}"
            )

            return


        # ====================================================
        # ENVIAR RESULTADOS NUEVOS
        # ====================================================

        for item_nuevo in nuevos_encontrados:

            mensaje = (

                "🎯 AG HAROLD JOSE 🎯\n\n"

                f"🎰 *"
                f"{item_nuevo['loteria']}"
                f"*\n"

                f"🕒 "
                f"{item_nuevo['hora']}  "

                f"{item_nuevo['resultado']}"
            )


            enviado = enviar_telegram(

                mensaje,

                disable_web_preview=True
            )


            if enviado:

                print(

                    "✅ Resultado enviado: "

                    f"{item_nuevo['loteria']} | "

                    f"{item_nuevo['hor
