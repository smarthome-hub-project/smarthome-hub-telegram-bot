"""
============================================================
AUTH MODULE - Smart Home Hub Bot
============================================================
Gestión de autenticación y autorización de usuarios.
"""

import os
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURACIÓN
# ============================================================
def _load_authorized_users() -> set:
    """Carga la lista de usuarios autorizados desde .env"""
    users_str = os.getenv("AUTHORIZED_USERS", "")
    if not users_str:
        logger.warning("⚠️ No hay usuarios autorizados configurados!")
        return set()
    
    try:
        users = set(int(uid.strip()) for uid in users_str.split(",") if uid.strip())
        logger.info(f"✅ Usuarios autorizados cargados: {len(users)}")
        return users
    except ValueError as e:
        logger.error(f"❌ Error parseando AUTHORIZED_USERS: {e}")
        return set()


# Lista de usuarios autorizados (se carga al inicio)
AUTHORIZED_USERS = _load_authorized_users()

# Password para auto-autorización
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")


# ============================================================
# FUNCIONES PÚBLICAS
# ============================================================

def is_authorized(user_id: int) -> bool:
    """Verifica si un user_id está en la lista blanca"""
    return user_id in AUTHORIZED_USERS


def add_authorized_user(user_id: int) -> bool:
    """Agrega un user_id a la lista (en runtime, no persiste)"""
    if user_id in AUTHORIZED_USERS:
        return False
    AUTHORIZED_USERS.add(user_id)
    logger.info(f"➕ Usuario {user_id} autorizado dinámicamente")
    return True


def get_authorized_count() -> int:
    """Devuelve el número de usuarios autorizados"""
    return len(AUTHORIZED_USERS)


# ============================================================
# DECORATOR PARA COMANDOS
# ============================================================

def authorized_only(func):
    """
    Decorator que verifica si el usuario está autorizado.
    Si no lo está, envía mensaje de acceso denegado.
    
    Uso:
        @authorized_only
        async def cmd_night(update, context):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        if not is_authorized(user_id):
            logger.warning(
                f"🚫 Acceso denegado a {user.username} (id: {user_id})"
            )
            
            denied_msg = (
                "🚫 *Acceso denegado*\n\n"
                "No estás autorizado para usar este bot.\n\n"
                f"Tu ID es: `{user_id}`\n\n"
                "Si tienes el password, escribe:\n"
                "`/auth <password>`\n\n"
                "_Solo el administrador puede otorgar acceso._"
            )
            
            await update.message.reply_text(denied_msg, parse_mode="Markdown")
            return
        
        # Si está autorizado, ejecuta el comando
        return await func(update, context)
    
    return wrapper