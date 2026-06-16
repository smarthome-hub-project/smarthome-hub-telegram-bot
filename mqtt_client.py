"""
============================================================
MQTT CLIENT - Smart Home Hub Bot
============================================================
Maneja la comunicación MQTT con HiveMQ broker
"""

import os
import logging
import paho.mqtt.client as mqtt
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MqttClient:
    """Cliente MQTT para el bot de Smart Home Hub"""

    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "broker.hivemq.com")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic_cmd = os.getenv("MQTT_TOPIC_CMD", "smarthome/default/cmd")
        self.topic_ack = os.getenv("MQTT_TOPIC_ACK", "smarthome/default/ack")
        self.topic_temp = os.getenv("MQTT_TOPIC_TEMP", "smarthome/default/temp")

        # Cliente único con ID único (para evitar colisiones)
        client_id = f"smarthome-bot-{os.getpid()}"
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id
        )

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Callback del usuario para mensajes ACK/TEMP
        self._ack_callback: Optional[Callable[[str], None]] = None
        self._temp_callback: Optional[Callable[[str], None]] = None

        self.connected = False

    # ============================================================
    # CALLBACKS INTERNOS
    # ============================================================
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback al conectar al broker"""
        if reason_code == 0:
            self.connected = True
            logger.info(f"✅ Conectado a MQTT broker: {self.broker}:{self.port}")

            # Suscribirse a topics de respuesta
            client.subscribe(self.topic_ack, qos=1)
            client.subscribe(self.topic_temp, qos=1)
            logger.info(f"📡 Suscrito a: {self.topic_ack}")
            logger.info(f"📡 Suscrito a: {self.topic_temp}")
        else:
            logger.error(f"❌ Error conectando MQTT. Code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback al desconectar"""
        self.connected = False
        logger.warning(f"⚠️ Desconectado de MQTT. Code: {reason_code}")

    def _on_message(self, client, userdata, msg):
        """Callback al recibir un mensaje"""
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        logger.info(f"📥 MQTT RX [{topic}]: {payload}")

        # Despachar según el topic
        if topic == self.topic_ack and self._ack_callback:
            self._ack_callback(payload)
        elif topic == self.topic_temp and self._temp_callback:
            self._temp_callback(payload)

    # ============================================================
    # API PÚBLICA
    # ============================================================
    def connect(self):
        """Conecta al broker MQTT"""
        try:
            logger.info(f"🔌 Conectando a MQTT: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, keepalive=60)
            # loop_start corre en un thread aparte
            self.client.loop_start()
        except Exception as e:
            logger.error(f"❌ Error conectando MQTT: {e}")
            raise

    def disconnect(self):
        """Desconecta del broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("👋 Desconectado de MQTT")

    def publish_command(self, command: str) -> bool:
        """
        Publica un comando al ESP32
        
        Args:
            command: Carácter del comando ('N', 'D', 'A', 'P', 'R', 'S', 'T')
        
        Returns:
            True si publicó correctamente, False si hubo error
        """
        if not self.connected:
            logger.warning("⚠️ No conectado a MQTT, no se puede publicar")
            return False

        try:
            result = self.client.publish(self.topic_cmd, command, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 MQTT TX [{self.topic_cmd}]: {command}")
                return True
            else:
                logger.error(f"❌ Error publicando: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"❌ Excepción publicando: {e}")
            return False

    def set_ack_callback(self, callback: Callable[[str], None]):
        """Registra callback para mensajes ACK del ESP32"""
        self._ack_callback = callback

    def set_temp_callback(self, callback: Callable[[str], None]):
        """Registra callback para mensajes TEMP del ESP32"""
        self._temp_callback = callback