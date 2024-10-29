import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
import langchain.globals as lcg
import base64

# Set verbose mode
lcg.set_verbose(True)

# Set up Google Generative AI model
os.environ["GOOGLE_API_KEY"] = 'AIzaSyC42poakq8cly-o_pK-g8gBgIZM9r-Yz1I'  # Replace with your actual API key
generation_config = {"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
model = GoogleGenerativeAI(model="gemini-1.0-pro", generation_config=generation_config)


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

# Custom styling for Streamlit
st.markdown(
    """
    <style>

       .st-emotion-cache-4z1n4l en6cib65{
    color:black;
    }


    .viewerBadge_text__fzr3E{
    visibility:hidden;
    }
.viewerBadge_link__qRIco {
    --tw-bg-opacity: 1;
    background-color: rgb(255 75 75 / var(--tw-bg-opacity));
    border-top-left-radius: .5rem;
    padding: 1rem 1.25rem;
    visibility: hidden;}

    a{
visibility:hidden;
    }

    #MainMenu{
    visibility:hidden;
    }

    .stActionButton{
    visibility:hidden;
    }

    .st-emotion-cache-h4xjwg ezrtsby2{
    visibility:hidden;
    }
        .title {
            font-size: 25px;
            font-weight: bold;
            font-family: 'Arial', sans-serif;
        }
        .content {
            font-family: 'Helvetica', sans-serif;
        #petient
        }
        span.st-emotion-cache-10trblm.e1nzilvr1{
            margin-top: 50px;
            color: darkmagenta;
                text-shadow: #FC0 1px 0 10px;

    text-align: center;
    font-size: 54px;
        }
       
    
}

p .st-emotion-cache-1sno8jx e1nzilvr4{
{
    font-size: 50px;
    font-family: auto;
    color: #96f700;
    text-shadow: 5px 3px 4px darkmagenta;
}
}
h1 {
    font-family: "Source Sans Pro", sans-serif;
    font-weight: 700;
    color: rgb(9 253 255);
    padding: 1.25rem 0px 1rem;
    margin: 0px;
    line-height: 1.2;
    font-size: 49px;
    text-align: center;
    text-shadow: 6px 6px 6px blue;
}

label.st-emotion-cache-1qg05tj.e1y5xkzn3 {
    color: #ffffff;
    font-weight: bold;
    text-shadow: 0px 0px 5px red;
}
button.st-emotion-cache-19rxjzo.ef3psqc12{
background-color: #008CBA;;
}
#bui638val-0{
-webkit-text-stroke: 1px white;

}

strong {
    color: #ffa475;
    font-size: 25px;
    font-weight: bold;
}


li {
    color: #ffffff;
    /* font-weight: bolder; */
    webkit-text-fill-color: black    ;
    -webkit-text-stroke: 1px white;
}

li::marker{
list-style-type: circle;
color:#2fbcff;

}


.st-emotion-cache-h4xjwg {
    position: fixed;
    top: 0px;
    left: 0px;
    right: 0px;
    height: 3.75rem;
    background-color: rgba(0, 0, 0, 0);
    outline: none;
    z-index: 999990;
    display: block;
}
    
    </style>
    """,
    unsafe_allow_html=True,
)

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
    chain_recipe = LLMChain(llm=model, prompt=prompt_template)
    results = chain_recipe.invoke({})

    # Extract and display recipe recommendations
    results_text = results['text']
    st.write("Recommended Recipes:")
    st.write(results_text)

# Footer
st.markdown(
    """
    <div class="footer">
        &copy; 2024 CODE_WIZARDS. All rights reserved.
        @kartik panaganti
        @Zahid shaikh
        @vijaykumar Maske
        @Prashant Dasari
    </div>
    """,
    unsafe_allow_html=True,
)



@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    section.main.st-emotion-cache-bm2z3a.ea3mdgi8 {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return

set_png_as_page_bg('backimg.jpg')
