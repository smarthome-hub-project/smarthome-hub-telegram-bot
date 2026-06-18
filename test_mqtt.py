"""Test de conexión MQTT directa"""
import paho.mqtt.client as mqtt
import time

connected_flag = False

def on_connect(client, userdata, flags, reason_code, properties):
    global connected_flag
    if reason_code == 0:
        connected_flag = True
        print("✅ CONECTADO al broker MQTT")
        client.subscribe("smarthome/davidhero/#", qos=1)
        print("📡 Suscrito a: smarthome/davidhero/#")
        print("⏳ Esperando mensajes desde Telegram...")
        print("    Envía /night, /day, /party al bot")
    else:
        print(f"❌ Error de conexión: code={reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    global connected_flag
    connected_flag = False
    print(f"⚠️ Desconectado: code={reason_code}")

def on_message(client, userdata, msg):
    print(f"📥 [{msg.topic}]: {msg.payload.decode()}")

print("=" * 60)
print("TEST MQTT - Smart Home Hub")
print("=" * 60)
print("\n🔌 Conectando a broker.hivemq.com:1883...")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

try:
    client.connect("broker.hivemq.com", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n👋 Saliendo...")
    client.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Tipo: {type(e).__name__}")