#!/usr/bin/env python3
import subprocess
import sys
import readline  # allows arrow-key editing of input
from ollamaapi import query_ollama
#from openai import OpenAI

#client = OpenAI()  # assumes OPENAI_API_KEY is set in environment


def run_command(cmd):
    """Run a shell command and return stdout+stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
    )
    return result.stdout + result.stderr


def main():
    prompt = "The user is using a linux command line. Your job is to help with commands. Be as concise as possible.\n\nThe user enters a command to the system. This is reproduced for you under 'Command:', the command is run by the system, and the output is reproduced for you under 'Output'. \nIf something is wrong or inefficient, let the user know. Otherwise just respond with 'OK'.\n"
    history = prompt
    if len(sys.argv) < 2:
        pass
    elif sys.argv[1][0].isupper():
        history = "You are a linux command line assistant. Answer the user's request as concisely as possible."
        history += "User request: " + " ".join(sys.argv[1:])
        for chunk in query_ollama(history):
            print(chunk, end="", flush=True)
        print()
    else:
        # 1. Collect command from args
        command = " ".join(sys.argv[1:])
        #print(f">>> Running: {command}")

        # 2. Run the command
        output = run_command(command)
        print(output)

        # 3. REPL loop for AI questions
        history += f"Command:\n{command}\n\nOutput:\n{output}\n\n"
        #print(history)
        # 4. Query AI model with context
        for chunk in query_ollama(history):
            print(chunk, end="", flush=True)
        print()

if __name__ == "__main__":
    main()
