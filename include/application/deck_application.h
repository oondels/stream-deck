#pragma once

#include <array>
#include <cstdint>

#include "domain/debounced_switch.h"
#include "domain/quadrature_encoder.h"
#include "ports/clock.h"
#include "ports/control_inputs.h"
#include "ports/device_transport.h"

namespace streamdeck::application {

class DeckApplication {
 public:
  static constexpr std::size_t kButtonCount = 8;

  DeckApplication(ports::ControlInputs& inputs, ports::Clock& clock,
                  ports::DeviceTransport& transport,
                  std::uint32_t debounce_ms = 30);

  void start();
  void tick();

 private:
  void scan_buttons(std::uint32_t now_ms);
  void scan_encoder(std::uint32_t now_ms);
  void emit(domain::ControlId control, domain::EventKind kind,
            std::uint32_t now_ms);
  static domain::ControlId button_control(std::size_t index);

  ports::ControlInputs& inputs_;
  ports::Clock& clock_;
  ports::DeviceTransport& transport_;
  std::array<domain::DebouncedSwitch, kButtonCount> buttons_;
  domain::QuadratureEncoder encoder_;
  std::uint32_t next_sequence_{1};
};

}  // namespace streamdeck::application
