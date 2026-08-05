#include "domain/input_event.h"

namespace streamdeck::domain {

const char* control_name(ControlId control) {
  switch (control) {
    case ControlId::Key1: return "key_1";
    case ControlId::Key2: return "key_2";
    case ControlId::Key3: return "key_3";
    case ControlId::Key4: return "key_4";
    case ControlId::Key5: return "key_5";
    case ControlId::Key6: return "key_6";
    case ControlId::Key7: return "key_7";
    case ControlId::EncoderClockwise: return "encoder_cw";
    case ControlId::EncoderCounterClockwise: return "encoder_ccw";
    case ControlId::EncoderPress: return "encoder_press";
  }
  return "unknown";
}

const char* event_name(EventKind kind) {
  switch (kind) {
    case EventKind::Press: return "press";
    case EventKind::Release: return "release";
    case EventKind::Rotate: return "rotate";
  }
  return "unknown";
}

}  // namespace streamdeck::domain
