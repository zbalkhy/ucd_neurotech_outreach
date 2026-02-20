#pragma once
#include <Arduino.h>

// Mount SD over SPI (VSPI pins). Call once in setup().
bool sdstream_init(int cs, int sck, int miso, int mosi, uint32_t spiHz = 16000000);

// Open the file to stream. If loop=true, it restarts at EOF (skips header after first pass).
bool sdstream_open(const char* path, bool loop);

// Returns true if a header line was found (first line of the file).
bool sdstream_has_header();

// Pointer to header text (without CR, ends with '\n'). Null if none.
const char* sdstream_header();

// Read the next full line (including '\n') into out. Returns number of bytes written, or 0 at EOF (when not looping).
size_t sdstream_next_line(char* out, size_t outcap);

// Close current file (optional).
void sdstream_close();
