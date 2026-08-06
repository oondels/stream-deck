#pragma once

#include <cstdint>

#if defined(STREAMDECK_BOARD_ESP32_C3)
#include "config/profiles/esp32_c3_compact.h"
#else
#include "config/profiles/esp32_wroom_32u.h"
#endif

namespace streamdeck::config {

inline constexpr auto kBoardName = profile::kBoardName;
inline constexpr auto kButtonPins = profile::kButtonPins;
inline constexpr auto kEncoderAPin = profile::kEncoderAPin;
inline constexpr auto kEncoderBPin = profile::kEncoderBPin;
inline constexpr auto kFutureLedPin = profile::kFutureLedPin;
inline constexpr std::uint32_t kBaudRate = 115200;
inline constexpr std::uint32_t kDebounceMs = 30;
inline constexpr std::size_t kPhysicalButtonCount = kButtonPins.size();

static_assert(kPhysicalButtonCount == 8,
              "profile must define seven keys and encoder press");

}  // namespace streamdeck::config
