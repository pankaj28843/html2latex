import pytest

from html2latex.utils import output_message


def test_warning_message(capsys):
    output_message.warning_message("Heads up")
    captured = capsys.readouterr()
    assert "WARNING: Heads up" in captured.err
    assert captured.out == ""


def test_information_message(capsys):
    output_message.information_message("FYI")
    captured = capsys.readouterr()
    assert "INFO: FYI" in captured.err


def test_error_message_no_terminate(capsys):
    output_message.error_message("Boom", terminate=False)
    captured = capsys.readouterr()
    assert "ERROR: Boom" in captured.err


def test_error_message_terminate():
    with pytest.raises(SystemExit):
        output_message.error_message("Stop", terminate=True)
