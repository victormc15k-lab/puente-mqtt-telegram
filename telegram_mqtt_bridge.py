import time
import requests
import paho.mqtt.client as mqtt

BOT_TOKEN = "8716886232:AAECk-KO3lUeUBNE7WuQldJgC04f316y6aE"
CHAT_ID = "2037539973"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

TOPIC_COMIDA_CMD    = "victo2026/comida/cmd"
TOPIC_COMIDA_STATUS = "victo2026/comida/status"
TOPIC_COMIDA_EVENT  = "victo2026/comida/evento"
TOPIC_COMIDA_LEVEL  = "victo2026/comida/nivel"

TOPIC_AGUA_CMD    = "victo2026/agua/cmd"
TOPIC_AGUA_STATUS = "victo2026/agua/status"
TOPIC_AGUA_EVENT  = "victo2026/agua/evento"
TOPIC_AGUA_LEVEL  = "victo2026/agua/nivel"

TOPIC_TEMP_CMD    = "victo2026/temperatura/cmd"
TOPIC_TEMP_STATUS = "victo2026/temperatura/status"
TOPIC_TEMP_EVENT  = "victo2026/temperatura/evento"
TOPIC_TEMP_VALOR  = "victo2026/temperatura/valor"

ultimo_update_id = None
esperando_info_comida = False

MENU = (
    "🐾 ¿Qué deseas hacer?\n\n"
    "🍖 COMIDA:\n"
    "/dispensar /extra /nivel\n\n"
    "💧 AGUA:\n"
    "/dispensar_agua /nivel_agua\n\n"
    "🌡 TEMPERATURA:\n"
    "/temp\n\n"
    "⚙️ GENERAL:\n"
    "/status /auto /manual"
)

def enviar_telegram(texto):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": texto}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Error enviando mensaje a Telegram:", e)

def enviar_con_menu(texto):
    enviar_telegram(texto)
    enviar_telegram(MENU)

def obtener_updates():
    global ultimo_update_id
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 10}
    if ultimo_update_id is not None:
        params["offset"] = ultimo_update_id + 1
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        return data.get("result", [])
    except Exception as e:
        print("Error obteniendo updates:", e)
        return []

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Conectado a MQTT con codigo:", reason_code)
    client.subscribe(TOPIC_COMIDA_STATUS)
    client.subscribe(TOPIC_COMIDA_EVENT)
    client.subscribe(TOPIC_COMIDA_LEVEL)
    client.subscribe(TOPIC_AGUA_STATUS)
    client.subscribe(TOPIC_AGUA_EVENT)
    client.subscribe(TOPIC_AGUA_LEVEL)
    client.subscribe(TOPIC_TEMP_STATUS)
    client.subscribe(TOPIC_TEMP_EVENT)
    client.subscribe(TOPIC_TEMP_VALOR)

def on_message(client, userdata, msg):
    global esperando_info_comida

    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT] {topic}: {payload}")

    if topic == TOPIC_COMIDA_STATUS:
        if esperando_info_comida and payload != "ONLINE":
            enviar_telegram(f"🍖 [COMIDA - STATUS] {payload}")
            esperando_info_comida = False

    elif topic == TOPIC_COMIDA_EVENT:
        if payload.startswith("Nivel tanque:"):
            pass
        elif payload.startswith("ALERTA: Nivel de comida"):
            pass
        else:
            enviar_telegram(f"🍖 [COMIDA - EVENTO] {payload}")

    elif topic == TOPIC_COMIDA_LEVEL:
        pass

    elif topic == TOPIC_AGUA_STATUS:
        if payload != "ONLINE":
            enviar_telegram(f"💧 [AGUA - STATUS] {payload}")

    elif topic == TOPIC_AGUA_EVENT:
        enviar_telegram(f"💧 [AGUA - EVENTO] {payload}")

    elif topic == TOPIC_AGUA_LEVEL:
        enviar_telegram(f"💧 [AGUA - NIVEL] {payload}")

    elif topic == TOPIC_TEMP_STATUS:
        if payload != "ONLINE":
            enviar_telegram(f"🌡 [TEMPERATURA - STATUS] {payload}")

    elif topic == TOPIC_TEMP_EVENT:
        enviar_telegram(f"🌡 [TEMPERATURA - EVENTO] {payload}")

    elif topic == TOPIC_TEMP_VALOR:
        enviar_telegram(f"🌡 [TEMPERATURA] {payload} °C")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bridge_telegram_mascotas")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def procesar_mensaje(texto):
    global esperando_info_comida

    texto = texto.strip().lower()

    if texto == "/start":
        enviar_telegram(MENU)

    elif texto == "/dispensar":
        mqtt_client.publish(TOPIC_COMIDA_CMD, "DISPENSAR_NORMAL")
        enviar_con_menu("🍖 Dispensando porción normal...")

    elif texto == "/extra":
        mqtt_client.publish(TOPIC_COMIDA_CMD, "DISPENSAR_EXTRA")
        enviar_con_menu("🍖 Dispensando porción extra...")

    elif texto == "/nivel":
        esperando_info_comida = True
        mqtt_client.publish(TOPIC_COMIDA_CMD, "STATUS")
        enviar_telegram("🍖 Consultando nivel de comida...")

    elif texto == "/dispensar_agua":
        mqtt_client.publish(TOPIC_AGUA_CMD, "DISPENSAR")
        enviar_con_menu("💧 Dispensando agua...")

    elif texto == "/nivel_agua":
        mqtt_client.publish(TOPIC_AGUA_CMD, "STATUS")
        enviar_con_menu("💧 Consultando nivel de agua...")

    elif texto == "/temp":
        mqtt_client.publish(TOPIC_TEMP_CMD, "LEER")
        enviar_con_menu("🌡 Leyendo temperatura...")

    elif texto == "/status":
        esperando_info_comida = True
        mqtt_client.publish(TOPIC_COMIDA_CMD, "STATUS")
        mqtt_client.publish(TOPIC_AGUA_CMD, "STATUS")
        mqtt_client.publish(TOPIC_TEMP_CMD, "STATUS")
        enviar_con_menu("⚙️ Consultando estado de todos los nodos...")

    elif texto == "/auto":
        mqtt_client.publish(TOPIC_COMIDA_CMD, "MODO_AUTO")
        mqtt_client.publish(TOPIC_AGUA_CMD, "MODO_AUTO")
        enviar_con_menu("⚙️ Modo automático activado")

    elif texto == "/manual":
        mqtt_client.publish(TOPIC_COMIDA_CMD, "MODO_MANUAL")
        mqtt_client.publish(TOPIC_AGUA_CMD, "MODO_MANUAL")
        enviar_con_menu("⚙️ Modo manual activado")

    else:
        enviar_telegram("Comando no reconocido.")
        enviar_telegram(MENU)

def main():
    global ultimo_update_id

    print("Conectando a MQTT...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    enviar_telegram("🐾 Sistema de mascotas iniciado")
    enviar_telegram(MENU)

    while True:
        updates = obtener_updates()
        for upd in updates:
            ultimo_update_id = upd["update_id"]
            if "message" in upd and "text" in upd["message"]:
                chat_id = str(upd["message"]["chat"]["id"])
                texto = upd["message"]["text"]
                if chat_id == CHAT_ID:
                    print("Telegram:", texto)
                    procesar_mensaje(texto)
        time.sleep(2)

if __name__ == "__main__":
    main()