import requests


class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama2"):
        self.url = f"{base_url}/api/generate"
        self.model = model

    def generate(self, prompt, system, temperature=0.0, timeout=1800):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "stream": False
            
            
        }
        r = requests.post(self.url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()["response"]
