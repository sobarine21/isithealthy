import os
import paddleocr
import streamlit as st
from PIL import Image
import google.generativeai as genai
import requests
import pandas as pd
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Set up Google API keys
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
GOOGLE_CX = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

# Initialize PaddleOCR for text extraction
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Function to interact with Google Search API
def google_search(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    response = service.cse().list(q=query, cx=GOOGLE_CX).execute()
    results = response.get("items", [])
    search_results = []
    
    for result in results:
        search_results.append({
            "Title": result.get("title"),
            "URL": result.get("link"),
            "Snippet": result.get("snippet"),
        })
    return search_results

# Function to extract text from image using PaddleOCR
def extract_text_from_image(image_path):
    result = ocr.ocr(image_path, cls=True)
    extracted_text = []
    for line in result[0]:
        text = line[1][0]
        extracted_text.append(text)
    return "\n".join(extracted_text)

# Function to analyze ingredients using Google Gemini API
def analyze_ingredients_with_gemini(extracted_text):
    try:
        # Load and configure the model for Google Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Generate response from Gemini model
        response = model.generate_content(extracted_text)
        return response.text
    except Exception as e:
        return f"Error analyzing with Gemini: {e}"

# Streamlit UI
def main():
    st.title('Nutrition Label Scanner')

    st.write("Upload a PNG or JPG image of a food label, and we'll scan it for allergens and unhealthy ingredients.")

    # Image uploader
    uploaded_image = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])

    if uploaded_image:
        image = Image.open(uploaded_image)
        image_path = os.path.join("temp", uploaded_image.name)
        image.save(image_path)
        
        st.image(image, caption='Uploaded Image.', use_column_width=True)

        # Extract text from image using PaddleOCR
        st.write("Extracting text from the image...")
        extracted_text = extract_text_from_image(image_path)
        st.text_area("Extracted Text", extracted_text, height=300)

        # Send extracted text to Google Gemini API for analysis
        st.write("Analyzing extracted text for allergens and unhealthy ingredients...")
        analysis_result = analyze_ingredients_with_gemini(extracted_text)
        st.text_area("Analysis Result", analysis_result, height=300)

        # Optionally, search for articles about unhealthy ingredients using Google Search API
        ingredients = analysis_result.split("\n")
        if ingredients:
            st.write("Searching for related articles...")
            for ingredient in ingredients[:5]:  # Limit to top 5 results
                search_results = google_search(ingredient)
                for result in search_results:
                    st.write(f"- {result['Title']}: {result['URL']}")

        else:
            st.write("No relevant analysis found.")

if __name__ == '__main__':
    main()
