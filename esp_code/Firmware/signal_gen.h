#pragma once
#include <stdint.h>

// Configure the synthetic alpha generator once (call in setup)
void sg_config(float freq_hz, float amp_uv, float phase_rad = 0.0f);

// Get alpha value at time t_ms (milliseconds)
float sg_alpha_ms(uint32_t t_ms);
