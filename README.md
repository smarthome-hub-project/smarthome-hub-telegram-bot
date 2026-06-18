# 🤖 Smart Home Hub - Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)](https://core.telegram.org/bots/api)
[![MQTT](https://img.shields.io/badge/MQTT-3.1.1-660066)](https://mqtt.org/)
[![Railway](https://img.shields.io/badge/Hosted-Railway-0B0D0E?logo=railway)](https://railway.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Bot conversacional de **Telegram** para controlar el sistema **Smart Home Hub IoT** desde cualquier lugar del mundo. Soporta comandos slash, botones interactivos, lenguaje natural y notas de voz transcritas.

---

## 📋 Tabla de contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Interfaces de usuario](#-interfaces-de-usuario)
- [Instalación local](#-instalación-local)
- [Configuración](#-configuración)
- [Despliegue en Railway](#-despliegue-en-railway)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Módulos](#-módulos)
- [Comandos disponibles](#-comandos-disponibles)
- [Seguridad](#-seguridad)
- [Troubleshooting](#-troubleshooting)
- [Licencia](#-licencia)

---

## ✨ Características

- 🤖 **Bot 24/7** desplegado en Railway.app
- 🎛 **Múltiples interfaces de usuario**:
  - Comandos slash (`/night`, `/day`, etc.)
  - ReplyKeyboard (menú persistente con botones)
  - InlineKeyboard (botones contextuales)
  - Lenguaje natural ("prende la luz", "modo fiesta")
  - Notas de voz transcritas con Whisper (modo local)
- 🔐 **Autenticación** por `user_id` con auto-autorización vía password
- 📡 **Comunicación MQTT bidireccional** con el sistema embebido
- 🌐 **Multilenguaje**: español e inglés
- 🔔 **Notificaciones push** automáticas (ACK, cambios de temperatura)
- 🎤 **Feature flag** para deshabilitar voz en entornos con recursos limitados

---

## 🏗 Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  📱 Usuario en Telegram                                     │
│  Slash commands | Botones | Texto libre | Voz               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  ☁️ Bot Python (Railway.app 24/7)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   auth.py    │  │    nlp.py    │  │  voice.py    │     │
│  │ (lista blanca)│  │ (lenguaje    │  │  (Whisper)   │     │
│  │              │  │  natural)    │  │  *opcional*  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ keyboards.py │  │mqtt_client.py│                        │
│  │  (botones)   │  │   (paho-mqtt)│                        │
│  └──────────────┘  └──────┬───────┘                        │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  📡 HiveMQ Public Broker (MQTT)                            │
│  Topics: smarthome/davidhero/{cmd,ack,temp}                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  📶 ESP32-C6 + 🔌 STM32 L476RG                              │
│  Ejecutan los comandos y reportan estado                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎛 Interfaces de usuario

El bot soporta **cinco modos de interacción** para máxima accesibilidad:

### 1. Comandos slash tradicionales
```
/night   /day      /relax    /alarm
/party   /standby  /temp     /status
```

### 2. ReplyKeyboard (menú persistente)
Aparece automáticamente con `/start`:
```
[🌙 Night]  [☀️ Day]
[😌 Relax]  [🚨 Alarm]
[🎉 Party]  [⏹ Standby]
[🌡 Temp ]  [ℹ️ Estado]
        [❓ Ayuda]
```

### 3. InlineKeyboard (botones contextuales)
Activado con `/menu`:
```
┌────────────────────────┐
│ [🌙 Night]  [☀️ Day]   │
│ [😌 Relax]  [🚨 Alarm] │
│ [🎉 Party]  [⏹ Stby]  │
│ [🌡 Temp]              │
│ [ℹ️ Estado del sistema]│
└────────────────────────┘
```

### 4. Lenguaje natural
```
"prende la luz"        → /day
"modo nocturno"        → /night
"hacer una fiesta"     → /party
"qué temperatura"      → /temp
"voy a dormir"         → /night
"ver película"         → /relax
"emergencia"           → /alarm
```

### 5. Notas de voz (solo en modo local)
Envía un audio diciendo el comando y el bot lo transcribe con Whisper.

---

## 🚀 Instalación local

### Requisitos previos

- Python 3.11+
- pip
- Git
- Cuenta de Telegram + bot creado con [@BotFather](https://t.me/BotFather)
- FFmpeg (solo si quieres usar notas de voz)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/smarthome-hub-project/smarthome-hub-telegram-bot.git
cd smarthome-hub-telegram-bot

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias básicas
pip install -r requirements.txt

# 5. (Opcional) Instalar Whisper para voz local
pip install openai-whisper
# O alternativa más ligera:
pip install pywhispercpp

# 6. Configurar variables de entorno (ver siguiente sección)
cp .env.example .env
# Editar .env con tu editor preferido

# 7. Ejecutar el bot
python bot.py
```

---

## ⚙ Configuración

### Variables de entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto:

```env
# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=tu_token_de_botfather

# === MQTT ===
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC_CMD=smarthome/tu_usuario/cmd
MQTT_TOPIC_ACK=smarthome/tu_usuario/ack
MQTT_TOPIC_TEMP=smarthome/tu_usuario/temp

# === AUTENTICACIÓN ===
AUTHORIZED_USERS=123456789,987654321
AUTH_PASSWORD=tu_password_secreto

# === VOZ (opcional) ===
ENABLE_VOICE=true        # false para deshabilitar
WHISPER_MODEL=tiny       # tiny, base, small, medium
WHISPER_LANGUAGE=es      # es, en, fr, etc.
WHISPER_THREADS=2
```

### Obtener tu user_id de Telegram

Usa [@userinfobot](https://t.me/userinfobot):
1. Envía `/start`
2. Te responderá con tu `Id`

### Crear tu bot

Usa [@BotFather](https://t.me/BotFather):
1. `/newbot`
2. Elige nombre y username
3. Copia el token que te dará

---

## 🌐 Despliegue en Railway

### Preparación

1. Crea cuenta en [railway.app](https://railway.app)
2. Conecta con GitHub
3. Crea un nuevo proyecto: **"Deploy from GitHub repo"**
4. Selecciona este repositorio

### Configuración del servicio

```
Tipo: Background Worker
Build Command: (automático con railpack.json)
Start Command: python bot.py
```

### Variables de entorno en Railway

Agregar todas las variables del `.env` excepto:

- ✅ `TELEGRAM_BOT_TOKEN` (obligatoria)
- ✅ `AUTHORIZED_USERS` (obligatoria)
- ✅ `AUTH_PASSWORD` (obligatoria)
- ✅ `MQTT_BROKER`, `MQTT_PORT`, `MQTT_TOPIC_*` (obligatorias)
- ⚠️ `ENABLE_VOICE=false` (recomendado para tier gratis)

### Archivo `railpack.json`

```json
{
  "$schema": "https://schema.railpack.com",
  "provider": "python",
  "packages": {
    "python": "3.11"
  }
}
```

> 💡 **Nota**: Las notas de voz se deshabilitan en Railway por limitaciones de memoria (Whisper requiere ~150 MB). Se ejecutan únicamente cuando corres el bot localmente.

---

## 📁 Estructura del proyecto

```
telegram-bot/
├── bot.py                  # Punto de entrada principal
├── auth.py                 # Autenticación y autorización
├── nlp.py                  # Procesamiento de lenguaje natural
├── voice.py                # Transcripción de voz (Whisper)
├── keyboards.py            # Definiciones de teclados
├── mqtt_client.py          # Cliente MQTT
├── requirements.txt        # Dependencias Python
├── railpack.json           # Configuración Railway
├── Procfile                # Comando de inicio
├── .env                    # Variables de entorno (NO subir)
├── .env.example            # Plantilla de variables
├── .gitignore
└── README.md
```

---

## 🔧 Módulos

### `bot.py`
Punto de entrada. Configura handlers, registra comandos y arranca el polling de Telegram.

### `auth.py`
Sistema de autenticación con lista blanca de `user_id` y password compartido.

```python
@authorized_only
async def cmd_secret(update, context):
    # Solo usuarios autorizados llegan aquí
    ...
```

### `nlp.py`
Procesamiento de lenguaje natural basado en diccionario de palabras clave en español e inglés.

```python
command, phrase = parse_natural_command("prende la luz")
# Returns: ("D", "prende")
```

### `voice.py`
Transcripción de audio usando Whisper local. Se carga solo si `ENABLE_VOICE=true`.

```python
text = transcribe_audio("/tmp/audio.ogg")
# Returns: "modo nocturno"
```

### `keyboards.py`
Definiciones de ReplyKeyboard e InlineKeyboard con sus respectivos callback_data.

### `mqtt_client.py`
Cliente MQTT con conexión persistente, suscripción a topics de respuesta y publicación de comandos.

---

## 📜 Comandos disponibles

### Públicos (sin autenticación)

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra el menú |
| `/myid` | Muestra tu ID de Telegram |
| `/auth <password>` | Auto-autorización con password |

### Protegidos (requieren autenticación)

| Comando | Descripción | Acción MQTT |
|---------|-------------|-------------|
| `/help` | Lista todos los comandos | - |
| `/menu` | Muestra botones interactivos | - |
| `/examples` | Ejemplos de lenguaje natural | - |
| `/status` | Estado del sistema | - |
| `/night` | Modo nocturno (LEDs 15%) | Publica `N` |
| `/day` | Modo día (LEDs 100%) | Publica `D` |
| `/relax` | Modo relax | Publica `R` |
| `/alarm` | Modo alarma | Publica `A` |
| `/party` | Modo fiesta | Publica `P` |
| `/standby` | Modo standby (5%) | Publica `S` |
| `/temp` | Consultar temperatura | Publica `T` |

---

## 🛡 Seguridad

### Lista blanca de usuarios

Solo los `user_id` listados en `AUTHORIZED_USERS` pueden ejecutar comandos:

```env
AUTHORIZED_USERS=123456789,987654321
```

### Auto-autorización

Usuarios nuevos pueden auto-autorizarse con el password:

```
/auth mi_password_secreto
```

### Buenas prácticas implementadas

- ✅ Token en variable de entorno (no en código)
- ✅ `.env` excluido del repositorio (`.gitignore`)
- ✅ Decorator `@authorized_only` para proteger comandos
- ✅ Logs de intentos no autorizados
- ✅ Validación de comandos antes de ejecutar

### Recomendaciones

- 🔄 Rotar el token periódicamente con `/revoke` en @BotFather
- 🔐 Usar passwords fuertes y únicos
- 📝 Revisar logs regularmente
- 🌐 Considerar broker MQTT privado para producción

---

## 🐛 Troubleshooting

### Bot no responde

```bash
# Verifica que esté ejecutándose
python bot.py

# Verifica el token en .env
echo $TELEGRAM_BOT_TOKEN
```

### Error 409 Conflict

```
ERROR: Conflict: terminated by other getUpdates request
```

**Causa**: Hay dos instancias del bot corriendo al mismo tiempo (local + Railway).

**Solución**: Apaga una de las dos (Ctrl+C local o "Pause" en Railway).

### MQTT desconectado

```bash
# Verifica conectividad
ping broker.hivemq.com

# Verifica el puerto 1883
telnet broker.hivemq.com 1883
```

### Notas de voz no funcionan

1. Verifica que `ENABLE_VOICE=true` en `.env`
2. Verifica que FFmpeg esté instalado: `ffmpeg -version`
3. Verifica que Whisper esté instalado: `pip list | grep whisper`

### Variables no se cargan

Verifica que `load_dotenv()` esté ANTES de los imports que usan variables:

```python
from dotenv import load_dotenv
load_dotenv()  # ANTES

from auth import ...  # DESPUÉS
```

---

## 🔗 Proyectos relacionados

| Proyecto | Descripción |
|----------|-------------|
| [smarthome-hub-stm32-cmsis](https://github.com/smarthome-hub-project/smarthome-hub-stm32-cmsis) | Firmware bare metal del STM32 |
| [smarthome-hub-stm32-zephyr](https://github.com/smarthome-hub-project/smarthome-hub-stm32-zephyr) | Firmware con Zephyr RTOS |
| [smarthome-hub-esp32](https://github.com/smarthome-hub-project/smarthome-hub-esp32) | Bridge BLE/MQTT con ESP32-C6 |
| [smarthome-hub-web](https://github.com/smarthome-hub-project/smarthome-hub-web) | Web App con Web Bluetooth |

---

## 👨‍💻 Autor

**David Henao Rojas**

- GitHub: [@dahenaor-source](https://github.com/dahenaor-source)
- Proyecto académico de Estructuras Computacionales

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

<div align="center">

⭐ Si te resulta útil, déjale una estrella al repo

</div>