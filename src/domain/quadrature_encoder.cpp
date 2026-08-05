#include "domain/quadrature_encoder.h"

namespace streamdeck::domain {

RotationDirection QuadratureEncoder::update(bool channel_a_high,
                                             bool channel_b_high) {
  const auto current_state = static_cast<std::uint8_t>(
      (channel_a_high ? 0b10 : 0) | (channel_b_high ? 0b01 : 0));

  if (!initialized_) {
    initialized_ = true;
    previous_state_ = current_state;
    return RotationDirection::None;
  }

  static constexpr std::int8_t kTransitionDelta[16] = {
      0, -1, 1, 0,
      1, 0, 0, -1,
      -1, 0, 0, 1,
      0, 1, -1, 0,
  };

  const auto transition = static_cast<std::uint8_t>(
      (previous_state_ << 2U) | current_state);
  const auto delta = kTransitionDelta[transition];
  previous_state_ = current_state;

  if (delta == 0) {
    if ((transition & 0b0011U) == ((transition >> 2U) & 0b0011U)) {
      return RotationDirection::None;
    }
    accumulator_ = 0;
    return RotationDirection::None;
  }

  accumulator_ = static_cast<std::int8_t>(accumulator_ + delta);
  if (accumulator_ >= 4) {
    accumulator_ = 0;
    return RotationDirection::Clockwise;
  }
  if (accumulator_ <= -4) {
    accumulator_ = 0;
    return RotationDirection::CounterClockwise;
  }
  return RotationDirection::None;
}

}  // namespace streamdeck::domain
