import asyncio
import logging
from collections.abc import Callable
from copy import deepcopy
from functools import wraps
from itertools import cycle
from typing import Coroutine

from elevenlabs.client import AsyncElevenLabs
from google.genai import Client, types
from google.genai.errors import ClientError

from src.config import ELEVENLABS_API_KEY, GEMINI_API_KEY

MAIN_LLM = 'gemini-2.5-flash'
ALT_LLM = 'gemini-2.5-flash-lite'

NUTRITIONIST_INSTRUCTION = (
    "Role: Expert Nutritionist & Food Data Analyst (2025-2026).\n"
    "Objective: Calculate nutritional values using professional estimation when specific details are missing."

    "\nConstraints:"""
    "\n1. Estimation Policy: If the user provides a product name without exact weight/volume, use standard industry averages (e.g., 1 medium apple = 180g, 1 bowl of soup = 300ml, 1 portion of chicken breast = 150g). Do not ask for weight unless the portion is completely ambiguous."
    "\n2. Data Accuracy: Use 2025–2026 data. Use 'google_search' only if you are unsure about a specific product's composition."
    "\n3. Scope: Provide Energy (kcal), Protein (g), Fats (g), Carbohydrates (g), and Fiber (g)."
    "\n4. Output Format: You MUST return ONLY a valid JSON object OR a brief clarifying question in Russian. No conversational filler, no markdown blocks."
    '\n5. JSON Schema: {"energy": int, "protein": int, "fats": int, "carbohydrates": int, "fiber": int}'
    "\n6. Data Integrity: All values must be integers. If data is unavailable, set values to 0."
    "\n7. Language: Respond to questions in Russian. JSON remains in English as specified."
    
    "Example 1 (Correct):"
    "\nUser: 'яблоко'"
    'Response: {"energy": 95, "protein": 0, "fats": 0, "carbohydrates": 25, "fiber": 4}'
    
    "Example 2 (Correct - ambiguity):"
    "\nUser: 'какая-то еда'"
    "Response: 'Уточните, пожалуйста, что именно вы съели?'"
    "\nCRITICAL: If you found the data, your entire response must start with '{' and end with '}'. "
    "Any text outside the JSON is a violation of protocol and will break the system. "
    "DO NOT explain your calculations. Output the result in JSON only. "
    "NO MARKDOWN. NO BULLET POINTS. NO INTROS."

)

logger = logging.getLogger(__name__)

default_gemini_config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
)

nutritionist_gemini_config = deepcopy(default_gemini_config)
nutritionist_gemini_config.system_instruction = NUTRITIONIST_INSTRUCTION


class GeminiClient:

    def __init__(self, model, alt_models, config, rpd_threshold=5):
        self.client = Client(api_key=GEMINI_API_KEY).aio
        self.main_model = model
        self.current_model = model
        self.alt_models = list(alt_models)
        self.config = config if config else deepcopy(default_gemini_config)
        self._models_iter = iter(self.alt_models)
        self._on_low_limit = Callable | None

    def set_low_limit_handler(self, handler):
        """Регистрирует внешний обработчик для низких лимитов."""
        self._on_low_limit = handler

    def reset_models_iterator(self):
        self._models_iter = iter(self.alt_models)
        self.current_model = self.main_model
        logger.info('Iterator reset to main model: %s', self.main_model)

    @staticmethod
    def model_switcher(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            other_errors_attempt = 0

            while True:

                try:
                    return await func(self, *args, **kwargs)
                except ClientError as e:
                    if e.code == 429:
                        logger.warning('Limit exhausted for %s', self.current_model)

                        try:
                            self.current_model = next(self._models_iter)
                            logger.info('Switched to %s', self.current_model)
                            await asyncio.sleep(1)
                            continue

                        except StopIteration:
                            logger.error('All models limits have been exhausted.')

                            await self._on_low_limit()
                            self.reset_models_iterator()
                            return None

                    else:
                        if other_errors_attempt >= 2:
                            logger.error('Standard retry limit reached for error: %s', e)
                            return None

                        other_errors_attempt += 1
                        wait = (other_errors_attempt + 1) * 2
                        logger.info('%s\nRetrying in %s seconds...',e, wait)
                        await asyncio.sleep(wait)

        return wrapper

    @model_switcher
    async def get_response(self, prompt: str):
        logger.info('Google LLM is - %s', self.current_model)

        response = await self.client.models.generate_content(
            model=self.current_model,
            contents=prompt,
            config=self.config
        )
        return response.text


class ElevenLabsClient:

    def __init__(self, low_limit_threshold=2000):
        self.client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)
        self.threshold = low_limit_threshold
        self._on_low_limit: Coroutine | None = None

    def set_low_limit_handler(self, handler):
        """Регистрирует внешний обработчик для низких лимитов."""
        self._on_low_limit = handler

    @staticmethod
    def log_limits(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):

            result = await func(self, *args, **kwargs)

            sub = await self.client.user.subscription.get()
            remains = sub.character_limit - sub.character_count

            logger.info('Character spent: %s | Remains: %s', sub.character_count, remains)
            # Если лимит низкий и есть обработчик — вызываем его
            if remains < self.threshold and self._on_low_limit:
                await self._on_low_limit(remains)

            return result

        return wrapper

    @log_limits
    async def speech_to_text(self, audio: bytes):
        return await self.client.speech_to_text.convert(
            model_id='scribe_v2',
            file=audio,
            language_code='ru',
        )
