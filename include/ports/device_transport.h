#pragma once

#include "domain/input_event.h"

namespace streamdeck::ports {

class DeviceTransport {
 public:
  virtual ~DeviceTransport() = default;
  virtual bool probe_requested() = 0;
  virtual void publish_hello() = 0;
  virtual void publish_input(const domain::InputEvent& event) = 0;
};

}  // namespace streamdeck::ports
