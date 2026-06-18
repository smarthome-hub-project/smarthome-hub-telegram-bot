"""Test de carga del .env"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("TEST DE CARGA DEL .ENV")
print("=" * 60)

print(f"\n📁 Carpeta actual: {os.getcwd()}")
print(f"📄 ¿Existe .env? {os.path.exists('.env')}")

if os.path.exists('.env'):
    print(f"📊 Tamaño .env: {os.path.getsize('.env')} bytes")
    
    print("\n📖 Contenido raw del archivo:")
    with open('.env', 'rb') as f:
        content = f.read()
        print(f"   Primeros 50 bytes: {content[:50]}")
        
        bom_utf8 = b'\xef\xbb\xbf'
        bom_utf16_le = b'\xff\xfe'
        bom_utf16_be = b'\xfe\xff'
        
        has_utf8_bom = content[:3] == bom_utf8
        has_utf16_bom = content[:2] in [bom_utf16_le, bom_utf16_be]
        
        print(f"   ¿Tiene BOM UTF-8? {has_utf8_bom}")
        print(f"   ¿Tiene BOM UTF-16? {has_utf16_bom}")

print("\n🔍 Variables ANTES de load_dotenv():")
print(f"   AUTHORIZED_USERS = {os.getenv('AUTHORIZED_USERS')}")
print(f"   AUTH_PASSWORD    = {os.getenv('AUTH_PASSWORD')}")

# Cargar .env
load_dotenv()

print("\n🔍 Variables DESPUÉS de load_dotenv():")
token = os.getenv('TELEGRAM_BOT_TOKEN', 'NO ENCONTRADO')
print(f"   TELEGRAM_BOT_TOKEN = {token[:20]}...")
print(f"   MQTT_BROKER      = {os.getenv('MQTT_BROKER')}")
print(f"   AUTHORIZED_USERS = {os.getenv('AUTHORIZED_USERS')}")
print(f"   AUTH_PASSWORD    = {os.getenv('AUTH_PASSWORD')}")

print("\n📋 Análisis de AUTHORIZED_USERS:")
users_str = os.getenv("AUTHORIZED_USERS", "")
print(f"   Valor raw: '{users_str}'")
print(f"   Tipo: {type(users_str)}")
print(f"   Longitud: {len(users_str)}")
print(f"   ¿Está vacío? {not users_str}")

if users_str:
    print(f"   Intentando parsear...")
    try:
        users = set(int(uid.strip()) for uid in users_str.split(",") if uid.strip())
        print(f"   ✅ Usuarios parseados: {users}")
    except ValueError as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)