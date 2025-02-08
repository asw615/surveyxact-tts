import os
import pandas as pd
import subprocess
import json
from bs4 import BeautifulSoup

# Load Excel file
data_path = "DMJ1LYMR9J9J.xlsx"  # Adjust if needed
df = pd.read_excel(data_path, sheet_name="Translations")

# Define Piper voice models with correct paths
language_models = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx")
}

# Define corresponding config files
config_files = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx.json"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx.json")
}

# Function to clean HTML tags from text
def clean_text(text):
    return BeautifulSoup(text, "html.parser").get_text()

# Output folder (for local use)
output_base = "TTS_outputs"
os.makedirs(output_base, exist_ok=True)

# GitHub Pages hosting directory
hosting_base = "surveyxact-tts/docs"
os.makedirs(hosting_base, exist_ok=True)

# Dictionary to store text-to-URL mapping
tts_mapping = {}

# Process each language
for lang, model in language_models.items():
    lang_folder = os.path.join(output_base, lang)
    os.makedirs(lang_folder, exist_ok=True)
    
    for i, text in enumerate(df[lang].dropna()):
        cleaned_text = clean_text(text)  # Remove HTML tags
        file_name = f"output_{i}.wav"
        file_path = os.path.join(lang_folder, file_name)
        hosted_url = f"https://asw615.github.io/surveyxact-tts/{lang}/{file_name}"
        
        # Run Piper CLI command using stdin for text input
        cmd = [
            "/opt/anaconda3/bin/piper", "--model", model, "--config", config_files[lang], "--output_file", file_path
        ]
        
        subprocess.run(cmd, input=cleaned_text, text=True, check=True)
        
        print(f"Generated: {file_path}")
        
        # Copy files to GitHub Pages directory
        lang_hosting_folder = os.path.join(hosting_base, lang)
        os.makedirs(lang_hosting_folder, exist_ok=True)
        os.rename(file_path, os.path.join(lang_hosting_folder, file_name))
        
        # Store mapping
        tts_mapping[cleaned_text] = hosted_url

# Save mapping file
with open(os.path.join(hosting_base, "tts_mapping.json"), "w") as json_file:
    json.dump(tts_mapping, json_file, indent=4)

print("TTS generation complete. Now commit and push to GitHub.")
