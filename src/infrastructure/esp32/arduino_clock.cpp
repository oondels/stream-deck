#include "infrastructure/esp32/arduino_clock.h"

#include <Arduino.h>

namespace streamdeck::infrastructure::esp32 {

std::uint32_t ArduinoClock::milliseconds() const { return millis(); }

}  // namespace streamdeck::infrastructure::esp32
