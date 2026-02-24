import json
import ssl
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy import text
from app.config import settings
from app.db import engine

class MqttService:
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client = client

        if settings.MQTT_USERNAME:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        if settings.MQTT_TLS:
            ctx = ssl.create_default_context()
            client.tls_set_context(ctx)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        while True:
            try:
                client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
                client.loop_forever()
            except Exception as e:
                self.connected = False
                time.sleep(3)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self.connected = True
        base = settings.TOPIC_BASE
        # Escuchamos telemetría/estado/acks de todos los devices
        client.subscribe(f"{base}/+/status")
        client.subscribe(f"{base}/+/telemetry")
        client.subscribe(f"{base}/+/cmd/ack")
        client.subscribe(f"{base}/+/schedule/ack")
        client.subscribe(f"{base}/+/schedule/state")

    def _on_disconnect(self, client, userdata, reason_code, properties):
        self.connected = False

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8", errors="ignore")
            data = json.loads(payload) if payload and payload.strip().startswith("{") else {}
        except Exception:
            return

        # topic: pilly/dev/{mac}/status
        parts = topic.split("/")
        if len(parts) < 4:
            return
        mac = parts[2]  # TOPIC_BASE = pilly/dev -> ["pilly","dev","{mac}","status"]
        kind = parts[3]

        if kind in ("status", "telemetry"):
            self._upsert_state(mac, data)

    def _upsert_state(self, mac: str, data: dict):
        online = bool(data.get("online", True))
        ip = data.get("ip")
        ssid = data.get("ssid")
        rssi = data.get("rssi")
        fw = data.get("fw") or data.get("fw_version")

        q = text("""
        WITH d AS (
          SELECT id FROM devices WHERE mac = :mac LIMIT 1
        )
        INSERT INTO device_state (device_id, online, last_seen, ip, ssid, rssi, fw_version, updated_at)
        SELECT d.id, :online, now(), :ip, :ssid, :rssi, :fw, now()
        FROM d
        ON CONFLICT (device_id) DO UPDATE SET
          online = EXCLUDED.online,
          last_seen = now(),
          ip = EXCLUDED.ip,
          ssid = EXCLUDED.ssid,
          rssi = EXCLUDED.rssi,
          fw_version = EXCLUDED.fw_version,
          updated_at = now();
        """)
        with engine.begin() as conn:
            conn.execute(q, {"mac": mac, "online": online, "ip": ip, "ssid": ssid, "rssi": rssi, "fw": fw})

    def publish_cmd(self, mac: str, cmd: dict):
        if not self.client:
            return False
        topic = f"{settings.TOPIC_BASE}/{mac}/cmd"
        self.client.publish(topic, json.dumps(cmd), qos=1)
        return True

    def publish_schedule_set(self, mac: str, payload: dict):
        if not self.client:
            return False
        topic = f"{settings.TOPIC_BASE}/{mac}/schedule/set"
        self.client.publish(topic, json.dumps(payload), qos=1)
        return True

mqtt_service = MqttService()