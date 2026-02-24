import json
import logging
from typing import Optional, Dict, Any, Callable
import paho.mqtt.client as mqtt
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client()
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Set credentials if provided
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            self.connected = True
            # Subscribe to all device topics
            self.client.subscribe(f"{settings.MQTT_BASE_TOPIC}/+/status")
            self.client.subscribe(f"{settings.MQTT_BASE_TOPIC}/+/response")
        else:
            logger.error(f"Failed to connect to MQTT Broker. Return code: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT Broker")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {topic}: {payload}")
            
            # Extract device_id from topic
            parts = topic.split('/')
            if len(parts) >= 3:
                device_id = parts[2]
                message_type = parts[3] if len(parts) > 3 else "unknown"
                
                # Call registered handlers
                handler_key = f"{device_id}:{message_type}"
                if handler_key in self.message_handlers:
                    self.message_handlers[handler_key](device_id, payload)
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def connect(self):
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            self.client.loop_start()
            logger.info("MQTT client loop started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish(self, device_id: str, command: str, payload: Dict[str, Any]) -> bool:
        """
        Publish a command to a specific device
        Topic: medication/devices/{device_id}/command
        """
        topic = f"{settings.MQTT_BASE_TOPIC}/{device_id}/command"
        message = {
            "command": command,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            result = self.client.publish(topic, json.dumps(message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published command '{command}' to {device_id}")
                return True
            else:
                logger.error(f"Failed to publish to {device_id}: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def register_handler(self, device_id: str, message_type: str, handler: Callable):
        """Register a callback for specific device and message type"""
        key = f"{device_id}:{message_type}"
        self.message_handlers[key] = handler
    
    def send_ota_update(self, device_id: str, firmware_url: str, version: str) -> bool:
        """Send OTA update command"""
        return self.publish(device_id, "ota_update", {
            "url": firmware_url,
            "version": version
        })
    
    def send_reboot(self, device_id: str) -> bool:
        """Send reboot command"""
        return self.publish(device_id, "reboot", {})
    
    def send_wifi_change(self, device_id: str, ssid: str, password: str) -> bool:
        """Send WiFi configuration change"""
        return self.publish(device_id, "wifi_change", {
            "ssid": ssid,
            "password": password
        })
    
    def send_led_control(self, device_id: str, compartment: int, color: str, brightness: int) -> bool:
        """Send LED control command"""
        return self.publish(device_id, "led_control", {
            "compartment": compartment,
            "color": color,
            "brightness": brightness
        })
    
    def request_status(self, device_id: str) -> bool:
        """Request device status update"""
        return self.publish(device_id, "get_status", {})


# Global MQTT service instance
mqtt_service = MQTTService()
