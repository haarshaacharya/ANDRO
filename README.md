# 🤖 ANDRO — Personal AI Assistant

An intelligent, local personal AI desktop assistant built with Python that interacts through voice and text, understands natural language (English, Hindi, and Hinglish), and automates web browsers, desktop applications, screen vision analysis, and Git operations with production-grade reliability.

---

## 📌 About ANDRO

**ANDRO** is designed to run locally on Windows, powered by local LLM models through Ollama (e.g. `qwen3:8b` for conversational reasoning and function execution, and `llava`/`moondream` for vision tasks). 

It bridges natural voice conversations with practical computer automation—allowing you to open applications, search and play YouTube videos, perform web research, type text, capture screenshots, analyze your screen for errors, search files, and manage Git repositories using simple everyday speech or typed commands.

ANDRO supports **English**, **Hindi**, and **Hinglish** natural language phrasing (e.g., *"Open YouTube and play Techno Gamerz"*, *"Notepad kholo aur hello likho"*, *"Screen par kya error hai"*).

---

## ✨ Features

### 🎙️ Voice Interaction
- **Microphone Input:** Real-time voice capture powered by `SpeechRecognition` and `PyAudio`.
- **Speech Synthesis:** Fast, natural voice feedback powered by `pyttsx3` with non-blocking background thread processing.
- **Bilingual Understanding:** Seamlessly processes commands spoken in English, Hindi, or conversational Hinglish.

---

### 🔴🟢 Privacy-First Wake Word System
- **Starts in SLEEPING Mode:** When launched, ANDRO stays in `🔴 SLEEPING` mode without performing actions or recording unnecessary audio.
- **Strict Wake Phrase:** Activates strictly on *"Hey ANDRO"* or *"Hello ANDRO"*.
- **False-Positive Prevention:** Rejects unrelated phrases such as *"Android development"*, *"Android phone"*, or *"Android studio"*.
- **Continuous Active State:** Once activated, ANDRO transitions to `🟢 ACTIVE` mode and remains active across multiple commands without timing out or sleeping after a single response.
- **Sleep Command:** Returns to `🔴 SLEEPING` mode only when the user explicitly says *"Bye ANDRO"* or *"Goodbye ANDRO"* (does **not** close the application).
- **Emergency STOP:** Saying or typing *"STOP ANDRO"* immediately aborts active tasks while keeping ANDRO active.
- **Complete Exit / Shutdown:** Saying or typing *"Exit ANDRO"*, *"Close ANDRO"*, or *"Shutdown ANDRO"* responds with *"Goodbye. Shutting down ANDRO."*, safely stops tasks, halts background listening loops, and cleanly terminates the application.
- **Speech Echo Prevention:** Automatically pauses microphone listening while ANDRO is speaking, with a post-speech cooldown buffer to prevent the assistant from hearing and executing its own voice.

---

### 🧠 AI Agent
- **Local Ollama Integration:** Powered by local models (`qwen3:8b`) with zero cloud lock-in.
- **Structured Tool Routing:** Employs dynamic function calling to route queries to specialized automation tools.
- **Conversational Fallback:** Naturally answers questions, helps with coding, or chats if no automation tool is needed.
- **Multi-Step Execution:** Breaks compound requests into sequential sub-tasks (e.g. *"Open Notepad and type Hello from ANDRO"*).

---

### ⚡ Fast Command Routing
- High-precision sub-millisecond intent matcher intercepts common unambiguous commands (e.g. *"Open Chrome"*, *"Search Techno Gamerz"*, *"Take a screenshot"*, *"Check Git status"*) directly in `< 1ms` without waiting for LLM completion delays.

---

### 🌐 Browser Automation
- **Chrome Personal Profile:** Automatically launches Google Chrome using the configured personal `Profile 1` directory.
- **Website Navigation:** Instantly opens requested domains (e.g. `storagge.in`, `github.com`, `google.com`).
- **Google Search:** Searches queries directly on Google in browser tabs.
- **YouTube Search & Playback:** 
  - *"Search Techno Gamerz"* $\rightarrow$ Opens YouTube search results.
  - *"Open YouTube and play Techno Gamerz"* $\rightarrow$ Resolves top video and starts playback immediately.
- **Playwright Automation:** Browser automation foundation via Playwright for browser interactions.

---

### 💻 Desktop Automation
- **Application Launcher:** Launches desktop apps (e.g. Chrome, Notepad, Calculator, Paint, File Explorer, VS Code).
- **Text Typing:** Injects text, Unicode, and emojis into focused windows using clipboard simulation (`pyperclip` + `pyautogui`).
- **Keyboard Control:** Presses individual keys (`Enter`, `Esc`, `Tab`, `Space`, `F5`) and executes shortcut combinations (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`).
- **Mouse Control:** Swift mouse cursor movement and left/right/double click execution.
- **Screenshots:** Captures high-resolution timestamped screenshots to `Pictures/ANDRO_Screenshots`.
- **Failsafe Protection:** Enabled `pyautogui.FAILSAFE` for emergency cursor corner aborts.

---

### 👁️ Smart Screen Vision
- **On-Demand Inspection:** Triggered only when requested (e.g. *"What is on my screen?"*, *"Explain this error"*).
- **Ollama Vision Inference:** Uses multimodal vision models (`llava`, `moondream`, `qwen2.5-vl`) to inspect active windows, error dialogues, and UI elements.
- **Privacy Rule:** Temporary screen captures are wiped immediately from memory and disk after inference completes. No continuous screen monitoring.

---

### 📂 File Search
- **Local Search:** Fast multi-directory scanning across user workspaces, documents, and desktop folders.
- **Natural Phrasing:** Understands commands like *"Find my ANDRO project"* or *"Mera project dhundo"*.

---

### 🔧 Git Automation
- **Repository Inspection:** Checks `git status`, tracked files, staged changes, and current branch.
- **Staging & Commits:** Runs `git add .` and `git commit -m "<message>"`.
- **Safety Confirmation:** `git push` strictly requires explicit user confirmation (`YES` / `NO`) before pushing commits to GitHub.

---

### 🖥️ Modern GUI
- **CustomTkinter Dashboard:** Dark obsidian and glassmorphic UI layout.
- **Visual Bubble Stream:** Distinct chat bubbles for user messages and formatted response cards for ANDRO.
- **Quick Action Chips:** One-click shortcuts for Screen Vision, YouTube, Google Search, Notepad, and Git.
- **5-State Live Status Indicator:**
  - 🔴 `SLEEPING` — Waiting for wake phrase
  - 🟢 `ACTIVE` — Listening and ready for commands
  - 🟡 `LISTENING` — Actively capturing microphone audio
  - 🟠 `PROCESSING` — Thinking and executing tools
  - 🔵 `SPEAKING` — Delivering voice response

---

### 📊 Logging & Reliability
- **Local Daily Activity Logging:** Structured logs saved locally to `logs/andro_YYYY-MM-DD.log` recording state transitions, commands, and tool results.
- **Centralized Error Handling:** User-friendly explanations for missing models, network outages, or locked profiles with zero raw Python tracebacks.
- **Multi-Step Failure Halting:** If a sequential sub-task fails, ANDRO halts remaining dependent steps and reports the exact issue.

---

### ⚡ Performance Optimization
- **Low-Latency Voice Capture:** Ambient noise calibration reduced to `0.15s` with `pause_threshold = 0.4s`.
- **Fast Desktop Actions:** PyAutoGUI pause delay tuned to `0.05s` with `0.01s` clipboard typing.
- **Crisp Speech Rate:** PyTTSx3 speech synthesis rate tuned to `205 WPM`.
- **Sub-Second Intent Routing:** Pre-router executes standard tools in under `1ms`.

---

## 🛠️ Technologies Used

| Technology / Library | Purpose |
| :--- | :--- |
| **Python 3.10+** | Core programming language |
| **Ollama** | Local LLM runtime (`qwen3:8b`, `llava`) |
| **SpeechRecognition** | Audio transcription & voice command input |
| **PyAudio** | Cross-platform audio I/O streaming |
| **pyttsx3** | Local offline Text-to-Speech synthesis |
| **PyAutoGUI** | GUI automation, keyboard keys, shortcuts, mouse |
| **Pyperclip** | Fast Unicode clipboard text injection |
| **Pillow (PIL)** | Safe native image grabbing for screen vision |
| **Playwright** | Browser automation engine |
| **CustomTkinter** | Modern dark-themed desktop GUI |
| **Rich** | Formatted colored terminal logging |
| **Git** | Version control integration |

---

<<<<<<< HEAD
=======
## 📦 Installation

### 1. Clone the Repository
```powershell
git clone https://github.com/haarshaacharya/ANDRO.git
cd ANDRO
```

### 2. Set Up Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Install Playwright Browsers (Optional for browser automation)
```powershell
playwright install chromium
```

### 5. Install and Start Ollama
1. Download Ollama from [https://ollama.com](https://ollama.com).
2. Pull the required models:
```powershell
# Core conversational & reasoning model
ollama pull qwen3:8b

# Vision model for screen analysis (optional but recommended)
ollama pull llava
```

---

## 🚀 HOW TO START ANDRO

### Option 1: One-Click Windows Launcher (Standard)
> **Double-click `START_ANDRO.bat`** in the project root folder.
- Automatically sets the project directory.
- Activates the existing `.venv` virtual environment.
- Launches the modern ANDRO Desktop GUI.
- Validates the environment and shows clear helpful error messages if Python or `.venv` is missing.

### Option 2: Hidden Terminal Desktop Startup (Recommended)
> **Double-click `START_ANDRO.vbs`** in the project root folder.
- Launches `START_ANDRO.bat` silently in the background without displaying any Command Prompt or PowerShell terminal window.
- The ANDRO GUI opens directly like a native Windows desktop application.

### Option 3: Diagnostic & Debug Launcher (Console Output + Pause)
> **Double-click `DEBUG_ANDRO.bat`** in the project root folder.
- Runs ANDRO with a visible console window.
- Prints the Python executable path, Python version, and working directory.
- Pauses when the application terminates so you can inspect any debug or error messages.

### Option 4: Manual Terminal Launch
```powershell
# Run the Desktop GUI
python gui.py

# Or run the Interactive Terminal & Wake-Word mode
python main.py
```

---

## 🗣️ Voice & Text Command Lifecycle

```
 Double-click START_ANDRO.vbs / START_ANDRO.bat
                      ↓
               ANDRO GUI opens
                      ↓
               🔴 ANDRO is SLEEPING
                      ↓
            User says "Hey ANDRO"
                      ↓
               🟢 ANDRO becomes ACTIVE
                      ↓
             User gives commands...
                      ↓
  "Bye ANDRO"  ──────────────→  🔴 ANDRO sleeps (ready to wake up again)
  "STOP ANDRO" ──────────────→  🛑 Abort active task only (remains active)
  "Exit ANDRO" ──────────────→  👋 Cleanly shut down & close application
```

---

## 📋 Command Reference Table

| Intent | Voice / Text Command | Behavior |
| :--- | :--- | :--- |
| **Activate Assistant** | *"Hey ANDRO"* / *"Hello ANDRO"* | Wakes ANDRO up from `🔴 SLEEPING` to `🟢 ACTIVE`. |
| **Go to Sleep** | *"Bye ANDRO"* / *"Goodbye ANDRO"* | Puts ANDRO to sleep (`🔴 SLEEPING`). **Does NOT close the app.** |
| **Emergency Stop** | *"STOP ANDRO"* / *"Stop"* / *"Ruko"* | Aborts current multi-step task safely; ANDRO remains `🟢 ACTIVE`. |
| **Complete Exit** | *"Exit ANDRO"* / *"Close ANDRO"* / *"Shutdown ANDRO"* | Speaks farewell, halts loops, closes GUI, and **completely closes application**. |
| **Screen Vision** | *"What is on my screen?"* / *"Explain this error"* | Captures screen on demand and visually analyzes active error or window. |
| **YouTube Play** | *"Open YouTube, search Techno Gamerz and play the first video"* | Resolves top video stream and begins playback immediately. |
| **YouTube Search** | *"Search Techno Gamerz on YouTube"* | Opens YouTube search results page in Chrome Profile 1. |
| **Google Search** | *"Search latest AI news on Google"* | Opens search results directly on Google in browser. |
| **Desktop Automation** | *"Open Notepad and type Hello from ANDRO"* | Multi-step task: launches Notepad, focuses, and injects text. |
| **Screenshots** | *"Take a screenshot"* | Captures screen to `Pictures/ANDRO_Screenshots`. |
| **Git Status** | *"Check my Git status"* | Inspects modified files and branch status. |
| **Git Commit** | *"Commit changes with message Added new feature"* | Stages all changes and creates commit. |
| **Git Push** | *"Push my changes to GitHub"* | Requests explicit confirmation (`YES`/`NO`) before pushing. |

---

## 📁 Project Structure

```
ANDRO/
│
├── START_ANDRO.vbs           # Silent Windows desktop launcher (hidden terminal)
├── START_ANDRO.bat           # One-click Windows batch launcher (direct .venv python)
├── DEBUG_ANDRO.bat           # Diagnostic & debug launcher (visible console + pause)
├── main.py                   # Terminal interactive & wake-word entry point
├── agent.py                  # Multi-step AI agent & intent routing engine
├── gui.py                    # CustomTkinter modern desktop GUI dashboard
├── requirements.txt          # Project dependencies
├── README.md                 # Complete project documentation
├── .gitignore                # Git ignore rules for clean repository
│
├── tools/                    # Modular automation tool suite
│   ├── voice.py              # Low-latency microphone speech recognition
│   ├── speaker.py            # Non-blocking Text-to-Speech synthesis
│   ├── wake_word.py          # Strict wake-word, sleep, stop & exit command matcher
│   ├── state_manager.py      # Audio state tracker & echo prevention
│   ├── logger.py             # Local daily activity logging
│   ├── browser_control.py    # Chrome Profile 1 & YouTube stream resolver
│   ├── browser.py            # Browser navigation fallbacks
│   ├── desktop.py            # Safe PyAutoGUI keyboard/mouse automation
│   ├── vision.py             # Multi-tier screen vision & Ollama analyzer
│   ├── system.py             # Windows application launcher & Chrome finder
│   ├── files.py              # Local workspace and disk file search
│   └── git_tools.py          # Git status, staging, commit & push tools
│
└── logs/                     # Local daily log storage (.gitignore protected)
    └── .gitkeep
```

---

## 🔒 Privacy & Safety

- **Local AI Processing:** LLM reasoning and Vision analysis run completely on your local machine through Ollama.
- **On-Demand Vision:** Screen capture is never continuous; screenshots are captured strictly on user command and wiped immediately after analysis.
- **Safe Git Operations:** Remote pushes require explicit user confirmation (`YES` / `NO`).
- **Emergency Abort:** Immediate `"STOP ANDRO"` command aborts compound tasks safely.
- **Failsafe Controls:** PyAutoGUI failsafe is enabled to prevent uncontrolled cursor movements.
- **Local Activity Logs:** Daily activity records are stored locally in `logs/` without external telemetry.

---

## 🚧 Current Limitations

- **Ollama Dependency:** Requires the local Ollama service to be running with the configured model (`qwen3:8b`).
- **Voice Recognition:** Recognition accuracy depends on microphone quality and ambient background noise.
- **Vision Model Hardware:** Vision analysis requires sufficient GPU/RAM resources for responsive inference.
- **Windows Focus:** Desktop typing automation assumes standard Windows focus behavior for target windows.

---

## 🚀 Future Improvements

- [ ] Support for offline local speech-to-text models (e.g. Whisper.cpp / Faster-Whisper).
- [ ] Multi-monitor support for smart screen vision analysis.
- [ ] Extended application plugins for media players and development environments.
- [ ] Customizable theme settings in GUI dashboard.

---

## 👨‍💻 Author

**Haarsh Aacharya**  
*Creator & Developer of ANDRO*
