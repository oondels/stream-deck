#pragma once

#include <array>
#include <cstdint>

namespace streamdeck::config::profile {

// GPIO18/19 are connected internally to native USB. GPIO2, GPIO8 and GPIO9
// are strapping pins and are intentionally not used as control inputs.
inline constexpr const char* kBoardName = "esp32-c3";
inline constexpr std::array<std::uint8_t, 8> kButtonPins{
    0, 1, 3, 4, 5, 6, 7, 10,
};
inline constexpr std::uint8_t kEncoderAPin = 20;
inline constexpr std::uint8_t kEncoderBPin = 21;
inline constexpr std::uint8_t kFutureLedPin = 8;

}  // namespace streamdeck::config::profile
