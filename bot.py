"""
============================================================
SMART HOME HUB - TELEGRAM BOT
Versión 4.0 - Con autenticación de usuarios
============================================================
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# ⚠️ CARGAR .ENV ANTES DE IMPORTAR auth.py
load_dotenv()

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from mqtt_client import MqttClient
from auth import (
    is_authorized,
    add_authorized_user,
    get_authorized_count,
    authorized_only,
    AUTH_PASSWORD,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN no encontrado en .env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

mqtt_client = MqttClient()

bot_application = None
event_loop = None

subscribed_chat_ids = set()

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
# CALLBACKS DE MQTT
# ============================================================

def on_ack_received(payload: str):
    logger.info(f"💬 ACK recibido: {payload}")
    info = STATE_INFO.get(payload.upper(), {"emoji": "✅", "name": payload})
    message = f"{info['emoji']} *{info['name']}* activado correctamente"
    _broadcast_message(message)


def on_temp_received(payload: str):
    logger.info(f"🌡 TEMP recibida: {payload}")
    message = f"🌡 Temperatura actual: *{payload} °C*"
    _broadcast_message(message)


def _broadcast_message(message: str):
    if not bot_application or not event_loop:
        logger.warning("⚠️ Bot no inicializado, no se puede enviar mensaje")
        return
    
    if not subscribed_chat_ids:
        logger.warning("⚠️ No hay usuarios suscritos")
        return
    
    for chat_id in subscribed_chat_ids:
        try:
            asyncio.run_coroutine_threadsafe(
                _send_message_async(chat_id, message),
                event_loop
            )
        except Exception as e:
            logger.error(f"❌ Error enviando a {chat_id}: {e}")


async def _send_message_async(chat_id: int, message: str):
    try:
        await bot_application.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ Error en send_message_async: {e}")


# ============================================================
# COMANDOS PÚBLICOS
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    
    if is_authorized(user_id):
        subscribed_chat_ids.add(update.effective_chat.id)
        welcome_msg = (
            f"👋 Hola {user.first_name}!\n\n"
            f"🏠 Bienvenido al *Smart Home Hub*\n"
            f"✅ Estás autorizado para controlar el sistema.\n\n"
            f"📡 MQTT: {'🟢 Conectado' if mqtt_client.connected else '🔴 Desconectado'}\n\n"
            f"Escribe /help para ver los comandos."
        )
    else:
        welcome_msg = (
            f"👋 Hola {user.first_name}!\n\n"
            f"🚫 No estás autorizado para usar este bot.\n\n"
            f"Tu ID es: `{user_id}`\n\n"
            f"Si tienes el password, escribe:\n"
            f"`/auth <password>`"
        )
    
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    logger.info(f"Usuario {user.username} ({user_id}) inició el bot")


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = (
        f"🆔 *Tu información:*\n\n"
        f"User ID: `{user.id}`\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"Nombre: {user.first_name} {user.last_name or ''}\n\n"
        f"Estado: {'✅ Autorizado' if is_authorized(user.id) else '🚫 No autorizado'}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    if is_authorized(user.id):
        await update.message.reply_text("✅ Ya estás autorizado.", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: `/auth <password>`",
            parse_mode="Markdown"
        )
        return
    
    provided_password = context.args[0]
    
    if not AUTH_PASSWORD:
        await update.message.reply_text("❌ Auto-autorización deshabilitada.")
        logger.warning(f"Intento de /auth sin AUTH_PASSWORD configurado")
        return
    
    if provided_password == AUTH_PASSWORD:
        add_authorized_user(user.id)
        subscribed_chat_ids.add(update.effective_chat.id)
        await update.message.reply_text(
            "✅ *Autorización exitosa!*\n\nYa puedes usar todos los comandos.\nEscribe /help para ver las opciones.",
            parse_mode="Markdown"
        )
        logger.info(f"✅ Usuario autorizado vía /auth: {user.username} ({user.id})")
    else:
        await update.message.reply_text("❌ Password incorrecto.")
        logger.warning(f"🚫 Intento fallido de /auth por {user.username} ({user.id})")


# ============================================================
# COMANDOS PROTEGIDOS
# ============================================================

@authorized_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_msg = (
        "📋 *Comandos disponibles:*\n\n"
        "*🎛 Control de modos:*\n"
        "🌙 /night - Modo nocturno (15%)\n"
        "☀️ /day - Modo día (100%)\n"
        "😌 /relax - Modo relax\n"
        "🚨 /alarm - Modo alarma\n"
        "🎉 /party - Modo fiesta\n"
        "⏹ /standby - Modo standby (5%)\n\n"
        "*📊 Información:*\n"
        "🌡 /temp - Consultar temperatura\n"
        "ℹ️ /status - Estado del sistema\n"
        "🆔 /myid - Ver tu ID\n\n"
        "*❓ Ayuda:*\n"
        "/help - Mostrar esta ayuda"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def send_mqtt_command(update: Update, command: str, mode_name: str, emoji: str):
    subscribed_chat_ids.add(update.effective_chat.id)
    
    if not mqtt_client.connected:
        await update.message.reply_text(
            "⚠️ *MQTT desconectado*",
            parse_mode="Markdown"
        )
        return

    success = mqtt_client.publish_command(command)
    if success:
        await update.message.reply_text(
            f"{emoji} Enviando comando *{mode_name}*...",
            parse_mode="Markdown"
        )
        logger.info(f"Comando {command} por {update.effective_user.username}")
    else:
        await update.message.reply_text("❌ Error al enviar el comando.")


@authorized_only
async def cmd_night(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "N", "Nocturno", "🌙")


@authorized_only
async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "D", "Día", "☀️")


@authorized_only
async def cmd_relax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "R", "Relax", "😌")


@authorized_only
async def cmd_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "A", "Alarma", "🚨")


@authorized_only
async def cmd_party(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "P", "Fiesta", "🎉")


@authorized_only
async def cmd_standby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_mqtt_command(update, "S", "Standby", "⏹")


@authorized_only
async def cmd_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subscribed_chat_ids.add(update.effective_chat.id)
    
    if not mqtt_client.connected:
        await update.message.reply_text("⚠️ MQTT desconectado")
        return
    
    success = mqtt_client.publish_command("T")
    if success:
        await update.message.reply_text("🌡 Consultando temperatura...")
    else:
        await update.message.reply_text("❌ Error al solicitar la temperatura")


@authorized_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status_msg = (
        "📊 *Estado del sistema:*\n\n"
        f"🔌 Bot: 🟢 Online\n"
        f"📡 MQTT: {'🟢 Conectado' if mqtt_client.connected else '🔴 Desconectado'}\n"
        f"📶 Broker: {mqtt_client.broker}\n"
        f"📤 Topic CMD: `{mqtt_client.topic_cmd}`\n"
        f"👥 Usuarios autorizados: {get_authorized_count()}\n"
        f"📬 Chats suscritos: {len(subscribed_chat_ids)}"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚫 No estás autorizado.\nSi tienes el password: `/auth <password>`",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        "🤔 No entendí ese mensaje.\nEscribe /help para ver los comandos."
    )


async def post_init(application: Application) -> None:
    global event_loop
    event_loop = asyncio.get_event_loop()
    logger.info("✅ Event loop capturado para broadcasts MQTT")


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    global bot_application
    
    logger.info("🚀 Iniciando Smart Home Hub Bot v4.0 (con auth)...")

    if get_authorized_count() == 0:
        logger.warning("⚠️ ATENCIÓN: No hay usuarios autorizados configurados!")
        logger.warning("⚠️ Configura AUTHORIZED_USERS en el .env")

    bot_application = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    mqtt_client.set_ack_callback(on_ack_received)
    mqtt_client.set_temp_callback(on_temp_received)
    mqtt_client.connect()

    bot_application.add_handler(CommandHandler("start", cmd_start))
    bot_application.add_handler(CommandHandler("myid", cmd_myid))
    bot_application.add_handler(CommandHandler("auth", cmd_auth))
    bot_application.add_handler(CommandHandler("help", cmd_help))
    bot_application.add_handler(CommandHandler("night", cmd_night))
    bot_application.add_handler(CommandHandler("day", cmd_day))
    bot_application.add_handler(CommandHandler("relax", cmd_relax))
    bot_application.add_handler(CommandHandler("alarm", cmd_alarm))
    bot_application.add_handler(CommandHandler("party", cmd_party))
    bot_application.add_handler(CommandHandler("standby", cmd_standby))
    bot_application.add_handler(CommandHandler("temp", cmd_temp))
    bot_application.add_handler(CommandHandler("status", cmd_status))
    bot_application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown)
    )

    logger.info("✅ Bot listo. Escuchando mensajes...")
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()