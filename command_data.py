from dataclasses import dataclass, asdict
import json
from pathlib import Path


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

