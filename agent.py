import json
from pathlib import Path
from rich.console import Console

import ollama
from tools.files import find_files
from tools.system import open_app
from tools.speaker import speak
from tools.browser import open_website, search_google, search_youtube
from tools.git_tools import (
    is_git_repository,
    git_status,
    git_add_all,
    git_commit,
    git_push,
)


SYSTEM_PROMPT = """You are ANDRO, a powerful and intelligent personal AI assistant and computer-using agent.

You help the user with programming, projects, computer tasks, files, desktop applications, web browser automation, and Git operations.
You can understand English as well as Hindi / Hinglish phrasing (e.g. "Chrome khol do", "Mera project dhundo", "YouTube pe Techno Gamerz search karo", "Google pe Python tutorials search karo", "Storagge.in khol do").

You have access to tools for:
- Searching files, folders, and projects (`search_files`)
- Opening desktop applications like Chrome, Notepad, Calculator, Paint, Explorer, VS Code (`open_app`)
- Opening websites, domains, or URLs in the web browser (`open_website`)
- Searching Google in the web browser (`search_google`)
- Searching YouTube in the web browser (`search_youtube`)
- Git operations: checking repository status (`git_status`), staging changes (`git_add`), committing changes (`git_commit`), and pushing to GitHub (`git_push`)

When the user asks you to perform one or more of these actions (including compound requests like "Open Chrome, go to YouTube, search for Techno Gamerz" or "Open Google and search for Python courses"), choose the appropriate tool and provide any required parameters.
If the user asks a general question, a programming question, or wants to chat, respond directly and concisely without calling any tool.

Safety note: Never perform sensitive online actions (passwords, logins, payments, deleting data) without user confirmation.

Always be concise, friendly, and helpful.
"""

# Ollama Tool Definitions
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files, folders, or projects on the user's computer by name or search keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The exact name, keyword, or pattern of the file, folder, or project to search for (e.g. 'ANDRO', 'main.py', 'notes').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open or launch a desktop application such as Chrome, Notepad, Calculator, Paint, Explorer, or VS Code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g. 'chrome', 'notepad', 'calculator', 'paint', 'explorer', 'vscode').",
                    }
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website, domain, or URL in the web browser (e.g. 'storagge.in', 'youtube.com', 'google.com', 'github.com').",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The website domain or URL to open (e.g. 'storagge.in', 'youtube.com', 'google.com').",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search Google for a query, topic, news, or question in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to search on Google (e.g. 'Python tutorials', 'artificial intelligence news', 'best Python courses').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Search YouTube for videos, channels, or tutorials in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to search on YouTube (e.g. 'Techno Gamerz', 'Techno Gamerz latest video', 'Python tutorials').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Check the Git status of the current project repository (shows changed, untracked, and staged files).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_add",
            "description": "Stage all changes (git add .) in the current project repository.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Commit staged changes in the Git repository with a commit message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A commit message describing what changes are being committed.",
                    }
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_push",
            "description": "Push committed changes to the GitHub remote repository. Requires user confirmation before execution.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


class AndroAgent:
    """Intelligent AI Agent for ANDRO with natural language tool routing and browser automation."""

    def __init__(self, project_path: Path, console: Console, model: str = "qwen3:8b"):
        self.project_path = project_path
        self.console = console
        self.model = model
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def andro_say(self, text: str):
        """Print and speak ANDRO's response."""
        text = str(text)
        self.console.print(f"\n[bold cyan]ANDRO >[/bold cyan] {text}\n")
        speak(text)

    def print_git_result(self, title: str, result: dict):
        """Print Git tool results and speak them."""
        if result.get("success"):
            self.console.print(f"\n[bold green]✅ {title}[/bold green]")
            self.console.print(f"[cyan]{result['message']}[/cyan]\n")
            speak(result["message"])
        else:
            self.console.print(f"\n[bold red]❌ {title} failed[/bold red]")
            self.console.print(f"[red]{result['message']}[/red]\n")
            speak(result["message"])

    def execute_tool(self, tool_name: str, args: dict, trigger_push_confirmation=None) -> bool:
        """Execute a detected tool with given arguments."""

        # ---------------------------------
        # 1. FILE SEARCH
        # ---------------------------------
        if tool_name == "search_files":
            query = args.get("query") or args.get("search_query") or ""
            query = str(query).strip()
            if not query:
                self.andro_say("What file or folder would you like me to search for?")
                return True

            self.console.print(f"\n[yellow]🔍 ANDRO is searching for: {query}[/yellow]")
            results = find_files(query)
            if results:
                self.console.print("\n[bold green]📂 Results found:[/bold green]\n")
                speak(f"I found {len(results)} matching files or folders.")
                for index, result in enumerate(results, start=1):
                    self.console.print(f"{index}. [{result['type'].upper()}] {result['name']}")
                    self.console.print(f"   📍 {result['path']}\n")
            else:
                message = "No matching files or folders were found."
                self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")
                speak(message)
            return True

        # ---------------------------------
        # 2. OPEN APPLICATION
        # ---------------------------------
        elif tool_name == "open_app":
            app_name = args.get("app_name") or args.get("name") or ""
            app_name = str(app_name).strip()
            if not app_name:
                self.andro_say("Which application would you like me to open?")
                return True

            self.console.print(f"\n[yellow]💻 ANDRO is opening: {app_name}[/yellow]")
            result = open_app(app_name)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 3. OPEN WEBSITE / URL
        # ---------------------------------
        elif tool_name == "open_website":
            url = args.get("url") or args.get("website") or ""
            url = str(url).strip()
            if not url:
                self.andro_say("Which website would you like me to open?")
                return True

            self.console.print(f"\n[yellow]🌐 ANDRO is opening website: {url}[/yellow]")
            result = open_website(url)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 4. GOOGLE SEARCH
        # ---------------------------------
        elif tool_name == "search_google":
            query = args.get("query") or args.get("search_query") or ""
            query = str(query).strip()
            if not query:
                self.andro_say("What would you like me to search on Google?")
                return True

            self.console.print(f"\n[yellow]🔎 ANDRO is searching Google for: '{query}'[/yellow]")
            result = search_google(query)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 5. YOUTUBE SEARCH
        # ---------------------------------
        elif tool_name == "search_youtube":
            query = args.get("query") or args.get("search_query") or ""
            query = str(query).strip()
            if not query:
                self.andro_say("What would you like me to search on YouTube?")
                return True

            self.console.print(f"\n[yellow]🎬 ANDRO is searching YouTube for: '{query}'[/yellow]")
            result = search_youtube(query)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 6. GIT STATUS
        # ---------------------------------
        elif tool_name == "git_status":
            if not is_git_repository(str(self.project_path)):
                message = "This project is not a Git repository."
                self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")
                speak(message)
                return True

            self.console.print("\n[yellow]🔍 ANDRO is checking Git status...[/yellow]")
            result = git_status(str(self.project_path))
            self.print_git_result("Git Status", result)
            return True

        # ---------------------------------
        # 7. GIT ADD
        # ---------------------------------
        elif tool_name in ["git_add", "git_add_all"]:
            if not is_git_repository(str(self.project_path)):
                message = "This project is not a Git repository."
                self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")
                speak(message)
                return True

            self.console.print("\n[yellow]➕ ANDRO is staging changes...[/yellow]")
            result = git_add_all(str(self.project_path))
            self.print_git_result("Git Add", result)
            return True

        # ---------------------------------
        # 8. GIT COMMIT
        # ---------------------------------
        elif tool_name == "git_commit":
            if not is_git_repository(str(self.project_path)):
                message = "This project is not a Git repository."
                self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")
                speak(message)
                return True

            commit_message = args.get("message") or args.get("commit_message") or ""
            commit_message = str(commit_message).strip()
            if not commit_message:
                message = "Please provide a commit message."
                self.console.print(f"\n[yellow]{message}[/yellow]")
                self.console.print("[cyan]Example: commit Added new feature[/cyan]\n")
                speak(message)
                return True

            self.console.print(f"\n[yellow]💾 ANDRO is creating commit: {commit_message}[/yellow]")
            result = git_commit(str(self.project_path), commit_message)
            self.print_git_result("Git Commit", result)
            return True

        # ---------------------------------
        # 9. GIT PUSH
        # ---------------------------------
        elif tool_name == "git_push":
            if not is_git_repository(str(self.project_path)):
                message = "This project is not a Git repository."
                self.console.print(f"\n[bold red]❌ {message}[/bold red]\n")
                speak(message)
                return True

            warning = (
                "This will push commits to the configured GitHub repository. "
                "Say yes to continue or no to cancel."
            )
            self.console.print(
                "\n[bold yellow]⚠️ This will push commits to the configured remote repository.[/bold yellow]"
            )
            self.console.print("[yellow]Type YES to continue or NO to cancel.[/yellow]\n")
            speak(warning)
            if trigger_push_confirmation:
                trigger_push_confirmation()
            return True

        return False

    def _fallback_parse(self, user_input: str) -> tuple:
        """Rule-based fallback if Ollama model is offline or returns edge cases."""
        text = user_input.lower().strip()

        # Exit
        if text in ["exit", "quit", "bye"]:
            return ("exit", {})

        # YouTube searches & multi-step YouTube commands
        if "youtube" in text:
            if any(k in text for k in ["search", "dhundo", "dhoondo", "play", "dekho"]):
                query = text
                for remove_phrase in [
                    "open chrome and search for",
                    "open chrome and search",
                    "open chrome, go to youtube, search for",
                    "open chrome, go to youtube and search for",
                    "open chrome, go to youtube, search",
                    "open youtube and search for",
                    "open youtube and search",
                    "open youtube in a new tab and search for",
                    "search youtube for",
                    "search for",
                    "search on youtube for",
                    "search on youtube",
                    "youtube pe search karo",
                    "youtube pe search kar do",
                    "youtube pe search",
                    "on youtube",
                    "in youtube",
                    "youtube par",
                    "youtube pe",
                    "youtube",
                    "search",
                    "please",
                    "khol do and search",
                    "khol do",
                ]:
                    query = query.replace(remove_phrase, "").strip()
                query = query.strip(" :,.-")
                if query:
                    return ("search_youtube", {"query": query})
            # Just open youtube
            if any(text.startswith(p) for p in ["open youtube", "launch youtube", "youtube khol", "youtube open", "go to youtube"]):
                return ("open_website", {"url": "https://www.youtube.com"})

        # Google searches & multi-step Google commands
        if "google" in text:
            if any(k in text for k in ["search", "dhundo", "dhoondo", "look for", "find"]):
                query = text
                for remove_phrase in [
                    "open chrome and search for",
                    "open chrome and search",
                    "open google and search for",
                    "open google and search",
                    "search google for",
                    "search for",
                    "search on google for",
                    "search on google",
                    "google pe search karo",
                    "google pe search kar do",
                    "google pe search",
                    "on google",
                    "in google",
                    "google par",
                    "google pe",
                    "google",
                    "search",
                    "please",
                    "khol do and search",
                    "khol do",
                ]:
                    query = query.replace(remove_phrase, "").strip()
                query = query.strip(" :,.-")
                if query:
                    return ("search_google", {"query": query})
            # Just open google
            if any(text.startswith(p) for p in ["open google", "launch google", "google khol", "google open", "go to google"]):
                return ("open_website", {"url": "https://www.google.com"})

        # General web searches (e.g. "search for artificial intelligence news")
        if text.startswith("search for ") or text.startswith("search "):
            query = text.split("search for ", 1)[-1] if text.startswith("search for ") else text.split("search ", 1)[-1]
            query = query.strip(" :,.-")
            if query and not any(k in query for k in ["file", "folder", "project", "repo"]):
                return ("search_google", {"query": query})

        # Opening specific websites
        for prefix in ["open ", "launch ", "go to ", "khol do ", "khol "]:
            if text.startswith(prefix):
                target = text[len(prefix):].strip()
                for w in ["website", "site", "page", "please", "in a new tab", "in new tab"]:
                    target = target.replace(w, "").strip()
                if "." in target or target in ["storagge.in", "storagge", "github", "gmail", "chatgpt", "reddit", "wikipedia"]:
                    return ("open_website", {"url": target})

        # Open desktop apps
        for prefix in ["open ", "launch ", "start ", "khol ", "khol do ", "open karo "]:
            if text.startswith(prefix) or prefix in text:
                parts = text.split(prefix, 1)
                app = parts[1].strip()
                for w in ["please", "app", "application", "karo", "kar do", "ko", "me"]:
                    app = app.replace(w, "").strip()
                if app:
                    return ("open_app", {"app_name": app})

        if "chrome khol" in text or "chrome open" in text or "open chrome" in text:
            return ("open_app", {"app_name": "chrome"})
        if "notepad khol" in text or "notepad open" in text or "open notepad" in text:
            return ("open_app", {"app_name": "notepad"})
        if "calculator khol" in text or "calc khol" in text or "open calc" in text or "open calculator" in text:
            return ("open_app", {"app_name": "calculator"})

        # File search
        for kw in ["find", "search for", "search", "locate", "look for", "dhundo", "dhoondo"]:
            if kw in text:
                parts = text.split(kw, 1)
                query = parts[1].strip() if len(parts) > 1 else ""
                for w in ["my", "project", "folder", "file", "please", "karo", "kar do", "ko"]:
                    query = query.replace(w, "").strip()
                if query:
                    return ("search_files", {"query": query})
                elif "project" in text:
                    return ("search_files", {"query": "ANDRO"})

        if "dhundo" in text or "dhoondo" in text:
            q = text.replace("dhundo", "").replace("dhoondo", "").replace("mera", "").replace("meri", "").replace("project", "ANDRO").replace("ko", "").strip()
            return ("search_files", {"query": q or "ANDRO"})

        # Git commands
        if "git status" in text or "check git status" in text or "status check" in text or "check status" in text:
            return ("git_status", {})
        if "git add" in text or "stage changes" in text or "stage my changes" in text or "stage all" in text:
            return ("git_add", {})
        if text.startswith("commit "):
            msg = user_input[len("commit "):].strip()
            return ("git_commit", {"message": msg})
        if "commit" in text and ("message" in text or "with" in text):
            msg = text.split("message", 1)[-1].strip() if "message" in text else text.split("commit", 1)[-1].strip()
            return ("git_commit", {"message": msg})
        if "git push" in text or "push to github" in text or "push changes" in text or "push my changes" in text or "push kar do" in text:
            return ("git_push", {})

        return (None, {})

    def process_input(self, user_input: str, trigger_push_confirmation=None):
        """Process user input with Ollama natural language tool routing."""
        user_input = user_input.strip()
        if not user_input:
            return

        self.messages.append({
            "role": "user",
            "content": user_input,
        })

        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=AGENT_TOOLS,
            )

            # Check if model chose a tool
            message = response.message
            tool_calls = getattr(message, "tool_calls", None) or []

            if tool_calls:
                for tool_call in tool_calls:
                    func = getattr(tool_call, "function", None) or tool_call.get("function", {})
                    name = getattr(func, "name", None) or (func.get("name") if isinstance(func, dict) else "")
                    arguments = getattr(func, "arguments", None) or (func.get("arguments") if isinstance(func, dict) else {})

                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except Exception:
                            arguments = {}

                    executed = self.execute_tool(name, arguments, trigger_push_confirmation)
                    if executed:
                        return

            # No tool called or tool call not recognized: conversational response
            content = getattr(message, "content", None) or ""
            if content:
                self.messages.append({
                    "role": "assistant",
                    "content": content,
                })
                self.andro_say(content)
            else:
                # Fallback if content was empty
                fallback_tool, fallback_args = self._fallback_parse(user_input)
                if fallback_tool:
                    self.execute_tool(fallback_tool, fallback_args, trigger_push_confirmation)
                else:
                    self.andro_say("I didn't quite understand that. How can I help you?")

        except Exception as error:
            # Fallback to local heuristic parser if Ollama is offline / error occurs
            fallback_tool, fallback_args = self._fallback_parse(user_input)
            if fallback_tool:
                self.execute_tool(fallback_tool, fallback_args, trigger_push_confirmation)
            else:
                error_str = str(error)
                if "connection" in error_str.lower() or "connect" in error_str.lower():
                    msg = "Ollama is not running or unreachable. Please ensure Ollama is started with model 'qwen3:8b'."
                else:
                    msg = f"AI Error: {error_str}"
                self.console.print(f"\n[bold red]❌ {msg}[/bold red]\n")
                speak(msg)
