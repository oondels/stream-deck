#pragma once

#include <array>
#include <cstdint>

namespace streamdeck::config {

inline constexpr std::array<std::uint8_t, 8> kButtonPins{
    13, 14, 16, 17, 18, 19, 21, 25,
};
inline constexpr std::uint8_t kEncoderAPin = 22;
inline constexpr std::uint8_t kEncoderBPin = 23;
inline constexpr std::uint8_t kFutureLedPin = 26;
inline constexpr std::uint32_t kBaudRate = 115200;
inline constexpr std::uint32_t kDebounceMs = 30;
inline constexpr std::size_t kPhysicalButtonCount = kButtonPins.size();

}  // namespace streamdeck::config
