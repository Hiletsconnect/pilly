# ESP32 Advanced Examples

This document provides advanced usage examples for integrating your ESP32 with the management system.

## Example 1: Temperature Monitoring with Alarms

```cpp
#include "esp32_client.h"  // Include the base client code

const float TEMP_WARNING_THRESHOLD = 75.0;
const float TEMP_CRITICAL_THRESHOLD = 85.0;

float readTemperature() {
  // Your temperature sensor reading code
  // Example: DHT22, DS18B20, BME280, etc.
  return 72.5;  // Example value
}

void checkTemperature() {
  float temp = readTemperature();
  
  if (temp >= TEMP_CRITICAL_THRESHOLD) {
    String message = "Critical temperature: " + String(temp) + "°C";
    sendAlarm("temperature_critical", message, "error");
  } 
  else if (temp >= TEMP_WARNING_THRESHOLD) {
    String message = "High temperature: " + String(temp) + "°C";
    sendAlarm("temperature_warning", message, "warning");
  }
}

void loop() {
  // ... existing loop code ...
  
  checkTemperature();
  
  delay(60000);  // Check every minute
}
```

## Example 2: Low Memory Detection

```cpp
const int LOW_HEAP_THRESHOLD = 50000;  // 50KB

void checkMemory() {
  uint32_t freeHeap = ESP.getFreeHeap();
  
  if (freeHeap < LOW_HEAP_THRESHOLD) {
    String message = "Low memory: " + String(freeHeap) + " bytes free";
    sendAlarm("low_memory", message, "warning");
    
    // Optional: Trigger garbage collection or restart
    if (freeHeap < 20000) {  // Critical low
      sendAlarm("critical_memory", "Restarting due to low memory", "error");
      delay(1000);
      ESP.restart();
    }
  }
}
```

## Example 3: WiFi Reconnection with Alarms

```cpp
unsigned long lastWiFiCheck = 0;
const unsigned long WIFI_CHECK_INTERVAL = 10000;  // 10 seconds

void checkWiFiConnection() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - lastWiFiCheck >= WIFI_CHECK_INTERVAL) {
    lastWiFiCheck = currentMillis;
    
    if (WiFi.status() != WL_CONNECTED) {
      sendAlarm("wifi_disconnected", "WiFi connection lost, reconnecting...", "warning");
      connectWiFi();
      
      if (WiFi.status() == WL_CONNECTED) {
        sendAlarm("wifi_reconnected", "WiFi connection restored", "info");
      }
    }
  }
}

void loop() {
  checkWiFiConnection();
  // ... rest of loop code ...
}
```

## Example 4: Custom Sensor Data Reporting

```cpp
struct SensorData {
  float temperature;
  float humidity;
  float pressure;
  int lightLevel;
};

SensorData readAllSensors() {
  SensorData data;
  data.temperature = readTemperature();
  data.humidity = readHumidity();
  data.pressure = readPressure();
  data.lightLevel = analogRead(LIGHT_SENSOR_PIN);
  return data;
}

void reportSensorData() {
  SensorData data = readAllSensors();
  
  String message = "Temp: " + String(data.temperature) + 
                   "°C, Humidity: " + String(data.humidity) + 
                   "%, Pressure: " + String(data.pressure) + 
                   "hPa, Light: " + String(data.lightLevel);
  
  sendAlarm("sensor_reading", message, "info");
}

void loop() {
  static unsigned long lastReport = 0;
  
  if (millis() - lastReport >= 300000) {  // Every 5 minutes
    lastReport = millis();
    reportSensorData();
  }
  
  // ... rest of loop code ...
}
```

## Example 5: Scheduled Tasks

```cpp
#include <TimeLib.h>

void performDailyTask() {
  // Daily maintenance tasks
  sendAlarm("daily_task", "Performing daily maintenance", "info");
  
  // Example tasks:
  // - Clear old logs
  // - Restart sensors
  // - Run self-diagnostics
}

void checkScheduledTasks() {
  static int lastDay = -1;
  
  if (day() != lastDay) {
    lastDay = day();
    performDailyTask();
  }
}
```

## Example 6: Button Press Events

```cpp
const int BUTTON_PIN = 0;  // GPIO 0
bool lastButtonState = HIGH;

void checkButton() {
  bool currentState = digitalRead(BUTTON_PIN);
  
  if (currentState == LOW && lastButtonState == HIGH) {
    // Button pressed
    sendAlarm("button_press", "Button was pressed", "info");
    
    // Trigger some action
    // - Force update check
    // - Reset device
    // - Toggle feature
  }
  
  lastButtonState = currentState;
  delay(50);  // Debounce
}

void setup() {
  // ... existing setup ...
  pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
  checkButton();
  // ... rest of loop code ...
}
```

## Example 7: Watchdog Timer

```cpp
#include <esp_task_wdt.h>

const int WDT_TIMEOUT = 30;  // 30 seconds

void setupWatchdog() {
  esp_task_wdt_init(WDT_TIMEOUT, true);
  esp_task_wdt_add(NULL);
}

void loop() {
  // Feed the watchdog
  esp_task_wdt_reset();
  
  // Your code here
  // If loop hangs for > 30 seconds, ESP32 will restart
  
  // ... rest of loop code ...
}
```

## Example 8: Deep Sleep Mode

```cpp
const int SLEEP_DURATION = 3600;  // 1 hour in seconds

void enterDeepSleep() {
  sendAlarm("entering_sleep", "Device entering deep sleep for 1 hour", "info");
  delay(1000);  // Let the alarm send
  
  esp_sleep_enable_timer_wakeup(SLEEP_DURATION * 1000000ULL);
  esp_deep_sleep_start();
}

void loop() {
  // Do your work
  // ...
  
  // Go to sleep if battery low or at certain time
  if (batteryLow() || shouldSleep()) {
    enterDeepSleep();
  }
}
```

## Example 9: Multiple Devices with Different Names

```cpp
// Auto-generate device name from chip ID
String generateDeviceName() {
  uint64_t chipid = ESP.getEfuseMac();
  return "ESP32-" + String((uint32_t)chipid, HEX);
}

void setup() {
  // ... other setup ...
  
  String deviceName = generateDeviceName();
  // Use this name in registration
}
```

## Example 10: Error Recovery

```cpp
int consecutiveErrors = 0;
const int MAX_ERRORS = 5;

void handleError(String errorMessage) {
  consecutiveErrors++;
  
  sendAlarm("error_occurred", errorMessage, "error");
  
  if (consecutiveErrors >= MAX_ERRORS) {
    sendAlarm("too_many_errors", "Too many errors, restarting device", "error");
    delay(1000);
    ESP.restart();
  }
}

void clearErrorCount() {
  if (consecutiveErrors > 0) {
    consecutiveErrors = 0;
    sendAlarm("errors_cleared", "Error count reset", "info");
  }
}

// Call clearErrorCount() when operations succeed
```

## Best Practices

### 1. Rate Limiting
Don't send alarms too frequently:

```cpp
unsigned long lastAlarmTime = 0;
const unsigned long ALARM_COOLDOWN = 60000;  // 1 minute

void sendAlarmRateLimited(String type, String message, String severity) {
  unsigned long now = millis();
  if (now - lastAlarmTime >= ALARM_COOLDOWN) {
    sendAlarm(type, message, severity);
    lastAlarmTime = now;
  }
}
```

### 2. Batch Alarms
For non-critical events, batch them:

```cpp
String batchedMessages = "";
int messageCount = 0;

void addToBatch(String message) {
  if (messageCount > 0) batchedMessages += " | ";
  batchedMessages += message;
  messageCount++;
  
  if (messageCount >= 5) {
    sendAlarm("batched_events", batchedMessages, "info");
    batchedMessages = "";
    messageCount = 0;
  }
}
```

### 3. Error Handling
Always handle network errors:

```cpp
bool sendAlarmSafe(String type, String message, String severity) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot send alarm: WiFi not connected");
    return false;
  }
  
  // Try to send
  // Return true on success, false on failure
}
```

### 4. Non-blocking Operations
Use millis() instead of delay():

```cpp
// BAD
void loop() {
  doSomething();
  delay(1000);
  doSomethingElse();
}

// GOOD
void loop() {
  static unsigned long lastAction = 0;
  
  if (millis() - lastAction >= 1000) {
    lastAction = millis();
    doSomething();
  }
  
  doSomethingElse();  // Runs every loop
}
```

### 5. Memory Management
Monitor and manage heap:

```cpp
void printMemoryStats() {
  Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("Min free heap: %d bytes\n", ESP.getMinFreeHeap());
  Serial.printf("Heap size: %d bytes\n", ESP.getHeapSize());
}
```

## Integration with Other Services

### MQTT Bridge Example
```cpp
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void publishToMQTT(String topic, String message) {
  if (mqttClient.connected()) {
    mqttClient.publish(topic.c_str(), message.c_str());
  }
}

// Send alarms to both HTTP and MQTT
void sendAlarmDual(String type, String message, String severity) {
  sendAlarm(type, message, severity);  // HTTP to management system
  publishToMQTT("esp32/alarms/" + type, message);  // MQTT
}
```

## Debugging Tips

### 1. Verbose Logging
```cpp
#define DEBUG_MODE true

void debugLog(String message) {
  if (DEBUG_MODE) {
    Serial.println("[DEBUG] " + message);
  }
}
```

### 2. Memory Leak Detection
```cpp
void checkMemoryLeak() {
  static uint32_t lastHeap = ESP.getFreeHeap();
  uint32_t currentHeap = ESP.getFreeHeap();
  
  if (lastHeap - currentHeap > 1000) {
    Serial.printf("Possible memory leak! Lost %d bytes\n", lastHeap - currentHeap);
  }
  
  lastHeap = currentHeap;
}
```

### 3. Crash Recovery
```cpp
#include <esp_system.h>

void setup() {
  Serial.begin(115200);
  
  esp_reset_reason_t reason = esp_reset_reason();
  
  if (reason == ESP_RST_PANIC || reason == ESP_RST_WDT) {
    sendAlarm("crash_detected", "Device recovered from crash", "error");
  }
  
  // ... rest of setup ...
}
```

## Conclusion

These examples should help you build robust ESP32 applications that integrate seamlessly with the management system. Remember to:

- Test thoroughly before deployment
- Handle errors gracefully
- Monitor resource usage
- Use appropriate alarm severities
- Implement rate limiting for alarms
- Keep firmware versions organized

For more help, check the main README.md or open an issue on GitHub!
