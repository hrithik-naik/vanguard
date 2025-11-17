import requests

class LLMProvider:
    def __init__(self, config: dict):
        self.provider = config['llm']['provider']
        self.model = config['llm']['model']
        self.api_key = config['llm']['api_key']
        self.api_base = config['llm'].get('api_base', 'http://localhost:11434')
        self.temperature = config['llm'].get('temperature', 0.0)
    
    def generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._gemini(prompt)
        elif self.provider == "ollama":
            return self._ollama(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _gemini(self, prompt: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text
    
    def _ollama(self, prompt: str) -> str:
        response = requests.post(
            f"{self.api_base}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": self.temperature}
            }
        )
        return response.json()['response']