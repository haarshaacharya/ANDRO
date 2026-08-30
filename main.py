from ollama import chat
from rich.console import Console
from pathlib import Path

from tools.files import find_files
from tools.system import open_app
from tools.voice import listen
from tools.speaker import speak
from tools.git_tools import (
    is_git_repository,
    git_status,
    git_add_all,
    git_commit,
    git_push,
)

console = Console()

# Current ANDRO project folder
PROJECT_PATH = Path(__file__).parent.resolve()


# ---------------------------------
# ANDRO SPEAK FUNCTION
# ---------------------------------

def andro_say(text):
    """Print and speak ANDRO's response."""

    text = str(text)

    console.print(
        f"\n[bold cyan]ANDRO >[/bold cyan] {text}\n"
    )

    speak(text)


# ---------------------------------
# AI SYSTEM PROMPT
# ---------------------------------

SYSTEM_PROMPT = """
You are ANDRO, a powerful personal AI assistant.

You help the user with programming, projects, planning,
files, Git, applications, and computer-related tasks.

You can:
- Search files
- Open applications
- Help with Git and GitHub
- Answer programming questions
- Help with projects

Be helpful, concise, and friendly.
"""


# ---------------------------------
# FILE SEARCH COMMAND
# ---------------------------------

def search_query_from_command(command):
    """Extract a file search query from common commands."""

    command_lower = command.lower()

    keywords = [
        "find",
        "search for",
        "search",
        "locate",
        "look for",
        "dhundo",
        "dhoondo",
    ]

    for keyword in keywords:

        if keyword in command_lower:

            query = command_lower.split(keyword, 1)[1].strip()

            for word in [
                "my",
                "project",
                "folder",
                "file",
                "please",
                "karo",
                "kar do",
                "ko",
            ]:
                query = query.replace(word, "").strip()

            return query

    return None


# ---------------------------------
# OPEN APP COMMAND
# ---------------------------------

def app_name_from_command(command):
    """Extract app name from an open command."""

    command_lower = command.lower().strip()

    prefixes = [
        "open ",
        "launch ",
        "start ",
        "khol ",
        "khol do ",
    ]

    for prefix in prefixes:

        if command_lower.startswith(prefix):

            app_name = command_lower[len(prefix):].strip()

            for word in [
                "please",
                "app",
                "application",
                "karo",
                "kar do",
            ]:
                app_name = app_name.replace(word, "").strip()

            return app_name

    return None


# ---------------------------------
# GIT COMMAND DETECTION
# ---------------------------------

def get_git_command(command):
    """Detect simple Git commands."""

    command_lower = command.lower().strip()

    # Git status
    if (
        "git status" in command_lower
        or "check git status" in command_lower
        or "check status" in command_lower
    ):
        return "status"

    # Stage changes
    if (
        "git add" in command_lower
        or "stage changes" in command_lower
        or "stage my changes" in command_lower
    ):
        return "add"

    # Commit command
    if command_lower.startswith("commit "):

        message = command[len("commit "):].strip()

        if message:
            return ("commit", message)

        return "commit_missing_message"

    # Push command
    if (
        "git push" in command_lower
        or "push to github" in command_lower
        or "push changes" in command_lower
    ):
        return "push"

    return None


# ---------------------------------
# PRINT GIT RESULT
# ---------------------------------

def print_git_result(title, result):
    """Print Git tool results and speak them."""

    if result["success"]:

        console.print(
            f"\n[bold green]✅ {title}[/bold green]"
        )

        console.print(
            f"[cyan]{result['message']}[/cyan]\n"
        )

        speak(result["message"])

    else:

        console.print(
            f"\n[bold red]❌ {title} failed[/bold red]"
        )

        console.print(
            f"[red]{result['message']}[/red]\n"
        )

        speak(result["message"])


# ---------------------------------
# START ANDRO
# ---------------------------------

console.print("[bold cyan]🤖 ANDRO is online![/bold cyan]")

console.print(
    "[yellow]Type 'exit' to close ANDRO.[/yellow]"
)

console.print(
    "[yellow]Type 'voice' to speak to ANDRO.[/yellow]"
)

console.print(
    "[yellow]Git commands: git status, stage changes, "
    "commit <message>, push to GitHub[/yellow]\n"
)


# ---------------------------------
# AI MEMORY
# ---------------------------------

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# Push confirmation state
waiting_for_push_confirmation = False


# ---------------------------------
# MAIN LOOP
# ---------------------------------

while True:

    user_input = console.input(
        "[bold green]YOU > [/bold green]"
    )

    command_lower = user_input.lower().strip()


    # ---------------------------------
    # VOICE INPUT
    # ---------------------------------

    if command_lower == "voice":

        voice_result = listen()

        if voice_result["success"]:

            user_input = voice_result["text"]

            console.print(
                f"\n[bold magenta]🎤 YOU SAID > "
                f"{user_input}[/bold magenta]\n"
            )

            command_lower = user_input.lower().strip()

        else:

            console.print(
                f"\n[bold red]❌ ANDRO: "
                f"{voice_result['message']}[/bold red]\n"
            )

            speak(voice_result["message"])

            continue


    # ---------------------------------
    # EXIT
    # ---------------------------------

    if command_lower in ["exit", "quit", "bye"]:

        goodbye_message = "Goodbye! See you soon."

        console.print(
            "\n[bold red]ANDRO: Goodbye! 👋[/bold red]"
        )

        speak(goodbye_message)

        break


    # ---------------------------------
    # PUSH CONFIRMATION
    # ---------------------------------

    if waiting_for_push_confirmation:

        if command_lower in ["yes", "y", "haan", "ha"]:

            console.print(
                "\n[yellow]🚀 ANDRO is pushing changes "
                "to GitHub...[/yellow]"
            )

            result = git_push(str(PROJECT_PATH))

            print_git_result("Push", result)

            waiting_for_push_confirmation = False

            continue


        elif command_lower in ["no", "n", "cancel", "nahi"]:

            message = "Push cancelled. Nothing was pushed."

            console.print(
                f"\n[yellow]❌ {message}[/yellow]\n"
            )

            speak(message)

            waiting_for_push_confirmation = False

            continue


        else:

            message = (
                "Please type yes to push or no to cancel."
            )

            console.print(
                f"\n[yellow]{message}[/yellow]\n"
            )

            speak(message)

            continue


    # ---------------------------------
    # FILE SEARCH TOOL
    # ---------------------------------

    search_query = search_query_from_command(user_input)

    if search_query:

        console.print(
            f"\n[yellow]🔍 ANDRO is searching for: "
            f"{search_query}[/yellow]"
        )

        results = find_files(search_query)

        if results:

            console.print(
                "\n[bold green]📂 Results found:[/bold green]\n"
            )

            speak(
                f"I found {len(results)} matching files or folders."
            )

            for index, result in enumerate(
                results,
                start=1
            ):

                console.print(
                    f"{index}. [{result['type'].upper()}] "
                    f"{result['name']}"
                )

                console.print(
                    f"   📍 {result['path']}\n"
                )

        else:

            message = (
                "No matching files or folders were found."
            )

            console.print(
                f"\n[bold red]❌ {message}[/bold red]\n"
            )

            speak(message)

        continue


    # ---------------------------------
    # OPEN APP TOOL
    # ---------------------------------

    app_name = app_name_from_command(user_input)

    if app_name:

        console.print(
            f"\n[yellow]💻 ANDRO is opening: "
            f"{app_name}[/yellow]"
        )

        result = open_app(app_name)

        if result["success"]:

            console.print(
                f"\n[bold green]✅ ANDRO: "
                f"{result['message']}[/bold green]\n"
            )

            speak(result["message"])

        else:

            console.print(
                f"\n[bold red]❌ ANDRO: "
                f"{result['message']}[/bold red]\n"
            )

            speak(result["message"])

        continue


    # ---------------------------------
    # GIT AGENT
    # ---------------------------------

    git_command = get_git_command(user_input)

    if git_command:

        # Check Git repository
        if not is_git_repository(str(PROJECT_PATH)):

            message = (
                "This project is not a Git repository."
            )

            console.print(
                f"\n[bold red]❌ {message}[/bold red]\n"
            )

            speak(message)

            continue


        # Git status
        if git_command == "status":

            console.print(
                "\n[yellow]🔍 ANDRO is checking "
                "Git status...[/yellow]"
            )

            result = git_status(
                str(PROJECT_PATH)
            )

            print_git_result(
                "Git Status",
                result
            )

            continue


        # Git add
        if git_command == "add":

            console.print(
                "\n[yellow]➕ ANDRO is staging "
                "changes...[/yellow]"
            )

            result = git_add_all(
                str(PROJECT_PATH)
            )

            print_git_result(
                "Git Add",
                result
            )

            continue


        # Missing commit message
        if git_command == "commit_missing_message":

            message = (
                "Please provide a commit message."
            )

            console.print(
                f"\n[yellow]{message}[/yellow]"
            )

            console.print(
                "[cyan]Example: commit Added Chrome support"
                "[/cyan]\n"
            )

            speak(message)

            continue


        # Git commit
        if isinstance(git_command, tuple):

            _, commit_message = git_command

            console.print(
                f"\n[yellow]💾 ANDRO is creating commit: "
                f"{commit_message}[/yellow]"
            )

            result = git_commit(
                str(PROJECT_PATH),
                commit_message
            )

            print_git_result(
                "Git Commit",
                result
            )

            continue


        # Git push
        if git_command == "push":

            warning = (
                "This will push commits to the configured "
                "GitHub repository. Say yes to continue "
                "or no to cancel."
            )

            console.print(
                "\n[bold yellow]⚠️ This will push commits "
                "to the configured remote repository."
                "[/bold yellow]"
            )

            console.print(
                "[yellow]Type YES to continue or NO "
                "to cancel.[/yellow]\n"
            )

            speak(warning)

            waiting_for_push_confirmation = True

            continue


    # ---------------------------------
    # AI CHAT
    # ---------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    response = chat(
        model="qwen3:8b",
        messages=messages
    )

    answer = response.message.content

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    andro_say(answer)