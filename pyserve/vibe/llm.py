import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class VibeLLMClient:
    def __init__(self, api_url=None, api_key=None, model="gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if api_url:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=api_url
            )
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, prompt: str, timeout: int = 20) -> str:
        if not self.api_key:
            raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        system_prompt = """Ты веб-разработчик, который создает HTML страницы. 
ВАЖНО: Отвечай ТОЛЬКО чистым HTML кодом с встроенными CSS стилями и JS скриптами. 
НЕ добавляй никаких объяснений, комментариев или текста до/после кода.
НЕ используй markdown форматирование (```html).
Создавай красивые, современные и адаптивные страницы.
Используй встроенные CSS стили в теге <style> внутри <head>.
Ответ должен начинаться с <!DOCTYPE html> и заканчиваться </html>."""
        
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                ),
                timeout=timeout
            )
            
            return response.choices[0].message.content
                    
        except asyncio.TimeoutError:
            raise TimeoutError("LLM request timed out")
        except Exception as e:
            raise RuntimeError(f"LLM error: {e}")
        

