#include <Arduino.h>

#include "application/deck_application.h"
#include "config/board_profile.h"
#include "infrastructure/esp32/arduino_clock.h"
#include "infrastructure/esp32/esp32_inputs.h"
#include "infrastructure/esp32/serial_json_transport.h"

namespace {

streamdeck::infrastructure::esp32::Esp32Inputs inputs;
streamdeck::infrastructure::esp32::ArduinoClock clock_source;
streamdeck::infrastructure::esp32::SerialJsonTransport transport;
streamdeck::application::DeckApplication application(
    inputs, clock_source, transport, streamdeck::config::kDebounceMs);

}  // namespace

void setup() {
  inputs.begin();
  transport.begin();
  application.start();
}

void loop() {
  application.tick();
  yield();
}
