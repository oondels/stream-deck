#include "application/deck_application.h"

namespace streamdeck::application {

DeckApplication::DeckApplication(ports::ControlInputs& inputs,
                                 ports::Clock& clock,
                                 ports::DeviceTransport& transport,
                                 std::uint32_t debounce_ms)
    : inputs_(inputs),
      clock_(clock),
      transport_(transport),
      buttons_{domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms),
               domain::DebouncedSwitch(debounce_ms)} {}

void DeckApplication::start() { transport_.publish_hello(); }

void DeckApplication::tick() {
  if (transport_.probe_requested()) {
    transport_.publish_hello();
  }
  const auto now_ms = clock_.milliseconds();
  scan_buttons(now_ms);
  scan_encoder(now_ms);
}

void DeckApplication::scan_buttons(std::uint32_t now_ms) {
  for (std::size_t index = 0; index < buttons_.size(); ++index) {
    domain::SwitchTransition transition{};
    if (!buttons_[index].update(inputs_.button_pressed(index), now_ms,
                                transition)) {
      continue;
    }
    emit(button_control(index),
         transition == domain::SwitchTransition::Pressed
             ? domain::EventKind::Press
             : domain::EventKind::Release,
         now_ms);
  }
}

void DeckApplication::scan_encoder(std::uint32_t now_ms) {
  const auto direction =
      encoder_.update(inputs_.encoder_a_high(), inputs_.encoder_b_high());
  if (direction == domain::RotationDirection::Clockwise) {
    emit(domain::ControlId::EncoderClockwise, domain::EventKind::Rotate,
         now_ms);
  } else if (direction == domain::RotationDirection::CounterClockwise) {
    emit(domain::ControlId::EncoderCounterClockwise,
         domain::EventKind::Rotate, now_ms);
  }
}

void DeckApplication::emit(domain::ControlId control, domain::EventKind kind,
                           std::uint32_t now_ms) {
  transport_.publish_input({control, kind, next_sequence_++, now_ms});
}

domain::ControlId DeckApplication::button_control(std::size_t index) {
  static constexpr std::array<domain::ControlId, kButtonCount> kControls{
      domain::ControlId::Key1,
      domain::ControlId::Key2,
      domain::ControlId::Key3,
      domain::ControlId::Key4,
      domain::ControlId::Key5,
      domain::ControlId::Key6,
      domain::ControlId::Key7,
      domain::ControlId::EncoderPress,
  };
  return kControls[index];
}

}  // namespace streamdeck::application
