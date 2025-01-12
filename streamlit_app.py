import os
import easyocr
import streamlit as st
from PIL import Image
from googleapiclient.discovery import build

# Configure the API key securely from Streamlit's secrets
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
GOOGLE_CX = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

# Initialize EasyOCR for text extraction
reader = easyocr.Reader(['en'])

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

# Function to extract text from image using EasyOCR
def extract_text_from_image(image_path):
    result = reader.readtext(image_path)
    extracted_text = []
    for detection in result:
        text = detection[1]
        extracted_text.append(text)
    return "\n".join(extracted_text)

# Streamlit UI
def main():
    st.title("Nutrition Label Scanner")

    st.write("Upload a PNG or JPG image of a food label, and we'll scan it for allergens and unhealthy ingredients.")

    # Image uploader
    uploaded_image = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])

    if uploaded_image:
        image = Image.open(uploaded_image)

        # Ensure the "temp" directory exists
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        image_path = os.path.join(temp_dir, uploaded_image.name)
        image.save(image_path)

        st.image(image, caption="Uploaded Image.", use_column_width=True)

        # Extract text from image using EasyOCR
        st.write("Extracting text from the image...")
        extracted_text = extract_text_from_image(image_path)
        st.text_area("Extracted Text", extracted_text, height=300)

        # Optionally, search for articles about unhealthy ingredients using Google Search API
        if extracted_text:
            st.write("Searching for related articles...")
            ingredients = extracted_text.split("\n")
            for ingredient in ingredients[:5]:  # Limit to top 5 results
                search_results = google_search(ingredient)
                for result in search_results:
                    st.write(f"- {result['Title']}: {result['URL']}")

if __name__ == "__main__":
    main()
