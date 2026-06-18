"""
============================================================
VOICE MODULE - Smart Home Hub Bot
============================================================
Transcripción de notas de voz usando openai-whisper (sin PyAV).
Más compatible con Railway que faster-whisper.
============================================================
"""

import os
import logging
import whisper

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURACIÓN DEL MODELO
# ============================================================
# Modelos disponibles:
#   "tiny"     →  75 MB,  más rápido,  menor precisión
#   "base"     → 142 MB,  rápido,      buena precisión
#   "small"    → 466 MB,  medio,       muy buena precisión
#   "medium"   → 1.5 GB,  lento,       excelente precisión
#   "large"    → 3.0 GB,  muy lento,   máxima precisión
MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")

# Idioma esperado
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")


# ============================================================
# INSTANCIA GLOBAL DEL MODELO (lazy loading)
# ============================================================
_model = None


def _get_model():
    """Carga el modelo solo cuando se necesita (lazy)"""
    global _model
    
    if _model is None:
        logger.info(f"🤖 Cargando modelo Whisper '{MODEL_SIZE}'...")
        logger.info(f"   (Primera vez tarda más por la descarga)")
        
        _model = whisper.load_model(MODEL_SIZE)
        
        logger.info(f"✅ Modelo Whisper cargado: {MODEL_SIZE}")
    
    return _model


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe un archivo de audio a texto.
    
    Args:
        audio_path: Ruta al archivo de audio (mp3, wav, ogg, opus, etc.)
    
    Returns:
        Texto transcrito (string vacío si falla)
    """
    if not os.path.exists(audio_path):
        logger.error(f"❌ Archivo no encontrado: {audio_path}")
        return ""
    
    try:
        logger.info(f"🎤 Transcribiendo audio: {audio_path}")
        
        model = _get_model()
        
        # Transcribir
        result = model.transcribe(
            audio_path,
            language=WHISPER_LANGUAGE,
            fp16=False,  # Desactivar half-precision (CPU no lo soporta bien)
        )
        
        transcription = result["text"].strip()
        
        logger.info(f"✅ Transcripción: '{transcription}'")
        
        return transcription
        
    except Exception as e:
        logger.error(f"❌ Error transcribiendo audio: {e}")
        return ""


# ============================================================
# FUNCIÓN PARA INICIALIZAR EL MODELO AL ARRANQUE
# ============================================================

def preload_model():
    """
    Pre-carga el modelo al arrancar el bot.
    Útil para que la primera transcripción no sea lenta.
    """
    try:
        _get_model()
        return True
    except Exception as e:
        logger.error(f"❌ Error pre-cargando modelo: {e}")
        return False