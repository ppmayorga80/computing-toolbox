"""testing cprint functions"""
import os

import art

from computing_toolbox.utils.cprint import CPrint


def test_output_buffering():
    """test output buffering flag"""
    CPrint.output_buffering(flag=True)
    assert os.environ.get("PYTHONUNBUFFERED") is None

    CPrint.output_buffering(flag=False)
    assert os.environ.get("PYTHONUNBUFFERED") == "1"


def test_print_functions(capsys):
    """test all print functions"""
    msg = "hello, world"
    end = "\n"

    # print normal mode
    CPrint.print(mode="std", text=msg, end=end)
    captured = capsys.readouterr()
    assert captured.out == f"{msg}{end}"

    # print warning, error, info and success modes, `endswith` because color prints
    # starts with special characters defining the colors...
    for mode in ("war", "err", "inf", "suc"):
        CPrint.print(mode=mode, text=msg, end=end)
        captured = capsys.readouterr()
        assert captured.err.endswith(f"{msg}{end}")

    # test ascii-art messages
    lines = art.text2art(msg)
    CPrint.print(mode="std", text=msg, ascii_art=True)
    captured = capsys.readouterr()
    output_lines = captured.out
    lines_as_list = lines.split("\n")
    output_lines_as_list = output_lines.split("\n")
    responses = [
        o.endswith(f"{m}") for o, m in zip(output_lines_as_list, lines_as_list)
    ]
    assert all(responses)
