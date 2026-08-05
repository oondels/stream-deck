#pragma once

#include "ports/control_inputs.h"

namespace streamdeck::infrastructure::esp32 {

class Esp32Inputs final : public ports::ControlInputs {
 public:
  void begin();
  bool button_pressed(std::size_t index) const override;
  bool encoder_a_high() const override;
  bool encoder_b_high() const override;
};

}  // namespace streamdeck::infrastructure::esp32
