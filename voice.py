"""
============================================================
VOICE MODULE - Smart Home Hub Bot
============================================================
Transcripción de notas de voz usando faster-whisper (local).
Optimizado para Railway con caché persistente.
"""

import os
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURACIÓN DEL MODELO
# ============================================================
MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Directorio donde se guarda el modelo descargado
# En Railway, /tmp es volátil pero al menos persiste durante la ejecución
MODEL_DOWNLOAD_PATH = os.getenv("WHISPER_CACHE_DIR", None)


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
        
        kwargs = {
            "model_size_or_path": MODEL_SIZE,
            "device": DEVICE,
            "compute_type": COMPUTE_TYPE,
        }
        
        if MODEL_DOWNLOAD_PATH:
            kwargs["download_root"] = MODEL_DOWNLOAD_PATH
            logger.info(f"   Cache: {MODEL_DOWNLOAD_PATH}")
        
        _model = WhisperModel(**kwargs)
        
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
        segments, info = model.transcribe(
            audio_path,
            language=WHISPER_LANGUAGE,
            beam_size=5,
        )
        
        # Concatenar todos los segmentos
        transcription = " ".join(segment.text for segment in segments).strip()
        
        logger.info(f"✅ Transcripción: '{transcription}'")
        logger.debug(f"   Idioma detectado: {info.language} ({info.language_probability:.2f})")
        
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