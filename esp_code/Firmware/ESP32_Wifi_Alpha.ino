//READ ME
//Wifi losing and connection protocals arn't amazing at the moment so if anything goes wrong push the reset button on the ESP32 
//Make sure to add your wifi settings and parameters :)
//self note consider advancing t_ms via dt_us so it stays exact at any rate

#include <WiFi.h>
#include "signal_gen.h"
#include "sd_stream.h"     
#include <Preferences.h>

// ---- Provisioned WiFi Settings (set over USB Serial) ----
Preferences prefs;
static const uint16_t DEFAULT_PORT = 9000; //This will be dynamic 
static const uint32_t SETUP_WINDOW_MS = 8000; // 8 sec to accept WIFI command at boot


static String g_ssid = "";
static String g_pass = "";
static uint16_t g_port = DEFAULT_PORT;


// -------- Sample Rate ---------
const float fs = 250.0f;  // 250 Hz sample rate so its like 4ms per sample 
const uint32_t dt_us = (uint32_t)(1e6 / fs);

// ------- Signal Type ---------
#define USE_SYNTH_ALPHA 0 //Toggle for the alpha generator for debugging

#define USE_SD_STREAM 1   // set to 0 to disable SD streaming

// Signal params
// fs is the sample rate of the esp32 make sure to set it!
const float f_alpha = 10.0f; // 10 Hz frequency
const float alpha_amp = 50.0f;  // amplitude (arbitrary µV it will eventually be information from the ADS1229)

// Timekeeping holding variables for sample pacing
static uint32_t t0_us = 0;
static uint32_t t_ms  = 0;

// Streaming
// placeholder is DEFAULT_PORT; we restart it on g_port after provisioning
WiFiServer server(DEFAULT_PORT);
WiFiClient client;

// Batch send buffer
static char outbuf[512];
static size_t olen = 0;
static unsigned long lastFlushMs = 0;

//Wifi Connection Safety
unsigned long lastActivityMs = 0;   // last successful send time 
const unsigned long CLIENT_TIMEOUT_MS = 5000; // How long to wait before disconnecting

// COM Pinging for Bjon 


//WIFI Handshake!!!
static bool readSerialLine(char *out, size_t maxLen) {
  static char buf[256];
  static size_t len = 0;

  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      size_t n = (len < maxLen - 1) ? len : (maxLen - 1);
      memcpy(out, buf, n);
      out[n] = 0;
      len = 0;
      return true;
    }
    if (len < sizeof(buf) - 1) buf[len++] = c;
  }
  return false;
}

static String getKV(const char* line, const char* key) {
  // expects space-separated key=value, e.g. "WIFI ssid=abc pass=123 port=9000"
  String s(line);
  String k = String(key) + "=";
  int i = s.indexOf(k);
  if (i < 0) return "";
  i += k.length();
  int j = s.indexOf(' ', i);
  if (j < 0) j = s.length();
  return s.substring(i, j);
}

static void loadCreds() {
  prefs.begin("net", true);
  g_ssid = prefs.getString("ssid", "");
  g_pass = prefs.getString("pass", "");
  g_port = prefs.getUShort("port", DEFAULT_PORT);
  prefs.end();
}

static void saveCreds() {
  prefs.begin("net", false);
  prefs.putString("ssid", g_ssid);
  prefs.putString("pass", g_pass);
  prefs.putUShort("port", g_port);
  prefs.end();
}

static bool connectWifiBlocking(uint32_t timeout_ms = 15000) {
  if (g_ssid.length() == 0) return false;

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(g_ssid.c_str(), g_pass.c_str());

  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - t0) < timeout_ms) {
    delay(250);
  }
  return (WiFi.status() == WL_CONNECTED);
}

static void startServerOnPort(uint16_t port) {
  server.stop();
  server = WiFiServer(port);
  server.begin();
}


void setup() {
  Serial.begin(115200);
  delay(200);
  
  sg_config(f_alpha, alpha_amp); // Configer signal generator
  
  // SD bring-up + open your CSV
  if (!sdstream_init(/*CS=*/5, /*SCK=*/18, /*MISO=*/19, /*MOSI=*/23, /*SPI Hz=*/16000000)) {
    Serial.println("SD mount failed");
  }
  if (!sdstream_open("/AndyAlphaWaveDataCSV.csv", /*loop=*/true)) { // This has true or false for repeating the data over and over
    Serial.println("Open /AndyAlphaWaveDataCSV.csv failed");
  }

// Wifi Set up 
// ---- Provisioning / auto-connect ----
loadCreds();

Serial.println("# Provision over USB Serial:");
Serial.printf("# WIFI ssid=YOURSSID pass=YOURPASS port=%u\n", DEFAULT_PORT);
Serial.println("# Commands: STATUS, CLEAR");

bool connected = false;
bool haveCreds = (g_ssid.length() > 0);

uint32_t t_setup = millis();

// 1) Setup window: listen for WIFI command for a few seconds
while ((millis() - t_setup) < SETUP_WINDOW_MS) {
  char line[200];
  if (readSerialLine(line, sizeof(line))) {

    if (!strncmp(line, "WIFI ", 5)) {
      String ssid = getKV(line, "ssid");
      String pass = getKV(line, "pass");
      String port = getKV(line, "port");

      if (ssid.length() == 0 || port.length() == 0) {
        Serial.println("ERR missing_fields");
      } else {
        g_ssid = ssid;
        g_pass = pass;
        g_port = (uint16_t)port.toInt();
        saveCreds();
        haveCreds = true;
        Serial.println("OK saved");

        connected = connectWifiBlocking();
        if (!connected) Serial.println("ERR wifi_failed");
        else break;
      }
    }

    else if (!strcmp(line, "STATUS")) {
      Serial.printf("OK status ssid=%s ip=%s port=%u\n",
        g_ssid.c_str(),
        (WiFi.status()==WL_CONNECTED ? WiFi.localIP().toString().c_str() : "0.0.0.0"),
        g_port);
    }

    else if (!strcmp(line, "CLEAR")) {
      prefs.begin("net", false);
      prefs.clear();
      prefs.end();
      g_ssid = ""; g_pass = ""; g_port = DEFAULT_PORT;
      haveCreds = false;
      Serial.println("OK cleared");
    }

    else {
      Serial.println("ERR unknown_cmd");
    }
  }
  delay(10);
}

// 2) If not connected yet, try saved creds
if (!connected && haveCreds) {
  Serial.println("# Auto-connect...");
  connected = connectWifiBlocking();
  if (!connected) Serial.println("ERR wifi_failed");
}

// 3) If still not connected, wait forever for WIFI command (first-time setup)
while (!connected) {
  char line[200];
  if (readSerialLine(line, sizeof(line))) {

    if (!strncmp(line, "WIFI ", 5)) {
      String ssid = getKV(line, "ssid");
      String pass = getKV(line, "pass");
      String port = getKV(line, "port");

      if (ssid.length() == 0 || port.length() == 0) {
        Serial.println("ERR missing_fields");
      } else {
        g_ssid = ssid;
        g_pass = pass;
        g_port = (uint16_t)port.toInt();
        saveCreds();
        Serial.println("OK saved");

        connected = connectWifiBlocking();
        if (!connected) Serial.println("ERR wifi_failed");
      }
    }

    else if (!strcmp(line, "STATUS")) {
      Serial.printf("OK status ssid=%s ip=%s port=%u\n",
        g_ssid.c_str(),
        (WiFi.status()==WL_CONNECTED ? WiFi.localIP().toString().c_str() : "0.0.0.0"),
        g_port);
    }

    else if (!strcmp(line, "CLEAR")) {
      prefs.begin("net", false);
      prefs.clear();
      prefs.end();
      g_ssid = ""; g_pass = ""; g_port = DEFAULT_PORT;
      Serial.println("OK cleared");
    }

    else {
      Serial.println("ERR unknown_cmd");
    }
  }
  delay(10);
}


Serial.println("\nConnected.");
Serial.print("ESP32 IP: "); Serial.println(WiFi.localIP());

// start TCP server on provisioned port
startServerOnPort(g_port);
Serial.printf("TCP server started on port %u. Waiting for a client...\n", g_port);

// Initialize Time
t0_us = micros();
t_ms  = 0;

}

void loop() {
  if (!client || !client.connected()) {
    WiFiClient possibleClient = server.available();
    if (possibleClient) {
      client = possibleClient;
      client.setNoDelay(true); // For real time streaming 
      Serial.println("Client connected.");

      #if USE_SD_STREAM
        if (sdstream_has_header()) client.print(sdstream_header());
        else client.println("# sd_stream");
      #else
        client.println("# t_ms,value"); //This is the header line for the data in python!
      #endif

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
 
  // Singal Retrival
  #if USE_SD_STREAM
    // Read one full line from the SD file and stream it verbatim this tick
    char line[256];
    size_t L = sdstream_next_line(line, sizeof(line));
    if (L > 0) {
      // append to your TCP outbuf
      size_t space = sizeof(outbuf) - olen;
      if (L >= space) {
        client.write((const uint8_t*)outbuf, olen);
        olen = 0;
        lastFlushMs = millis();
        space = sizeof(outbuf);
      }
      memcpy(outbuf + olen, line, L);
      olen += L;

      // same low-latency flush policy as before
      if (olen >= 256 || (millis() - lastFlushMs) >= 20) {
        client.write((const uint8_t*)outbuf, olen);
        olen = 0;
        lastFlushMs = millis();
        lastActivityMs = lastFlushMs;
      }
    }

  #else
    // Generate sine wave
    float alpha = 0.0f;
    #if USE_SYNTH_ALPHA
      alpha = sg_alpha_ms(t_ms);
    #else
      float t = t_ms / 1000.0f;
      alpha = alpha_amp * sinf(2 * PI * f_alpha * t);
    #endif

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
  #endif


}
