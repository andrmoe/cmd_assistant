from command_data import CommandData, CommandSession, SessionManager
from ollamaapi import query_ollama
from typing import Callable, Generator
from pathlib import Path

class Assistant:
    default_prompt: str
    session: CommandSession
    session_manager: SessionManager
    ai_api: Callable[[str], Generator[str, None, None]]

    def __init__(self, ai_api: Callable[[str], Generator[str, None, None]] = query_ollama, 
                 save_path: Path = Path.cwd() / "sessions"):
        self.ai_api = ai_api
        self.default_prompt = "You are a linux command line assistant."
        save_path.mkdir(parents=False, exist_ok=True)
        self.session_manager = SessionManager(save_path)
        s = self.session_manager.load_most_recent_session()
        if s is None:
            s = self.session_manager.create_new_session(self.default_prompt)
        self.session = s

    def command_session_to_prompt(self) -> str:
        prompt = self.session.prompt + "\n\n"
        for command in self.session.commands:
            prompt += "Command:\n" + command.command + "\n\n"
            if command.stdin:
                prompt += "Stdin:\n" + command.stdin + "\n\n"
            if command.ai_response:
                prompt += "Assistant:\n" + command.ai_response + "\n"
        return prompt

    def new_command(self, command: CommandData) -> Generator[str, None, None]:
        self.session.commands.append(command)
        prompt = self.command_session_to_prompt()
        for chunk in self.ai_api(prompt):
            command.ai_response += chunk
            yield chunk
        self.session.save()
