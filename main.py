from ollama import chat
from rich.console import Console
from pathlib import Path

from tools.files import find_files
from tools.system import open_app
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

SYSTEM_PROMPT = """
You are ANDRO, a powerful personal AI assistant.

You help the user with programming, projects, planning,
files, Git, and computer-related tasks.

You can search files and open applications.

Be helpful and concise.
"""


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


def print_git_result(title, result):
    """Print Git tool results nicely."""

    if result["success"]:
        console.print(f"\n[bold green]✅ {title}[/bold green]")
        console.print(f"[cyan]{result['message']}[/cyan]\n")
    else:
        console.print(f"\n[bold red]❌ {title} failed[/bold red]")
        console.print(f"[red]{result['message']}[/red]\n")


console.print("[bold cyan]🤖 ANDRO is online![/bold cyan]")
console.print("[yellow]Type 'exit' to close ANDRO.[/yellow]")
console.print(
    "[yellow]Git commands: git status, stage changes, "
    "commit <message>, push to GitHub[/yellow]\n"
)

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

# Push confirmation state
waiting_for_push_confirmation = False


while True:

    user_input = console.input("[bold green]YOU > [/bold green]")
    command_lower = user_input.lower().strip()

    # ---------------------------------
    # EXIT
    # ---------------------------------

    if command_lower in ["exit", "quit", "bye"]:
        console.print("\n[bold red]ANDRO: Goodbye! 👋[/bold red]")
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

            print_git_result("Push", result)

            waiting_for_push_confirmation = False
            continue

        elif command_lower in ["no", "n", "cancel", "nahi"]:

            console.print(
                "\n[yellow]❌ Push cancelled. Nothing was pushed.[/yellow]\n"
            )

            waiting_for_push_confirmation = False
            continue

        else:

            console.print(
                "\n[yellow]Please type YES to push or NO to cancel.[/yellow]\n"
            )

            continue

    # ---------------------------------
    # FILE SEARCH TOOL
    # ---------------------------------

    search_query = search_query_from_command(user_input)

    if search_query:

        console.print(
            f"\n[yellow]🔍 ANDRO is searching for: {search_query}[/yellow]"
        )

        results = find_files(search_query)

        if results:

            console.print("\n[bold green]📂 Results found:[/bold green]\n")

            for index, result in enumerate(results, start=1):

                console.print(
                    f"{index}. [{result['type'].upper()}] "
                    f"{result['name']}"
                )

                console.print(
                    f"   📍 {result['path']}\n"
                )

        else:

            console.print(
                "\n[bold red]❌ No matching files or folders found.[/bold red]\n"
            )

        continue

    # ---------------------------------
    # OPEN APP TOOL
    # ---------------------------------

    app_name = app_name_from_command(user_input)

    if app_name:

        console.print(
            f"\n[yellow]💻 ANDRO is opening: {app_name}[/yellow]"
        )

        result = open_app(app_name)

        if result["success"]:

            console.print(
                f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n"
            )

        else:

            console.print(
                f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n"
            )

        continue

    # ---------------------------------
    # GIT AGENT
    # ---------------------------------

    git_command = get_git_command(user_input)

    if git_command:

        # Make sure current project is a Git repository
        if not is_git_repository(str(PROJECT_PATH)):

            console.print(
                "\n[bold red]❌ This project is not a Git repository.[/bold red]\n"
            )

            continue

        # Git status
        if git_command == "status":

            console.print(
                "\n[yellow]🔍 ANDRO is checking Git status...[/yellow]"
            )

            result = git_status(str(PROJECT_PATH))

            print_git_result("Git Status", result)

            continue

        # Git add
        if git_command == "add":

            console.print(
                "\n[yellow]➕ ANDRO is staging changes...[/yellow]"
            )

            result = git_add_all(str(PROJECT_PATH))

            print_git_result("Git Add", result)

            continue

        # Missing commit message
        if git_command == "commit_missing_message":

            console.print(
                "\n[yellow]Please provide a commit message.[/yellow]"
            )

            console.print(
                '[cyan]Example: commit Added Chrome support[/cyan]\n'
            )

            continue

        # Git commit
        if isinstance(git_command, tuple):

            _, commit_message = git_command

            console.print(
                f"\n[yellow]💾 ANDRO is creating commit:[/yellow] "
                f"{commit_message}"
            )

            result = git_commit(
                str(PROJECT_PATH),
                commit_message
            )

            print_git_result("Git Commit", result)

            continue

        # Git push
        if git_command == "push":

            console.print(
                "\n[bold yellow]⚠️ This will push commits to the configured "
                "remote repository.[/bold yellow]"
            )

            console.print(
                "[yellow]Type YES to continue or NO to cancel.[/yellow]\n"
            )

            waiting_for_push_confirmation = True

            continue

    # ---------------------------------
    # AI CHAT
    # ---------------------------------

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = chat(
        model="qwen3:8b",
        messages=messages
    )

    answer = response.message.content

    messages.append({
        "role": "assistant",
        "content": answer
    })

    console.print(
        f"\n[bold cyan]ANDRO >[/bold cyan] {answer}\n"
    )