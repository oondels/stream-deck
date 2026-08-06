#pragma once

#include <array>
#include <cstdint>

namespace streamdeck::config::profile {

inline constexpr const char* kBoardName = "esp32";
inline constexpr std::array<std::uint8_t, 8> kButtonPins{
    13, 14, 16, 17, 18, 19, 21, 25,
};
inline constexpr std::uint8_t kEncoderAPin = 22;
inline constexpr std::uint8_t kEncoderBPin = 23;
inline constexpr std::uint8_t kFutureLedPin = 26;

}  // namespace streamdeck::config::profile
