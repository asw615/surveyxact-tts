import os
import pandas as pd
import subprocess
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

# Output folder
output_base = "TTS_outputs"
os.makedirs(output_base, exist_ok=True)

# Process each language
for lang, model in language_models.items():
    lang_folder = os.path.join(output_base, lang)
    os.makedirs(lang_folder, exist_ok=True)
    
    for i, text in enumerate(df[lang].dropna()):
        cleaned_text = clean_text(text)  # Remove HTML tags
        file_path = os.path.join(lang_folder, f"output_{i}.wav")
        
        # Run Piper CLI command using stdin for text input
        cmd = [
            "/opt/anaconda3/bin/piper", "--model", model, "--config", config_files[lang], "--output_file", file_path
        ]
        
        subprocess.run(cmd, input=cleaned_text, text=True, check=True)
        
        print(f"Generated: {file_path}")

print("TTS generation complete.")
