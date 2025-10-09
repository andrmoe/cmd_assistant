from command_data import CommandData, CommandSession
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
