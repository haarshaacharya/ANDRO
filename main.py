import sys
import threading
from pathlib import Path
from rich.console import Console

from tools.voice import listen
from tools.speaker import speak
from tools.wake_word import WakeWordListener
from tools.logger import log_activity
from tools.state_manager import state_manager, AssistantState
from tools.git_tools import git_push
from agent import AndroAgent

console = Console()

# Current ANDRO project folder
PROJECT_PATH = Path(__file__).parent.resolve()

# Initialize Natural Language AI Agent
agent = AndroAgent(
    project_path=PROJECT_PATH,
    console=console,
    model="qwen3:8b",
)

listener = WakeWordListener()

# ---------------------------------
# STATE VARIABLES
# ---------------------------------
waiting_for_push_confirmation = False


def trigger_push_confirmation():
    """Enable waiting for push confirmation state."""
    global waiting_for_push_confirmation
    waiting_for_push_confirmation = True


def print_banner():
    console.print("\n[bold cyan]🤖 ANDRO — Personal AI Assistant v1.1[/bold cyan]")
    console.print("[yellow]Modes & Commands:[/yellow]")
    console.print(" • [bold green]Voice Mode:[/bold green] Say [bold white]'Hey ANDRO'[/bold white] to activate, [bold white]'Bye ANDRO'[/bold white] to sleep.")
    console.print(" • [bold green]Text Commands:[/bold green] Type commands directly or type [bold white]'voice'[/bold white] / [bold white]'wake'[/bold white].")
    console.print(" • [bold green]Emergency Stop:[/bold green] Say/type [bold red]'STOP ANDRO'[/bold red] to stop active tasks.")
    console.print(" • [bold green]Complete Exit:[/bold green] Say/type [bold red]'Exit ANDRO'[/bold red] or [bold red]'exit'[/bold red] to close completely.\n")
    console.print("[cyan]Try natural commands like:\n"
                  " • 'What is on my screen?' or 'Explain this error'\n"
                  " • 'Open Notepad and type Hello from ANDRO'\n"
                  " • 'Open YouTube, search Techno Gamerz and play the first video'\n"
                  " • 'search Techno Gamerz' or 'Search Python tutorials on Google'\n"
                  " • 'Open Storagge.in' or 'Open Google'\n"
                  " • 'Find my ANDRO project' or 'Mera project dhundo'\n"
                  " • 'Check my Git status' or 'Push my changes to GitHub'[/cyan]\n")


def run_wake_word_loop():
    """Continuous background / interactive Wake-Word voice loop with echo prevention."""
    global waiting_for_push_confirmation
    state_manager.set_state(AssistantState.SLEEPING, "Waiting for 'Hey ANDRO'")
    console.print("\n[bold red]🔴 ANDRO SLEEPING — Waiting for 'Hey ANDRO'[/bold red]\n")

    while True:
        cur_state = state_manager.get_state()

        if cur_state == AssistantState.SLEEPING:
            # Sleeping state: low-resource, privacy-first audio check
            detected = listener.listen_for_wake_word(timeout=3.0)
            if detected:
                state_manager.set_state(AssistantState.ACTIVE, "Listening for commands...")
                console.print("\n[bold green]🟢 ANDRO ACTIVE — Listening[/bold green]")
                console.print("[cyan]Say your commands or say 'Bye ANDRO' to sleep.[/cyan]\n")
                speak("Yes, I'm listening.")
                # Wait for activation speech to finish before listening to next command
                state_manager.wait_after_speech(1.0)
        else:
            # Active state: listen for commands continuously
            voice_result = listener.listen_command(timeout=8.0, phrase_time_limit=12.0)

            if not voice_result.get("success"):
                if voice_result.get("timeout"):
                    # Silent pause - keep waiting in ACTIVE state
                    continue
                continue

            user_text = voice_result["text"].strip()
            console.print(f"\n[bold magenta]🎤 YOU SAID > {user_text}[/bold magenta]\n")

            # 1. Check for Complete Exit command
            if listener.is_exit_command(user_text):
                state_manager.set_state(AssistantState.SLEEPING, "Shutting down ANDRO")
                console.print("\n[bold red]ANDRO: Goodbye. Shutting down ANDRO. 👋[/bold red]\n")
                log_activity("SHUTDOWN", "Shutdown command received in wake word loop.")
                agent.stop()
                speak("Goodbye. Shutting down ANDRO.")
                state_manager.wait_after_speech(1.5)
                sys.exit(0)

            # 2. Check for Sleep / Deactivation command (Bye ANDRO must ONLY sleep)
            if listener.is_sleep_command(user_text):
                state_manager.set_state(AssistantState.SLEEPING, "Waiting for 'Hey ANDRO'")
                console.print("\n[bold red]🔴 ANDRO SLEEPING — Waiting for 'Hey ANDRO'[/bold red]\n")
                speak("Goodbye. Going to sleep.")
                continue

            # 3. Check for Emergency STOP command
            if listener.is_stop_command(user_text):
                agent.stop()
                console.print("\n[bold yellow]🛑 Task stopped by user.[/bold yellow]\n")
                speak("Current task stopped.")
                continue

            # Push Confirmation handling
            if waiting_for_push_confirmation:
                if any(w in user_text.lower() for w in ["yes", "haan", "ha", "push"]):
                    console.print("\n[yellow]🚀 ANDRO is pushing changes to GitHub...[/yellow]")
                    result = git_push(str(PROJECT_PATH))
                    agent.print_git_result("Push", result)
                    waiting_for_push_confirmation = False
                elif any(w in user_text.lower() for w in ["no", "cancel", "nahi"]):
                    console.print("\n[yellow]❌ Push cancelled.[/yellow]\n")
                    speak("Push cancelled.")
                    waiting_for_push_confirmation = False
                else:
                    speak("Please say yes to push or no to cancel.")
                continue

            # Execute active command — ANDRO REMAINS ACTIVE!
            state_manager.set_state(AssistantState.PROCESSING, f"Executing: {user_text}")
            try:
                agent.process_input(user_text, trigger_push_confirmation=trigger_push_confirmation)
            finally:
                if state_manager.get_state() != AssistantState.SLEEPING:
                    state_manager.set_state(AssistantState.ACTIVE, "Ready for next command")


# ---------------------------------
# MAIN INTERACTIVE ENTRY POINT
# ---------------------------------
if __name__ == "__main__":
    try:
        print_banner()

        console.print("[yellow]Choose startup mode:[/yellow]")
        console.print(" [bold cyan]1[/bold cyan] — 🎙️ Wake Word Mode (Starts in 🔴 SLEEPING, activates on 'Hey ANDRO')")
        console.print(" [bold cyan]2[/bold cyan] — ⌨️ Text Terminal Mode (Direct typed commands + voice command trigger)")

        try:
            mode_choice = console.input("\n[bold green]Enter mode (1 or 2, default is 2) > [/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

        if mode_choice == "1" or mode_choice.lower() in ["wake", "voice", "v"]:
            run_wake_word_loop()
        else:
            # Standard Interactive Text Terminal Mode
            state_manager.set_state(AssistantState.ACTIVE, "Text Terminal Mode Active")
            console.print("\n[bold green]⌨️ Text Terminal Mode Active.[/bold green]")
            console.print("[cyan]Type your commands below. Type 'wake' for wake-word mode, 'voice' to speak once, or 'exit' to close.[/cyan]\n")

            while True:
                try:
                    user_input = console.input("[bold green]YOU > [/bold green]").strip()
                except (KeyboardInterrupt, EOFError):
                    break

                if not user_input:
                    continue

                command_lower = user_input.lower().strip()

                # Voice command trigger
                if command_lower == "voice":
                    voice_result = listen()
                    if voice_result["success"]:
                        user_input = voice_result["text"]
                        console.print(f"\n[bold magenta]🎤 YOU SAID > {user_input}[/bold magenta]\n")
                        command_lower = user_input.lower().strip()
                    else:
                        console.print(f"\n[bold red]❌ ANDRO: {voice_result['message']}[/bold red]\n")
                        speak(voice_result["message"])
                        continue

                # Switch to continuous wake word mode
                if command_lower in ["wake", "wakeword", "wake word"]:
                    run_wake_word_loop()
                    continue

                # Complete Exit
                if listener.is_exit_command(command_lower):
                    console.print("\n[bold red]ANDRO: Goodbye. Shutting down ANDRO. 👋[/bold red]\n")
                    log_activity("SHUTDOWN", "Shutdown command received in text terminal.")
                    agent.stop()
                    speak("Goodbye. Shutting down ANDRO.")
                    state_manager.wait_after_speech(1.5)
                    break

                # Emergency Stop
                if command_lower in ["stop andro", "stop", "ruk jao", "ruko"]:
                    agent.stop()
                    console.print("\n[bold yellow]🛑 Task stopped by user.[/bold yellow]\n")
                    speak("Current task stopped.")
                    continue

                # Push Confirmation
                if waiting_for_push_confirmation:
                    if command_lower in ["yes", "y", "haan", "ha"]:
                        console.print("\n[yellow]🚀 ANDRO is pushing changes to GitHub...[/yellow]")
                        result = git_push(str(PROJECT_PATH))
                        agent.print_git_result("Push", result)
                        waiting_for_push_confirmation = False
                        continue
                    elif command_lower in ["no", "n", "cancel", "nahi"]:
                        message = "Push cancelled. Nothing was pushed."
                        console.print(f"\n[yellow]❌ {message}[/yellow]\n")
                        speak(message)
                        waiting_for_push_confirmation = False
                        continue
                    else:
                        message = "Please type yes to push or no to cancel."
                        console.print(f"\n[yellow]{message}[/yellow]\n")
                        speak(message)
                        continue

                # Process command with Agent
                agent.process_input(user_input, trigger_push_confirmation=trigger_push_confirmation)

    except (KeyboardInterrupt, SystemExit):
        console.print("\n[bold red]👋 ANDRO closed.[/bold red]\n")
        sys.exit(0)