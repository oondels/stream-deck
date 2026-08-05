#pragma once

#include <cstddef>

namespace streamdeck::ports {

class ControlInputs {
 public:
  virtual ~ControlInputs() = default;
  virtual bool button_pressed(std::size_t index) const = 0;
  virtual bool encoder_a_high() const = 0;
  virtual bool encoder_b_high() const = 0;
};

}  // namespace streamdeck::ports
