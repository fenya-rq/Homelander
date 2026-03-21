import logging
from itertools import cycle

from elevenlabs.client import AsyncElevenLabs
from google.genai import Client, types
from google.genai.errors import ClientError

from src.config import ELEVEN_LABS_API_KEY, GEMINI_API_KEY

# Those models can't take system rules ,need to pass it with each request
GEMMA_MODELS = (
    'gemma-3-27b-it',
    'gemma-3-12b-it',
)

FREE_TIER_MODELS = (
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash-preview-tts',
    'gemini-3.1-flash-lite-preview',
)

SYSTEM_INSTRUCTION = (
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

model_pool = cycle(FREE_TIER_MODELS)

gemini_client = Client(api_key=GEMINI_API_KEY).aio

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
)


async def get_response(prompt: str, max_retries: int = 3):
    current_model = next(model_pool)

    while True:
        try:

            response = await gemini_client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=config
            )
            return response.text

        except ClientError as e:
            max_retries -= 1
            # 429 - лимит запросов, 503/504 - перегрузка сервиса
            if e.code in (429, 503):
                current_model = next(model_pool)
                logger.error(f'Лимит исчерпан. Переключаюсь на {current_model}...')

                if max_retries == 0:
                    logger.error('Макс. количество попыток исчерпано. Прерываю...')
                    raise e

                continue
            else:
                raise e


class ElevenLabsClient:

    def __init__(self):
        self.client = AsyncElevenLabs(api_key=ELEVEN_LABS_API_KEY)

    async def speech_to_text(self, audio: bytes):
        return await self.client.speech_to_text.convert(
            model_id='scribe_v2',
            file=audio,
            language_code='ru',
        )


elevenlabs_client = ElevenLabsClient()
