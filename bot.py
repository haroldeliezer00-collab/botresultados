import os
import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
from datetime import datetime

TOKEN = '8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk'
CANAL_ID = '@pruebajsj'
URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'

app = Flask('')

@app.route('/')
def home():
    return "¡El bot de resultados AGENCIA HAROLD JOSE está activo!"

# Estado global
resultados_enviados = set()
datos_dia = {}  # Estructura: datos_dia[nombre_loteria][hora] = "03 🐛"
tablas_enviadas = set() # Para llevar control de qué tablas ya se enviaron por hora
primera_ejecucion = True

# Encabezado oficial personalizado
HEADER_AGENCIA = (
    "╔═══════ ⋆★⋆ ═══════╗\n"
    "   *★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★*\n"
    "  ╚═══════ ⋆★⋆ ═══════╝\n"
    " ╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
    "      *_Mas de 6 años brindando_*\n"
    "         *_confianza y seguridad_*\n"
    "    *_en cada rincón de Venezuela_*\n"
    "         *ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰɪᴄɪᴀʟᴇꜱ*\n"
    "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
    "📲JUEGA AQUI👇👇\n"
    "WHATSAPP: 04124489363\n\n"
)

# Mapeo de nombres largos de la web a los códigos cortos de tus tablas
MAPEO_CODIGOS = {
    "LA GRANJITA": "GRAJ",
    "LOTTO ACTIVO": "L.ACT",
    "SELVA PLUS": "SELV",
    "GUACHARO ACTIVO": "G.ARO",
    "LOTO CHAIMA": "CHAIM",
    "MONJE MILLONARIO": "MONJE",
    "LOTTO ANIMALITO": "L.ANIM",
    "LOTTO PANTERA": "L.PANT",
    "LOTTO REAL": "L.REAL",
    "LOTTO RD": "L.RD",
    "CENTENA ANIMALITOS": "C.A",
    "MEGA ANIMAL": "MEGA",
    "RULETON PERU": "R.PER",
    "RULETON COLOMBIA": "R.COL",
    "RULETON VENEZUELA": "R.VEN",
    "CONDOR GANA": "COND",
    "FRUTI GANA": "FRUI",
    "TROPI GANA": "TROP",
    "GRANJA MILLONARIA": "G.MIL",
    "ZOOLOGICO ACTIVO": "ZOOL",
    "LOTTO MAX": "L.MAX",
    "CENTENA PLUS": "C.PLUS",
    "GRANJITA PLUS": "G.PLUS",
    "LA RICACHONA": "RICAC",
    "CAZALOTON": "CAZAL",
    "RULETA ACTIVA": "R.ACT",
    "LOTTO GATO": "L.GATO",
    "GUACHARITO MILLONARIO": "G.ITO",
    "LOTTO INTER": "L.INT",
    "RULETA ROYAL": "ROYAL",
    "LOTTO ROYAL": "ROYAL",
    "GUACA ACTIVA 37": "GUACA",
    "GRANJAZO": "G.AZO",
    "PANTERA PLUS": "P.PLUS",
    "GATAZO": "GATAZO"
}

def limpiar_texto(texto):
    return " ".join(texto.split())

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    time.sleep(1)

def construir_tabla(titulo, horas, lista_loterias):
    """Construye una parrilla en formato de texto monoespaciado para Telegram"""
    tabla = f"📰 *{titulo}* 📰\n"
    tabla += "➖➖➖➖➖➖➖➖➖➖\n```text\n"
    
    # Cabecera de códigos de lotería
    header = " HORA"
    for loteria in lista_loterias:
        codigo = MAPEO_CODIGOS.get(loteria, loteria[:4].upper())
        header += f" {codigo:<5}"
    tabla += header + "\n"
    
    # Filas por hora
    for hora in horas:
        fila = f"⏰{hora}"
        for loteria in lista_loterias:
            res = datos_dia.get(loteria, {}).get(hora, "")
            if res:
                # Extraer números y emojis compactos (ej: "03🐛")
                res_limpio = res.replace(" ", "")
                fila += f" {res_limpio:<5}"
            else:
                # Si no ha salido o se retrasó demasiado
                fila += f" {'🔕🔕':<5}"
        tabla += fila + "\n"
        
    tabla += "```\nMUCHA SUERTE EN SUS JUGADAS"
    return tabla

def verificar_resultados():
    global primera_ejecucion
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))
        
        nuevos_encontrados = []

        for tarjeta in tarjetas:
            elemento_titulo = tarjeta.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto', re.IGNORECASE))
            
            texto_titulo = ""
            if elemento_titulo:
                texto_titulo = elemento_titulo.get_text(" ", strip=True).upper()
            else:
                lineas = [l.strip() for l in tarjeta.get_text("\n", strip=True).split("\n") if l.strip()]
                texto_titulo = lineas[0].upper() if lineas else ""

            if not texto_titulo or len(texto_titulo) > 35 or "PENDIENTE" in texto_titulo:
                continue
            
            nombre_loteria = limpiar_texto(texto_titulo)

            # Registrar en la base de datos del día
            if nombre_loteria not in datos_dia:
                datos_dia[nombre_loteria] = {}

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

                match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)', texto_slot)
                if not match_res:
                    continue
                
                resultado_final = limpiar_texto(match_res.group(1)).upper()

                # Guardar en memoria general del día para las tablas
                datos_dia[nombre_loteria][hora] = resultado_final

                clave = (nombre_loteria, hora, resultado_final)

                if primera_ejecucion:
                    resultados_enviados.add(clave)
                else:
                    if clave not in resultados_enviados:
                        item_dict = {'loteria': nombre_loteria, 'hora': hora, 'resultado': resultado_final}
                        if item_dict not in nuevos_encontrados:
                            nuevos_encontrados.append(item_dict)
                            resultados_enviados.add(clave)

        if primera_ejecucion:
            primera_ejecucion = False
            print(f"🚀 Sincronización inicial lista. Total de registros base: {len(resultados_enviados)}")
            return

        # 1. Enviar resultados individuales conforme van saliendo
        for item_nuevo in nuevos_encontrados:
            mensaje = (
                f"{HEADER_AGENCIA}"
                f"📊 *RESULTADO PROGRAMADO*\n"
                f"🕒 Hora: {item_nuevo['hora']}\n"
                f"🔹 Resultado: 🎰 {item_nuevo['loteria']} 🎰\n\n"
                f"🕒 {item_nuevo['hora']} {item_nuevo['resultado']}"
            )
            enviar_telegram(mensaje)

        # 2. Control de envío automático de tablas de resumen por bloques de horas
        hora_actual_str = datetime.now().strftime("%I:%M %p")
        minuto_actual = datetime.now().minute

        # Si pasa de los 12 minutos de cada hora y aún no se ha enviado la tabla de esa hora, la mandamos
        hora_corte = datetime.now().strftime("%I:12 %p")
        
        # Ejemplo: Enviar tablas automáticamente al completar los primeros minutos pasados de la hora (ej: 01:12 PM)
        bloque_hora_key = datetime.now().strftime("%I:00 %p")
        if minuto >= 12 and bloque_hora_key not in tablas_enviadas:
            # Generar y enviar bloques de tablas solicitadas
            horas_tabla = ["08:00", "09:00", "10:00", "11:00", "12:00", "01:00"]
            
            loterias_grupo_1 = ["LA GRANJITA", "LOTTO ACTIVO", "SELVA PLUS"]
            loterias_grupo_2 = ["GUACHARO ACTIVO", "LOTO CHAIMA", "MONJE MILLONARIO"]
            loterias_grupo_3 = ["LOTTO ANIMALITO", "LOTTO PANTERA", "LOTTO REAL"]
            loterias_grupo_4 = ["LOTTO RD", "CENTENA ANIMALITOS", "MEGA ANIMAL"]
            loterias_grupo_5 = ["RULETON PERU", "RULETON COLOMBIA", "RULETON VENEZUELA"]
            loterias_grupo_6 = ["CONDOR GANA", "FRUTI GANA", "TROPI GANA"]
            loterias_grupo_7 = ["GRANJA MILLONARIA", "ZOOLOGICO ACTIVO", "LOTTO MAX"]

            # Enviar tabla principal por partes o combinadas según gustes
            t1 = construir_tabla("RESULTADOS ANIMALITOS", horas_tabla, loterias_grupo_1 + loterias_grupo_2[:1])
            enviar_telegram(f"{HEADER_AGENCIA}\n{t1}")
            
            tablas_enviadas.add(bloque_hora_key)

    except Exception as e:
        print(f"⚠️ Error general: {e}")

def loop_bot():
    verificar_resultados()
    schedule.every(2).minutes.do(verificar_resultados)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    t = Thread(target=loop_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
