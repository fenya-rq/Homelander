import logging
from itertools import cycle

from google.genai import Client, types
from google.genai.errors import ClientError

from src.config import GEMINI_API_KEY

FREE_TIER_MODELS = (
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash-preview-tts',
    'gemma-3-27b-it',
    'gemma-3-12b-it',
)

SYSTEM_INSTRUCTION = (
    'Role: You are an expert nutritionist. Your task is to calculate the nutritional value of food products.\n'
    'Requirements:\n'
    '1. Use only up-to-date data for 2025–2026.\n'
    '2. Be strictly professional: provide Calories, Proteins, Fats, and Carbohydrates for the entire package/container.\n'
    '3. Always use the google_search tool to verify current product compositions and nutritional facts.\n'
    '4. Output Format: You MUST return only a valid JSON object in the following format: '
    '{"калории": 0, "белки": 0, "жиры": 0, "углеводы": 0}.\n'
    '5. If data cannot be found, set all fields to null.\n'
    '6. Do not include any conversational text, explanations, or markdown code blocks outside of the JSON.'
)

logger = logging.getLogger(__name__)

model_pool = cycle(FREE_TIER_MODELS)

aclient = Client(api_key=GEMINI_API_KEY).aio

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[types.Tool(google_search=types.GoogleSearch())], # Подключаем поиск для актуальности 2026 года
    temperature=0.2, # Снижаем температуру для точности фактов
)


async def get_response(prompt: str):
    current_model = next(model_pool)

    while True:
        try:

            response = await aclient.models.generate_content(
                model=current_model,
                contents=prompt,
                config=config
            )
            return response.text

        except ClientError as e:
            # 429 - лимит запросов, 503/504 - перегрузка сервиса
            if e.code in (429, 503):
                current_model = next(model_pool)
                logger.error(f'Лимит исчерпан. Переключаюсь на {current_model}...')

                continue
            else:
                raise e
