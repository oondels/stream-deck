#pragma once

#include <cstdint>

namespace streamdeck::domain {

enum class RotationDirection : std::int8_t {
  None = 0,
  Clockwise = 1,
  CounterClockwise = -1,
};

class QuadratureEncoder {
 public:
  RotationDirection update(bool channel_a_high, bool channel_b_high);

 private:
  bool initialized_{false};
  std::uint8_t previous_state_{0};
  std::int8_t accumulator_{0};
};

}  // namespace streamdeck::domain
