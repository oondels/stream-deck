#include "domain/debounced_switch.h"

namespace streamdeck::domain {

DebouncedSwitch::DebouncedSwitch(std::uint32_t debounce_ms)
    : debounce_ms_(debounce_ms) {}

bool DebouncedSwitch::update(bool pressed, std::uint32_t now_ms,
                             SwitchTransition& transition) {
  if (!initialized_) {
    initialized_ = true;
    candidate_pressed_ = pressed;
    candidate_since_ms_ = now_ms;
    return false;
  }

  if (pressed != candidate_pressed_) {
    candidate_pressed_ = pressed;
    candidate_since_ms_ = now_ms;
    return false;
  }

  if (candidate_pressed_ == stable_pressed_ ||
      static_cast<std::uint32_t>(now_ms - candidate_since_ms_) < debounce_ms_) {
    return false;
  }

  stable_pressed_ = candidate_pressed_;
  transition = stable_pressed_ ? SwitchTransition::Pressed
                               : SwitchTransition::Released;
  return true;
}

bool DebouncedSwitch::is_pressed() const { return stable_pressed_; }

}  // namespace streamdeck::domain
