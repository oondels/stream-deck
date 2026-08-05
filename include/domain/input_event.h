#pragma once

#include <cstdint>

namespace streamdeck::domain {

enum class ControlId : std::uint8_t {
  Key1,
  Key2,
  Key3,
  Key4,
  Key5,
  Key6,
  Key7,
  EncoderClockwise,
  EncoderCounterClockwise,
  EncoderPress,
};

enum class EventKind : std::uint8_t { Press, Release, Rotate };

struct InputEvent {
  ControlId control;
  EventKind kind;
  std::uint32_t sequence;
  std::uint32_t uptime_ms;
};

const char* control_name(ControlId control);
const char* event_name(EventKind kind);

}  // namespace streamdeck::domain
