import os
import sys
from pathlib import Path
from command_data import CommandData
from assistant import Assistant
from typing import Iterable
from abbreviation import abbreviation

def parse_command_history(history: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line in history.split('\n'):
        t = line.strip().split("  ")
        if len(t) < 2 or not t[0].isdigit():
            raise EnvironmentError(f"Could not parse command history. There's either a bug in the parser, "
                                   f"or a weird bash shell. Unparsed line:\n{line}")
        result.append((int(t[0]), "  ".join(t[1:])))
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


def shell() -> int:
    history = get_command_history()
    parsed_history = parse_command_history(history)
    last_command = parsed_history[-1][1]
    
    output = read_stdin(forward_input=last_command[:len(abbreviation)] != abbreviation)
 
    cmd = CommandData(command=last_command, stdin=output, ai_response="")

    assistant = Assistant()
    print_ai_response(assistant.new_command(cmd))

    return 0  # TODO: Return error if exception

if __name__ == '__main__':
    exit(shell())
