import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ── Load environment variables (override=True ensures .env always wins) ───────
load_dotenv(override=True)

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your-google-ai-studio-key-here":
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set. Please add your Google AI Studio key to the .env file."
    )


def _build_system_prompt() -> str:
    """
    Build the system prompt dynamically so the timestamp is always current.
    This is called fresh on every request rather than at module load time.
    """
    return f"""You are an advanced medical record semantic extraction assistant.
You possess deep language understanding and must map complex, casual, or synonymous phrased user queries into a strict JSON schema.

Today's date and time is: {datetime.now().isoformat()}

Your ONLY job is to extract search filters based on the user's semantic intent and return them as a strict JSON object. Do NOT add any explanation or extra text.

Extract ONLY the following fields from context if they are mentioned or implied:
- "name"   : (string) patient first name, lowercase. Look for the subject of the query (e.g. "looking for danny" -> "danny").
- "gender" : (string) "male" or "female" only. Infer from synonyms: "guy", "boy", "man", "gentleman" -> "male". "woman", "girl", "lady" -> "female".
- "age"    : (integer) the patient's age as a number. Reconcile approximations or words (e.g. "mid-twenties" -> 25, "forty five" -> 45) if needed.
- "doctor" : (string) the doctor's last name, lowercase. Use context clues: "supervision of", "treated by", "assigned to", "handled by" indicates the doctor. Ignore prefixes like "dr", "dr.", "doctor".
- "date"   : (object) with:
    - "from" : date string in YYYY-MM-DD format (exact start boundary of the requested timeframe)
    - "to"   : date string in YYYY-MM-DD format (exact end boundary of the requested timeframe)

CRITICAL date resolution rules:
- Compute the exact logical start and end boundaries of the requested timeframe.
- Do NOT just default the "to" date to today unless the user explicitly asks for "up to now", "recently", "last year", or "in the last [X] days/months".
- For specific years (e.g., "in 2019" or "for 2019"): Set "from" to "2019-01-01" and "to" to "2019-12-31".
- For specific months (e.g., "August 2020"): Set "from" to "2020-08-01" and "to" to "2020-08-31".
- All dates MUST be in YYYY-MM-DD format.

Rules:
- If a field is not implied or explicitly mentioned, do NOT include it in the JSON.
- Act as an intelligent data mapper. Use context and synonyms to slot data into the correct fields.
- Return ONLY valid JSON. No markdown, no code fences, no explanation.

Example outputs:
For query: "find the records for a woman named sarah treated under supervision of smith in 2020"
{{"name": "sarah", "gender": "female", "doctor": "smith", "date": {{"from": "2020-01-01", "to": "2020-12-31"}}}}

For query: "show me patients assigned to rice last week"
{{"doctor": "rice", "date": {{"from": "2026-02-23", "to": "2026-03-02"}}}}
"""


def parse_query(input_text: str) -> dict:
    """
    Send the user's natural language query to Google Gemini and return
    a structured dictionary of filters ready for the query builder.

    The client is created inside this function so that every call picks up
    the latest GOOGLE_API_KEY from environment — avoids stale key issues
    after hot-reloads or .env changes.

    Args:
        input_text (str): The raw user query string.

    Returns:
        dict: Extracted filters e.g. {"name": "john", "age": 45, ...}
    """
    # Re-read the env on every call so key changes take effect immediately
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_API_KEY", "")
    model   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key or api_key == "your-google-ai-studio-key-here":
        raise EnvironmentError("GOOGLE_API_KEY is missing or not set in the .env file.")

    # Create a fresh client on each call — lightweight and avoids stale keys
    client = genai.Client(api_key=api_key)

    system_prompt = _build_system_prompt()
    full_prompt   = f"{system_prompt}\n\nUser query: {input_text}"

    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0,      # Deterministic — no creativity needed
                max_output_tokens=2000,  # Generous limit — dates can be long
                # NOTE: response_mime_type='application/json' is intentionally
                # omitted — it causes Gemini to truncate JSON mid-string.
                # The prompt already instructs pure JSON output, and the
                # code-fence stripper below handles any markdown wrapping.
            ),
        )

        # response.text can be None if Gemini's safety filter blocks the response
        # or if the response candidates have an unexpected structure
        raw_json: str | None = response.text

        # Fallback: try to extract text from candidates directly
        if raw_json is None:
            try:
                raw_json = response.candidates[0].content.parts[0].text
            except (IndexError, AttributeError):
                raise ValueError(
                    "Gemini returned an empty or blocked response. "
                    "Try rephrasing your query."
                )

        raw_json = raw_json.strip()

        # Strip markdown code fences if the model wraps output anyway
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
            raw_json = raw_json.strip()

        filters: dict = json.loads(raw_json)
        return filters

    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}. Raw: {raw_json!r}")
    except Exception as e:
        raise RuntimeError(f"Google Gemini API error: {e}")
