from command_data import CommandData, CommandSession, SessionManager
from ollamaapi import query_ollama
from typing import Callable, Generator
from pathlib import Path
from abbreviation import abbreviation
from prompts import command_session_to_prompt


class Assistant:
    initial_message: str
    session: CommandSession
    session_manager: SessionManager
    ai_api: Callable[[str], Generator[str, None, None]]

    def __init__(self, session_manager: SessionManager, session_id: int | None = None, 
                 verbose: bool = False, ai_api: Callable[[str], Generator[str, None, None]] = query_ollama):
        self.verbose = verbose
        self.ai_api = ai_api
        self.session_manager = session_manager
        self.initial_message = ""
        if session_id is None:
            s = self.session_manager.load_most_recent_session()
        else:
            s = self.session_manager.load(session_id)
            # Passing a session id indicates that the user switched sessions. 
            # They should therefore see the last message from that session.
            if s.commands:
                self.initial_message = s.commands[-1].ai_response  # TODO: Truncate this and make it prettier.
        self.session = s

    def new_command(self, command: CommandData, give_ai_response: bool = True) -> Generator[str, None, None]:
        self.session.commands.append(command)
        prompt = command_session_to_prompt(self.session)
        if self.verbose:
                yield f"Prompt to {abbreviation}:\n{prompt}\n"
        if give_ai_response:
            for chunk in self.ai_api(prompt):
                command.ai_response += chunk
                yield chunk
        self.session.save()
