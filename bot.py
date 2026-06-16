"""
============================================================
SMART HOME HUB - TELEGRAM BOT
Versión 3.0 - Bidireccional con respuestas del STM32
============================================================
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from mqtt_client import MqttClient

# ============================================================
# CONFIGURACIÓN
# ============================================================
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN no encontrado en .env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Cliente MQTT global
mqtt_client = MqttClient()

# Referencias globales
bot_application = None
event_loop = None

# Lista de chat_ids que han interactuado (para notificaciones automáticas)
subscribed_chat_ids = set()

# Mapeo de estado → emoji y texto
STATE_INFO = {
    "NIGHT":   {"emoji": "🌙", "name": "Nocturno"},
    "DAY":     {"emoji": "☀️", "name": "Día"},
    "RELAX":   {"emoji": "😌", "name": "Relax"},
    "ALARM":   {"emoji": "🚨", "name": "Alarma"},
    "PARTY":   {"emoji": "🎉", "name": "Fiesta"},
    "STANDBY": {"emoji": "⏹", "name": "Standby"},
    "OFF":     {"emoji": "⭕", "name": "Apagado"},
}


# ============================================================
# CALLBACKS DE MQTT (vienen del ESP32/STM32)
# ============================================================

def on_ack_received(payload: str):
    """Cuando el ESP32 responde con ACK:<estado>"""
    logger.info(f"💬 ACK recibido: {payload}")
    
    # Buscar info del estado
    info = STATE_INFO.get(payload.upper(), {"emoji": "✅", "name": payload})
    message = f"{info['emoji']} *{info['name']}* activado correctamente"
    
    # Enviar a todos los usuarios suscritos
    _broadcast_message(message)


def on_temp_received(payload: str):
    """Cuando el ESP32 envía la temperatura"""
    logger.info(f"🌡 TEMP recibida: {payload}")
    
    # Formatear el mensaje
    message = f"🌡 Temperatura actual: *{payload} °C*"
    
    # Enviar a todos los usuarios suscritos
    _broadcast_message(message)


def _broadcast_message(message: str):
    """Envía un mensaje a todos los chat_ids registrados"""
    if not bot_application or not event_loop:
        logger.warning("⚠️ Bot no inicializado, no se puede enviar mensaje")
        return
    
    if not subscribed_chat_ids:
        logger.warning("⚠️ No hay usuarios suscritos")
        return
    
    # Como estamos en un thread MQTT, debemos usar asyncio.run_coroutine_threadsafe
    for chat_id in subscribed_chat_ids:
        try:
            asyncio.run_coroutine_threadsafe(
                _send_message_async(chat_id, message),
                event_loop
            )
        except Exception as e:
            logger.error(f"❌ Error enviando a {chat_id}: {e}")


async def _send_message_async(chat_id: int, message: str):
    """Envía un mensaje async a un usuario específico"""
    try:
        await bot_application.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ Error en send_message_async: {e}")


# ============================================================
# COMANDOS DEL BOT
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # Suscribir este chat_id para recibir notificaciones
    subscribed_chat_ids.add(update.effective_chat.id)
    
    welcome_msg = (
        f"👋 Hola {user.first_name}!\n\n"
        f"🏠 Soy el *Smart Home Hub Bot*\n"
        f"Controlo tu sistema IoT remotamente vía MQTT.\n\n"
        f"📡 MQTT: {'🟢 Conectado' if mqtt_client.connected else '🔴 Desconectado'}\n\n"
        f"Escribe /help para ver los comandos."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    logger.info(f"Usuario {user.username} ({user.id}) inició el bot. Chat: {update.effective_chat.id}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_msg = (
        "📋 *Comandos disponibles:*\n\n"
        "🌙 /night - Modo nocturno (15%)\n"
        "☀️ /day - Modo día (100%)\n"
        "😌 /relax - Modo relax\n"
        "🚨 /alarm - Modo alarma\n"
        "🎉 /party - Modo fiesta\n"
        "⏹ /standby - Modo standby (5%)\n"
        "🌡 /temp - Consultar temperatura\n"
        "ℹ️ /status - Estado del sistema\n"
        "❓ /help - Mostrar esta ayuda"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def send_mqtt_command(update: Update, command: str, mode_name: str, emoji: str):
    """Función helper para enviar comandos por MQTT"""
    # Suscribir este chat al broadcast
    subscribed_chat_ids.add(update.effective_chat.id)
    
    if not mqtt_client.connected:
        await update.message.reply_text(
            "⚠️ *MQTT desconectado*\nNo puedo enviar el comando al ESP32.",
            parse_mode="Markdown"
        )
        return

    success = mqtt_client.publish_command(command)
    if success:
        await update.message.reply_text(
            f"{emoji} Enviando comando *{mode_name}*...",
            parse_mode="Markdown"
        )
        logger.info(f"Comando {command} ({mode_name}) enviado por {update.effective_user.username}")
    else:
        await update.message.reply_text("❌ Error al enviar el comando.")


async def cmd_night(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "N", "Nocturno", "🌙")


async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "D", "Día", "☀️")


async def cmd_relax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "R", "Relax", "😌")


async def cmd_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "A", "Alarma", "🚨")


async def cmd_party(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "P", "Fiesta", "🎉")


async def cmd_standby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "S", "Standby", "⏹")


async def cmd_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Suscribir este chat al broadcast
    subscribed_chat_ids.add(update.effective_chat.id)
    
    if not mqtt_client.connected:
        await update.message.reply_text("⚠️ MQTT desconectado")
        return
    
    success = mqtt_client.publish_command("T")
    if success:
        await update.message.reply_text("🌡 Consultando temperatura...")
    else:
        await update.message.reply_text("❌ Error al solicitar la temperatura")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status_msg = (
        "📊 *Estado del sistema:*\n\n"
        f"🔌 Bot: 🟢 Online\n"
        f"📡 MQTT: {'🟢 Conectado' if mqtt_client.connected else '🔴 Desconectado'}\n"
        f"📶 Broker: {mqtt_client.broker}\n"
        f"📤 Topic CMD: `{mqtt_client.topic_cmd}`\n"
        f"👥 Usuarios suscritos: {len(subscribed_chat_ids)}"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤔 No entendí ese mensaje.\nEscribe /help para ver los comandos."
    )


# ============================================================
# SETUP POST-INIT (capturamos el event loop)
# ============================================================
async def post_init(application: Application) -> None:
    """Se ejecuta después de inicializar la aplicación"""
    global event_loop
    event_loop = asyncio.get_event_loop()
    logger.info("✅ Event loop capturado para broadcasts MQTT")


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    global bot_application
    
    logger.info("🚀 Iniciando Smart Home Hub Bot v3.0...")

    # Crear app de Telegram con post_init
    bot_application = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    # Conectar MQTT (callbacks)
    mqtt_client.set_ack_callback(on_ack_received)
    mqtt_client.set_temp_callback(on_temp_received)
    mqtt_client.connect()

    # Registrar comandos
    bot_application.add_handler(CommandHandler("start", cmd_start))
    bot_application.add_handler(CommandHandler("help", cmd_help))
    bot_application.add_handler(CommandHandler("night", cmd_night))
    bot_application.add_handler(CommandHandler("day", cmd_day))
    bot_application.add_handler(CommandHandler("relax", cmd_relax))
    bot_application.add_handler(CommandHandler("alarm", cmd_alarm))
    bot_application.add_handler(CommandHandler("party", cmd_party))
    bot_application.add_handler(CommandHandler("standby", cmd_standby))
    bot_application.add_handler(CommandHandler("temp", cmd_temp))
    bot_application.add_handler(CommandHandler("status", cmd_status))
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    logger.info("✅ Bot listo. Escuchando mensajes...")
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()