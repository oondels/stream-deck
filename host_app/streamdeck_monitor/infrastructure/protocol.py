from __future__ import annotations

import json

from streamdeck_monitor.domain.messages import (
    DeviceMessage,
    ProtocolError,
    decode_mapping,
)


class JsonProtocolCodec:
    def encode_probe(self) -> str:
        return '{"v":1,"type":"probe"}'

    def decode_line(self, line: str) -> DeviceMessage:
        try:
            data = json.loads(line)
        except json.JSONDecodeError as error:
            raise ProtocolError(f"invalid JSON: {error.msg}") from error
        if not isinstance(data, dict):
            raise ProtocolError("message must be a JSON object")
        return decode_mapping(data)
