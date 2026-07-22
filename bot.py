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
    return "¡El bot de AG HAROLD JOSE está activo y cazando resultados!"

resultados_enviados = set()
primera_ejecucion = True

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
        
        # Buscar cualquier texto o bloque que contenga formato de hora y resultado
        # Esto extrae directamente cualquier elemento visible en la página
        textos_pagina = soup.stripped_strings
        texto_completo = " ".join(list(textos_pagina))

        # Buscamos patrones de sorteos en la página de manera global por si el diseño cambia
        # Patrón flexible para capturar el nombre, la hora y el resultado numérico/animalito
        
        # Vamos a escanear todos los bloques contenedores posibles
        bloques = soup.find_all(['div', 'section', 'article', 'li'])
        
        nuevos_encontrados = []

        for bloque in bloques:
            contenido = bloque.get_text(" ", strip=True)
            
            # Buscar si el bloque tiene una hora (ej: 10:00 AM, 02:30 PM) y un resultado con guion
            match_hora = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', contenido, re.IGNORECASE)
            match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑ\s]+)', contenido, re.IGNORECASE)
            
            if match_hora and match_res:
                hora = match_hora.group(1).upper()
                resultado_bruto = match_res.group(1).upper()
                
                if "PENDIENTE" in contenido.upper():
                    continue

                # Intentar deducir el nombre de la lotería del bloque o de sus padres cercanos
                nombre_loteria = "LOTTO ACTIVO" # Valor por defecto seguro
                for parent in bloque.parents:
                    p_text = parent.get_text(" ", strip=True).upper()
                    if "GRANJITA" in p_text and len(p_text) < 50:
                        nombre_loteria = "LA GRANJITA"
                        break
                    elif "ACTIVO" in p_text and len(p_text) < 50:
                        nombre_loteria = "LOTTO ACTIVO"
                        break
                    elif "SELVA" in p_text and len(p_text) < 50:
                        nombre_loteria = "SELVA PLUS"
                        break
                    elif "GUACHARO" in p_text and len(p_text) < 50:
                        nombre_loteria = "GUACHARO ACTIVO"
                        break
                    elif "GUACHARITO" in p_text and len(p_text) < 50:
                        nombre_loteria = "GUACHARITO MILLONARIO"
                        break

                clave = (nombre_loteria, hora, resultado_bruto)

                if primera_ejecucion:
                    resultados_enviados.add(clave)
                else:
                    if clave not in resultados_enviados:
                        nuevos_encontrados.append({
                            'loteria': nombre_loteria,
                            'hora': hora,
                            'resultado': resultado_bruto,
                            'clave': clave
                        })

        if primera_ejecucion:
            primera_ejecucion = False
            print(f"🚀 Sincronización inicial lista. Total de resultados en memoria: {len(resultados_enviados)}")
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
            
            resultados_enviados.add(item_nuevo['clave'])
            time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error en verificación: {e}")

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
                
