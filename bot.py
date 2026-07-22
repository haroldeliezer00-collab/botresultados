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

# Estructura global para acumular los resultados de todo el día: { hora: { loteria: resultado } }
acumulado_dia = {}
todas_las_loterias = set()
todas_las_horas = set()

def limpiar_texto(texto):
    return " ".join(texto.split())

def verificar_resultados():
    global primera_ejecucion, acumulado_dia, todas_las_loterias, todas_las_horas
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
            nombre_loteria = ""
            
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text and "-" not in t_text:
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

                # Guardar en el acumulado global del día
                if hora not in acumulado_dia:
                    acumulado_dia[hora] = {}
                acumulado_dia[hora][nombre_loteria] = resultado_final
                todas_las_loterias.add(nombre_loteria)
                todas_las_horas.add(hora)

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

        if nuevos_encontrados:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            # 1. Enviar primero los resultados individuales uno a uno
            for item_nuevo in nuevos_encontrados:
                mensaje_individual = (
                    "🎯 AG HAROLD JOSE 🎯\n\n"
                    f"🎰 *{item_nuevo['loteria']}*\n"
                    f"🕒 {item_nuevo['hora']}  {item_nuevo['resultado']}"
                )
                payload_ind = {"chat_id": CANAL_ID, "text": mensaje_individual, "parse_mode": "Markdown"}
                requests.post(url, json=payload_ind)
                time.sleep(1)

            # 2. Generar el Boletín Consolidado con el Encabezado Oficial y Tablas por bloques
            lista_loterias = sorted(list(todas_las_loterias))
            lista_horas = sorted(list(todas_horas))

            # Dividir las loterías en bloques de 3 columnas para que encajen perfecto
            bloques_loterias = [lista_loterias[i:i + 3] for i in range(0, len(lista_loterias), 3)]

            cuerpo_total_tablas = ""
            for bloque in bloques_loterias:
                # Nombres cortados para la cabecera de la tabla
                cabeza_lotes = " ".join([l[:6].ljust(7) for l in bloque])
                cuerpo_total_tablas += f" HORA🎰{cabeza_lotes}\n"
                cuerpo_total_tablas += "---------------------------------\n"

                for h in lista_horas:
                    fila_str = f"⏰{h} "
                    for lot in bloque:
                        res = acumulado_dia.get(h, {}).get(lot, "....🚫")
                        # Extraer solo el número o abreviar para la tabla compacta
                        match_num = re.search(r'^(\d{1,2})', res)
                        num_corto = match_num.group(1).ljust(7) if match_num else "....   "
                        fila_str += f"{num_corto} "
                    cuerpo_total_tablas += f"{fila_str}\n"
                cuerpo_total_tablas += "\n"

            encabezado_oficial = (
                "╔═══════ ⋆★⋆ ═══════╗\n"
                "   *★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★*\n"
                "╚═══════ ⋆★⋆ ═══════╝\n"
                "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲\U0001f31fON𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
                "      *_Mas de 6 años brindando_*\n"
                "         *_confianza y seguridad_*\n"
                "      *_en cada rincón de Venezuela_*\n"
                "       *ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰ𝙸𝙲𝙸𝙰𝙻𝙴ꜱ*\n"
                "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
                "📲JUEGA AQUI👇👇\n"
                "WHATSAPP: 04124489363"
            )

            mensaje_boletin = (
                f"{encabezado_oficial}\n\n"
                "📰RESULTADOS ANIMALITOS📰\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"```text\n{cuerpo_total_tablas}```\n"
                "MUCHA SUERTE EN SUS JUGADAS"
            )

            payload_boletin = {"chat_id": CANAL_ID, "text": mensaje_boletin, "parse_mode": "Markdown"}
            requests.post(url, json=payload_boletin)

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
            
