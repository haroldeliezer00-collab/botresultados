import os
import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3

# Desactivar advertencias de certificados SSL por seguridad con páginas del Estado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = '8738717666:AAGminLobxUmKtbHvTaqnjLxClxbDN6E3tk'
CANAL_ID = '@pruebajsj'
URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

app = Flask('')

@app.route('/')
def home():
    return "¡El bot de resultados AG HAROLD JOSE está activo!"

resultados_enviados = set()
primera_ejecucion = True

# Diccionario de emojis para los animalitos (incluyendo nombres compuestos)
ANIMAL_EMOJIS = {
    'CARNERO': '🐏',
    'TORO': '🐂',
    'CIEMPIES': '🐛',
    'ALACRAN': '🦂',
    'LEON': '🦁',
    'RANA': '🐸',
    'PERICO': '🦜',
    'CHIVO': '🐐',
    'COCHINO': '🐖',
    'GALLO': '🐓',
    'CARACOL': '🐌',
    'CULEBRA': '🐍',
    'ZAMURO': '🐦‍⬛',
    'GATO': '🐈',
    'BALLENA': '🐋',
    'CAIMAN': '🐊',
    'AGUILA': '🦅',
    'TIGRE': '🐅',
    'PAVITO': '🦃',
    'PAVO REAL': '🦚',
    'BURRO': '🫏',
    'MONO': '🐒',
    'IGUANA': '🦎',
    'BUFALO': '🐃',
    'GALLINA': '🐔',
    'VACA': '🐄',
    'PERRO': '🐕',
    'ZORRO': '🦊',
    'OSO': '🐻',
    'PESCADO': '🐟',
    'ZEBRA': '🦓',
    'CIERVO': '🦌',
    'CAMELOS': '🐫'
}

def limpiar_texto(texto):
    return " ".join(texto.split())

def obtener_emoji(resultado_texto):
    partes = resultado_texto.split('-')
    if len(partes) > 1:
        nombre_animal = partes[1].strip().upper()
        return ANIMAL_EMOJIS.get(nombre_animal, '')
    return ''

def enviar_saludo_matutino():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje = (
            "🎯 *AGENCIA HAROLD JOSE* 🎯\n\n"
            "🌅 *¡Buenos días a todos!* 🌅\n\n"
            "Ya arrancamos un nuevo día con la mejor energía. "
            "Por aquí estaremos compartiendo todos los resultados de los animalitos a medida que vayan saliendo.\n\n"
            "📢 *Nuestros canales oficiales:*\n"
            "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n"
            "📸 Instagram: https://www.instagram.com/agharold.jose (@agharold.jose)\n"
            "💬 Canal de WhatsApp: https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
            "¡Mucha suerte en sus jugadas el día de hoy y a ganar! 🍀🔥"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("☀️ Saludo matutino enviado con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar el saludo matutino: {e}")

def enviar_tasa_dolar():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(URL_BCV, headers=headers, timeout=15, verify=False)
        
        precio_dolar = "No disponible"
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            dolar_div = soup.find('div', id='dolar')
            if dolar_div:
                strong_elem = dolar_div.find('strong')
                if strong_elem:
                    precio_dolar = strong_elem.get_text(strip=True)

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje = (
            "💵 *TASA OFICIAL BCV* 💵\n\n"
            f"🏦 *Moneda:* Dólar Estadounidense\n"
            f"📈 *Precio Oficial:* Bs. *{precio_dolar}*\n\n"
            "🔗 Fuente: [Banco Central de Venezuela](https://www.bcv.org.ve/)"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("💵 Tasa del dólar oficial enviada con éxito.")
    except Exception as e:
        print(f"⚠️ Error al obtener o enviar la tasa del dólar: {e}")

def enviar_aviso_taquilla():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        mensaje_promo = (
            "🎯 *AGENCIA HAROLD JOSE* 🎯\n"
            "Tu centro de apuestas de confianza. Atendemos vía WhatsApp y Telegram.\n\n"
            "📢 *¡AVISO IMPORTANTE PARA NUESTROS JUGADORES!* 📢\n\n"
            "Recuerda que para jugar con nosotros debes acceder primero a nuestro *Canal de WhatsApp* para verificar si la taquilla se encuentra activa el día de hoy:\n"
            "👉 https://whatsapp.com/channel/0029Vaza7YIGzzKJq7as7s1T\n\n"
            "📲 *Si la taquilla está activa*, puedes revisar nuestro catálogo y escribirnos directamente:\n"
            "🎟️ Catálogo y WhatsApp: https://wa.me/c/584124489363\n\n"
            "💬 También estamos disponibles por Telegram:\n"
            "👉 t.me/ag_haroldjose\n\n"
            "¡Mucha suerte en sus jugadas! 🍀🔥"
        )
        payload = {"chat_id": CANAL_ID, "text": mensaje_promo, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, json=payload)
        print("📢 Aviso de taquilla enviado con éxito.")
    except Exception as e:
        print(f"⚠️ Error al enviar el aviso de taquilla: {e}")

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
            nombre_loteria = ""
            
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
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

                # Actualizado para aceptar nombres compuestos de dos palabras (ej. PAVO REAL)
                match_res = re.search(r'(\d{1,2}\s*-\s*[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
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
            emoji = obtener_emoji(item_nuevo['resultado'])
            emoji_str = f" {emoji}" if emoji else ""
            
            mensaje = (
                "🎯 AG HAROLD JOSE 🎯\n\n"
                f"🎰 *{item_nuevo['loteria']}*\n"
                f"🕒 {item_nuevo['hora']}  {item_nuevo['resultado']}{emoji_str}"
            )
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CANAL_ID, "text": mensaje, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
            time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error general: {e}")

def loop_bot():
    verificar_resultados()
    
    schedule.every().day.at("11:00").do(enviar_saludo_matutino)
    schedule.every().day.at("13:30").do(enviar_aviso_taquilla)
    schedule.every().day.at("17:00").do(enviar_tasa_dolar)
    schedule.every().day.at("17:30").do(enviar_aviso_taquilla)
    schedule.every().day.at("21:30").do(enviar_aviso_taquilla)
    
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
