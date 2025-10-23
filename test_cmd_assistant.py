import pytest
import io
import json
from pathlib import Path
from typing import Generator
import argparse

from abbreviation import abbreviation
from command_data import CommandData, CommandSession, SessionManager
from assistant import Assistant
from ollamaapi import query_ollama
from shell import *
from cli import get_arg_parser


def test_session_save(tmp_path: Path) -> None:
    session = CommandSession(id=0, prompt="Hello", save_dir=str(tmp_path), 
                             commands=[CommandData(command="fake command", stdin="fake output", ai_response="OK")],
                             context=[])
    session.save()

    path = tmp_path / "session.0.json"
    session_dict = json.loads(path.read_text(encoding="utf-8"))
    assert session_dict["id"] == 0
    assert session_dict["prompt"] == "Hello"
    assert session_dict["save_dir"] == str(tmp_path)
    assert session_dict["commands"][0]["command"] == "fake command"
    assert session_dict["commands"][0]["stdin"] == "fake output"
    assert session_dict["commands"][0]["ai_response"] == "OK"


def test_create_new_session(tmp_path: Path) -> None:
    (tmp_path / "dummydir").mkdir()
    (tmp_path / "dummyfile").touch()
    session_manager = SessionManager(tmp_path)
    session0 = session_manager.create_new_session("Hello")
    assert session0.id == 0
    session0_dict = json.loads((tmp_path / "session.0.json").read_text(encoding="utf-8"))
    assert session0_dict["id"] == 0
    for i in range(1, 5):
        (tmp_path / f"session.{i}.json").touch()
    session5 = session_manager.create_new_session("Hello")
    assert session5.id == 5
    session5_dict = json.loads((tmp_path / "session.5.json").read_text(encoding="utf-8"))
    assert session5_dict["id"] == 5


def test_find_most_recent_session(tmp_path: Path) -> None:
    session_manager = SessionManager(tmp_path)
    assert session_manager.find_most_recent_session() is None
    for _ in range(5):
        session_manager.create_new_session("Hello")
    most_recent_session_path = session_manager.find_most_recent_session()
    assert most_recent_session_path is not None
    assert most_recent_session_path.name == "session.4.json"
    assert session_manager.sessions[2].prompt is not None
    session_manager.sessions[2].prompt += " World!"
    session_manager.sessions[2].save()
    most_recent_session_path = session_manager.find_most_recent_session()
    assert most_recent_session_path is not None
    assert most_recent_session_path.name == f"session.{session_manager.sessions[2].id}.json"


def test_session_from_file(tmp_path: Path) -> None:
    session_manager = SessionManager(tmp_path)
    session = session_manager.create_new_session("Hello")
    loaded_session = CommandSession.from_file(tmp_path / session.filename)
    assert session == loaded_session
    for i in range(10):
        cmd = CommandData("Count for me.", "", f"{i}")
        session.commands.append(cmd)
    session.save()
    loaded_session = CommandSession.from_file(tmp_path / session.filename)
    assert session == loaded_session

    # Test of parser validation
    session_dict = json.loads((tmp_path / session.filename).read_text(encoding="utf-8"))
    session_dict["commands"] = {f'command_{i}': cmd for i, cmd in enumerate(session_dict["commands"])}
    (tmp_path / session.filename).write_text(json.dumps(session_dict), encoding="utf-8")
    with pytest.raises(TypeError):
        CommandSession.from_file(tmp_path / session.filename)

def mock_ai_api(prompt: str) -> Generator[str | list[int], None, None]:
        if "linux" in prompt:
            yield "response to linux"
        if "mock_command" in prompt:
            yield "response to mock_command"
        if "mock_stdin" in prompt:
            yield "response to mock_stdin"
        if "mock_ai_response" in prompt:
            yield "response to mock_ai_response"


def test_assistant_creation(tmp_path: Path) -> None:
    session_manager = SessionManager(path=tmp_path)
    assistant0 = Assistant(session_manager=session_manager, ai_api=mock_ai_api)
    assert (tmp_path / assistant0.session.filename).is_file()
    assistant1 = Assistant(session_manager=session_manager, ai_api=mock_ai_api)
    assert assistant0.session == assistant1.session


def test_assistant_load_session(tmp_path: Path) -> None:
    session_manager = SessionManager(path=tmp_path)
    session = session_manager.create_new_session()
    assistant = Assistant(session_manager, session.id)
    assert session == assistant.session


def test_assistant_new_command(tmp_path: Path) -> None:
    session_manager = SessionManager(path=tmp_path)
    assistant = Assistant(session_manager=session_manager, ai_api=mock_ai_api)
    command = CommandData(command="mock_command", stdin="mock_stdin", ai_response="")
    response = "".join([chunk for chunk in assistant.new_command(command)])
    most_recent_session = assistant.session_manager.load_most_recent_session()
    assert most_recent_session is not None
    if most_recent_session is not None:
        assert most_recent_session.commands[-1].ai_response == response
    assert "mock_command" in response
    assert "mock_stdin" in response

    response = "".join([chunk for chunk in assistant.new_command(command)])
    assert "linux" in assistant.session.commands[0].ai_response
    assert "mock_command" in assistant.session.commands[0].ai_response
    assert "mock_stdin" in assistant.session.commands[0].ai_response
    assert "linux" in response
    assert "mock_command" in response
    assert "mock_stdin" in response


# TODO: Mock the api call
def test_query_ollama() -> None:
    chunks = list(query_ollama("Repeat 'test' back to me once."))
    assert chunks
    with pytest.raises(IOError):
        list(query_ollama("Repeat 'test' back to me once.", url="http://localhost:11434/api/wrongendpoint"))


def test_print_ai_response(capsys: pytest.CaptureFixture[str]) -> None:
    print_ai_response(mock_ai_api("You are a linux command line assistant.\n"
                                  "Command:\n"
                                  "mock_command\n\n"
                                  "Stdin:\n"
                                  "mock_stdin\n\n"
                                  "Assistant:\n"
                                  "mock_ai_response\n"))
    captured = capsys.readouterr()
    output = captured.out.strip()
    assert "linux" in output
    assert "mock_command" in output
    assert "mock_stdin" in output
    assert "mock_ai_response" in output


def test_shell_with_pipe(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    monkeypatch.setenv("HISTORY", f"299  <fake command> | {abbreviation} --listen")
    command_output = "<fake command output>\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(command_output))
    assert shell(["--listen", "--path", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert command_output in captured.out


def test_shell_without_pipe(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    monkeypatch.setenv("HISTORY", f"300  {abbreviation} --listen")
    monkeypatch.setattr("sys.stdin", io.StringIO("<user request>\n"))
    assert shell(["--listen", "--path", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == welcome_message(0)


def test_shell_switch_session(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    session_manager = SessionManager(tmp_path)
    flag = "This is the switch session test"
    session = session_manager.create_new_session()
    session.commands.append(CommandData("<command>", "<stdin>", ai_response=flag))
    session.save()
    monkeypatch.setenv("HISTORY", f"301  {abbreviation} --listen")
    monkeypatch.setattr("sys.stdin", io.StringIO("<user request>\n")) 
    assert shell(["--listen", "--path", str(tmp_path), "--switch-session", str(session.id)]) == 0
    captured = capsys.readouterr()
    assert flag in captured.out.strip()


def test_shell_new_session(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    session_manager = SessionManager(tmp_path)
    flag = "This is the new session test"
    session = session_manager.create_new_session()
    session.commands.append(CommandData("<command>", "<stdin>", ai_response=flag))
    session.save()
    monkeypatch.setenv("HISTORY", f"302  {abbreviation} --listen")
    monkeypatch.setattr("sys.stdin", io.StringIO("<user request>\n")) 
    assert shell(["--listen", "--path", str(tmp_path), "--new-session"]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == welcome_message(1)
    assert sum(1 for f in tmp_path.iterdir() if f.is_file()) == 2


def test_missing_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HISTORY", raising=False)
    with pytest.raises(EnvironmentError):
        get_command_history()


@pytest.mark.parametrize("history_var", [
    "301 <fake command>  --listen",  # Too few spaces after index, red herring "  " later
    "3b2  <fake command>",  # Non-integer index
    "<fake command>",       # No index
])
def test_malformed_history(monkeypatch: pytest.MonkeyPatch, history_var: str) -> None:
    monkeypatch.setenv("HISTORY", history_var)
    with pytest.raises(EnvironmentError):
        parse_command_history(get_command_history())


@pytest.mark.parametrize("switch_session_arg", ["-10", "ls"])
def test_shell_invalid_switch_session_arg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, switch_session_arg: str) -> None:
    session_manager = SessionManager(tmp_path)
    session_manager.create_new_session()
    monkeypatch.setenv("HISTORY", f"303  {abbreviation} --listen")
    monkeypatch.setattr("sys.stdin", io.StringIO("<user request>\n")) 
    assert shell(["--listen", "--path", str(tmp_path), "--switch-session", "0"]) == 0
    with pytest.raises(argparse.ArgumentTypeError):
        shell(["--listen", "--path", str(tmp_path), "--switch-session", switch_session_arg])


def test_shell_verbose(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    monkeypatch.setenv("HISTORY", f"304  {abbreviation} --listen --verbose")
    monkeypatch.setattr("sys.stdin", io.StringIO("<user request>\n"))
    assert shell(["--listen", "--path", str(tmp_path), "--verbose"]) == 0
    captured = capsys.readouterr()
    assert "<assistant>" in captured.out.strip()
    assert "<stdin>" in captured.out.strip()
    assert f"{abbreviation} --listen --verbose" in captured.out.strip()
    assert "<user request>" in captured.out.strip()

def test_shell_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("HISTORY", f"305  {abbreviation} --help")
    with pytest.raises(SystemExit):
        shell(["--help"])
    captured = capsys.readouterr()
    assert f"usage: {abbreviation}" in captured.out.strip()
    assert "--help" in captured.out.strip()
    assert "--listen" in captured.out.strip()
    assert "--path" in captured.out.strip()
    assert "--new-session" in captured.out.strip()
    assert "--switch-session" in captured.out.strip()
    assert "SESSION_ID" in captured.out.strip()
    assert "--verbose" in captured.out.strip()

def test_shell_all_options_have_help() -> None:
    parser = get_arg_parser()
    missing_help = [action.option_strings for action in parser._actions if action.option_strings and not action.help]
    assert not missing_help, f"Missing help for options: {missing_help}"

def test_keyboard_interupt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("shell.read_stdin", lambda forward_input: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setenv("HISTORY", f"306  {abbreviation} --listen")
    with pytest.raises(SystemExit):
        shell(["--listen", "--path", str(tmp_path)])
