from command_data import CommandData, CommandSession, SessionManager
import json
from pathlib import Path


def test_session_save(tmp_path):
    session = CommandSession(id=0, prompt="Hello", save_dir=str(tmp_path), 
                             commands=[CommandData(command="fake command", stdin="fake output", ai_response="OK")])
    session.save()

    path = tmp_path / "session.0.json"
    session_dict = json.loads(path.read_text(encoding="utf-8"))
    assert session_dict["id"] == 0
    assert session_dict["prompt"] == "Hello"
    assert session_dict["save_dir"] == str(tmp_path)
    assert session_dict["commands"][0]["command"] == "fake command"
    assert session_dict["commands"][0]["stdin"] == "fake output"
    assert session_dict["commands"][0]["ai_response"] == "OK"


def test_create_new_session(tmp_path: Path):
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


def test_find_most_recent_session(tmp_path: Path):
    session_manager = SessionManager(tmp_path)
    assert session_manager.find_most_recent_session() is None
    for _ in range(5):
        session_manager.create_new_session("Hello")
    assert session_manager.find_most_recent_session().name == "session.4.json"
    session_manager.sessions[2].prompt += " World!"
    session_manager.sessions[2].save()
    assert session_manager.find_most_recent_session().name == f"session.{session_manager.sessions[2].id}.json"


def test_session_from_file(tmp_path: Path):
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
