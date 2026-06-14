# Smart Home Hub - Telegram Bot

Bot de Telegram para controlar el sistema Smart Home Hub remotamente.

## Comandos disponibles

- `/start` - Iniciar el bot
- `/help` - Ver ayuda
- `/night` - Modo nocturno (LEDs al 15%)
- `/day` - Modo día (LEDs al 100%)
- `/relax` - Modo relax
- `/alarm` - Modo alarma
- `/party` - Modo fiesta
- `/standby` - Modo standby
- `/temp` - Consultar temperatura
- `/status` - Estado del sistema

## Arquitectura

Telegram → Bot (Python) → MQTT → ESP32-C6 → UART → STM32 L476RG

## Tecnologías

- python-telegram-bot v21.6
- Hosting: Render.com
- Broker MQTT: HiveMQ Public