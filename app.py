import os
from pathlib import Path

import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.globals import set_verbose
from langchain_google_genai import ChatGoogleGenerativeAI




print("VISIT THE LINK BELOW TO SEE THE APP IN ACTION")
print("---------------------------------------------------------")
print("| https://recipe--recommendation--system.streamlit.app/ |")
print("---------------------------------------------------------")


# Set verbose mode
set_verbose(True)

# Set up Google Generative AI model
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        google_api_key = None

if not google_api_key:
    st.error(
        "Missing GOOGLE_API_KEY. Set it as an environment variable or in Streamlit Secrets."
    )
    st.stop()

os.environ["GOOGLE_API_KEY"] = google_api_key
generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
model_name = os.getenv("GEMINI_MODEL")
if not model_name:
    try:
        model_name = st.secrets["GEMINI_MODEL"]
    except Exception:
        # Safer default: widely available on v1beta generateContent.
        # Newer models (e.g., 1.5/2.x) may not be enabled for all projects.
        model_name = "gemini-1.0-pro"

def build_llm(name: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=name, google_api_key=google_api_key, **generation_config
    )


model = build_llm(model_name)


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
    prompt_template = PromptTemplate(
        input_variables=[],
        template=prompt
    )

    # Create and run the chain
    chain_recipe = prompt_template | model | StrOutputParser()
    try:
        with st.spinner("Generating recipes..."):
            results_text = chain_recipe.invoke({})
    except Exception as e:
        error_text = str(e)
        if "NOT_FOUND" in error_text or "is not found" in error_text:
            # Automatic fallback for accounts/projects that don't have access to a given model.
            for fallback_name in ("gemini-3.1-flash-lite-preview", "gemini-3.1-flash-preview"):
                if fallback_name == model_name:
                    continue
                try:
                    chain_recipe_fallback = prompt_template | build_llm(fallback_name) | StrOutputParser()
                    with st.spinner(f"Retrying with {fallback_name}..."):
                        results_text = chain_recipe_fallback.invoke({})
                    st.info(
                        f"Model '{model_name}' was not available; used '{fallback_name}' instead. "
                        "To control this, set GEMINI_MODEL in Streamlit Secrets."
                    )
                    break
                except Exception:
                    results_text = None
            if results_text is not None:
                st.write("Recommended Recipes:")
                st.write(results_text)
                st.stop()

        st.error(
            "Gemini request failed. Set GOOGLE_API_KEY and (optionally) GEMINI_MODEL in Streamlit Secrets. "
            "If you see NOT_FOUND, your project may not have that model enabled."
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

