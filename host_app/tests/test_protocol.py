import pytest

from streamdeck_monitor.domain.messages import DeviceHello, InputEvent, ProtocolError
from streamdeck_monitor.infrastructure.protocol import JsonProtocolCodec


def test_decodes_hello_and_ignores_extra_fields() -> None:
    message = JsonProtocolCodec().decode_line(
        '{"v":1,"type":"hello","device":"stream-deck-mini",'
        '"board":"esp32","firmware":"0.1.0","future":true}'
    )
    assert message == DeviceHello(
        device="stream-deck-mini", board="esp32", firmware="0.1.0"
    )


@pytest.mark.parametrize(
    ("control", "event"),
    [
        ("key_1", "press"),
        ("key_7", "release"),
        ("encoder_press", "press"),
        ("encoder_cw", "rotate"),
        ("encoder_ccw", "rotate"),
    ],
)
def test_decodes_valid_input(control: str, event: str) -> None:
    message = JsonProtocolCodec().decode_line(
        f'{{"v":1,"type":"input","control":"{control}",'
        f'"event":"{event}","seq":4,"uptime_ms":900}}'
    )
    assert message == InputEvent(
        control=control, event=event, sequence=4, uptime_ms=900
    )


@pytest.mark.parametrize(
    "line",
    [
        "not-json",
        "[]",
        '{"v":2,"type":"hello","device":"stream-deck-mini","board":"esp32","firmware":"x"}',
        '{"v":1,"type":"input","control":"key_8","event":"press","seq":1,"uptime_ms":1}',
        '{"v":1,"type":"input","control":"encoder_cw","event":"press","seq":1,"uptime_ms":1}',
        '{"v":true,"type":"input","control":"key_1","event":"press","seq":1,"uptime_ms":1}',
    ],
)
def test_rejects_invalid_messages(line: str) -> None:
    with pytest.raises(ProtocolError):
        JsonProtocolCodec().decode_line(line)
