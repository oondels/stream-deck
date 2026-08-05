#pragma once

#include <cstdint>

namespace streamdeck::domain {

enum class SwitchTransition : std::uint8_t { Pressed, Released };

class DebouncedSwitch {
 public:
  explicit DebouncedSwitch(std::uint32_t debounce_ms = 30);

  bool update(bool pressed, std::uint32_t now_ms, SwitchTransition& transition);
  bool is_pressed() const;

 private:
  std::uint32_t debounce_ms_;
  std::uint32_t candidate_since_ms_{0};
  bool initialized_{false};
  bool stable_pressed_{false};
  bool candidate_pressed_{false};
};

}  // namespace streamdeck::domain
