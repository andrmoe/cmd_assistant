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


def create_new_session(prompt: str, save_directory: Path) -> CommandSession:
    existing_file_names = [p.name for p in save_directory.iterdir() if p.is_file()]
    existing_ids = []
    for file_name in existing_file_names:
        parts = file_name.split('.')
        # filename must have the form "session.<number>.json"
        if len(parts) == 3 and parts[0] == "session" and parts[1].isdigit() and parts[2] == "json":
            existing_ids.append(int(parts[1]))
    new_id = (0 if not existing_ids else max(existing_ids) + 1)
    session = CommandSession(id=new_id, prompt=prompt, save_dir=str(save_directory), commands=[])
    session.save()
    return session
