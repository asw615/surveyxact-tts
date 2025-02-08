import os
import json
import subprocess
import pyperclip
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup

# Use the external "regex" library for \p{L} support
import regex  # pip install regex


# -------------------------------------------------------------------------
# 1) HTML TEMPLATE
#    We define a <script> block that does the same letter-only approach
#    in JavaScript, so front-end keys match exactly the Python side.
# -------------------------------------------------------------------------
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
      console.log("Letter-only TTS Mapping loaded:", ttsMapping);
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
    // 3) Letter-only cleanup function
    //    We remove all chars except letters, using \p{L} with the 'u' flag.
    // ----------------------------------------------------------------------
    function letterOnlyKey(rawText) {
      let s = rawText.toLowerCase();
      // Strip out anything not a letter
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
      // create the "letter-only" key from the DOM text
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
        // If the element is inside .battery-grid AND has <input> or <label>, skip
        const inBattery = !!elem.closest(".battery-grid");
        if (inBattery && (elem.querySelector("input") || elem.querySelector("label"))) {
          return;
        }
        const inTableCell = !!elem.closest("td");

        // A) If "closed-vertical-choice" and <label>
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
            // B) closed-vertical-choice but not a <label> => wrap
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
          // C) not in a table cell => wrap in a div
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
          // D) in a table cell => just append
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


# -------------------------------------------------------------------------
# 2) MAIN APP
# -------------------------------------------------------------------------
class TTSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SurveyXact TTS Generator — Letters-only Matching")

        # Window sizing + theme
        self.geometry("800x650")
        ctk.set_appearance_mode("System")       # or "Dark"/"Light"
        ctk.set_default_color_theme("dark-blue")  # or "blue"/"green"

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Header label
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="SurveyXact TTS Generator (Letters-only Matching)",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5))

        # Survey ID
        self.survey_id_label = ctk.CTkLabel(self.main_frame, text="Survey ID:")
        self.survey_id_label.grid(row=1, column=0, padx=(20,5), pady=10, sticky="e")

        self.survey_id_entry = ctk.CTkEntry(self.main_frame, width=220)
        self.survey_id_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        # Excel File
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

        # Generate & Copy Buttons
        self.generate_button = ctk.CTkButton(
            self.main_frame,
            text="Generate TTS",
            command=self.run_tts
        )
        self.generate_button.grid(row=3, column=0, padx=10, pady=(10,5), sticky="e")

        self.copy_button = ctk.CTkButton(
            self.main_frame,
            text="Copy HTML",
            command=self.copy_html
        )
        self.copy_button.grid(row=3, column=1, padx=10, pady=(10,5), sticky="w")

        # HTML snippet label
        self.html_label = ctk.CTkLabel(
            self.main_frame,
            text="Final tts.html Code Snippet:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.html_label.grid(row=4, column=0, columnspan=3, padx=20, pady=(20,5), sticky="w")

        # Text box for HTML snippet
        self.html_textbox = ctk.CTkTextbox(self.main_frame, width=700, height=250)
        self.html_textbox.grid(row=5, column=0, columnspan=3, padx=20, pady=5, sticky="nsew")

        # Status label
        self.status_label = ctk.CTkLabel(self.main_frame, text="", text_color="gray")
        self.status_label.grid(row=6, column=0, columnspan=3, padx=20, pady=10, sticky="w")

        # Let the middle row expand
        self.main_frame.rowconfigure(5, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Piper model paths
        self.language_models = {
            "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx"),
            "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx")
        }
        self.config_files = {
            "da": os.path.expanduser("~/piper_models/da_DK/da_DK-talesyntese-medium.onnx.json"),
            "en": os.path.expanduser("~/piper_models/en_US/en_US-hfc_female-medium.onnx.json")
        }

    def browse_excel(self):
        """Open file dialog to pick the Excel file."""
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
        """Generate TTS and store letter-only keys in the JSON mapping."""
        survey_id = self.survey_id_entry.get().strip()
        excel_file = self.excel_path_entry.get().strip()

        if not survey_id:
            messagebox.showerror("Error", "Please enter a Survey ID.")
            return
        if not excel_file:
            messagebox.showerror("Error", "Please select an Excel file.")
            return

        # 1) Read Excel
        try:
            df = pd.read_excel(excel_file, sheet_name="Translations")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file:\n{e}")
            return

        # 2) Prepare output
        output_base = "TTS_outputs"
        os.makedirs(output_base, exist_ok=True)

        hosting_base = f"docs/{survey_id}"
        os.makedirs(hosting_base, exist_ok=True)

        tts_mapping = {}

        # 3) We'll define two text transformations:
        #    A) text_for_tts: the "original" text with normal spacing for Piper
        #    B) letter_key: the "stripped" version used as the JSON key

        def cleanup_for_tts(raw):
            """Basic cleanup for the text read by Piper (strip or unify spaces)."""
            # Remove HTML tags
            text = BeautifulSoup(raw, "html.parser").get_text()
            # Replace non-breaking spaces
            text = text.replace("\u00a0", " ")
            # Collapse multiple spaces (including newlines)
            import re
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        def letter_only_key(raw):
            """Remove all non-letter chars, and lowercase the rest (using 'regex' library)."""
            s = raw.lower()
            # \p{L} => any Unicode letter
            s = regex.sub(r'[^\p{L}]', '', s)
            return s

        # 4) Generate TTS
        try:
            for lang, model_path in self.language_models.items():
                if lang not in df.columns:
                    continue  # skip if that column doesn't exist

                lang_folder = os.path.join(output_base, lang)
                os.makedirs(lang_folder, exist_ok=True)

                for i, raw_text in enumerate(df[lang].dropna()):
                    # A) text we pass to Piper
                    text_for_tts = cleanup_for_tts(raw_text)

                    # B) letter-only key for the dictionary
                    key = letter_only_key(text_for_tts)

                    file_name = f"output_{i}.wav"
                    file_path = os.path.join(lang_folder, file_name)
                    hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"

                    # Piper call
                    cmd = [
                        "/opt/anaconda3/bin/piper",
                        "--model", model_path,
                        "--config", self.config_files[lang],
                        "--output_file", file_path
                    ]
                    subprocess.run(cmd, input=text_for_tts, text=True, check=True)

                    # Move wav to hosting folder
                    lang_hosting_folder = os.path.join(hosting_base, lang)
                    os.makedirs(lang_hosting_folder, exist_ok=True)
                    final_host_path = os.path.join(lang_hosting_folder, file_name)
                    os.rename(file_path, final_host_path)

                    # Store the letter-only key => URL
                    tts_mapping[key] = hosted_url

        except Exception as e:
            messagebox.showerror("Error", f"TTS generation failed:\n{e}")
            return

        # 5) Save the mapping
        mapping_json_path = os.path.join(hosting_base, "tts_mapping.json")
        with open(mapping_json_path, "w", encoding="utf-8") as json_file:
            json.dump(tts_mapping, json_file, indent=4, ensure_ascii=False)

        # 6) Prepare the final HTML snippet
        tts_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/tts_mapping.json"
        updated_html = HTML_TEMPLATE.replace("PLACEHOLDER_FOR_TTS_MAPPING_URL", tts_url)

        # 7) Display snippet
        self.html_textbox.delete("0.0", "end")
        self.html_textbox.insert("0.0", updated_html)

        # 8) Status
        self.status_label.configure(
            text=f"TTS Complete! Mapping saved to {mapping_json_path}",
            text_color="green"
        )

    def copy_html(self):
        """Copy the HTML snippet to the clipboard."""
        html_code = self.html_textbox.get("0.0", "end")
        pyperclip.copy(html_code)
        self.status_label.configure(
            text="HTML code copied to clipboard!",
            text_color="blue"
        )


# -------------------------------------------------------------------------
# 3) MAIN RUNNER
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = TTSApp()
    app.mainloop()
