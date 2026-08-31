import sys
import time
import threading
from pathlib import Path
from rich.console import Console

# Core ANDRO imports
from tools.voice import listen
from tools.speaker import speak
from tools.wake_word import WakeWordListener
from tools.git_tools import git_push
from agent import AndroAgent

PROJECT_PATH = Path(__file__).parent.resolve()
console = Console()

# Try importing CustomTkinter; fallback to standard Tkinter with sleek dark styles if not installed
try:
    import customtkinter as ctk
    GUI_FRAMEWORK = "customtkinter"
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    ctk = None
    GUI_FRAMEWORK = "tkinter"


class AndroGUI:
    """Modern Futuristic GUI for ANDRO Personal AI Assistant."""

    def __init__(self):
        self.agent = AndroAgent(
            project_path=PROJECT_PATH,
            console=console,
            model="qwen3:8b",
        )
        self.listener = WakeWordListener()
        self.state = "SLEEPING"  # SLEEPING, ACTIVE, PROCESSING
        self.is_wake_word_running = False
        self.waiting_for_push = False

        if GUI_FRAMEWORK == "customtkinter":
            self._init_customtkinter()
        else:
            self._init_standard_tkinter()

    # -------------------------------------------------------------
    # CUSTOMTKINTER IMPLEMENTATION
    # -------------------------------------------------------------
    def _init_customtkinter(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("ANDRO — Personal AI Assistant")
        self.root.geometry("880x680")
        self.root.minsize(760, 560)
        self.root.configure(fg_color="#0b0f19")

        # Top Header Frame
        header_frame = ctk.CTkFrame(self.root, fg_color="#111827", corner_radius=12)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 ANDRO AI ASSISTANT",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#38bdf8",
        )
        title_label.pack(side="left", padx=16, pady=12)

        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="🔴 SLEEPING",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f87171",
            fg_color="#1e293b",
            corner_radius=8,
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="right", padx=16, pady=12)

        # Quick Actions Bar
        quick_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        quick_frame.pack(fill="x", padx=16, pady=4)

        actions = [
            ("👁️ What's on screen?", "What is on my screen?"),
            ("🎬 Open YouTube", "Open YouTube"),
            ("🔎 Search Google", "Search latest artificial intelligence news on Google"),
            ("📝 Open Notepad", "Open Notepad and type Hello from ANDRO"),
            ("💾 Git Status", "Check my Git status"),
        ]
        for label, cmd in actions:
            btn = ctk.CTkButton(
                quick_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                fg_color="#1e293b",
                hover_color="#334155",
                text_color="#e2e8f0",
                height=30,
                command=lambda c=cmd: self.send_command(c),
            )
            btn.pack(side="left", padx=4)

        # Chat / Transcript Log
        self.chat_box = ctk.CTkTextbox(
            self.root,
            fg_color="#111827",
            text_color="#f1f5f9",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=12,
            wrap="word",
        )
        self.chat_box.pack(fill="both", expand=True, padx=16, pady=8)

        # Action Status Banner
        self.action_status = ctk.CTkLabel(
            self.root,
            text="ANDRO is sleeping. Click '🎙️ Start Wake Word' or say 'Hey ANDRO'.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
            anchor="w",
        )
        self.action_status.pack(fill="x", padx=20, pady=2)

        # Bottom Input Controls
        bottom_frame = ctk.CTkFrame(self.root, fg_color="#111827", corner_radius=12)
        bottom_frame.pack(fill="x", padx=16, pady=(4, 16))

        self.input_entry = ctk.CTkEntry(
            bottom_frame,
            placeholder_text="Type a command or say 'Hey ANDRO'...",
            font=ctk.CTkFont(size=14),
            fg_color="#1e293b",
            text_color="#f8fafc",
            border_color="#334155",
            height=42,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=12)
        self.input_entry.bind("<Return>", lambda event: self.handle_send_click())

        self.send_btn = ctk.CTkButton(
            bottom_frame,
            text="🚀 Send",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            width=90,
            height=42,
            command=self.handle_send_click,
        )
        self.send_btn.pack(side="left", padx=4, pady=12)

        self.voice_btn = ctk.CTkButton(
            bottom_frame,
            text="🎙️ Wake Word: OFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            width=150,
            height=42,
            command=self.toggle_wake_word,
        )
        self.voice_btn.pack(side="left", padx=4, pady=12)

        self.stop_btn = ctk.CTkButton(
            bottom_frame,
            text="🛑 STOP",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            width=90,
            height=42,
            command=self.handle_stop_click,
        )
        self.stop_btn.pack(side="left", padx=(4, 12), pady=12)

        self.append_log("🤖 ANDRO is initialized and ready!\n🔴 State: SLEEPING (Waiting for 'Hey ANDRO' or text command).\n")

    # -------------------------------------------------------------
    # FALLBACK STANDARD TKINTER IMPLEMENTATION
    # -------------------------------------------------------------
    def _init_standard_tkinter(self):
        import tkinter as tk
        from tkinter import scrolledtext

        self.root = tk.Tk()
        self.root.title("ANDRO — Personal AI Assistant")
        self.root.geometry("880x680")
        self.root.configure(bg="#0b0f19")

        header_frame = tk.Frame(self.root, bg="#111827")
        header_frame.pack(fill="x", padx=16, pady=10)

        title_label = tk.Label(
            header_frame,
            text="🤖 ANDRO AI ASSISTANT",
            font=("Segoe UI", 18, "bold"),
            fg="#38bdf8",
            bg="#111827",
        )
        title_label.pack(side="left", padx=12, pady=10)

        self.status_badge = tk.Label(
            header_frame,
            text="🔴 SLEEPING",
            font=("Segoe UI", 12, "bold"),
            fg="#f87171",
            bg="#1e293b",
            padx=10,
            pady=4,
        )
        self.status_badge.pack(side="right", padx=12, pady=10)

        self.chat_box = scrolledtext.ScrolledText(
            self.root,
            bg="#111827",
            fg="#f1f5f9",
            font=("Consolas", 11),
            wrap="word",
        )
        self.chat_box.pack(fill="both", expand=True, padx=16, pady=8)

        self.action_status = tk.Label(
            self.root,
            text="ANDRO is sleeping. Tip: Run 'pip install customtkinter' for modern UI.",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#0b0f19",
            anchor="w",
        )
        self.action_status.pack(fill="x", padx=20, pady=2)

        bottom_frame = tk.Frame(self.root, bg="#111827")
        bottom_frame.pack(fill="x", padx=16, pady=10)

        self.input_entry = tk.Entry(
            bottom_frame,
            font=("Segoe UI", 12),
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#f8fafc",
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self.input_entry.bind("<Return>", lambda event: self.handle_send_click())

        self.send_btn = tk.Button(
            bottom_frame,
            text="🚀 Send",
            font=("Segoe UI", 10, "bold"),
            bg="#0284c7",
            fg="white",
            command=self.handle_send_click,
        )
        self.send_btn.pack(side="left", padx=4, pady=8)

        self.voice_btn = tk.Button(
            bottom_frame,
            text="🎙️ Wake Word: OFF",
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg="white",
            command=self.toggle_wake_word,
        )
        self.voice_btn.pack(side="left", padx=4, pady=8)

        self.stop_btn = tk.Button(
            bottom_frame,
            text="🛑 STOP",
            font=("Segoe UI", 10, "bold"),
            bg="#ef4444",
            fg="white",
            command=self.handle_stop_click,
        )
        self.stop_btn.pack(side="left", padx=8, pady=8)

    # -------------------------------------------------------------
    # UI LOGIC & THREAD-SAFE STATE UPDATES
    # -------------------------------------------------------------
    def set_state(self, new_state: str, status_msg: str = ""):
        """Update ANDRO state badge and status message safely."""
        self.state = new_state
        if new_state == "SLEEPING":
            text = "🔴 SLEEPING"
            color = "#f87171"
        elif new_state == "ACTIVE":
            text = "🟢 ACTIVE"
            color = "#4ade80"
        elif new_state == "PROCESSING":
            text = "🟡 PROCESSING"
            color = "#fbbf24"
        else:
            text = new_state
            color = "#38bdf8"

        def update():
            if GUI_FRAMEWORK == "customtkinter":
                self.status_badge.configure(text=text, text_color=color)
                if status_msg:
                    self.action_status.configure(text=status_msg)
            else:
                self.status_badge.config(text=text, fg=color)
                if status_msg:
                    self.action_status.config(text=status_msg)

        self.root.after(0, update)

    def append_log(self, text: str):
        """Append text to conversation area safely."""
        def update():
            self.chat_box.insert("end", text + "\n")
            self.chat_box.see("end")

        self.root.after(0, update)

    def handle_send_click(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, "end")
        self.send_command(text)

    def send_command(self, text: str):
        """Execute a text command in a background worker thread."""
        self.append_log(f"👤 YOU > {text}")
        self.set_state("PROCESSING", f"Executing: '{text}'...")

        threading.Thread(
            target=self._worker_execute_command,
            args=(text,),
            daemon=True,
        ).start()

    def _worker_execute_command(self, text: str):
        """Worker thread for Agent command processing."""
        try:
            # Check for Push confirmation
            if self.waiting_for_push:
                if any(w in text.lower() for w in ["yes", "y", "haan", "ha"]):
                    self.append_log("🚀 ANDRO: Pushing changes to GitHub...")
                    result = git_push(str(PROJECT_PATH))
                    self.append_log(f"Git Push: {result.get('message')}")
                    speak(result.get("message"))
                    self.waiting_for_push = False
                elif any(w in text.lower() for w in ["no", "cancel", "n", "nahi"]):
                    self.append_log("❌ ANDRO: Push cancelled.")
                    speak("Push cancelled.")
                    self.waiting_for_push = False
                else:
                    speak("Please type yes to push or no to cancel.")
                self.set_state("ACTIVE", "Ready for next command.")
                return

            def trigger_push():
                self.waiting_for_push = True

            self.agent.process_input(text, trigger_push_confirmation=trigger_push)
        except Exception as err:
            self.append_log(f"❌ Error: {err}")
        finally:
            if self.state == "PROCESSING":
                self.set_state("ACTIVE", "Ready for your next command.")

    def handle_stop_click(self):
        """Handle emergency stop button click."""
        self.agent.stop()
        self.append_log("\n🛑 EMERGENCY STOP triggered: Task cancelled.\n")
        speak("Current task stopped.")
        self.set_state("ACTIVE", "Task stopped safely. ANDRO is ACTIVE.")

    def toggle_wake_word(self):
        """Toggle background Wake-Word listening loop."""
        if not self.is_wake_word_running:
            self.is_wake_word_running = True
            if GUI_FRAMEWORK == "customtkinter":
                self.voice_btn.configure(text="🎙️ Wake Word: ON", fg_color="#10b981")
            else:
                self.voice_btn.config(text="🎙️ Wake Word: ON", bg="#10b981")

            self.set_state("SLEEPING", "Wake-Word active. Say 'Hey ANDRO' to activate.")
            self.append_log("\n🎙️ Wake Word loop started. Say 'Hey ANDRO' anytime!\n")
            threading.Thread(target=self._wake_word_worker, daemon=True).start()
        else:
            self.is_wake_word_running = False
            if GUI_FRAMEWORK == "customtkinter":
                self.voice_btn.configure(text="🎙️ Wake Word: OFF", fg_color="#334155")
            else:
                self.voice_btn.config(text="🎙️ Wake Word: OFF", bg="#334155")
            self.append_log("\n🔇 Wake Word loop stopped.\n")
            self.set_state("ACTIVE", "Wake Word stopped. You can type commands.")

    def _wake_word_worker(self):
        """Background worker thread for continuous wake-word listening."""
        while self.is_wake_word_running:
            if self.state == "SLEEPING":
                detected = self.listener.listen_for_wake_word(timeout=3.0)
                if detected and self.is_wake_word_running:
                    self.set_state("ACTIVE", "🟢 Wake word detected! Listening...")
                    self.append_log("\n🟢 'Hey ANDRO' detected! ANDRO is now ACTIVE.\n")
                    speak("Yes, I'm listening.")
            elif self.state == "ACTIVE":
                voice_result = self.listener.listen_command(timeout=7.0, phrase_time_limit=12.0)
                if not self.is_wake_word_running:
                    break

                if voice_result.get("success"):
                    user_text = voice_result["text"].strip()
                    self.append_log(f"🎤 YOU SAID > {user_text}")

                    # Check for sleep command
                    if self.listener.is_sleep_command(user_text):
                        self.set_state("SLEEPING", "🔴 ANDRO SLEEPING — Waiting for 'Hey ANDRO'")
                        self.append_log("\n🔴 Deactivating: Goodbye. Going to sleep.\n")
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
                    # Timeout / silence - continue staying ACTIVE!
                    time.sleep(0.1)

    def run(self):
        """Start the GUI main event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    gui = AndroGUI()
    gui.run()
