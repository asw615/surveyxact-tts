import os
import pandas as pd
import subprocess
import json
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import simpledialog

# 1. Optional mini-GUI to get the Survey ID.
root = tk.Tk()
root.withdraw()  # hide the main window
surveyID = simpledialog.askstring("Survey ID", "Please enter the Survey ID:", parent=root)
if not surveyID:
    print("No Survey ID provided, exiting.")
    exit(1)

# 2. Load Excel file
data_path = "DMJ1LYMR9J9J.xlsx"  # Adjust if needed
df = pd.read_excel(data_path, sheet_name="Translations")

# 3. Define Piper voice models with correct paths
language_models = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx")
}

# 4. Define corresponding config files
config_files = {
    "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx.json"),
    "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx.json")
}

# 5. Helper function to clean HTML tags from text
def clean_text(text):
    return BeautifulSoup(text, "html.parser").get_text()

# 6. Local output folder (for intermediate use)
output_base = "TTS_outputs"
os.makedirs(output_base, exist_ok=True)

# 7. GitHub Pages hosting directory + subfolder named after SurveyID
#    e.g. 'surveyxact-tts/docs/DMJ1LYMR9J9J'
hosting_base = f"docs/{surveyID}"
os.makedirs(hosting_base, exist_ok=True)

# 8. Dictionary to store text-to-URL mappings
tts_mapping = {}

# 9. Process each language
for lang, model in language_models.items():
    lang_folder = os.path.join(output_base, lang)
    os.makedirs(lang_folder, exist_ok=True)
    
    # Iterate over all text entries in the column for this language
    for i, text in enumerate(df[lang].dropna()):
        cleaned_text = clean_text(text)  # remove HTML tags, etc.
        file_name = f"output_{i}.wav"
        file_path = os.path.join(lang_folder, file_name)
        # The final hosted URL now references the surveyID subfolder
        hosted_url = f"https://asw615.github.io/surveyxact-tts/{surveyID}/{lang}/{file_name}"

        # Run Piper CLI command using stdin for text input
        cmd = [
            "/opt/anaconda3/bin/piper",
            "--model", model,
            "--config", config_files[lang],
            "--output_file", file_path
        ]
        subprocess.run(cmd, input=cleaned_text, text=True, check=True)
        
        print(f"Generated: {file_path}")
        
        # Copy (move) files into the GitHub Pages directory
        # e.g. 'surveyxact-tts/docs/<surveyID>/<lang>/output_0.wav'
        lang_hosting_folder = os.path.join(hosting_base, lang)
        os.makedirs(lang_hosting_folder, exist_ok=True)

        # Move the generated WAV into the hosting folder
        final_host_path = os.path.join(lang_hosting_folder, file_name)
        os.rename(file_path, final_host_path)

        # Store mapping (cleaned_text -> hosted_url)
        tts_mapping[cleaned_text] = hosted_url

# 10. Save mapping file (tts_mapping.json) inside the SurveyID folder
mapping_json_path = os.path.join(hosting_base, "tts_mapping.json")
with open(mapping_json_path, "w", encoding="utf-8") as json_file:
    json.dump(tts_mapping, json_file, indent=4, ensure_ascii=False)

print(f"TTS generation complete.\nMapping saved to {mapping_json_path}\nNow commit/push to GitHub.")
