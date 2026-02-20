#include "signal_gen.h"
#include <math.h>

#ifndef PI
#define PI 3.14159265358979323846f
#endif

static float g_freq  = 10.0f;
static float g_amp   = 50.0f;
static float g_phase = 0.0f;

void sg_config(float freq_hz, float amp_uv, float phase_rad) {
  g_freq  = freq_hz;
  g_amp   = amp_uv;
  g_phase = phase_rad;
}

float sg_alpha_ms(uint32_t t_ms) {
  const float t_s = 0.001f * (float)t_ms;                  // ms → seconds
  return g_amp * sinf(2.0f * PI * g_freq * t_s + g_phase);
}
