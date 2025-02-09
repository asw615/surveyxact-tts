import os
import json
import subprocess
import pyperclip
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup

import regex
import unicodedata

# HTML template for the TTS mapping page
HTML_TEMPLATE = r"""</style>
</head>
<body>
  <!-- 1) CSS for loader animation -->
  <style>
    .loader {
      width: 16px;
      margin-left: 10px;
      aspect-ratio: 1;
      display: inline-block;
      vertical-align: middle;
      --c: no-repeat linear-gradient(#000 0 0);
      background: 
        var(--c) 0% 50%,
        var(--c) 50% 50%,
        var(--c) 100% 50%;
      background-size: 20% 100%;
      animation: l1 1s infinite linear;
    }
    @keyframes l1 {
      0%   { background-size: 20% 100%, 20% 100%, 20% 100% }
      33%  { background-size: 20% 10%,  20% 100%, 20% 100% }
      50%  { background-size: 20% 100%, 20% 10%,  20% 100% }
      66%  { background-size: 20% 100%, 20% 100%, 20% 10%  }
      100% { background-size: 20% 100%, 20% 100%, 20% 100% }
    }
  </style>

  <script>
  document.addEventListener('DOMContentLoaded', async function() {
    // ----------------------------------------------------------------------
    // 1) Fetch the TTS mapping
    // ----------------------------------------------------------------------
    const TTS_MAPPING_URL = "PLACEHOLDER_FOR_TTS_MAPPING_URL";
    let ttsMapping = {};
    try {
      const response = await fetch(TTS_MAPPING_URL);
      ttsMapping = await response.json();
      console.log("Letter-only TTS Mapping (with NFC) loaded:", ttsMapping);
    } catch (error) {
      console.error("Failed to load TTS mapping:", error);
    }

    // ----------------------------------------------------------------------
    // 2) Loader animation
    // ----------------------------------------------------------------------
    function startReadingAnimation(iconElem) {
      iconElem.style.display = "none";
      const loader = document.createElement("div");
      loader.className = "loader";
      iconElem.parentNode.insertBefore(loader, iconElem.nextSibling);
      iconElem._currentAnim = loader;
    }
    function stopReadingAnimation(iconElem) {
      if (iconElem._currentAnim) {
        iconElem._currentAnim.remove();
        iconElem._currentAnim = null;
      }
      iconElem.style.display = "inline-block";
    }

    // ----------------------------------------------------------------------
    // 3) Letter-only cleanup with NFC normalization
    // ----------------------------------------------------------------------
    function letterOnlyKey(rawText) {
      // Force NFC normalization
      let s = rawText.normalize("NFC");
      // Lowercase
      s = s.toLowerCase();
      // Remove everything except letters
      s = s.replace(/[^\p{L}]/gu, "");
      return s;
    }

    // ----------------------------------------------------------------------
    // 4) Function to play TTS
    // ----------------------------------------------------------------------
    function playTTS(rawText, iconElem) {
      if (!ttsMapping) {
        console.warn("ttsMapping is empty or not loaded.");
        return;
      }
      const textKey = letterOnlyKey(rawText);

      if (ttsMapping[textKey]) {
        const audio = new Audio(ttsMapping[textKey]);
        audio.play();
        startReadingAnimation(iconElem);
        audio.onended = () => stopReadingAnimation(iconElem);
      } else {
        console.warn(`No TTS audio found for letterOnlyKey: "${textKey}" (raw: "${rawText}")`);
      }
    }

    // ----------------------------------------------------------------------
    // 5) Speaker icon
    // ----------------------------------------------------------------------
    const SPEAKER_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Speaker_Icon.svg/480px-Speaker_Icon.svg.png";

    // ----------------------------------------------------------------------
    // 6) Classes that get a speaker icon
    // ----------------------------------------------------------------------
    const targetClasses = [
      "text-element",
      "question-title",
      "closed-vertical-choice",
      "row-header-text",
      "battery-grid"
    ];

    // ----------------------------------------------------------------------
    // 7) Container for questions
    // ----------------------------------------------------------------------
    const questionsContainer = document.querySelector("div.questions");
    if (!questionsContainer) {
      console.error("Questions container not found.");
      return;
    }

    // ----------------------------------------------------------------------
    // 8) Insert speaker icons
    // ----------------------------------------------------------------------
    targetClasses.forEach(cls => {
      const elems = questionsContainer.getElementsByClassName(cls);
      Array.from(elems).forEach(elem => {
        if (elem.classList.contains("audio-icon-added")) return;
        if (!elem.id) {
          elem.id = "elem_" + Math.random().toString(36).substr(2, 9);
        }
        // If in battery-grid with input or label, skip
        const inBattery = !!elem.closest(".battery-grid");
        if (inBattery && (elem.querySelector("input") || elem.querySelector("label"))) {
          return;
        }
        const inTableCell = !!elem.closest("td");

        if (cls === "closed-vertical-choice") {
          if (elem.tagName.toLowerCase() === "label") {
            elem.style.display = "inline-flex";
            elem.style.alignItems = "center";

            const icon = document.createElement("img");
            icon.src = SPEAKER_ICON_URL;
            icon.alt = "Speaker";
            icon.style.width = "24px";
            icon.style.height = "24px";
            icon.style.marginLeft = "4px";
            icon.style.cursor = "pointer";
            icon.style.display = "inline-block";
            icon.style.verticalAlign = "middle";

            icon.addEventListener("click", function(e) {
              e.preventDefault();
              const text = elem.innerText;
              if (!text) return;
              playTTS(text, icon);
            });

            elem.appendChild(icon);
            elem.insertAdjacentHTML("afterend", "<br>");
            elem.classList.add("audio-icon-added");

          } else {
            const wrapper = document.createElement("span");
            wrapper.style.display = "inline-flex";
            wrapper.style.alignItems = "center";
            elem.parentNode.insertBefore(wrapper, elem);
            wrapper.appendChild(elem);

            const icon = document.createElement("img");
            icon.src = SPEAKER_ICON_URL;
            icon.alt = "Speaker";
            icon.style.width = "24px";
            icon.style.height = "24px";
            icon.style.marginLeft = "4px";
            icon.style.cursor = "pointer";
            icon.style.display = "inline-block";
            icon.style.verticalAlign = "middle";

            icon.addEventListener("click", function(e) {
              e.preventDefault();
              const text = elem.innerText;
              if (!text) return;
              playTTS(text, icon);
            });

            wrapper.appendChild(icon);
            wrapper.insertAdjacentHTML("afterend", "<br>");
            elem.classList.add("audio-icon-added");
          }
        } else if (!inTableCell) {
          const wrapper = document.createElement("div");
          wrapper.style.display = "inline-flex";
          wrapper.style.alignItems = "center";
          elem.parentNode.insertBefore(wrapper, elem);
          wrapper.appendChild(elem);

          const icon = document.createElement("img");
          icon.src = SPEAKER_ICON_URL;
          icon.alt = "Speaker";
          icon.style.width = "24px";
          icon.style.height = "24px";
          icon.style.marginLeft = "8px";
          icon.style.cursor = "pointer";
          icon.style.display = "inline-block";
          icon.style.verticalAlign = "middle";

          icon.addEventListener("click", function(e) {
            e.preventDefault();
            const text = elem.innerText;
            if (!text) return;
            playTTS(text, icon);
          });

          wrapper.appendChild(icon);
          elem.classList.add("audio-icon-added");
        } else {
          const icon = document.createElement("img");
          icon.src = SPEAKER_ICON_URL;
          icon.alt = "Speaker";
          icon.style.width = "24px";
          icon.style.height = "24px";
          icon.style.marginLeft = "4px";
          icon.style.cursor = "pointer";
          icon.style.display = "inline-block";
          icon.style.verticalAlign = "middle";

          icon.addEventListener("click", function(e) {
            e.preventDefault();
            const text = elem.innerText;
            if (!text) return;
            playTTS(text, icon);
          });

          elem.insertAdjacentElement("beforeend", icon);
          elem.classList.add("audio-icon-added");
        }
      });
    });
  });
  </script>
</body>
</html>
"""

class TTSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SurveyXact TTS Generator (NFC Normalization)")
        self.geometry("800x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Header
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="SurveyXact TTS Generator (with Unicode Normalization)",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5))

        # Survey ID
        self.survey_id_label = ctk.CTkLabel(self.main_frame, text="Survey ID:")
        self.survey_id_label.grid(row=1, column=0, padx=(20,5), pady=10, sticky="e")

        self.survey_id_entry = ctk.CTkEntry(self.main_frame, width=220)
        self.survey_id_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        # Excel file
        self.excel_label = ctk.CTkLabel(self.main_frame, text="Excel File:")
        self.excel_label.grid(row=2, column=0, padx=(20,5), pady=10, sticky="e")

        self.excel_path_entry = ctk.CTkEntry(self.main_frame, width=220, state="disabled")
        self.excel_path_entry.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        self.excel_browse_button = ctk.CTkButton(
            self.main_frame, 
            text="Browse...",
            command=self.browse_excel
        )
        self.excel_browse_button.grid(row=2, column=2, padx=(5,20), pady=10, sticky="w")

        # TTS Generation Method: Piper or OpenAI API
        self.tts_method_label = ctk.CTkLabel(self.main_frame, text="TTS Generation Method:")
        self.tts_method_label.grid(row=3, column=0, padx=20, pady=10, sticky="e")

        self.tts_method_var = ctk.StringVar(value="piper")
        self.piper_radio = ctk.CTkRadioButton(
            self.main_frame, text="Piper", variable=self.tts_method_var, value="piper"
        )
        self.piper_radio.grid(row=3, column=1, padx=5, pady=10, sticky="w")

        self.openai_radio = ctk.CTkRadioButton(
            self.main_frame, text="OpenAI API", variable=self.tts_method_var, value="openai"
        )
        self.openai_radio.grid(row=3, column=2, padx=5, pady=10, sticky="w")

        # OpenAI API Key (only enabled when OpenAI API is selected)
        self.openai_api_key_label = ctk.CTkLabel(self.main_frame, text="OpenAI API Key:")
        self.openai_api_key_label.grid(row=4, column=0, padx=(20,5), pady=10, sticky="e")

        self.openai_api_key_entry = ctk.CTkEntry(self.main_frame, width=220)
        self.openai_api_key_entry.grid(row=4, column=1, padx=5, pady=10, sticky="w")
        self.openai_api_key_entry.configure(state="disabled")
        self.tts_method_var.trace_add("write", lambda *args: self.update_api_key_state())

        # Generate and Copy buttons
        self.generate_button = ctk.CTkButton(
            self.main_frame,
            text="Generate TTS",
            command=self.run_tts
        )
        self.generate_button.grid(row=5, column=0, padx=10, pady=(10,5), sticky="e")

        self.copy_button = ctk.CTkButton(
            self.main_frame,
            text="Copy HTML",
            command=self.copy_html
        )
        self.copy_button.grid(row=5, column=1, padx=10, pady=(10,5), sticky="w")

        # HTML Code label and textbox
        self.html_label = ctk.CTkLabel(
            self.main_frame,
            text="Final tts.html Code Snippet:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.html_label.grid(row=6, column=0, columnspan=3, padx=20, pady=(20,5), sticky="w")

        self.html_textbox = ctk.CTkTextbox(self.main_frame, width=700, height=250)
        self.html_textbox.grid(row=7, column=0, columnspan=3, padx=20, pady=5, sticky="nsew")

        # Status label
        self.status_label = ctk.CTkLabel(self.main_frame, text="", text_color="gray")
        self.status_label.grid(row=8, column=0, columnspan=3, padx=20, pady=10, sticky="w")

        self.main_frame.rowconfigure(7, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Paths for Piper branch (unused in OpenAI branch)
        self.language_models = {
            "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx"),
            "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx")
        }
        self.config_files = {
            "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx.json"),
            "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx.json")
        }

    def update_api_key_state(self):
        if self.tts_method_var.get() == "openai":
            self.openai_api_key_entry.configure(state="normal")
        else:
            self.openai_api_key_entry.configure(state="disabled")

    def browse_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if file_path:
            self.excel_path_entry.configure(state="normal")
            self.excel_path_entry.delete(0, "end")
            self.excel_path_entry.insert(0, file_path)
            self.excel_path_entry.configure(state="disabled")

    def run_tts(self):
        survey_id = self.survey_id_entry.get().strip()
        excel_file = self.excel_path_entry.get().strip()

        if not survey_id:
            messagebox.showerror("Error", "Please enter a Survey ID.")
            return
        if not excel_file:
            messagebox.showerror("Error", "Please select an Excel file.")
            return

        try:
            df = pd.read_excel(excel_file, sheet_name="Translations")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file:\n{e}")
            return

        output_base = "TTS_outputs"
        os.makedirs(output_base, exist_ok=True)
        hosting_base = f"docs/{survey_id}"
        os.makedirs(hosting_base, exist_ok=True)

        tts_mapping = {}

        # Clean up text for TTS (includes NFC normalization)
        def cleanup_for_tts(raw):
            txt = BeautifulSoup(raw, "html.parser").get_text()
            txt = unicodedata.normalize("NFC", txt)
            txt = txt.replace("\u00a0", " ")
            import re
            txt = re.sub(r"\s+", " ", txt)
            return txt.strip()

        # Key function: lowercase and remove non-letter characters (with NFC)
        def letter_only_key(raw):
            s = unicodedata.normalize("NFC", raw)
            s = s.lower()
            s = regex.sub(r'[^\p{L}]', '', s)
            return s

        try:
            if self.tts_method_var.get() == "openai":
                # OpenAI API branch using the new Audio API.
                api_key = self.openai_api_key_entry.get().strip()
                if not api_key:
                    messagebox.showerror("Error", "Please enter the OpenAI API key.")
                    return

                # Import the OpenAI client and instantiate it with your API key.
                from openai import OpenAI
                client = OpenAI(api_key=api_key)

                # Loop through languages (using the keys defined in self.language_models)
                for lang in self.language_models.keys():
                    if lang not in df.columns:
                        continue

                    lang_folder = os.path.join(output_base, lang)
                    os.makedirs(lang_folder, exist_ok=True)

                    for i, raw_text in enumerate(df[lang].dropna()):
                        text_for_tts = cleanup_for_tts(raw_text)
                        key = letter_only_key(text_for_tts)

                        file_name = f"output_{i}.wav"
                        file_path = os.path.join(lang_folder, file_name)
                        hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"

                        # Call the new OpenAI Audio API.
                        # Here, we specify:
                        #   - model: "tts-1"
                        #   - voice: "alloy" (change if desired)
                        #   - input: the cleaned text
                        #   - response_format: "wav" to get WAV files.
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input=text_for_tts,
                            response_format="wav"
                        )
                        # Stream the generated audio to file.
                        response.stream_to_file(file_path)

                        lang_hosting_folder = os.path.join(hosting_base, lang)
                        os.makedirs(lang_hosting_folder, exist_ok=True)
                        final_host_path = os.path.join(lang_hosting_folder, file_name)
                        os.rename(file_path, final_host_path)

                        tts_mapping[key] = hosted_url

            else:
                # Piper branch (original method)
                for lang, model_path in self.language_models.items():
                    if lang not in df.columns:
                        continue

                    lang_folder = os.path.join(output_base, lang)
                    os.makedirs(lang_folder, exist_ok=True)

                    for i, raw_text in enumerate(df[lang].dropna()):
                        text_for_tts = cleanup_for_tts(raw_text)
                        key = letter_only_key(text_for_tts)

                        file_name = f"output_{i}.wav"
                        file_path = os.path.join(lang_folder, file_name)
                        hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"

                        cmd = [
                            "/opt/anaconda3/bin/piper",
                            "--model", model_path,
                            "--config", self.config_files[lang],
                            "--output_file", file_path
                        ]
                        subprocess.run(cmd, input=text_for_tts, text=True, check=True)

                        lang_hosting_folder = os.path.join(hosting_base, lang)
                        os.makedirs(lang_hosting_folder, exist_ok=True)
                        final_host_path = os.path.join(lang_hosting_folder, file_name)
                        os.rename(file_path, final_host_path)

                        tts_mapping[key] = hosted_url

        except Exception as e:
            messagebox.showerror("Error", f"TTS generation failed:\n{e}")
            return

        mapping_json_path = os.path.join(hosting_base, "tts_mapping.json")
        with open(mapping_json_path, "w", encoding="utf-8") as json_file:
            json.dump(tts_mapping, json_file, indent=4, ensure_ascii=False)

        tts_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/tts_mapping.json"
        updated_html = HTML_TEMPLATE.replace("PLACEHOLDER_FOR_TTS_MAPPING_URL", tts_url)

        self.html_textbox.delete("0.0", "end")
        self.html_textbox.insert("0.0", updated_html)

        self.status_label.configure(
            text=f"TTS Complete! Mapping saved to {mapping_json_path}",
            text_color="green"
        )

    def copy_html(self):
        html_code = self.html_textbox.get("0.0", "end")
        pyperclip.copy(html_code)
        self.status_label.configure(
            text="HTML code copied to clipboard!",
            text_color="blue"
        )

if __name__ == "__main__":
    app = TTSApp()
    app.mainloop()
