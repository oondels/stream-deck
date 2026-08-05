#include "infrastructure/esp32/esp32_inputs.h"

#include <Arduino.h>

#include "config/board_profile.h"

namespace streamdeck::infrastructure::esp32 {

void Esp32Inputs::begin() {
  for (const auto pin : config::kButtonPins) {
    pinMode(pin, INPUT_PULLUP);
  }
  pinMode(config::kEncoderAPin, INPUT_PULLUP);
  pinMode(config::kEncoderBPin, INPUT_PULLUP);
}

bool Esp32Inputs::button_pressed(std::size_t index) const {
  return index < config::kButtonPins.size() &&
         digitalRead(config::kButtonPins[index]) == LOW;
}

bool Esp32Inputs::encoder_a_high() const {
  return digitalRead(config::kEncoderAPin) == HIGH;
}

bool Esp32Inputs::encoder_b_high() const {
  return digitalRead(config::kEncoderBPin) == HIGH;
}

}  // namespace streamdeck::infrastructure::esp32
