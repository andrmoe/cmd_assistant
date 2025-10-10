#!/usr/bin/env python3
import subprocess
import sys
from ollamaapi import query_ollama
from typing import Iterable
from command_data import CommandData
from prompts import command_session_to_prompt


"""Run a shell command and return stdout+stderr."""
def run_command(cmd: str) -> str:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    output_lines = []
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        output_lines.append(line)

    process.wait()
    return "".join(output_lines)


"""Takes an iterable of strings and prints them as they arrive. Returns the full printed string"""
def print_ai_response(response_iter: Iterable[str]) -> str:
    response = ""
    for chunk in response_iter:
        print(chunk, end="", flush=True)
        response += chunk
        
    print()
    return response


"""Takes a request string and prints an ai response token by token. Returns the result."""
def answer_simple_request(request: str) -> str:
    history = "You are a linux command line assistant. Answer the user's request as concisely as possible."
    history += "User request: " + request
    return print_ai_response(query_ollama(history))


"""Takes a command string an executes it. Prints an ai response to the command string and output. Returns (command output, ai response)."""
def run_and_help_with_command(command: str) -> tuple[str, str]:
    output = run_command(command)
    history = "The user is using a linux command line. Your job is to help with commands. Be as concise as possible.\n\nThe user enters a command to the system. This is reproduced for you under 'Command:', the command is run by the system, and the output is reproduced for you under 'Output'. \nIf something is wrong or inefficient, let the user know. Otherwise just respond with 'OK'.\n"
    history += f"Command:\n{command}\n\nOutput:\n{output}\n\n"
    ai_response = print_ai_response(query_ollama(history))
    return output, ai_response


def read_command_data() -> CommandData:
    cmd = CommandData("<command missing>", "", None)
    for line in sys.stdin:
        print(line, end="")
        cmd.append_stdin(line)
    return cmd
    

def main() -> None:
    if len(sys.argv) < 2:
        prompt = "The user is using a linux command line. Your job is to help with commands. Be as concise as possible.\n\nThe user enters a command to the system. This is reproduced for you under 'Command:', the command is run by the system, and the output is reproduced for you under 'Output'. \nIf something is wrong or inefficient, let the user know. Otherwise just respond with 'OK'.\n"
        command_data = read_command_data()
        request = prompt+f"Command:\n{' '.join(sys.argv[1:])}\n\nOutput:\n{command_data.stdin}\n\n"+'\n'
        print(request)
        command_data.ai_response = print_ai_response(query_ollama(request))
    elif sys.argv[1][0].isupper():
        answer_simple_request(" ".join(sys.argv[1:]))
    else:
        command = sys.argv[1:]
        run_and_help_with_command(command)


if __name__ == "__main__":
    main()
