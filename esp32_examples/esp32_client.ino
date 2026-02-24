/*
 * ESP32 Management System - Example Client Code
 * 
 * This example shows how to connect your ESP32 to the management system
 * and enable OTA updates, monitoring, and alarm reporting.
 * 
 * Features:
 * - Automatic device registration
 * - OTA firmware updates
 * - Heartbeat monitoring
 * - Alarm reporting
 * - Network info reporting (MAC, IP, SSID)
 * 
 * Hardware: ESP32 (any variant)
 * Framework: Arduino / PlatformIO
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Update.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION - CHANGE THESE VALUES
// ============================================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL = "http://your-server-url.com";  // No trailing slash
const char* DEVICE_NAME = "ESP32-Device-01";
const char* FIRMWARE_VERSION = "1.0.0";

// Update intervals
const unsigned long HEARTBEAT_INTERVAL = 30000;  // 30 seconds
const unsigned long UPDATE_CHECK_INTERVAL = 300000;  // 5 minutes

// ============================================
// GLOBAL VARIABLES
// ============================================
String macAddress;
unsigned long lastHeartbeat = 0;
unsigned long lastUpdateCheck = 0;
unsigned long bootTime = 0;

// ============================================
// SETUP
// ============================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=================================");
  Serial.println("ESP32 Management System Client");
  Serial.println("=================================\n");
  
  // Get MAC address
  macAddress = WiFi.macAddress();
  Serial.print("MAC Address: ");
  Serial.println(macAddress);
  
  // Connect to WiFi
  connectWiFi();
  
  // Register device with server
  registerDevice();
  
  bootTime = millis();
  
  Serial.println("\nSetup complete! Starting main loop...\n");
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }
  
  // Send heartbeat
  unsigned long currentMillis = millis();
  if (currentMillis - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = currentMillis;
    sendHeartbeat();
  }
  
  // Check for firmware updates
  if (currentMillis - lastUpdateCheck >= UPDATE_CHECK_INTERVAL) {
    lastUpdateCheck = currentMillis;
    checkForUpdates();
  }
  
  // Your application code here
  // ...
  
  delay(1000);
}

// ============================================
// WIFI CONNECTION
// ============================================
void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("SSID: ");
    Serial.println(WiFi.SSID());
  } else {
    Serial.println("\nFailed to connect to WiFi!");
    sendAlarm("wifi_connection_failed", "Could not connect to WiFi", "error");
  }
}

// ============================================
// DEVICE REGISTRATION
// ============================================
void registerDevice() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("Registering device with server...");
  
  HTTPClient http;
  String url = String(SERVER_URL) + "/api/esp32/register";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<512> doc;
  doc["mac_address"] = macAddress;
  doc["device_name"] = DEVICE_NAME;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["ssid"] = WiFi.SSID();
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["uptime"] = (millis() - bootTime) / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK) {
      Serial.println("Device registered successfully!");
      String response = http.getString();
      Serial.println("Response: " + response);
    } else {
      Serial.printf("Registration failed with code: %d\n", httpCode);
    }
  } else {
    Serial.printf("Registration request failed: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

// ============================================
// HEARTBEAT
// ============================================
void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = String(SERVER_URL) + "/api/esp32/heartbeat";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["mac_address"] = macAddress;
  doc["uptime"] = (millis() - bootTime) / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Heartbeat sent");
  } else {
    Serial.printf("Heartbeat failed: %d\n", httpCode);
  }
  
  http.end();
}

// ============================================
// ALARM REPORTING
// ============================================
void sendAlarm(String alarmType, String message, String severity) {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("Sending alarm: " + alarmType);
  
  HTTPClient http;
  String url = String(SERVER_URL) + "/api/esp32/alarm";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  doc["mac_address"] = macAddress;
  doc["alarm_type"] = alarmType;
  doc["message"] = message;
  doc["severity"] = severity;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Alarm sent successfully");
  } else {
    Serial.printf("Alarm send failed: %d\n", httpCode);
  }
  
  http.end();
}

// ============================================
// OTA UPDATE
// ============================================
void checkForUpdates() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("Checking for firmware updates...");
  
  HTTPClient http;
  String url = String(SERVER_URL) + "/api/esp32/check_update";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["mac_address"] = macAddress;
  doc["current_version"] = FIRMWARE_VERSION;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == HTTP_CODE_OK) {
    String response = http.getString();
    
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      bool updateAvailable = responseDoc["update_available"];
      
      if (updateAvailable) {
        String newVersion = responseDoc["version"];
        String downloadUrl = responseDoc["url"];
        int fileSize = responseDoc["size"];
        
        Serial.println("Update available!");
        Serial.println("New version: " + newVersion);
        Serial.println("Download URL: " + downloadUrl);
        Serial.printf("File size: %d bytes\n", fileSize);
        
        sendAlarm("ota_update_started", "Starting OTA update to version " + newVersion, "info");
        
        // Perform OTA update
        if (performOTA(downloadUrl)) {
          sendAlarm("ota_update_success", "OTA update successful! Rebooting...", "info");
          delay(1000);
          ESP.restart();
        } else {
          sendAlarm("ota_update_failed", "OTA update failed", "error");
        }
      } else {
        Serial.println("Firmware is up to date");
      }
    }
  } else {
    Serial.printf("Update check failed: %d\n", httpCode);
  }
  
  http.end();
}

bool performOTA(String url) {
  HTTPClient http;
  http.begin(url);
  
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    bool canBegin = Update.begin(contentLength);
    
    if (canBegin) {
      Serial.println("Starting OTA update...");
      
      WiFiClient * stream = http.getStreamPtr();
      size_t written = Update.writeStream(*stream);
      
      if (written == contentLength) {
        Serial.println("Written : " + String(written) + " successfully");
      } else {
        Serial.println("Written only : " + String(written) + "/" + String(contentLength));
      }
      
      if (Update.end()) {
        Serial.println("OTA done!");
        if (Update.isFinished()) {
          Serial.println("Update successfully completed. Rebooting...");
          http.end();
          return true;
        } else {
          Serial.println("Update not finished? Something went wrong!");
        }
      } else {
        Serial.println("Error Occurred. Error #: " + String(Update.getError()));
      }
    } else {
      Serial.println("Not enough space to begin OTA");
    }
  } else {
    Serial.printf("HTTP GET failed, error: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();
  return false;
}
