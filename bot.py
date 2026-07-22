import os
import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re

TOKEN = '8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk'
CANAL_ID = '@pruebajsj'
URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'

app = Flask('')

@app.route('/')
def home():
    return "¡El bot de resultados AG HAROLD JOSE está activo!"

resultados_enviados = set()
primera_ejecucion = True

LISTA_LOTERIAS_OFICIALES = [
    "LOTTO ACTIVO", "LA GRANJITA", "SELVA PLUS", "GUACHARO ACTIVO", 
    "LOTO CHAIMA", "RULETON PERU", "RULETON COLOMBIA", "RULETON VENEZUELA", 
    "LOTTO ANIMALITO", "LOTTO PANTERA", "MONJE MILLONARIO", "LOTTO REAL", 
    "LOTTO INTER", "CAZALOTON", "MEGA ANIMAL", "CENTENA ANIMALITOS", 
    "CENTENA PLUS", "GUACHARITO MILLONARIO", "RULETA ACTIVA", "GRANJITA PLUS", 
    "LA RICACHONA", "GUACA ACTIVA 37", "LOTTO MAX", "TROPI GANA", 
    "CONDOR GANA", "GRANJA MILLONARIA", "FRUTI GANA", "GRANJAZO", 
    "LOTTO GATO", "GATAZO", "ZOOLOGICO ACTIVO", "LOTTO RD"
]

def limpiar_texto(texto):
    return " ".join(texto.split())

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
        
        # Buscar contenedores de tarjetas individuales
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))
        
        nuevos_encontrados = []

        for tarjeta in tarjetas:
            # Extraer estrictamente el título de la tarjeta para evitar cruces de nombres
            elemento_titulo = tarjeta.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto', re.IGNORECASE))
            
            texto_titulo = ""
            if elemento_titulo:
                texto_titulo = elemento_titulo.get_text(" ", strip=True).upper()
            else:
                texto_titulo = tarjeta.get_text(" ", strip=True).upper()

            # Identificar el nombre oficial exacto que corresponde a esta tarjeta
            nombre_loteria = ""
            for oficial in LISTA_LOTERIAS_OFICIALES:
                if oficial in texto_titulo:
                    nombre_loteria = oficial
                    break
            
            # Si la tarjeta no coincide exactamente con una lotería oficial, se ignora
            if not nombre_loteria:
                continue

            # Buscar los slots/sorteos individuales dentro de ESTA tarjeta específica
            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                
                # Ignorar si el sorteo sigue pendiente
                if "PENDIENTE" in texto_slot:
                    continue
                
                # Buscar la hora exacta
                match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_slot)
                if not match_h:
                    continue
                hora = match_h.group(1).upper()

                # Buscar el resultado (número - animalito)
                match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)', texto_slot)
                if not match_res:
                    continue
                
                resultado_final = limpiar_texto(match_res.group(1)).upper()

                # Clave única por lotería, hora y resultado
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

        for item_nuevo in nuevos_encontrados:
            mensaje = (
                "🎯 AG HAROLD JOSE 🎯\n\n"
                f"🎰 *{item_nuevo['loteria']}*\n"
                f"🕒 {item_nuevo['hora']}  {item_nuevo['resultado']}"
            )
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
            time.sleep(1)

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
                                            
