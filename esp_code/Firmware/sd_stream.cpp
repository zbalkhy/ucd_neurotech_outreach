#include "sd_stream.h"
#include <SPI.h>
#include <SD.h>

static int      g_cs=5, g_sck=18, g_miso=19, g_mosi=23;
static uint32_t g_spiHz = 16000000;

static File  g_file;
static bool  g_loop   = false;
static bool  g_inited = false;

static char  g_path[64] = {0};

static char  g_header[256];
static bool  g_has_header = false;

static const size_t READBUF_SZ = 512;
static uint8_t rbuf[READBUF_SZ];
static size_t  rpos = 0, rlen = 0;

static bool refill() {
  if (!g_file) return false;
  rlen = g_file.read(rbuf, READBUF_SZ);
  rpos = 0;
  return rlen > 0;
}

static bool read_line_into(char* out, size_t outcap, size_t& outlen) {
  outlen = 0;
  for (;;) {
    if (rpos >= rlen) {
      if (!refill()) return false; // EOF / no more data
    }
    uint8_t b = rbuf[rpos++];
    if (b == '\n') {
      // trim trailing CR
      while (outlen && out[outlen - 1] == '\r') outlen--;
      if (outlen < outcap - 1) out[outlen++] = '\n';
      out[outlen] = '\0';
      return true;
    } else {
      if (outlen < outcap - 1) out[outlen++] = (char)b; // discard overflow until newline
    }
  }
}

bool sdstream_init(int cs, int sck, int miso, int mosi, uint32_t spiHz) {
  g_cs = cs; g_sck = sck; g_miso = miso; g_mosi = mosi; g_spiHz = spiHz;
  SPI.begin(g_sck, g_miso, g_mosi, g_cs);
  if (!SD.begin(g_cs, SPI, g_spiHz)) return false;
  g_inited = true;
  return true;
}

bool sdstream_open(const char* path, bool loop) {
  if (!g_inited) return false;
  if (g_file) g_file.close();

  strncpy(g_path, path, sizeof(g_path) - 1);
  g_path[sizeof(g_path) - 1] = '\0';

  g_file = SD.open(g_path, FILE_READ);
  g_loop = loop;
  rpos = rlen = 0;
  g_has_header = false;

  if (!g_file) return false;

  // Read first line as header (optional)
  size_t hlen = 0;
  if (read_line_into(g_header, sizeof(g_header), hlen)) {
    g_has_header = true;
  }
  return true;
}

bool sdstream_has_header() { return g_has_header; }
const char* sdstream_header() { return g_has_header ? g_header : nullptr; }

size_t sdstream_next_line(char* out, size_t outcap) {
  if (!g_file) return 0;

  size_t len = 0;
  if (read_line_into(out, outcap, len)) return len;

  // EOF
  if (g_loop) {
    g_file.close();
    g_file = SD.open(g_path, FILE_READ);
    rpos = rlen = 0;

    // Skip header on subsequent loops
    size_t dummy = 0;
    (void)read_line_into(g_header, sizeof(g_header), dummy);

    // Try to read the first data line
    if (read_line_into(out, outcap, len)) return len;
  }
  return 0;
}

void sdstream_close() { if (g_file) g_file.close(); }
