//READ ME
//Wifi losing and connection protocals arn't amazing at the moment so if anything goes wrong push the reset button on the ESP32 
//Make sure to add your wifi settings and parameters :)
//self note consider advancing t_ms via dt_us so it stays exact at any rate

#include <WiFi.h>

// WiFi Settings (Put the wifi Username and Passowrd here)
const char* ssid     = "*******";
const char* password = "******";
const uint16_t PORT = 9000;

// Signal params
// fs is the sample rate of the esp32 make sure to set it!
const float fs = 250.0f;                 // 250 Hz sample rate so its like 4ms per sample 
const uint32_t dt_us = (uint32_t)(1e6 / fs);
const float f_alpha = 10.0f;             // 10 Hz frequency
const float alpha_amp = 50.0f;           // amplitude (arbitrary µV it will eventually be information from the ADS1229)

// Timekeeping holding variables for sample pacing
static uint32_t t0_us = 0;
static uint32_t t_ms  = 0;

// Streaming
WiFiServer server(PORT);   // TCP port (must match the port inPython)
WiFiClient client;

// Batch send buffer
static char outbuf[512];
static size_t olen = 0;
static unsigned long lastFlushMs = 0;

//Wifi Connection Safety
unsigned long lastActivityMs = 0;   // last successful send time 
const unsigned long CLIENT_TIMEOUT_MS = 5000; // How long to wait before disconnecting

void setup() {
  Serial.begin(115200);
  delay(200);

  // Wifi Set up 
  WiFi.mode(WIFI_STA); // Keep in mind STA is station mode there is also WIFI_AP and WIFI_AP_STA
  WiFi.begin(ssid, password);

  // in setup(), after Serial.begin(...)
  WiFi.setSleep(false);

  // Initialize Time 
  t0_us = micros();
  t_ms  = 0;
  
  //Wifi Connection Status and Info 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected.");
  Serial.print("ESP32 IP: "); Serial.println(WiFi.localIP());

  server.begin();
  Serial.printf("TCP server started on port %u. Waiting for a client...\n", PORT);
}

void loop() {
  if (!client || !client.connected()) {
    WiFiClient possibleClient = server.available();
    if (possibleClient) {
      client = possibleClient;
      client.setNoDelay(true); // For real time streaming 
      Serial.println("Client connected.");
      client.println("# t_ms,value"); //This is the header line for the data in python!
      lastActivityMs = millis(); //Update time for safety check

      // reset batch state on (re)connect
      olen = 0;
      lastFlushMs = millis();
    }
    delay(10);
    // no client right now — don't keep stale bytes buffered
    if (!client || !client.connected()) {
      olen = 0;
    }
    return;
  }

  // Client inactivity timeout 
  if (client && client.connected()) {
    if ((millis() - lastActivityMs) > CLIENT_TIMEOUT_MS) {
      // flush any buffered bytes before stopping
      if (olen) { client.write((const uint8_t*)outbuf, olen); olen = 0; }
      Serial.println("Client timed out, closing.");
      client.stop();
      return;
    }
  }

  // Maintains Sample Rate -
  uint32_t now = micros();
  if ((int32_t)(now - t0_us) < (int32_t)dt_us) {
    // be polite to WiFi/RTOS
    delay(1);
    return;
  }
  t0_us += dt_us;
  t_ms  += (uint32_t)(1000.0f / fs + 0.5f);

  // Generate sine wave
  float t = t_ms / 1000.0f;
  float alpha = alpha_amp * sinf(2 * PI * f_alpha * t);

  // Send Data (batched)
  if (client && client.connected()) {
    // append one CSV line into the buffer
    size_t space = sizeof(outbuf) - olen;
    int n = snprintf(outbuf + olen, space, "%u,%.2f\n", t_ms, alpha);

    if (n < 0) {
      // formatting failed; skip this sample
    } else if ((size_t)n >= space) {
      // buffer full
      client.write((const uint8_t*)outbuf, olen);
      olen = 0;
      lastFlushMs = millis();

      // reformat into empty buffer (should fit now)
      n = snprintf(outbuf, sizeof(outbuf), "%u,%.2f\n", t_ms, alpha);
      if (n > 0) olen = (size_t)n;
    } else {
      olen += (size_t)n;
    }

    // flush if buffer is chunky OR every ~20 ms to keep latency low
    if (olen >= 256 || (millis() - lastFlushMs) >= 20) {
      client.write((const uint8_t*)outbuf, olen);
      olen = 0;
      lastFlushMs = millis();
      lastActivityMs = lastFlushMs;  // activity for your timeout watchdog
    }
  } else {
    // no client; make sure buffer doesn’t grow stale
    olen = 0;
  }

}
