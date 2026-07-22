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
        
        # Buscar contenedores principales de las loterías
        tarjetas = soup.find_all(['div', 'section'], class_=re.compile(r'flex|card|grid', re.IGNORECASE))
        
        nuevos_encontrados = []

        for tarjeta in tarjetas:
            texto_tarjeta = tarjeta.get_text(" ", strip=True).upper()
            
            # Identificar el nombre oficial de la lotería
            nombre_loteria = ""
            for oficial in LISTA_LOTERIAS_OFICIALES:
                if oficial in texto_tarjeta:
                    nombre_loteria = oficial
                    break
            
            if not nombre_loteria:
                continue

            # Buscar slots o cajitas individuales de cada sorteo dentro de la tarjeta
            slots_sorteo = tarjeta.find_all(['div', 'li', 'span'], class_=re.compile(r'item|slot|draw|box|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                
                # Ignorar completamente si el slot sigue pendiente
                if "PENDIENTE" in texto_slot:
                    continue
                
                # Buscar el patrón de la hora exacta en este slot
                match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_slot)
                if not match_h:
                    continue
                hora = match_h.group(1).upper()

                # Buscar el resultado numérico y animalito correspondiente
                match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)', texto_slot)
                if not match_res:
                    continue
                
                resultado_final = limpiar_texto(match_res.group(1)).upper()

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
                f"🎰 {item_nuevo['loteria']}\n"
                f"🕒 {item_nuevo['hora']} {item_nuevo['resultado']}"
            )
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CANAL_ID, "text": mensaje}
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
        
