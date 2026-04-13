import os
import json
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st




print("VISIT THE LINK BELOW TO SEE THE APP IN ACTION")
print("---------------------------------------------------------")
print("| https://recipe--recommendation--system.streamlit.app/ |")
print("---------------------------------------------------------")


def get_secret_or_env(key: str):
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets[key]
    except Exception:
        return None


google_api_key = get_secret_or_env("GOOGLE_API_KEY")
if not google_api_key:
    st.error(
        "Missing GOOGLE_API_KEY. Set it as a Streamlit Environment Variable or in Streamlit Secrets."
    )
    st.stop()

# Generation config for Gemini REST API
generation_config = {
    "temperature": 0.7,
    "topP": 1,
    "topK": 1,
    "maxOutputTokens": 2048,
}

configured_model = get_secret_or_env("GEMINI_MODEL") or get_secret_or_env("GOOGLE_MODEL")
configured_api_version = get_secret_or_env("GEMINI_API_VERSION")


def _normalize_model_name(model: str) -> str:
    model = (model or "").strip()
    if model.startswith("models/"):
        return model[len("models/") :]
    return model


PREFERRED_MODEL_ORDER: list[str] = [
    # Prefer fast/cheap models first.
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    # Older naming used by some projects.
    "gemini-pro",
    "gemini-1.0-pro",
]


def _gemini_generate_content(
    *, api_key: str, api_version: str, model: str, prompt: str
) -> str:
    model = _normalize_model_name(model)
    url = (
        f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            data = json.loads(error_body)
        except Exception:
            raise
        raise RuntimeError(data) from e

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError({"error": {"message": "No candidates returned", "raw": data}})

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError({"error": {"message": "Empty response text", "raw": data}})

    return text


def _gemini_list_models(*, api_key: str, api_version: str) -> list[dict]:
    url = f"https://generativelanguage.googleapis.com/{api_version}/models?key={api_key}"
    request = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("models") or []


def _get_model_candidates_for_version(api_version: str) -> list[str]:
    if configured_model:
        return [_normalize_model_name(configured_model)]

    try:
        models = _gemini_list_models(api_key=google_api_key, api_version=api_version)
        supported: list[str] = []
        for m in models:
            methods = m.get("supportedGenerationMethods") or []
            if "generateContent" in methods and m.get("name"):
                supported.append(_normalize_model_name(m["name"]))

        if supported:
            preferred = [m for m in PREFERRED_MODEL_ORDER if m in supported]
            remaining = [m for m in supported if m not in preferred]
            return preferred + remaining
    except Exception:
        pass

    # Last resort static guesses.
    return PREFERRED_MODEL_ORDER


def generate_with_fallbacks(prompt: str) -> str:
    api_versions = [configured_api_version] if configured_api_version else ["v1", "v1beta"]

    last_error: Exception | None = None
    for api_version in api_versions:
        model_candidates = _get_model_candidates_for_version(api_version)
        for model in model_candidates:
            try:
                return _gemini_generate_content(
                    api_key=google_api_key,
                    api_version=api_version,
                    model=model,
                    prompt=prompt,
                )
            except Exception as e:
                last_error = e
                # Retry on common "model not found" failures
                if "NOT_FOUND" in str(e) or "not found" in str(e).lower():
                    continue
                raise

    raise last_error or RuntimeError("Gemini request failed")


# Function to build the dynamic prompt based on inputs
def build_prompt(input_data):
    prompt = "Recipe Recommendation System:\nPlease provide detailed recipes for 5 dishes based on the following preferences:\n"
    
    if input_data['calories']:
        prompt += f"Calories: {input_data['calories']}\n"
    if input_data['fat']:
        prompt += f"Fat: {input_data['fat']}\n"
    if input_data['carbohydrates']:
        prompt += f"Carbohydrates: {input_data['carbohydrates']}\n"
    if input_data['protein']:
        prompt += f"Protein: {input_data['protein']}\n"
    if input_data['veg_or_nonveg']:
        prompt += f"Veg or Non-Veg: {input_data['veg_or_nonveg']}\n"
    if input_data['cuisine']:
        prompt += f"Preferred cuisine: {input_data['cuisine']}\n"
    if input_data['preferred_ingredients']:
        prompt += f"Preferred ingredients: {input_data['preferred_ingredients']}\n"
    if input_data['dietary_restrictions']:
        prompt += f"Please exclude the following ingredients due to dietary restrictions: {input_data['dietary_restrictions']}\n"

    if input_data['cooking_time']:
        prompt += f"Preferred cooking time: {input_data['cooking_time']} minutes\n"
    
    # Final request for detailed recipes
    prompt += """
Please provide the full written recipes, including the following details for each dish:
- Recipe name
- Preparation time
- Cooking time
- Number of servings
- List of ingredients with exact quantities
- Step-by-step cooking instructions

Example format:

Recipe: Chicken Biryani

Prep time: 30-35 minutes
Cooking time: 1 hour
Serves: 4-5 people

Ingredients:
- Onion (1/2 kg)
- Chicken (1/2 kg, leg and thigh pieces)
- Biryani masala (1.5 tbsp)
- [Include other ingredients...]

Instructions:
1. Marinate the chicken with [marination ingredients] for 1 hour.
2. Prepare the biryani masala by [detailed steps...].
3. Cook the chicken by [detailed steps...].
4. Layer the rice and chicken for dum cooking by [detailed steps...].

Please make sure the output follows this structure.
"""

    return prompt

def load_css(file_name: str = "style.css") -> None:
    css_path = Path(__file__).with_name(file_name)
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return

    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


# Custom styling for Streamlit
load_css()

# Create a Streamlit web app
st.title('RECIPE RECOMMENDATION SYSTEM')

# User input form for recipe preferences
calories = st.text_input('Calories (in kcal)')
fat = st.text_input('Fat')
carbohydrates = st.text_input('Carbohydrates (in grams)')
protein = st.text_input('Protein (in grams)')
fiber = st.text_input('Fiber')
veg_or_nonveg = st.selectbox('Veg or Non-Veg', ['any','Veg', 'Non-Veg'])
cuisine = st.text_input('Preferred Cuisine (e.g., Italian, Indian)')
preferred_ingredients = st.text_input('Preferred Ingredients (comma-separated)')
dietary_restrictions = st.text_input('Dietary Restrictions (if any)')
meal_type = st.selectbox('Meal Type', ['any', 'Breakfast', 'Lunch', 'Dinner', 'Snack'])
cooking_time = st.text_input('Preferred Cooking Time (in minutes)')

# Button to trigger recipe recommendations
if st.button('Get Recipe Recommendations'):
    input_data = {
        'calories': calories.strip(),
        'fat': fat.strip(),
        'carbohydrates': carbohydrates.strip(),
        'protein': protein.strip(),
        'fiber': fiber.strip(),
        'veg_or_nonveg': veg_or_nonveg.strip(),
        'cuisine': cuisine.strip(),
        'preferred_ingredients': preferred_ingredients.strip(),
        'dietary_restrictions': dietary_restrictions.strip(),
        'meal_type': meal_type.strip(),
        'cooking_time': cooking_time.strip()
    }

    # Build prompt using user inputs
    prompt = build_prompt(input_data)
    try:
        with st.spinner("Generating recipes..."):
            results_text = generate_with_fallbacks(prompt)
    except Exception as e:
        error_text = str(e)
        if "NOT_FOUND" in error_text or "not found" in error_text.lower():
            try:
                models = _gemini_list_models(api_key=google_api_key, api_version="v1")
                supported = []
                for m in models:
                    methods = m.get("supportedGenerationMethods") or []
                    if "generateContent" in methods:
                        name = m.get("name")
                        if name:
                            supported.append(_normalize_model_name(name))

                if supported:
                    st.info(
                        "Your API key can access these `generateContent` models (set `GEMINI_MODEL` to one of them):"
                    )
                    st.code("\n".join(supported[:30]))
            except Exception:
                pass

        st.error(
            "Gemini request failed. Check GOOGLE_API_KEY. If the error says NOT_FOUND, set GEMINI_MODEL "
            "and/or GEMINI_API_VERSION (try v1) in Streamlit Secrets/Environment Variables."
        )
        st.exception(e)
        st.stop()

    st.write("Recommended Recipes:")
    st.write(results_text)

# Footer
st.markdown(
    """
    <div class="footer">
        &copy;
        @kartik panaganti
        @Zahid shaikh
        @vijaykumar Maske
        @Prashant Dasari
    </div>
    """,
    unsafe_allow_html=True,
)

