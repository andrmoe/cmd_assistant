from command_data import CommandData, CommandSession, create_new_session
import json


def test_session_save(tmp_path):
    session = CommandSession(id=0, prompt="Hello", save_dir=str(tmp_path), commands=[CommandData(command="fake command", stdin="fake output", ai_response="OK")])
    session.save()

    path = tmp_path / "session.0.json"
    session_dict = json.loads(path.read_text(encoding="utf-8"))
    assert session_dict["id"] == 0
    assert session_dict["prompt"] == "Hello"
    assert session_dict["save_dir"] == str(tmp_path)
    assert session_dict["commands"][0]["command"] == "fake command"
    assert session_dict["commands"][0]["stdin"] == "fake output"
    assert session_dict["commands"][0]["ai_response"] == "OK"


def test_create_new_session(tmp_path):
    session0 = create_new_session("Hello", tmp_path)
    assert session0.id == 0
    session0_dict = json.loads((tmp_path / "session.0.json").read_text(encoding="utf-8"))
    assert session0_dict["id"] == 0
    for i in range(1, 5):
        (tmp_path / f"session.{i}.json").write_text("")
    session5 = create_new_session("Hello", tmp_path)
    assert session5.id == 5
    session5_dict = json.loads((tmp_path / "session.5.json").read_text(encoding="utf-8"))
    assert session5_dict["id"] == 5
