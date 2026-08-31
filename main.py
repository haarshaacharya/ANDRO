from pathlib import Path
from rich.console import Console

from tools.voice import listen
from tools.speaker import speak
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


# ---------------------------------
# PUSH CONFIRMATION HELPER
# ---------------------------------

waiting_for_push_confirmation = False


def trigger_push_confirmation():
    """Enable waiting for push confirmation state."""
    global waiting_for_push_confirmation
    waiting_for_push_confirmation = True


# ---------------------------------
# START ANDRO
# ---------------------------------

console.print("[bold cyan]🤖 ANDRO is online![/bold cyan]")
console.print("[yellow]Type 'exit' to close ANDRO.[/yellow]")
console.print("[yellow]Type 'voice' to speak to ANDRO.[/yellow]")
console.print(
    "[cyan]Try natural commands like:\n"
    " • 'Open YouTube, search Techno Gamerz and play the first video'\n"
    " • 'YouTube kholo, Techno Gamerz search karo aur pehla video chalao'\n"
    " • 'Open Chrome and search Python tutorials on Google'\n"
    " • 'Open Storagge.in' or 'Open Google'\n"
    " • 'Find my ANDRO project' or 'Mera project dhundo'\n"
    " • 'Open Chrome' or 'Open Calculator'\n"
    " • 'Check my Git status' or 'Stage all my changes'\n"
    " • 'Commit changes with message Added new feature'\n"
    " • 'Push my changes to GitHub'[/cyan]\n"
)


# ---------------------------------
# MAIN LOOP
# ---------------------------------

while True:
    user_input = console.input("[bold green]YOU > [/bold green]")
    command_lower = user_input.lower().strip()

    if not command_lower:
        continue

    # ---------------------------------
    # VOICE INPUT
    # ---------------------------------
    if command_lower == "voice":
        voice_result = listen()

        if voice_result["success"]:
            user_input = voice_result["text"]
            console.print(
                f"\n[bold magenta]🎤 YOU SAID > {user_input}[/bold magenta]\n"
            )
            command_lower = user_input.lower().strip()
        else:
            console.print(
                f"\n[bold red]❌ ANDRO: {voice_result['message']}[/bold red]\n"
            )
            speak(voice_result["message"])
            continue

    # ---------------------------------
    # EXIT
    # ---------------------------------
    if command_lower in ["exit", "quit", "bye"]:
        goodbye_message = "Goodbye! See you soon."
        console.print("\n[bold red]ANDRO: Goodbye! 👋[/bold red]")
        speak(goodbye_message)
        break

    # ---------------------------------
    # PUSH CONFIRMATION
    # ---------------------------------
    if waiting_for_push_confirmation:
        if command_lower in ["yes", "y", "haan", "ha"]:
            console.print(
                "\n[yellow]🚀 ANDRO is pushing changes to GitHub...[/yellow]"
            )
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

    # ---------------------------------
    # NATURAL LANGUAGE AI AGENT ROUTING
    # ---------------------------------
    agent.process_input(
        user_input,
        trigger_push_confirmation=trigger_push_confirmation,
    )