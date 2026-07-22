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
        
        # Buscar contenedores principales de los sorteos
        tarjetas = soup.find_all(['div', 'section'], class_=re.compile(r'flex|card|grid', re.IGNORECASE))
        
        nuevos_encontrados = []

        for tarjeta in tarjetas:
            texto_tarjeta = tarjeta.get_text(" ", strip=True).upper()
            
            # Identificar el nombre exacto de la lotería según tu lista oficial
            nombre_loteria = ""
            for oficial in LISTA_LOTERIAS_OFICIALES:
                if oficial in texto_tarjeta:
                    nombre_loteria = oficial
                    break
            
            if not nombre_loteria:
                continue

            # Buscar todas las horas dentro de esta tarjeta específica
            elementos_hora = tarjeta.find_all(string=re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE))
            
            for elem_h in elementos_hora:
                try:
                    hora_texto = limpiar_texto(elem_h).upper()
                    match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', hora_texto)
                    if not match_h:
                        continue
                    hora = match_h.group(1).upper()

                    # Buscar el resultado numérico/animalito asociado en los elementos cercanos
                    padre_item = elem_h.parent
                    resultado_final = ""
                    
                    for _ in range(4):
                        if not padre_item:
                            break
                        txt_padre = padre_item.get_text(" ", strip=True)
                        match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+)', txt_padre)
                        if match_res and hora in txt_padre.upper():
                            resultado_final = limpiar_texto(match_res.group(1)).upper()
                            break
                        padre_item = padre_item.parent

                    if not resultado_final or "PENDIENTE" in resultado_final.upper():
                        continue

                    clave = (nombre_loteria, hora, resultado_final)

                    if primera_ejecucion:
                        resultados_enviados.add(clave)
                    else:
                        if clave not in resultados_enviados:
                            item_dict = {'loteria': nombre_loteria, 'hora': hora, 'resultado': resultado_final}
                            if item_dict not in nuevos_encontrados:
                                nuevos_encontrados.append(item_dict)
                                resultados_enviados.add(clave)
                except Exception:
                    continue

        if primera_ejecucion:
            primera_ejecucion = False
            print(f"🚀 Sincronización inicial lista. Total de registros base: {len(resultados_enviados)}")
            return

        for item_nuevo in nuevos_encontrados:
            mensaje = (
                "🎯 AG HAROLD JOSE 🎯\n\n"
                f"🎰 {item_nuevo['loteria']}\n"
                f"🕒 {item_novo['hora']} {item_nuevo['resultado']}"
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
                
