"""
============================================================
SMART HOME HUB - TELEGRAM BOT
Versión 1.0 - Bot básico local
============================================================
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================
load_dotenv()  # Cargar variables del archivo .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN no encontrado en .env")

# Configurar logging para ver qué pasa
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# COMANDOS DEL BOT
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - mensaje de bienvenida"""
    user = update.effective_user
    welcome_msg = (
        f"👋 Hola {user.first_name}!\n\n"
        f"🏠 Soy el *Smart Home Hub Bot*\n"
        f"Te ayudo a controlar tu sistema de iluminación remotamente.\n\n"
        f"Escribe /help para ver los comandos disponibles."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    logger.info(f"Usuario {user.username} ({user.id}) inició el bot")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help - lista de comandos"""
    help_msg = (
        "📋 *Comandos disponibles:*\n\n"
        "🌙 /night - Modo nocturno (LEDs al 15%)\n"
        "☀️ /day - Modo día (LEDs al 100%)\n"
        "😌 /relax - Modo relax (LEDs ambientales)\n"
        "🚨 /alarm - Modo alarma (parpadeo)\n"
        "🎉 /party - Modo fiesta (secuencias)\n"
        "⏹ /standby - Modo standby (5%)\n"
        "🌡 /temp - Consultar temperatura actual\n"
        "ℹ️ /status - Ver estado actual del sistema\n"
        "❓ /help - Mostrar esta ayuda"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def cmd_night(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /night"""
    await update.message.reply_text("🌙 Activando *modo nocturno*...", parse_mode="Markdown")
    # TODO: Enviar 'N' al ESP32 vía MQTT (próximas fases)
    logger.info(f"Comando NIGHT solicitado por {update.effective_user.username}")


async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /day"""
    await update.message.reply_text("☀️ Activando *modo día*...", parse_mode="Markdown")
    logger.info(f"Comando DAY solicitado por {update.effective_user.username}")


async def cmd_relax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /relax"""
    await update.message.reply_text("😌 Activando *modo relax*...", parse_mode="Markdown")
    logger.info(f"Comando RELAX solicitado por {update.effective_user.username}")


async def cmd_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /alarm"""
    await update.message.reply_text("🚨 Activando *modo alarma*...", parse_mode="Markdown")
    logger.info(f"Comando ALARM solicitado por {update.effective_user.username}")


async def cmd_party(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /party"""
    await update.message.reply_text("🎉 Activando *modo fiesta*!", parse_mode="Markdown")
    logger.info(f"Comando PARTY solicitado por {update.effective_user.username}")


async def cmd_standby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /standby"""
    await update.message.reply_text("⏹ Activando *modo standby*...", parse_mode="Markdown")
    logger.info(f"Comando STANDBY solicitado por {update.effective_user.username}")


async def cmd_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /temp"""
    await update.message.reply_text("🌡 Consultando temperatura...")
    # TODO: Pedir TEMP al ESP32 vía MQTT
    logger.info(f"TEMP solicitada por {update.effective_user.username}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status"""
    status_msg = (
        "📊 *Estado del sistema:*\n\n"
        "🔌 Bot: Online\n"
        "📡 MQTT: Pendiente (próxima fase)\n"
        "📶 ESP32: Pendiente (próxima fase)\n"
        "🔧 STM32: Pendiente (próxima fase)"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja mensajes que no son comandos"""
    await update.message.reply_text(
        "🤔 No entendí ese mensaje.\n"
        "Escribe /help para ver los comandos disponibles."
    )


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    """Punto de entrada del bot"""
    logger.info("Iniciando Smart Home Hub Bot...")

    # Crear la aplicación
    app = Application.builder().token(TOKEN).build()

    # Registrar comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("night", cmd_night))
    app.add_handler(CommandHandler("day", cmd_day))
    app.add_handler(CommandHandler("relax", cmd_relax))
    app.add_handler(CommandHandler("alarm", cmd_alarm))
    app.add_handler(CommandHandler("party", cmd_party))
    app.add_handler(CommandHandler("standby", cmd_standby))
    app.add_handler(CommandHandler("temp", cmd_temp))
    app.add_handler(CommandHandler("status", cmd_status))

    # Manejar mensajes que no son comandos
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    # Iniciar el bot (polling)
    logger.info("Bot listo. Escuchando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()