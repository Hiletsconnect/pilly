#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <HTTPClient.h>
#include <Update.h>
#include <Preferences.h>

// Configuration
#define LED_PIN 5
#define LED_COUNT 24
#define COMPARTMENTS 6
#define LEDS_PER_COMPARTMENT 3

// Device Configuration
const char* DEVICE_ID = "ESP32_001";  // Unique device ID
const char* MQTT_BASE_TOPIC = "medication/devices";

// WiFi credentials (can be changed via MQTT)
char wifi_ssid[32] = "YOUR_WIFI_SSID";
char wifi_password[64] = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
char mqtt_server[64] = "YOUR_MQTT_BROKER";
int mqtt_port = 1883;
char mqtt_user[32] = "";
char mqtt_password[64] = "";

// Objects
WiFiClient espClient;
PubSubClient mqttClient(espClient);
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
Preferences preferences;

// Topics
String statusTopic;
String commandTopic;
String responseTopic;

// LED compartment colors (6 compartments)
struct CompartmentConfig {
  uint32_t color;
  uint8_t brightness;
};

CompartmentConfig compartments[COMPARTMENTS];

// Function declarations
void setupWiFi();
void setupMQTT();
void reconnectWiFi();
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void publishStatus();
void handleOTAUpdate(String url, String version);
void handleReboot();
void handleWiFiChange(String ssid, String password);
void handleLEDControl(int compartment, String color, int brightness);
void setCompartmentColor(int compartment, uint32_t color, uint8_t brightness);
uint32_t hexToColor(String hex);
void loadConfig();
void saveConfig();

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== Medication System ESP32 ===");
  Serial.println("Device ID: " + String(DEVICE_ID));
  
  // Load configuration from preferences
  loadConfig();
  
  // Initialize NeoPixel strip
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  strip.setBrightness(50);
  
  // Initialize default compartment colors
  for (int i = 0; i < COMPARTMENTS; i++) {
    compartments[i].color = strip.Color(255, 255, 255); // White
    compartments[i].brightness = 100;
  }
  
  // Setup topics
  statusTopic = String(MQTT_BASE_TOPIC) + "/" + DEVICE_ID + "/status";
  commandTopic = String(MQTT_BASE_TOPIC) + "/" + DEVICE_ID + "/command";
  responseTopic = String(MQTT_BASE_TOPIC) + "/" + DEVICE_ID + "/response";
  
  // Setup WiFi and MQTT
  setupWiFi();
  setupMQTT();
  
  // Publish initial status
  publishStatus();
  
  Serial.println("=== Setup Complete ===\n");
}

void loop() {
  // Ensure WiFi is connected
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
  }
  
  // Ensure MQTT is connected
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  
  mqttClient.loop();
  
  // Publish status every 30 seconds
  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > 30000) {
    publishStatus();
    lastStatusUpdate = millis();
  }
}

void setupWiFi() {
  Serial.println("\n=== WiFi Setup ===");
  Serial.print("Connecting to: ");
  Serial.println(wifi_ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid, wifi_password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("MAC Address: ");
    Serial.println(WiFi.macAddress());
  } else {
    Serial.println("\nWiFi Connection Failed!");
  }
}

void reconnectWiFi() {
  Serial.println("WiFi disconnected. Reconnecting...");
  WiFi.disconnect();
  delay(1000);
  setupWiFi();
}

void setupMQTT() {
  Serial.println("\n=== MQTT Setup ===");
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  
  if (strlen(mqtt_user) > 0) {
    Serial.println("Using MQTT authentication");
  }
  
  reconnectMQTT();
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");
    
    String clientId = "ESP32_" + String(DEVICE_ID);
    bool connected;
    
    if (strlen(mqtt_user) > 0) {
      connected = mqttClient.connect(clientId.c_str(), mqtt_user, mqtt_password);
    } else {
      connected = mqttClient.connect(clientId.c_str());
    }
    
    if (connected) {
      Serial.println("Connected!");
      mqttClient.subscribe(commandTopic.c_str());
      Serial.println("Subscribed to: " + commandTopic);
      publishStatus();
    } else {
      Serial.print("Failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(". Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.println("\n=== MQTT Message Received ===");
  Serial.print("Topic: ");
  Serial.println(topic);
  
  // Parse JSON payload
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  String command = doc["command"];
  JsonObject params = doc["payload"];
  
  Serial.print("Command: ");
  Serial.println(command);
  
  // Handle different commands
  if (command == "reboot") {
    handleReboot();
  }
  else if (command == "ota_update") {
    String url = params["url"];
    String version = params["version"];
    handleOTAUpdate(url, version);
  }
  else if (command == "wifi_change") {
    String ssid = params["ssid"];
    String password = params["password"];
    handleWiFiChange(ssid, password);
  }
  else if (command == "led_control") {
    int compartment = params["compartment"];
    String color = params["color"];
    int brightness = params["brightness"];
    handleLEDControl(compartment, color, brightness);
  }
  else if (command == "get_status") {
    publishStatus();
  }
  else {
    Serial.println("Unknown command: " + command);
  }
}

void publishStatus() {
  StaticJsonDocument<512> doc;
  
  doc["device_id"] = DEVICE_ID;
  doc["mac_address"] = WiFi.macAddress();
  doc["ip_address"] = WiFi.localIP().toString();
  doc["wifi_ssid"] = WiFi.SSID();
  doc["rssi"] = WiFi.RSSI();
  doc["firmware_version"] = "1.0.0";
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  
  String output;
  serializeJson(doc, output);
  
  mqttClient.publish(statusTopic.c_str(), output.c_str());
  Serial.println("Status published");
}

void handleOTAUpdate(String url, String version) {
  Serial.println("\n=== OTA Update ===");
  Serial.println("URL: " + url);
  Serial.println("Version: " + version);
  
  // Send response that update is starting
  StaticJsonDocument<256> response;
  response["status"] = "starting";
  response["message"] = "OTA update initiated";
  String output;
  serializeJson(response, output);
  mqttClient.publish(responseTopic.c_str(), output.c_str());
  
  HTTPClient http;
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    bool canBegin = Update.begin(contentLength);
    
    if (canBegin) {
      Serial.println("Beginning OTA update...");
      WiFiClient* stream = http.getStreamPtr();
      size_t written = Update.writeStream(*stream);
      
      if (written == contentLength) {
        Serial.println("Written: " + String(written) + " successfully");
      } else {
        Serial.println("Written only: " + String(written) + "/" + String(contentLength));
      }
      
      if (Update.end()) {
        if (Update.isFinished()) {
          Serial.println("OTA Update successful! Rebooting...");
          response["status"] = "success";
          response["message"] = "Update complete, rebooting";
          serializeJson(response, output);
          mqttClient.publish(responseTopic.c_str(), output.c_str());
          delay(1000);
          ESP.restart();
        } else {
          Serial.println("OTA Update failed");
          response["status"] = "failed";
          response["message"] = "Update not finished";
          serializeJson(response, output);
          mqttClient.publish(responseTopic.c_str(), output.c_str());
        }
      } else {
        Serial.println("Error during update: " + String(Update.getError()));
        response["status"] = "failed";
        response["message"] = "Error during update";
        serializeJson(response, output);
        mqttClient.publish(responseTopic.c_str(), output.c_str());
      }
    } else {
      Serial.println("Not enough space for OTA");
      response["status"] = "failed";
      response["message"] = "Not enough space";
      serializeJson(response, output);
      mqttClient.publish(responseTopic.c_str(), output.c_str());
    }
  } else {
    Serial.println("HTTP error: " + String(httpCode));
    response["status"] = "failed";
    response["message"] = "HTTP error: " + String(httpCode);
    serializeJson(response, output);
    mqttClient.publish(responseTopic.c_str(), output.c_str());
  }
  
  http.end();
}

void handleReboot() {
  Serial.println("\n=== Rebooting Device ===");
  
  StaticJsonDocument<128> response;
  response["status"] = "rebooting";
  response["message"] = "Device will reboot now";
  String output;
  serializeJson(response, output);
  mqttClient.publish(responseTopic.c_str(), output.c_str());
  
  delay(1000);
  ESP.restart();
}

void handleWiFiChange(String ssid, String password) {
  Serial.println("\n=== WiFi Change ===");
  Serial.println("New SSID: " + ssid);
  
  // Save new credentials
  ssid.toCharArray(wifi_ssid, sizeof(wifi_ssid));
  password.toCharArray(wifi_password, sizeof(wifi_password));
  saveConfig();
  
  StaticJsonDocument<128> response;
  response["status"] = "success";
  response["message"] = "WiFi credentials updated, rebooting";
  String output;
  serializeJson(response, output);
  mqttClient.publish(responseTopic.c_str(), output.c_str());
  
  delay(1000);
  ESP.restart();
}

void handleLEDControl(int compartment, String color, int brightness) {
  Serial.println("\n=== LED Control ===");
  Serial.print("Compartment: ");
  Serial.println(compartment);
  Serial.print("Color: ");
  Serial.println(color);
  Serial.print("Brightness: ");
  Serial.println(brightness);
  
  if (compartment < 0 || compartment >= COMPARTMENTS) {
    Serial.println("Invalid compartment number");
    return;
  }
  
  uint32_t ledColor = hexToColor(color);
  setCompartmentColor(compartment, ledColor, brightness);
  
  // Save configuration
  compartments[compartment].color = ledColor;
  compartments[compartment].brightness = brightness;
  
  StaticJsonDocument<128> response;
  response["status"] = "success";
  response["message"] = "LED updated";
  response["compartment"] = compartment;
  String output;
  serializeJson(response, output);
  mqttClient.publish(responseTopic.c_str(), output.c_str());
}

void setCompartmentColor(int compartment, uint32_t color, uint8_t brightness) {
  int startLED = compartment * LEDS_PER_COMPARTMENT;
  
  // Extract RGB components and apply brightness
  uint8_t r = ((color >> 16) & 0xFF) * brightness / 100;
  uint8_t g = ((color >> 8) & 0xFF) * brightness / 100;
  uint8_t b = (color & 0xFF) * brightness / 100;
  
  uint32_t adjustedColor = strip.Color(r, g, b);
  
  for (int i = 0; i < LEDS_PER_COMPARTMENT; i++) {
    strip.setPixelColor(startLED + i, adjustedColor);
  }
  
  strip.show();
}

uint32_t hexToColor(String hex) {
  // Remove # if present
  if (hex.startsWith("#")) {
    hex = hex.substring(1);
  }
  
  // Convert hex string to long
  long number = strtol(hex.c_str(), NULL, 16);
  
  // Extract RGB
  uint8_t r = (number >> 16) & 0xFF;
  uint8_t g = (number >> 8) & 0xFF;
  uint8_t b = number & 0xFF;
  
  return strip.Color(r, g, b);
}

void loadConfig() {
  preferences.begin("medication", false);
  
  preferences.getString("wifi_ssid", wifi_ssid, sizeof(wifi_ssid));
  preferences.getString("wifi_pass", wifi_password, sizeof(wifi_password));
  preferences.getString("mqtt_server", mqtt_server, sizeof(mqtt_server));
  mqtt_port = preferences.getInt("mqtt_port", 1883);
  
  preferences.end();
  
  Serial.println("Configuration loaded from preferences");
}

void saveConfig() {
  preferences.begin("medication", false);
  
  preferences.putString("wifi_ssid", wifi_ssid);
  preferences.putString("wifi_pass", wifi_password);
  preferences.putString("mqtt_server", mqtt_server);
  preferences.putInt("mqtt_port", mqtt_port);
  
  preferences.end();
  
  Serial.println("Configuration saved to preferences");
}
