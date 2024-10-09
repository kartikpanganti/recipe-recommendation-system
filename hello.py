import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
import langchain.globals as lcg

# Set verbose to True or False based on your requirements
lcg.set_verbose(True)  # Enable verbose mode if needed

# Set up Google Generative AI model
os.environ["GOOGLE_API_KEY"] = 'AIzaSyC42poakq8cly-o_pK-g8gBgIZM9r-Yz1I'  # Replace with your actual API key
generation_config = {"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
model = GoogleGenerativeAI(model="gemini-1.0-pro", generation_config=generation_config)

# Function to build the dynamic prompt based on inputs
def build_prompt(input_data):
    prompt = "Recipe Recommendation System:\nPlease recommend 5 recipes based on the following preferences:\n"

    if input_data['meal_type']:
        prompt += f"Meal Type: {input_data['meal_type']}\n"
    if input_data['age']:
        prompt += f"Age of the person: {input_data['age']}\n"
    if input_data['gender']:
        prompt += f"Gender: {input_data['gender']}\n"
    if input_data['cuisine']:
        prompt += f"Preferred cuisine: {input_data['cuisine']}\n"
    if input_data['preferred_ingredients']:
        prompt += f"Preferred ingredients: {input_data['preferred_ingredients']}\n"
    if input_data['dietary_restrictions']:
        prompt += f"Dietary restrictions: {input_data['dietary_restrictions']}\n"
    if input_data['cooking_difficulty']:
        prompt += f"Cooking difficulty: {input_data['cooking_difficulty']}\n"
    if input_data['cooking_time']:
        prompt += f"Preferred cooking time: {input_data['cooking_time']} minutes\n"

    # If no inputs are provided
    if prompt.strip() == "Recipe Recommendation System:\nPlease recommend 5 recipes based on the following preferences:":
        prompt += "\nNo specific preferences provided."

    return prompt

# Custom styling for Streamlit
st.markdown(
    """
    <style>
    /* Custom styles here */
    </style>
    """,
    unsafe_allow_html=True,
)

# Create a Streamlit web app
st.title('RECIPE RECOMMENDATION SYSTEM')

# User input form for recipe preferences
age = st.text_input('Age (optional)')
gender = st.selectbox('Gender (optional)', ['', 'Male', 'Female'])
cuisine = st.text_input('Preferred Cuisine (e.g., Italian, Indian) (optional)')
preferred_ingredients = st.text_input('Preferred Ingredients (comma separated) (optional)')
dietary_restrictions = st.text_input('Dietary Restrictions (if any) (optional)')
meal_type = st.selectbox('Meal Type (optional)', ['', 'Breakfast', 'Lunch', 'Dinner', 'Snack'])
cooking_difficulty = st.selectbox('Cooking Difficulty (optional)', ['', 'Easy', 'Medium', 'Hard'])
cooking_time = st.text_input('Preferred Cooking Time in minutes (optional)')

# Button to trigger recommendations
if st.button('Get Recipe Recommendations'):
    input_data = {
        'age': age.strip(),
        'gender': gender.strip(),
        'cuisine': cuisine.strip(),
        'preferred_ingredients': preferred_ingredients.strip(),
        'dietary_restrictions': dietary_restrictions.strip(),
        'meal_type': meal_type.strip(),
        'cooking_difficulty': cooking_difficulty.strip(),
        'cooking_time': cooking_time.strip()
    }

    prompt = build_prompt(input_data)
    prompt_template = PromptTemplate(
        input_variables=[],
        template=prompt
    )

    chain_recipe = LLMChain(llm=model, prompt=prompt_template)

    results = chain_recipe.invoke({})

    # Extract recommendations
    results_text = results['text']
    st.write("Recommended Recipes:")

    st.write(results_text)

st.markdown(
    """
    <div class="footer">
        &copy; 2024 CODE_WIZARDS. All rights reserved.
        @kartik panaganti
        @Zahid shaikh
        @vijaykumar Maske
    </div>
    """,
    unsafe_allow_html=True,
)
