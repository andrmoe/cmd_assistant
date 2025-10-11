import requests
import json
from typing import Generator

def query_ollama(prompt: str, url: str = "http://localhost:11434/api/generate", 
                 model: str = "llama3.2-vision:latest") -> Generator[str, None, None]:
    
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt}

    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                if "response" in chunk:
                    #print(chunk["response"], end="", flush=True)
                    yield chunk["response"]
                if chunk.get("done", False):
                    break
        return
    else:
        raise IOError(f"Error {response.status_code}: {response.text}")
