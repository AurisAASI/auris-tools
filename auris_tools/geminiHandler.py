
# TODO Montar o handler adequado (WIP)
class GoogleGeminiHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gemini.googleapis.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate_text(self, prompt: str, model: str="gemini-1.5-turbo", max_tokens: int=1024) -> str:
        url = f"{self.base_url}/models/{model}:generateText"
        payload = {
            "prompt": {
                "text": prompt
            },
            "maxOutputTokens": max_tokens
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json().get("candidates", [{}])[0].get("output", "")
        else:
            logging.error(f"Error generating text: {response.text}")
            return ""