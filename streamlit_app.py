import os
import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
from googleapiclient.discovery import build
from PIL import Image
import easyocr

# Configure Gemini API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Google Search API configuration
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
GOOGLE_CX = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

# Function to extract text from an image using EasyOCR
def extract_text_from_image(image_path):
    results = reader.readtext(image_path)
    extracted_text = "\n".join([result[1] for result in results])  # Combine all text detected
    return extracted_text

# Function to interact with Gemini AI for text analysis
def analyze_text_with_gemini(text):
    try:
        # Load and configure the Gemini AI model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate response from Gemini model
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        return f"Error analyzing with Gemini: {e}"

# Function to interact with Google Search API
def google_search(query):
    try:
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
    except Exception as e:
        return [{"Title": "Error", "URL": "", "Snippet": str(e)}]

# Streamlit UI
def main():
    st.title("Nutrition Label Scanner with AI")
    st.write("Upload an image of a food label to analyze its content for allergens and unhealthy ingredients using AI.")
    
    # Upload image
    uploaded_image = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    
    if uploaded_image:
        # Display uploaded image
        image = Image.open(uploaded_image)
        image_path = os.path.join("temp", uploaded_image.name)
        os.makedirs("temp", exist_ok=True)
        image.save(image_path)
        
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Extract text from image using EasyOCR
        st.write("Extracting text from the image...")
        extracted_text = extract_text_from_image(image_path)
        st.text_area("Extracted Text", extracted_text, height=300)
        
        # Analyze text using Gemini AI
        st.write("Analyzing the text using Gemini AI...")
        analysis_result = analyze_text_with_gemini(extracted_text)
        st.text_area("AI Analysis Result", analysis_result, height=300)
        
        # Search for articles about unhealthy ingredients or allergens
        st.write("Searching for related articles...")
        if analysis_result:
            ingredients = analysis_result.split("\n")[:5]  # Limit to the top 5 lines of analysis
            for ingredient in ingredients:
                st.write(f"Search Results for: {ingredient}")
                search_results = google_search(ingredient)
                for result in search_results:
                    st.write(f"- **{result['Title']}**: [Link]({result['URL']})")
                    st.write(f"  _Snippet_: {result['Snippet']}")
        else:
            st.write("No relevant analysis found.")
        
        # Cleanup temporary image file
        os.remove(image_path)

if __name__ == "__main__":
    main()
