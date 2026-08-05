#pragma once

#include <cstddef>

#include "ports/device_transport.h"

namespace streamdeck::infrastructure::esp32 {

class SerialJsonTransport final : public ports::DeviceTransport {
 public:
  void begin();
  bool probe_requested() override;
  void publish_hello() override;
  void publish_input(const domain::InputEvent& event) override;

 private:
  static constexpr std::size_t kMaxLineLength = 255;
  bool consume_line();

  char line_[kMaxLineLength + 1]{};
  std::size_t line_length_{0};
  bool discarding_line_{false};
};

}  // namespace streamdeck::infrastructure::esp32
