import os
import sys
import time
import threading
from pathlib import Path
from rich.console import Console

# Core ANDRO tools
from tools.voice import listen
from tools.speaker import speak
from tools.wake_word import WakeWordListener
from tools.git_tools import git_push
from agent import AndroAgent

PROJECT_PATH = Path(__file__).parent.resolve()
console = Console()

# Try importing CustomTkinter; fallback to standard Tkinter with sleek styling
try:
    import customtkinter as ctk
    GUI_FRAMEWORK = "customtkinter"
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    ctk = None
    GUI_FRAMEWORK = "tkinter"


class AndroGUI:
    """World-Class Modern Desktop GUI for ANDRO Personal AI Assistant."""

    def __init__(self):
        self.agent = AndroAgent(
            project_path=PROJECT_PATH,
            console=console,
            model="qwen3:8b",
            on_message=self.add_assistant_message,
        )
        self.listener = WakeWordListener()
        self.state = "SLEEPING"  # SLEEPING, ACTIVE, PROCESSING
        self.is_wake_word_running = False
        self.waiting_for_push = False
        self.chat_history = []

        if GUI_FRAMEWORK == "customtkinter":
            self._init_customtkinter()
        else:
            self._init_standard_tkinter()

    # -------------------------------------------------------------
    # CUSTOMTKINTER MODERN INTERFACE
    # -------------------------------------------------------------
    def _init_customtkinter(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("ANDRO — Next-Gen Personal AI Assistant")
        self.root.geometry("1100x740")
        self.root.minsize(920, 620)
        self.root.configure(fg_color="#090d16")

        # Main Layout: Left Sidebar + Right Dashboard
        self.sidebar = ctk.CTkFrame(self.root, width=270, fg_color="#0f172a", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_content = ctk.CTkFrame(self.root, fg_color="#090d16", corner_radius=0)
        self.main_content.pack(side="right", fill="both", expand=True)

        # ==========================================
        # LEFT SIDEBAR COMPONENTS
        # ==========================================
        # 1. Branding Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(24, 16))

        logo_title = ctk.CTkLabel(
            brand_frame,
            text="🤖 ANDRO AI",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#38bdf8",
        )
        logo_title.pack(anchor="w")

        logo_sub = ctk.CTkLabel(
            brand_frame,
            text="Personal AI Assistant & Agent",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#64748b",
        )
        logo_sub.pack(anchor="w")

        # 2. Live Status Card
        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#1e293b", corner_radius=12)
        self.status_card.pack(fill="x", padx=16, pady=8)

        status_header = ctk.CTkLabel(
            self.status_card,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#94a3b8",
        )
        status_header.pack(anchor="w", padx=14, pady=(12, 4))

        self.status_pill = ctk.CTkLabel(
            self.status_card,
            text="🔴 SLEEPING",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#f87171",
            fg_color="#0f172a",
            corner_radius=8,
            padx=12,
            pady=6,
        )
        self.status_pill.pack(fill="x", padx=14, pady=4)

        self.status_detail = ctk.CTkLabel(
            self.status_card,
            text="Waiting for 'Hey ANDRO' or text command",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#94a3b8",
            wraplength=220,
            justify="left",
        )
        self.status_detail.pack(anchor="w", padx=14, pady=(4, 12))

        # 3. Voice Controls
        voice_label = ctk.CTkLabel(
            self.sidebar,
            text="VOICE CONTROL",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#64748b",
        )
        voice_label.pack(anchor="w", padx=20, pady=(16, 6))

        self.wake_btn = ctk.CTkButton(
            self.sidebar,
            text="🎙️ Wake Word: OFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#f8fafc",
            height=40,
            corner_radius=10,
            command=self.toggle_wake_word,
        )
        self.wake_btn.pack(fill="x", padx=16, pady=4)

        self.mic_btn = ctk.CTkButton(
            self.sidebar,
            text="🗣️ Speak Command",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#38bdf8",
            height=38,
            corner_radius=10,
            command=self.handle_voice_once,
        )
        self.mic_btn.pack(fill="x", padx=16, pady=4)

        # 4. Emergency STOP Button
        self.stop_btn = ctk.CTkButton(
            self.sidebar,
            text="🛑 EMERGENCY STOP",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            text_color="#ffffff",
            height=40,
            corner_radius=10,
            command=self.handle_stop_click,
        )
        self.stop_btn.pack(fill="x", padx=16, pady=(16, 8))

        # 5. System Specs Card
        specs_frame = ctk.CTkFrame(self.sidebar, fg_color="#111827", corner_radius=10)
        specs_frame.pack(fill="x", padx=16, pady=(16, 8))

        specs_text = (
            "🧠 Model: qwen3:8b (Ollama)\n"
            "🌐 Browser: Chrome Profile 1\n"
            "👁️ Vision: Smart Screen Vision\n"
            "⚡ Agent: Multi-Step Active"
        )
        specs_lbl = ctk.CTkLabel(
            specs_frame,
            text=specs_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#64748b",
            justify="left",
        )
        specs_lbl.pack(anchor="w", padx=12, pady=10)

        # Clear Chat Button
        clear_btn = ctk.CTkButton(
            self.sidebar,
            text="🗑️ Clear Chat History",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#1e293b",
            text_color="#64748b",
            height=28,
            command=self.clear_chat,
        )
        clear_btn.pack(side="bottom", pady=16)

        # ==========================================
        # RIGHT MAIN DASHBOARD
        # ==========================================
        # 1. Quick Action Cards Bar
        actions_bar = ctk.CTkFrame(self.main_content, fg_color="transparent", height=45)
        actions_bar.pack(fill="x", padx=20, pady=(16, 8))

        quick_actions = [
            ("👁️ Analyze Screen", "What is on my screen?"),
            ("🎬 YouTube & Play", "Open YouTube, search Techno Gamerz and play the first video"),
            ("🔎 Google Search", "Search latest artificial intelligence news on Google"),
            ("📝 Open Notepad", "Open Notepad and type Hello from ANDRO"),
            ("💾 Git Status", "Check my Git status"),
        ]

        for label, cmd in quick_actions:
            btn = ctk.CTkButton(
                actions_bar,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#1e293b",
                hover_color="#0284c7",
                text_color="#e2e8f0",
                height=34,
                corner_radius=8,
                command=lambda c=cmd: self.send_command(c),
            )
            btn.pack(side="left", padx=4)

        # 2. Scrollable Chat Stream (Bubble Stream)
        self.chat_container = ctk.CTkScrollableFrame(
            self.main_content,
            fg_color="#0b0f19",
            corner_radius=12,
            scrollbar_button_color="#334155",
            scrollbar_button_hover_color="#475569",
        )
        self.chat_container.pack(fill="both", expand=True, padx=20, pady=8)

        # 3. Live Action / Progress Status Bar
        self.live_bar = ctk.CTkLabel(
            self.main_content,
            text="✨ Ready for commands. Say 'Hey ANDRO' or type below.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#38bdf8",
            anchor="w",
        )
        self.live_bar.pack(fill="x", padx=26, pady=(4, 6))

        # 4. Floating Modern Input Dock
        dock_frame = ctk.CTkFrame(self.main_content, fg_color="#0f172a", corner_radius=16)
        dock_frame.pack(fill="x", padx=20, pady=(4, 18))

        self.input_entry = ctk.CTkEntry(
            dock_frame,
            placeholder_text="Ask ANDRO anything, e.g. 'Open YouTube and play Techno Gamerz'...",
            placeholder_text_color="#64748b",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="#1e293b",
            text_color="#f8fafc",
            border_color="#334155",
            border_width=1,
            height=46,
            corner_radius=12,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=10)
        self.input_entry.bind("<Return>", lambda event: self.handle_send_click())

        self.send_btn = ctk.CTkButton(
            dock_frame,
            text="⚡ Run",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            width=85,
            height=44,
            corner_radius=10,
            command=self.handle_send_click,
        )
        self.send_btn.pack(side="right", padx=(4, 12), pady=10)

        # Add Welcome Message Card
        self.add_assistant_message(
            "👋 **Hello! I am ANDRO, your Personal AI Assistant.**\n\n"
            "Here is what I can do for you:\n"
            " • 👁️ **Smart Screen Vision:** Ask *'What is on my screen?'* or *'Explain this error'*\n"
            " • 🧠 **Multi-Step Tasks:** *'Open Notepad and type Hello from ANDRO'*\n"
            " • 🎬 **YouTube Automation:** *'Open YouTube, search Techno Gamerz and play the first video'*\n"
            " • 🎙️ **Wake Word:** Say *'Hey ANDRO'* to activate, *'Bye ANDRO'* to sleep\n"
            " • 🛑 **Emergency Stop:** Say or click *'STOP'* anytime to cancel a task safely\n"
            " • 💻 **Desktop & Git:** Open apps, check Git status, stage, commit & push."
        )

    # -------------------------------------------------------------
    # FALLBACK STANDARD TKINTER
    # -------------------------------------------------------------
    def _init_standard_tkinter(self):
        import tkinter as tk
        from tkinter import scrolledtext

        self.root = tk.Tk()
        self.root.title("ANDRO — Personal AI Assistant")
        self.root.geometry("1000x700")
        self.root.configure(bg="#090d16")

        self.chat_container = scrolledtext.ScrolledText(
            self.root,
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 11),
            wrap="word",
        )
        self.chat_container.pack(fill="both", expand=True, padx=16, pady=16)

    # -------------------------------------------------------------
    # MESSAGE BUBBLE RENDERING (CHAT STREAM)
    # -------------------------------------------------------------
    def add_user_message(self, text: str):
        """Render a sleek blue bubble on the right for user messages."""
        if GUI_FRAMEWORK != "customtkinter":
            self.chat_container.insert("end", f"\n👤 YOU > {text}\n")
            self.chat_container.see("end")
            return

        bubble_container = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        bubble_container.pack(fill="x", padx=8, pady=6, anchor="e")

        bubble = ctk.CTkFrame(bubble_container, fg_color="#1d4ed8", corner_radius=14)
        bubble.pack(side="right", padx=4)

        user_tag = ctk.CTkLabel(
            bubble,
            text="👤 You",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#93c5fd",
        )
        user_tag.pack(anchor="e", padx=14, pady=(8, 2))

        msg_label = ctk.CTkLabel(
            bubble,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#ffffff",
            wraplength=520,
            justify="left",
        )
        msg_label.pack(anchor="w", padx=14, pady=(2, 10))

        self.root.after(50, lambda: self.chat_container._parent_canvas.yview_moveto(1.0))

    def add_assistant_message(self, text: str, is_error: bool = False):
        """Render a sleek obsidian glass card on the left for ANDRO messages."""
        if GUI_FRAMEWORK != "customtkinter":
            self.chat_container.insert("end", f"\n🤖 ANDRO > {text}\n")
            self.chat_container.see("end")
            return

        bubble_container = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        bubble_container.pack(fill="x", padx=8, pady=6, anchor="w")

        card_color = "#1e1b4b" if is_error else "#1e293b"
        border_color = "#dc2626" if is_error else "#334155"

        bubble = ctk.CTkFrame(
            bubble_container,
            fg_color=card_color,
            border_color=border_color,
            border_width=1,
            corner_radius=14,
        )
        bubble.pack(side="left", padx=4)

        tag_color = "#f87171" if is_error else "#38bdf8"
        andro_tag = ctk.CTkLabel(
            bubble,
            text="🤖 ANDRO AI",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=tag_color,
        )
        andro_tag.pack(anchor="w", padx=16, pady=(10, 2))

        # Format bold tags and text cleanly
        clean_text = text.replace("**", "")
        msg_label = ctk.CTkLabel(
            bubble,
            text=clean_text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#f1f5f9",
            wraplength=560,
            justify="left",
        )
        msg_label.pack(anchor="w", padx=16, pady=(2, 12))

        self.root.after(50, lambda: self.chat_container._parent_canvas.yview_moveto(1.0))

    def clear_chat(self):
        """Clear the visual conversation stream."""
        if GUI_FRAMEWORK == "customtkinter":
            for widget in self.chat_container.winfo_children():
                widget.destroy()
        self.add_assistant_message("Conversation cleared. How can I assist you now?")

    # -------------------------------------------------------------
    # STATE MANAGEMENT & DISPATCH
    # -------------------------------------------------------------
    def set_state(self, new_state: str, detail_msg: str = ""):
        """Update live status badges and banner smoothly."""
        self.state = new_state
        if new_state == "SLEEPING":
            text = "🔴 SLEEPING"
            color = "#f87171"
            bg = "#2d1215"
            default_detail = "Waiting for 'Hey ANDRO' or command"
        elif new_state == "ACTIVE":
            text = "🟢 ACTIVE"
            color = "#4ade80"
            bg = "#0f291e"
            default_detail = "Listening & ready for your commands"
        elif new_state == "PROCESSING":
            text = "🟡 PROCESSING"
            color = "#fbbf24"
            bg = "#2c2009"
            default_detail = "Thinking and executing task..."
        else:
            text = new_state
            color = "#38bdf8"
            bg = "#111827"
            default_detail = ""

        detail = detail_msg if detail_msg else default_detail

        def update():
            if GUI_FRAMEWORK == "customtkinter":
                self.status_pill.configure(text=text, text_color=color, fg_color=bg)
                self.status_detail.configure(text=detail)
                self.live_bar.configure(text=f"✨ {detail}")

        self.root.after(0, update)

    def handle_send_click(self):
        """Handle send button click."""
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, "end")
        self.send_command(text)

    def send_command(self, text: str):
        """Send a user command to ANDRO asynchronously."""
        self.add_user_message(text)
        self.set_state("PROCESSING", f"Executing: '{text}'...")

        threading.Thread(
            target=self._worker_execute_command,
            args=(text,),
            daemon=True,
        ).start()

    def _worker_execute_command(self, text: str):
        """Worker thread for Agent processing."""
        try:
            # Handle Git push confirmation
            if self.waiting_for_push:
                if any(w in text.lower() for w in ["yes", "y", "haan", "ha"]):
                    self.add_assistant_message("🚀 Pushing commits to GitHub...")
                    result = git_push(str(PROJECT_PATH))
                    self.add_assistant_message(f"Git Push: {result.get('message')}")
                    speak(result.get("message"))
                    self.waiting_for_push = False
                elif any(w in text.lower() for w in ["no", "cancel", "n", "nahi"]):
                    self.add_assistant_message("❌ Push cancelled by user.")
                    speak("Push cancelled.")
                    self.waiting_for_push = False
                else:
                    speak("Please type yes to push or no to cancel.")
                self.set_state("ACTIVE", "Ready for your next command.")
                return

            def trigger_push():
                self.waiting_for_push = True

            self.agent.process_input(text, trigger_push_confirmation=trigger_push)
        except Exception as err:
            self.add_assistant_message(f"❌ Error: {err}", is_error=True)
        finally:
            if self.state == "PROCESSING":
                self.set_state("ACTIVE", "Ready for your next command.")

    def handle_stop_click(self):
        """Emergency stop handler."""
        self.agent.stop()
        self.add_assistant_message("🛑 **EMERGENCY STOP TRIGGERED:** Current task was stopped safely.", is_error=True)
        speak("Current task stopped.")
        self.set_state("ACTIVE", "Task stopped safely. ANDRO is ACTIVE.")

    def handle_voice_once(self):
        """One-tap voice input button."""
        self.set_state("PROCESSING", "🎤 Listening to microphone...")
        threading.Thread(target=self._voice_once_worker, daemon=True).start()

    def _voice_once_worker(self):
        voice_result = listen()
        if voice_result.get("success"):
            user_text = voice_result["text"].strip()
            self.send_command(user_text)
        else:
            self.add_assistant_message(f"❌ {voice_result.get('message', 'Could not capture speech.')}", is_error=True)
            self.set_state("ACTIVE", "Ready for your next command.")

    def toggle_wake_word(self):
        """Toggle continuous background Wake-Word listening loop."""
        if not self.is_wake_word_running:
            self.is_wake_word_running = True
            if GUI_FRAMEWORK == "customtkinter":
                self.wake_btn.configure(text="🎙️ Wake Word: ON", fg_color="#10b981", hover_color="#059669")

            self.set_state("SLEEPING", "Wake-Word active. Say 'Hey ANDRO' anytime!")
            self.add_assistant_message("🎙️ **Wake Word system is now ON.** Say *'Hey ANDRO'* to activate me anytime!")
            threading.Thread(target=self._wake_word_worker, daemon=True).start()
        else:
            self.is_wake_word_running = False
            if GUI_FRAMEWORK == "customtkinter":
                self.wake_btn.configure(text="🎙️ Wake Word: OFF", fg_color="#334155", hover_color="#475569")
            self.add_assistant_message("🔇 **Wake Word system stopped.** You can still type commands or use 'Speak Command'.")
            self.set_state("ACTIVE", "Wake Word stopped. Ready for commands.")

    def _wake_word_worker(self):
        """Background continuous Wake-Word loop."""
        while self.is_wake_word_running:
            if self.state == "SLEEPING":
                detected = self.listener.listen_for_wake_word(timeout=3.0)
                if detected and self.is_wake_word_running:
                    self.set_state("ACTIVE", "🟢 'Hey ANDRO' detected! I am listening...")
                    self.add_assistant_message("🟢 **'Hey ANDRO' detected!** Yes, I'm listening.")
                    speak("Yes, I'm listening.")
            elif self.state == "ACTIVE":
                voice_result = self.listener.listen_command(timeout=7.0, phrase_time_limit=12.0)
                if not self.is_wake_word_running:
                    break

                if voice_result.get("success"):
                    user_text = voice_result["text"].strip()
                    self.add_user_message(user_text)

                    # Check for sleep command
                    if self.listener.is_sleep_command(user_text):
                        self.set_state("SLEEPING", "🔴 ANDRO SLEEPING — Waiting for 'Hey ANDRO'")
                        self.add_assistant_message("🔴 **Goodbye. Going to sleep.** Say *'Hey ANDRO'* whenever you need me.")
                        speak("Goodbye. Going to sleep.")
                        continue

                    # Check for stop command
                    if self.listener.is_stop_command(user_text):
                        self.handle_stop_click()
                        continue

                    # Process command
                    self.set_state("PROCESSING", f"Executing: '{user_text}'...")
                    try:
                        self.agent.process_input(user_text)
                    finally:
                        if self.is_wake_word_running and self.state != "SLEEPING":
                            self.set_state("ACTIVE", "Ready for your next command.")
                else:
                    time.sleep(0.1)

    def run(self):
        """Start the GUI mainloop."""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        gui = AndroGUI()
        gui.run()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 ANDRO GUI closed.")
        sys.exit(0)
