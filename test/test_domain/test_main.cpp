#include <array>
#include <vector>

#include <unity.h>

#include "application/deck_application.h"
#include "domain/debounced_switch.h"
#include "domain/quadrature_encoder.h"

using streamdeck::application::DeckApplication;
using streamdeck::domain::ControlId;
using streamdeck::domain::DebouncedSwitch;
using streamdeck::domain::InputEvent;
using streamdeck::domain::QuadratureEncoder;
using streamdeck::domain::RotationDirection;
using streamdeck::domain::SwitchTransition;

namespace {

class FakeClock final : public streamdeck::ports::Clock {
 public:
  std::uint32_t milliseconds() const override { return now; }
  std::uint32_t now{0};
};

class FakeInputs final : public streamdeck::ports::ControlInputs {
 public:
  bool button_pressed(std::size_t index) const override {
    return buttons[index];
  }
  bool encoder_a_high() const override { return encoder_a; }
  bool encoder_b_high() const override { return encoder_b; }

  std::array<bool, DeckApplication::kButtonCount> buttons{};
  bool encoder_a{false};
  bool encoder_b{false};
};

class FakeTransport final : public streamdeck::ports::DeviceTransport {
 public:
  bool probe_requested() override {
    const bool value = probe;
    probe = false;
    return value;
  }
  void publish_hello() override { ++hello_count; }
  void publish_input(const InputEvent& event) override {
    events.push_back(event);
  }

  bool probe{false};
  int hello_count{0};
  std::vector<InputEvent> events;
};

void test_debounce_requires_stable_interval() {
  DebouncedSwitch input(30);
  SwitchTransition transition{};
  TEST_ASSERT_FALSE(input.update(false, 0, transition));
  TEST_ASSERT_FALSE(input.update(true, 1, transition));
  TEST_ASSERT_FALSE(input.update(false, 10, transition));
  TEST_ASSERT_FALSE(input.update(true, 20, transition));
  TEST_ASSERT_FALSE(input.update(true, 49, transition));
  TEST_ASSERT_TRUE(input.update(true, 50, transition));
  TEST_ASSERT_EQUAL(static_cast<int>(SwitchTransition::Pressed),
                    static_cast<int>(transition));
  TEST_ASSERT_FALSE(input.update(true, 100, transition));
}

void test_debounce_handles_millis_wraparound() {
  DebouncedSwitch input(30);
  SwitchTransition transition{};
  TEST_ASSERT_FALSE(input.update(false, 0xFFFFFFE0U, transition));
  TEST_ASSERT_FALSE(input.update(true, 0xFFFFFFF0U, transition));
  TEST_ASSERT_TRUE(input.update(true, 0x0000000EU, transition));
  TEST_ASSERT_EQUAL(static_cast<int>(SwitchTransition::Pressed),
                    static_cast<int>(transition));
}

void test_debounce_reports_button_held_during_boot() {
  DebouncedSwitch input(30);
  SwitchTransition transition{};
  TEST_ASSERT_FALSE(input.update(true, 100, transition));
  TEST_ASSERT_TRUE(input.update(true, 130, transition));
  TEST_ASSERT_EQUAL(static_cast<int>(SwitchTransition::Pressed),
                    static_cast<int>(transition));
}

void test_encoder_emits_once_per_complete_detent() {
  QuadratureEncoder encoder;
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(false, false)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(true, false)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(true, true)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(false, true)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::Clockwise),
                    static_cast<int>(encoder.update(false, false)));
}

void test_encoder_rejects_invalid_jump() {
  QuadratureEncoder encoder;
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(false, false)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(true, true)));
  TEST_ASSERT_EQUAL(static_cast<int>(RotationDirection::None),
                    static_cast<int>(encoder.update(false, false)));
}

void test_application_publishes_debounced_event_and_probe_response() {
  FakeInputs inputs;
  FakeClock clock;
  FakeTransport transport;
  DeckApplication app(inputs, clock, transport, 30);

  app.start();
  TEST_ASSERT_EQUAL(1, transport.hello_count);
  app.tick();

  inputs.buttons[0] = true;
  clock.now = 1;
  app.tick();
  clock.now = 31;
  app.tick();

  TEST_ASSERT_EQUAL_UINT32(1, transport.events.size());
  TEST_ASSERT_EQUAL(static_cast<int>(ControlId::Key1),
                    static_cast<int>(transport.events[0].control));
  TEST_ASSERT_EQUAL_UINT32(1, transport.events[0].sequence);
  TEST_ASSERT_EQUAL_UINT32(31, transport.events[0].uptime_ms);

  transport.probe = true;
  app.tick();
  TEST_ASSERT_EQUAL(2, transport.hello_count);
}

}  // namespace

void setUp() {}
void tearDown() {}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_debounce_requires_stable_interval);
  RUN_TEST(test_debounce_handles_millis_wraparound);
  RUN_TEST(test_debounce_reports_button_held_during_boot);
  RUN_TEST(test_encoder_emits_once_per_complete_detent);
  RUN_TEST(test_encoder_rejects_invalid_jump);
  RUN_TEST(test_application_publishes_debounced_event_and_probe_response);
  return UNITY_END();
}
