import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence
import argparse
import re

from command_data import CommandData
from assistant import Assistant
from abbreviation import abbreviation


def parse_command_history(history: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line in history.split('\n'):
        re_match = re.match(r"^(\d+)\ {2}(.*)$", line.strip())
        if re_match is None:
            raise EnvironmentError(f"Could not parse command history. There's either a bug in the parser, "
                                   f"or a weird bash shell. Unparsed line:\n{line}")
        result.append((int(re_match.group(1)), re_match.group(2)))
    return result


def get_command_history() -> str:
    history = os.environ.get("HISTORY")
    if history is None:
        raise EnvironmentError("Command history is not available. Check if alias is present.")
    return history


def read_stdin(forward_input: bool=True) -> str:
    output = ""
    for line in sys.stdin:
        if forward_input:
            print(line, end="", flush=True)
        output += line
    return output


"""Takes an iterable of strings and prints them as they arrive. Returns the full printed string"""
def print_ai_response(response_iter: Iterable[str]) -> str:
    response = ""
    for chunk in response_iter:
        print(chunk, end="", flush=True)
        response += chunk
        
    print()
    return response


def default_storage_path() -> Path:
    return Path.home() / "kj-assistant" / ".sessions"


def shell(argv: Optional[Sequence[str]] = None) -> int:
    history = get_command_history()
    parsed_history = parse_command_history(history)
    last_command = parsed_history[-1][1]

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--no-reply", action="store_true")
    parser.add_argument("-p", "--path", default=str(default_storage_path()))
    args = parser.parse_args(argv)
    
    # Don't echo the input to the terminal, if the user didn't use a pipe.
    output = read_stdin(forward_input=not last_command.startswith(abbreviation))
 
    cmd = CommandData(command=last_command, stdin=output, ai_response="")

    assistant = Assistant(Path(args.path))

    print_ai_response(assistant.new_command(cmd, give_ai_response=not args.no_reply))

    return 0

if __name__ == '__main__':
    exit(shell())  # pragma: no cover - I don't know to test this.
