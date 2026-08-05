#pragma once

#include "ports/clock.h"

namespace streamdeck::infrastructure::esp32 {

class ArduinoClock final : public ports::Clock {
 public:
  std::uint32_t milliseconds() const override;
};

}  // namespace streamdeck::infrastructure::esp32
