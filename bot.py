"""
============================================================
SMART HOME HUB - TELEGRAM BOT
Versión 2.0 - Con integración MQTT
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

# Diccionario para guardar el chat_id del último usuario que pidió temp
# (para enviarle el resultado cuando llegue del ESP32)
last_temp_request_chat_id = None
bot_application = None  # Referencia al bot para enviar mensajes asíncronos

# ============================================================
# CALLBACKS DE MQTT (vienen del ESP32)
# ============================================================

def on_ack_received(payload: str):
    """Cuando el ESP32 responde con ACK:<estado>"""
    logger.info(f"💬 ACK recibido: {payload}")
    # En la siguiente fase enviaremos esto al usuario por Telegram


def on_temp_received(payload: str):
    """Cuando el ESP32 envía la temperatura"""
    logger.info(f"🌡 TEMP recibida: {payload}")
    # En la siguiente fase enviaremos esto al usuario por Telegram


# ============================================================
# COMANDOS DEL BOT
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_msg = (
        f"👋 Hola {user.first_name}!\n\n"
        f"🏠 Soy el *Smart Home Hub Bot*\n"
        f"Controlo tu sistema IoT remotamente vía MQTT.\n\n"
        f"📡 MQTT: {'🟢 Conectado' if mqtt_client.connected else '🔴 Desconectado'}\n\n"
        f"Escribe /help para ver los comandos."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    logger.info(f"Usuario {user.username} ({user.id}) inició el bot")


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
    if not mqtt_client.connected:
        await update.message.reply_text(
            "⚠️ *MQTT desconectado*\nNo puedo enviar el comando al ESP32.",
            parse_mode="Markdown"
        )
        return

    success = mqtt_client.publish_command(command)
    if success:
        await update.message.reply_text(
            f"{emoji} Activando *modo {mode_name}*...",
            parse_mode="Markdown"
        )
        logger.info(f"Comando {command} ({mode_name}) enviado por {update.effective_user.username}")
    else:
        await update.message.reply_text(
            "❌ Error al enviar el comando. Intenta de nuevo.",
        )


async def cmd_night(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "N", "nocturno", "🌙")


async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "D", "día", "☀️")


async def cmd_relax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "R", "relax", "😌")


async def cmd_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "A", "alarma", "🚨")


async def cmd_party(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "P", "fiesta", "🎉")


async def cmd_standby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "S", "standby", "⏹")


async def cmd_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        f"📤 Topic CMD: `{mqtt_client.topic_cmd}`"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤔 No entendí ese mensaje.\nEscribe /help para ver los comandos."
    )


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    global bot_application
    
    logger.info("🚀 Iniciando Smart Home Hub Bot v2.0...")

    # Conectar MQTT
    mqtt_client.set_ack_callback(on_ack_received)
    mqtt_client.set_temp_callback(on_temp_received)
    mqtt_client.connect()

    # Crear app de Telegram
    bot_application = Application.builder().token(TOKEN).build()

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