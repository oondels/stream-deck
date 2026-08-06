from streamdeck_monitor.gui.bootstrap import build_parser, main


def test_gui_parser_accepts_minimized() -> None:
    assert build_parser().parse_args(["--minimized"]).minimized


def test_gui_reports_missing_dependency(monkeypatch, capsys) -> None:
    def fail_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "streamdeck_monitor.gui.application":
            error = ModuleNotFoundError("No module named 'PySide6'")
            error.name = "PySide6"
            raise error
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fail_import)

    assert main([]) == 2
    assert "gui" in capsys.readouterr().err.lower()
