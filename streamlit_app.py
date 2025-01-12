import os
import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from PIL import Image
import easyocr
import pandas as pd
import matplotlib.pyplot as plt

# Configure Gemini API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Google Search API configuration
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
GOOGLE_CX = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

# Function to extract nutrition data from an image
def extract_nutrition_from_image(image_path):
    results = reader.readtext(image_path)
    extracted_text = [result[1] for result in results]
    nutrition_data = {}
    serving_info = None
    
    # Parse text to find nutrition fields
    for line in extracted_text:
        if "Energy" in line or "Calories" in line:
            nutrition_data["Energy (kcal)"] = line.split()[-1].replace("kcal", "").strip()
        elif "Total Fat" in line:
            nutrition_data["Total Fat (g)"] = line.split()[-1].strip()
        elif "Saturated Fat" in line:
            nutrition_data["Saturated Fat (g)"] = line.split()[-1].strip()
        elif "Protein" in line:
            nutrition_data["Protein (g)"] = line.split()[-1].strip()
        elif "Carbohydrate" in line:
            nutrition_data["Carbohydrate (g)"] = line.split()[-1].strip()
        elif "Sodium" in line:
            nutrition_data["Sodium (mg)"] = line.split()[-1].strip()
        elif "Serving size" in line:
            serving_info = line
    
    # Add serving info if available
    if serving_info:
        nutrition_data["Serving Size"] = serving_info.split(":")[-1].strip()
    
    return nutrition_data

# Function to analyze nutrition data using Gemini AI
def analyze_nutrition_with_gemini(nutrition_data):
    try:
        if not nutrition_data:
            return "No nutrition data found to analyze."
        
        analysis_prompt = "Analyze the following nutritional values:\n"
        for key, value in nutrition_data.items():
            analysis_prompt += f"{key}: {value}\n"
        analysis_prompt += """
        1. Assess if these values meet daily recommended needs.
        2. Highlight any nutritional risks (e.g., high sodium or fat).
        3. Suggest improvements for a healthier diet."""
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(analysis_prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing with Gemini: {e}"

# Function to search articles on nutrition components
def google_search_nutrition(nutrition_data):
    try:
        search_results = {}
        if not nutrition_data:
            return {"Error": "No nutrition data available for searching."}
        
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        for component, value in nutrition_data.items():
            query = f"Health impact of {component.lower()}"
            response = service.cse().list(q=query, cx=GOOGLE_CX).execute()
            items = response.get("items", [])
            search_results[component] = [
                {"Title": item.get("title"), "URL": item.get("link"), "Snippet": item.get("snippet")}
                for item in items
            ]
        return search_results
    except Exception as e:
        return {"Error": str(e)}

# Function to visualize nutrition data
def visualize_nutrition_data(nutrition_data):
    labels = []
    values = []
    
    # Iterate through nutrition data and filter valid numeric values
    for key, value in nutrition_data.items():
        try:
            # Only keep numeric values (handling strings that might not be numbers)
            numeric_value = float(value.split()[0])  # Get the first number
            labels.append(key)
            values.append(numeric_value)
        except ValueError:
            # Skip non-numeric values (e.g., "Energy" or "Serving size")
            continue
    
    # If valid numeric data exists, visualize it
    if labels and values:
        plt.figure(figsize=(8, 4))
        plt.barh(labels, values, color='skyblue')
        plt.xlabel("Amount")
        plt.title("Nutritional Components")
        st.pyplot(plt)
    else:
        st.write("No valid numeric nutrition data to visualize.")

# Streamlit UI
def main():
    st.title("Enhanced Nutrition Label Analysis with AI")
    st.write("Upload a nutrition label image to extract and analyze its contents.")

    uploaded_image = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    
    if uploaded_image:
        # Display uploaded image
        image = Image.open(uploaded_image)
        image_path = os.path.join("temp", uploaded_image.name)
        os.makedirs("temp", exist_ok=True)
        image.save(image_path)
        
        st.image(image, caption="Uploaded Nutrition Label", use_column_width=True)
        
        # Extract nutrition data
        st.write("Extracting nutritional information...")
        nutrition_data = extract_nutrition_from_image(image_path)
        st.write("Extracted Nutrition Data:")
        st.json(nutrition_data)
        
        # Visualize data
        st.write("Nutritional Data Visualization:")
        visualize_nutrition_data(nutrition_data)
        
        # Analyze nutrition data using AI
        st.write("Analyzing nutritional impact...")
        analysis_result = analyze_nutrition_with_gemini(nutrition_data)
        st.text_area("AI Analysis", analysis_result, height=300)
        
        # Search related articles
        st.write("Searching for related articles...")
        search_results = google_search_nutrition(nutrition_data)
        
        if "Error" in search_results:
            st.error(search_results["Error"])
        else:
            for component, articles in search_results.items():
                st.write(f"Articles for {component}:")
                for article in articles:
                    st.write(f"- **{article['Title']}**: [Link]({article['URL']})")
                    st.write(f"  _Snippet_: {article['Snippet']}")
        
        # Cleanup temporary image file
        os.remove(image_path)

if __name__ == "__main__":
    main()
