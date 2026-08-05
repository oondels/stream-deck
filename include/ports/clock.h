#pragma once

#include <cstdint>

namespace streamdeck::ports {

class Clock {
 public:
  virtual ~Clock() = default;
  virtual std::uint32_t milliseconds() const = 0;
};

}  // namespace streamdeck::ports
