import os
import re
import json
import subprocess
import pyperclip
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup

# -------------------------------------------------------------------------
# 1) HTML TEMPLATE
#    Notice we have a placeholder "PLACEHOLDER_FOR_TTS_MAPPING_URL"
#    which we'll replace with the correct URL referencing your SurveyID.
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
    // 1) Fetch the single TTS mapping (keys for both da, en, etc.)
    // ----------------------------------------------------------------------
    const TTS_MAPPING_URL = "PLACEHOLDER_FOR_TTS_MAPPING_URL";
    let ttsMapping = {};
    try {
      const response = await fetch(TTS_MAPPING_URL);
      ttsMapping = await response.json();
      console.log("Single TTS Mapping loaded:", ttsMapping);
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
    // 3) Cleanup text to avoid invisible chars or double spaces
    // ----------------------------------------------------------------------
    function cleanupText(rawText) {
      // Mirror the logic used in Python
      return rawText
        .replace(/\u00a0/g, " ") // non-breaking space -> normal space
        .replace(/\s+/g, " ")    // collapse multiple spaces
        .trim();
    }

    // ----------------------------------------------------------------------
    // 4) Function to play TTS from the single mapping
    // ----------------------------------------------------------------------
    function playTTS(rawText, iconElem) {
      if (!ttsMapping) {
        console.warn("ttsMapping is not loaded or empty.");
        return;
      }
      const text = cleanupText(rawText);
      if (ttsMapping[text]) {
        // Found an audio file
        const audio = new Audio(ttsMapping[text]);
        audio.play();
        startReadingAnimation(iconElem);
        audio.onended = () => stopReadingAnimation(iconElem);
      } else {
        console.warn(`No TTS audio found for text: "${text}" (raw: "${rawText}")`);
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
    // 8) Insert speaker icons, skipping battery radio/checkbox
    // ----------------------------------------------------------------------
    targetClasses.forEach(cls => {
      const elems = questionsContainer.getElementsByClassName(cls);
      Array.from(elems).forEach(elem => {
        // Skip if already has an icon
        if (elem.classList.contains("audio-icon-added")) return;
        if (!elem.id) {
          elem.id = "elem_" + Math.random().toString(36).substr(2, 9);
        }

        // If the element is inside .battery-grid AND has <input> or <label>, skip
        const inBattery = !!elem.closest(".battery-grid");
        if (inBattery && (elem.querySelector("input") || elem.querySelector("label"))) {
          return;
        }

        // Check if inside a <td>
        const inTableCell = !!elem.closest("td");

        // A) If "closed-vertical-choice"
        if (cls === "closed-vertical-choice") {
          if (elem.tagName.toLowerCase() === "label") {
            // Keep label + icon inline
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
            // If it's not a label, wrap in a span
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

        // B) Not in a table cell
        } else if (!inTableCell) {
          // Wrap in a div for inline-flex
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

        // C) Inside a table cell
        } else {
          // Just append the icon
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
# 2) MAIN APP CLASS (using CustomTkinter for a nicer interface)
# -------------------------------------------------------------------------
class TTSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("SurveyXact TTS Generator — Unified Cleanup")
        self.geometry("800x650")

        # Optional: set themes
        ctk.set_appearance_mode("System")       # or "Dark", "Light"
        ctk.set_default_color_theme("dark-blue")  # or "blue", "green"

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Header
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="SurveyXact TTS Generator",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.header_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5))

        # Survey ID
        self.survey_id_label = ctk.CTkLabel(self.main_frame, text="Survey ID:")
        self.survey_id_label.grid(row=1, column=0, padx=(20,5), pady=10, sticky="e")
        self.survey_id_entry = ctk.CTkEntry(self.main_frame, width=220)
        self.survey_id_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        # Excel path
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

        # Let row 5 expand
        self.main_frame.rowconfigure(5, weight=1)
        # Let column 1 expand
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
        """Main function to run TTS generation logic."""
        survey_id = self.survey_id_entry.get().strip()
        excel_file = self.excel_path_entry.get().strip()

        if not survey_id:
            messagebox.showerror("Error", "Please enter a Survey ID.")
            return
        if not excel_file:
            messagebox.showerror("Error", "Please select an Excel file.")
            return

        # 1) Try reading the Excel
        try:
            df = pd.read_excel(excel_file, sheet_name="Translations")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file:\n{e}")
            return

        # 2) Prepare output directories
        output_base = "TTS_outputs"
        os.makedirs(output_base, exist_ok=True)

        hosting_base = f"docs/{survey_id}"
        os.makedirs(hosting_base, exist_ok=True)

        # 3) Dictionary for text->URL
        tts_mapping = {}

        # 4) Function: unify text cleanup
        def cleanup_text_for_key(raw):
            # (Mimics the front-end's cleanupText())
            # 1) replace non-breaking space
            # 2) collapse multiple spaces
            # 3) trim
            text = raw.replace("\u00a0", " ")
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        # 5) Generate TTS for each language column in your DataFrame
        try:
            for lang, model_path in self.language_models.items():
                if lang not in df.columns:
                    # If your Excel doesn't have that language column, skip
                    continue
                lang_folder = os.path.join(output_base, lang)
                os.makedirs(lang_folder, exist_ok=True)

                # For each text in that column
                for i, text in enumerate(df[lang].dropna()):
                    # Remove any HTML tags (like <br>), then unify spaces
                    # (This is optional if your Excel might have HTML fragments)
                    cleaned_html = BeautifulSoup(text, "html.parser").get_text()
                    key_for_json = cleanup_text_for_key(cleaned_html)

                    file_name = f"output_{i}.wav"
                    file_path = os.path.join(lang_folder, file_name)
                    hosted_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/{lang}/{file_name}"

                    # Piper command
                    cmd = [
                        "/opt/anaconda3/bin/piper",
                        "--model", model_path,
                        "--config", self.config_files[lang],
                        "--output_file", file_path
                    ]
                    subprocess.run(cmd, input=key_for_json, text=True, check=True)

                    # Move to hosting folder
                    lang_hosting_folder = os.path.join(hosting_base, lang)
                    os.makedirs(lang_hosting_folder, exist_ok=True)
                    final_host_path = os.path.join(lang_hosting_folder, file_name)
                    os.rename(file_path, final_host_path)

                    # Store in mapping
                    tts_mapping[key_for_json] = hosted_url

        except Exception as e:
            messagebox.showerror("Error", f"TTS generation failed:\n{e}")
            return

        # 6) Save mapping.json
        mapping_json_path = os.path.join(hosting_base, "tts_mapping.json")
        with open(mapping_json_path, "w", encoding="utf-8") as json_file:
            json.dump(tts_mapping, json_file, indent=4, ensure_ascii=False)

        # 7) Generate final HTML snippet
        tts_url = f"https://asw615.github.io/surveyxact-tts/{survey_id}/tts_mapping.json"
        updated_html = HTML_TEMPLATE.replace("PLACEHOLDER_FOR_TTS_MAPPING_URL", tts_url)

        # Show snippet
        self.html_textbox.delete("0.0", "end")
        self.html_textbox.insert("0.0", updated_html)

        # Update status
        self.status_label.configure(
            text=f"TTS Complete! Mapping saved to {mapping_json_path}",
            text_color="green"
        )

    def copy_html(self):
        """Copy the HTML snippet from the text box to clipboard."""
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
    # You can override theme/appearance here if needed
    # ctk.set_appearance_mode("Dark")
    # ctk.set_default_color_theme("green")

    app = TTSApp()
    app.mainloop()
