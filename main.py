from ollama import chat
from rich.console import Console

from tools.files import find_files
from tools.system import open_app

console = Console()

SYSTEM_PROMPT = """
You are ANDRO, a powerful personal AI assistant.

You help the user with programming, projects, planning,
files, and computer-related tasks.

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
        "khol",
        "khol do",
    ]

    for prefix in prefixes:

        if command_lower.startswith(prefix):

            app_name = command_lower[len(prefix):].strip()

            # Clean common words
            for word in ["please", "app", "application", "karo", "kar do"]:
                app_name = app_name.replace(word, "").strip()

            return app_name

    return None


console.print("[bold cyan]🤖 ANDRO is online![/bold cyan]")
console.print("[yellow]Type 'exit' to close ANDRO.[/yellow]\n")

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


while True:

    user_input = console.input("[bold green]YOU > [/bold green]")

    # Exit command
    if user_input.lower() in ["exit", "quit", "bye"]:
        console.print("\n[bold red]ANDRO: Goodbye! 👋[/bold red]")
        break

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