"""
============================================================
NLP MODULE - Smart Home Hub Bot
============================================================
Procesamiento básico de lenguaje natural.
Mapea frases naturales a comandos del sistema.
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)


# ============================================================
# DICCIONARIO DE FRASES NATURALES → COMANDO
# ============================================================
NATURAL_COMMANDS = {
    # ----------------------------------------------------------
    # NIGHT MODE
    # ----------------------------------------------------------
    "N": [
        # Español
        "nocturno", "noche", "modo noche", "modo nocturno",
        "luz tenue", "luz baja", "atenuar", "bajar luz",
        "luz suave", "ambiente nocturno", "duermo",
        "ir a dormir", "voy a dormir", "vamos a dormir",
        # Inglés
        "night", "night mode", "dim", "dim light",
        "going to sleep", "bed time", "bedtime",
    ],
    
    # ----------------------------------------------------------
    # DAY MODE
    # ----------------------------------------------------------
    "D": [
        # Español
        "prende", "prender", "enciende", "encender",
        "luz", "luces", "luz fuerte", "luz al maximo", "luz al maximo",
        "iluminar", "iluminacion total", "todo encendido",
        "modo dia", "dia", "modo claro", "brillante",
        "luz blanca", "abrir", "despertar",
        # Inglés
        "day", "day mode", "turn on", "lights on",
        "bright", "bright light", "full light", "wake up",
        "on", "lights",
    ],
    
    # ----------------------------------------------------------
    # RELAX MODE
    # ----------------------------------------------------------
    "R": [
        # Español
        "relax", "relajar", "relajarse", "modo relax",
        "ambiente romantico", "romantico", "tranquilo",
        "calma", "calmado", "ambiente suave", "chill",
        "descansar", "leer", "ver pelicula", "pelicula",
        "ambiente acogedor", "acogedor",
        # Inglés
        "relax", "relaxing", "relax mode", "chill",
        "romantic", "romantic mood", "cozy", "movie",
        "movie time", "reading", "reading mode",
    ],
    
    # ----------------------------------------------------------
    # ALARM MODE
    # ----------------------------------------------------------
    "A": [
        # Español
        "alarma", "alerta", "modo alarma", "modo alerta",
        "peligro", "emergencia", "ladron", "intruso",
        "sos", "auxilio", "ayuda", "parpadeo", "parpadear",
        # Inglés
        "alarm", "alert", "alarm mode", "danger",
        "emergency", "intruder", "sos", "help",
        "blink", "blinking",
    ],
    
    # ----------------------------------------------------------
    # PARTY MODE
    # ----------------------------------------------------------
    "P": [
        # Español
        "fiesta", "modo fiesta", "party", "modo party",
        "discoteca", "rumba", "rumbear", "celebrar",
        "celebracion", "festejar", "festejo", "cumpleanos",
        "luces de colores", "show de luces",
        # Inglés
        "party", "party mode", "disco", "celebration",
        "celebrate", "birthday", "light show",
    ],
    
    # ----------------------------------------------------------
    # STANDBY MODE
    # ----------------------------------------------------------
    "S": [
        # Español
        "standby", "modo standby", "espera", "modo espera",
        "piloto", "modo piloto", "stand by",
        # Inglés
        "standby", "stand by", "standby mode", "idle",
        "idle mode", "pilot",
    ],
    
    # ----------------------------------------------------------
    # TEMPERATURE QUERY
    # ----------------------------------------------------------
    "T": [
        # Español
        "temperatura", "temp", "que temperatura", "cuanto hace",
        "cuanto calor", "cuanto frio", "clima", "ambiente",
        "calor", "frio", "grados", "cuantos grados",
        "termometro",
        # Inglés
        "temperature", "temp", "how hot", "how cold",
        "weather", "degrees", "thermometer", "what temp",
    ],
}


# ============================================================
# UTILIDADES
# ============================================================

def _normalize_text(text: str) -> str:
    """
    Normaliza texto:
    - Convierte a minúsculas
    - Elimina tildes y acentos
    - Elimina caracteres especiales
    """
    # Convertir a minúsculas
    text = text.lower().strip()
    
    # Eliminar tildes (decomposición unicode + filtrado)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Eliminar caracteres especiales (mantener letras, números y espacios)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    return text


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def parse_natural_command(text: str) -> tuple:
    """
    Analiza un texto natural y devuelve el comando correspondiente.
    
    Args:
        text: Texto del usuario (ej. "prende la luz")
    
    Returns:
        Tuple (command, matched_phrase) si encuentra coincidencia
        Tuple (None, None) si no encuentra nada
    
    Ejemplo:
        >>> parse_natural_command("prende la luz")
        ('D', 'prende')
        
        >>> parse_natural_command("hola que tal")
        (None, None)
    """
    if not text:
        return (None, None)
    
    normalized = _normalize_text(text)
    logger.debug(f"Texto normalizado: '{normalized}'")
    
    # Buscar la coincidencia MÁS LARGA primero (frases tienen prioridad sobre palabras)
    matches = []
    
    for command, phrases in NATURAL_COMMANDS.items():
        for phrase in phrases:
            phrase_normalized = _normalize_text(phrase)
            
            # Coincidencia exacta como palabra completa
            # Usamos \b para evitar matches parciales (ej. "dia" en "ediado")
            pattern = r'\b' + re.escape(phrase_normalized) + r'\b'
            
            if re.search(pattern, normalized):
                matches.append((command, phrase, len(phrase_normalized)))
    
    if not matches:
        return (None, None)
    
    # Ordenar por longitud descendente (frases largas tienen prioridad)
    matches.sort(key=lambda x: -x[2])
    
    best_command, best_phrase, _ = matches[0]
    logger.info(f"NLP match: '{text}' → '{best_phrase}' → comando '{best_command}'")
    
    return (best_command, best_phrase)


# ============================================================
# FUNCIÓN AUXILIAR PARA OBTENER SUGERENCIAS
# ============================================================

def get_command_examples() -> str:
    """Devuelve ejemplos de comandos naturales para mostrar al usuario"""
    examples = (
        "💬 *Ejemplos de lenguaje natural:*\n\n"
        "🌙 _\"modo nocturno\"_ o _\"voy a dormir\"_\n"
        "☀️ _\"prende la luz\"_ o _\"luz brillante\"_\n"
        "😌 _\"modo relax\"_ o _\"ver pelicula\"_\n"
        "🚨 _\"alarma\"_ o _\"emergencia\"_\n"
        "🎉 _\"fiesta\"_ o _\"hacer una rumba\"_\n"
        "⏹ _\"standby\"_ o _\"modo espera\"_\n"
        "🌡 _\"que temperatura\"_ o _\"cuanto calor\"_"
    )
    return examples