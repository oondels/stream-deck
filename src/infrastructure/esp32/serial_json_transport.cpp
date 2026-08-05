#include "infrastructure/esp32/serial_json_transport.h"

#include <Arduino.h>
#include <ArduinoJson.h>

#include "config/board_profile.h"
#include "domain/input_event.h"

namespace streamdeck::infrastructure::esp32 {

void SerialJsonTransport::begin() { Serial.begin(config::kBaudRate); }

bool SerialJsonTransport::probe_requested() {
  bool requested = false;
  while (Serial.available() > 0) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\r') {
      continue;
    }
    if (value == '\n') {
      if (!discarding_line_) {
        line_[line_length_] = '\0';
        requested = consume_line() || requested;
      }
      line_length_ = 0;
      discarding_line_ = false;
      continue;
    }
    if (discarding_line_) {
      continue;
    }
    if (line_length_ < kMaxLineLength) {
      line_[line_length_++] = value;
    } else {
      line_length_ = 0;
      discarding_line_ = true;
    }
  }
  return requested;
}

bool SerialJsonTransport::consume_line() {
  JsonDocument document;
  if (deserializeJson(document, line_, line_length_)) {
    return false;
  }
  return document["v"].is<int>() && document["v"].as<int>() == 1 &&
         document["type"].is<const char*>() &&
         strcmp(document["type"].as<const char*>(), "probe") == 0;
}

void SerialJsonTransport::publish_hello() {
  JsonDocument document;
  document["v"] = 1;
  document["type"] = "hello";
  document["device"] = "stream-deck-mini";
  document["board"] = "esp32";
  document["firmware"] = "0.1.0";
  serializeJson(document, Serial);
  Serial.write('\n');
}

void SerialJsonTransport::publish_input(const domain::InputEvent& event) {
  JsonDocument document;
  document["v"] = 1;
  document["type"] = "input";
  document["control"] = domain::control_name(event.control);
  document["event"] = domain::event_name(event.kind);
  document["seq"] = event.sequence;
  document["uptime_ms"] = event.uptime_ms;
  serializeJson(document, Serial);
  Serial.write('\n');
}

}  // namespace streamdeck::infrastructure::esp32
