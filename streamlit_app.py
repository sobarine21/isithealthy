import streamlit as st
import easyocr
import matplotlib.pyplot as plt
import google.generativeai as genai
import pandas as pd
from PIL import Image
import re
import requests

# Configure the Google Gemini AI API securely
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Function to extract nutritional data from the label
def extract_nutrition_data(image_path):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(image_path)
    nutrition_data = {}

    for result in results:
        text = result[1]
        match = re.match(r"^(.*?):\s*([\d.]+)\s*(.*)?$", text)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            unit = match.group(3).strip() if match.group(3) else ""
            nutrition_data[key] = f"{value} {unit}".strip()
    return nutrition_data

# Function to provide AI analysis on nutrition data
def ai_nutrition_analysis(nutrition_data):
    if not nutrition_data:
        return "No data available for analysis."
    
    prompt = "Analyze the following nutritional label data and provide insights about its health benefits and risks:\n"
    for key, value in nutrition_data.items():
        prompt += f"{key}: {value}\n"
    prompt += "\nProvide a summary of whether this is healthy and what improvements can be made."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing nutritional data: {e}"

# Function to visualize the nutritional data
def visualize_nutrition_data(nutrition_data):
    labels = []
    values = []

    for key, value in nutrition_data.items():
        try:
            numeric_value = float(value.split()[0]) if value else None
            if numeric_value is not None:
                labels.append(key)
                values.append(numeric_value)
        except (ValueError, IndexError):
            st.warning(f"Could not process value for {key}: {value}")

    if not values:
        st.error("No valid numeric data to visualize.")
        return

    plt.figure(figsize=(8, 4))
    plt.barh(labels, values, color='skyblue')
    plt.xlabel("Amount")
    plt.title("Nutritional Components")
    st.pyplot(plt)

# Function to search for related articles
def search_related_articles(query):
    try:
        search_url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(search_url)
        results = response.json()
        return [result["Text"] for result in results.get("RelatedTopics", []) if "Text" in result]
    except Exception as e:
        return [f"Error fetching articles: {e}"]

# Main Streamlit App
def main():
    st.title("Nutritional Label Analysis and Insights")
    st.write("Upload an image of a nutritional label to analyze its contents and get health insights.")

    # Upload Image
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Save image locally
        image_path = "uploaded_image.png"
        image.save(image_path)

        # Extract nutritional data
        nutrition_data = extract_nutrition_data(image_path)
        st.write("Extracted Nutritional Data:")
        st.json(nutrition_data)

        # Provide AI-based analysis
        st.write("AI-Based Nutritional Analysis:")
        ai_analysis = ai_nutrition_analysis(nutrition_data)
        st.write(ai_analysis)

        # Visualize nutritional data
        st.write("Visualization of Nutritional Data:")
        visualize_nutrition_data(nutrition_data)

        # Search related articles
        st.write("Related Articles on Nutritional Components:")
        article_query = "health benefits of " + ", ".join(nutrition_data.keys())
        articles = search_related_articles(article_query)
        for article in articles:
            st.write("- ", article)

if __name__ == "__main__":
    main()
