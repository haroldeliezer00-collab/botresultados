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
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers)
        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas_loteria = soup.find_all('div', class_=re.compile(r'flex flex-col.*'))
        
        nuevos_encontrados = []

        for tarjeta in tarjetas_loteria:
            try:
                nombre_loteria = ""
                posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'span'])
                
                for tag in posibles_titulos:
                    txt = limpiar_texto(tag.text).upper()
                    # Buscar coincidencia exacta o parcial con la lista oficial
                    for oficial in LISTA_LOTERIAS_OFICIALES:
                        if oficial in txt and len(txt) < 40 and "AM" not in txt and "PM" not in txt:
                            nombre_loteria = oficial
                            break
                    if nombre_loteria:
                        break

                if not nombre_loteria:
                    continue

                items_sorteo = tarjeta.find_all('div', class_='flex flex-col items-center gap-2 group relative')
                
                for item in items_sorteo:
                    try:
                        hora_elem = item.find('div', class_='text-center')
                        if not hora_elem:
                            continue
                        hora_texto = limpiar_texto(hora_elem.text)
                        match_hora = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)', hora_texto, re.IGNORECASE)
                        if not match_hora:
                            continue
                        hora = match_hora.group(0).upper()

                        res_elem = item.find('div', class_='bg-yellow-500')
                        if not res_elem:
                            continue
                        resultado_bruto = limpiar_texto(res_elem.text)
                        
                        if not resultado_bruto or resultado_bruto.upper() == "PENDIENTE":
                            continue

                        animal_texto = ""
                        for t in item.find_all(string=True):
                            t_str = limpiar_texto(t)
                            if "-" in t_str and any(char.isdigit() for char in t_str):
                                animal_texto = t_str
                                break
                        
                        if not animal_texto:
                            animal_texto = resultado_bruto

                        if "-" in animal_texto:
                            partes = [p.strip() for p in animal_texto.split("-") if p.strip()]
                            if len(partes) >= 2:
                                num = partes[0]
                                nombre = partes[1].split(":")[0].strip()
                                resultado_final = f"{num} - {nombre}"
                            else:
                                resultado_final = animal_texto
                        else:
                            resultado_final = f"{resultado_bruto} - {animal_texto}"

                        clave = (nombre_loteria, hora, resultado_final)

                        if primera_ejecucion:
                            resultados_enviados.add(clave)
                        else:
                            if clave not in resultados_enviados:
                                nuevos_encontrados.append({
                                    'loteria': nombre_loteria,
                                    'hora': hora,
                                    'resultado': resultado_final,
                                    'clave': clave
                                })
                    except Exception:
                        continue

            except Exception:
                continue

        if primera_ejecucion:
            primera_ejecucion = False
            print("🚀 Sincronización inicial completada. Esperando nuevos resultados...")
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
        print(f"⚠️ Error general: {e}")

def loop_bot():
    verificar_resultados()
    # Revisar cada 2 minutos para capturar el resultado apenas salga sin retrasos
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
    
