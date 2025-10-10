from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Self, Any


@dataclass
class CommandData:
    command: str
    stdin: str
    ai_response: str

    def append_stdin(self, line: str) -> None:
        self.stdin += line
    
    def append_ai_response(self, token: str) -> None:
        self.ai_response += token


@dataclass
class CommandSession:
    id: int
    prompt: str
    save_dir: str
    commands: list[CommandData]

    @property
    def filename(self) -> str:
        return f"session.{self.id}.json"

    def save(self) -> None:
        path = Path(self.save_dir) / self.filename
        path.write_text(json.dumps(asdict(self), indent=2))
    
    @classmethod
    def from_file(cls: type[Self], path: Path) -> Self:
        session_dict = json.loads(path.read_text(encoding="utf-8"))
        
        if session_dict["commands"] is not None:
            if not isinstance(session_dict["commands"], list):
                raise TypeError(f"'commands' must be a list, not a {type(session_dict["commands"]).__name__}.\n{session_dict["commands"]=}")
            session_dict["commands"] = [CommandData(**command) for command in session_dict["commands"]]

        return cls(**session_dict)


class SessionManager:
    path: Path
    sessions: list[CommandSession]

    def __init__(self, path: Path):
        self.path = path
        self.sessions = []

    def get_session_files(self) -> list[Path]:
        files = []
        for path in self.path.iterdir():
            if not path.is_file():
                continue
            parts = path.name.split('.')
            # filename must have the form "session.<number>.json"
            if len(parts) == 3 and parts[0] == "session" and parts[1].isdigit() and parts[2] == "json":
                files.append(path)
        return files

    def create_new_session(self, prompt: str) -> CommandSession:
        existing_ids = [int(p.name.split('.')[1]) for p in self.get_session_files()]
        new_id = (0 if not existing_ids else max(existing_ids) + 1)
        session = CommandSession(id=new_id, prompt=prompt, save_dir=str(self.path), commands=[])
        session.save()
        self.sessions.append(session)
        return session
    
    def find_most_recent_session(self) -> Path | None:
        session_files = self.get_session_files()
        return max(session_files, key=lambda p: p.stat().st_mtime, default=None)

