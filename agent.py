import json
import re
from pathlib import Path
from rich.console import Console

import ollama
from tools.files import find_files
from tools.system import open_app
from tools.speaker import speak
from tools.browser_control import (
    open_website,
    open_youtube,
    open_google,
    search_google,
    search_youtube,
    play_first_video,
)
from tools.git_tools import (
    is_git_repository,
    git_status,
    git_add_all,
    git_commit,
    git_push,
)


SYSTEM_PROMPT = """You are ANDRO, a powerful and intelligent personal AI assistant and computer-using agent.

You help the user with programming, projects, computer tasks, files, desktop applications, web browser automation, and Git operations.
You can understand English as well as Hindi / Hinglish phrasing (e.g. "Chrome khol do", "Mera project dhundo", "YouTube pe Techno Gamerz search karo", "YouTube kholo, Techno Gamerz search karo aur pehla video chalao", "Google pe Python tutorials search karo", "Storagge.in khol do").

TOOL ROUTING PRIORITY RULES:
1. If the user asks to play a video or search YouTube and play (e.g. "Open YouTube, search Techno Gamerz and play the first video", "Play Techno Gamerz on YouTube", "Techno Gamerz ka video chalao"), ALWAYS call `play_youtube_video` with query="Techno Gamerz". DO NOT call `open_website`.
2. If the user asks to search YouTube (e.g. "Search Techno Gamerz on YouTube", "Open YouTube and search Techno Gamerz", "search Techno Gamerz"), call `search_youtube` with query="Techno Gamerz".
3. If the user asks to search Google (e.g. "Search Python tutorials on Google", "Search for AI news"), call `search_google` with query="Python tutorials".
4. Only call `open_website` if the user ONLY wants to open a domain/website without searching or playing (e.g. "Open Storagge.in", "Open YouTube", "Open Google").
5. If the user asks to open an application (e.g. "Open Chrome", "Open Calculator", "Open Notepad"), call `open_app`.
6. If the user asks to search files/folders (e.g. "Find my ANDRO project", "Mera project dhundo"), call `search_files`.
7. For Git operations, call `git_status`, `git_add`, `git_commit`, or `git_push`.
8. For general conversation or programming questions, respond directly and concisely without calling any tool.

Safety note: Never perform sensitive online actions (passwords, logins, payments, deleting data) without user confirmation.

Always be concise, friendly, and helpful.
"""

# Ollama Tool Definitions
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Search YouTube and show the search results page WITHOUT opening or playing any video (e.g. 'search Techno Gamerz', 'search Python tutorials on YouTube').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to look up on YouTube.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_youtube_video",
            "description": "Search YouTube AND immediately play the first video result. Use this ONLY when the user explicitly asks to play a video (e.g. 'play Techno Gamerz', 'search Techno Gamerz and play the first video', 'Techno Gamerz chalao').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The video title, creator, or topic to play on YouTube.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search Google for a query, topic, news, or question in the web browser (e.g. 'Python tutorials', 'artificial intelligence news', 'best Python courses').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to search on Google (e.g. 'Python tutorials', 'artificial intelligence news').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a specific website or domain when NO search/playback is requested (e.g. 'storagge.in', 'github.com', 'google.com', 'youtube.com').",
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
    """Intelligent AI Agent for ANDRO with natural language tool routing and Playwright browser control."""

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
        # 3. PLAY FIRST YOUTUBE VIDEO
        # ---------------------------------
        elif tool_name == "play_youtube_video":
            query = args.get("query") or args.get("search_query") or ""
            query = str(query).strip()
            if not query:
                self.andro_say("What video or topic would you like me to play on YouTube?")
                return True

            self.console.print(f"\n[yellow]🎬 ANDRO is searching YouTube and playing the first video: '{query}'[/yellow]")
            result = play_first_video(query)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 4. YOUTUBE SEARCH
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
        # 5. GOOGLE SEARCH
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
        # 6. OPEN WEBSITE / URL
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
        # 7. GIT STATUS
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
        # 8. GIT ADD
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
        # 9. GIT COMMIT
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
        # 10. GIT PUSH
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

    def _parse_direct_intent(self, user_input: str) -> tuple:
        """High-precision intent detector for unambiguous commands (avoids misrouting)."""
        text = user_input.lower().strip()

        # Exit commands
        if text in ["exit", "quit", "bye"]:
            return ("exit", {})

        # YouTube video playback & compound search-and-play commands
        # e.g. "Open YouTube, search Techno Gamerz and play the first video"
        # e.g. "YouTube kholo, Techno Gamerz search karo aur pehla video chalao"
        # e.g. "Play Techno Gamerz on YouTube", "Techno Gamerz play karo"
        play_indicators = [
            "play the first video", "play first video", "play the video",
            "play video", "play", "pehla video chalao", "pehli video chalao",
            "video chalao", "chala do", "chalao", "play karo"
        ]

        has_play = any(k in text for k in play_indicators)
        has_youtube = "youtube" in text or "video" in text or text.startswith("play ")

        if has_youtube and has_play and not text in ["open youtube", "launch youtube", "youtube khol"]:
            query = text
            for phrase in [
                "open chrome, go to youtube, search for",
                "open chrome, go to youtube and search for",
                "open chrome and search youtube for",
                "open chrome and search",
                "open youtube, search for",
                "open youtube, search",
                "open youtube and search for",
                "open youtube and search",
                "open youtube",
                "search youtube for",
                "search on youtube for",
                "search on youtube",
                "search for",
                "and play the first video",
                "and play first video",
                "and play the video",
                "and play",
                "play the first video of",
                "play the first video for",
                "play the first video",
                "play first video",
                "play the video",
                "play video",
                "play",
                "youtube kholo,",
                "youtube kholo",
                "youtube pe",
                "youtube par",
                "youtube",
                "search karo aur pehla video chalao",
                "search karo aur video chalao",
                "search karo",
                "search kar do",
                "aur pehla video chalao",
                "pehla video chalao",
                "pehli video chalao",
                "pehla video",
                "video chalao",
                "chala do",
                "chalao",
                "play karo",
                "ka pehla video",
                "ka video",
                "on youtube",
                "in youtube",
                "please",
            ]:
                query = query.replace(phrase, "").strip()
            query = query.strip(" :,.-")
            if query:
                return ("play_youtube_video", {"query": query})

        # Explicit YouTube Search (e.g., "search Techno Gamerz on youtube", "search Techno Gamerz", "Techno Gamerz search karo")
        if "youtube" in text and any(k in text for k in ["search", "dhundo", "dhoondo", "look for"]):
            query = text
            for phrase in [
                "open chrome and search for", "open chrome and search",
                "open chrome, go to youtube, search for", "open chrome, go to youtube, search",
                "open youtube and search for", "open youtube and search",
                "open youtube in a new tab and search for",
                "search youtube for", "search for", "search on youtube for", "search on youtube",
                "youtube pe search karo", "youtube pe search kar do", "youtube pe search",
                "on youtube", "in youtube", "youtube par", "youtube pe", "youtube",
                "search", "please", "khol do and search", "khol do", "karo", "kar do"
            ]:
                query = query.replace(phrase, "").strip()
            query = query.strip(" :,.-")
            if query:
                return ("search_youtube", {"query": query})

        # Commands starting with "search X" when X is not a local file
        if text.startswith("search ") and not any(k in text for k in ["file", "folder", "project", "repo", "on google", "google"]):
            query = text[len("search "):].strip(" :,.-")
            # If the user previously mentioned YouTube or searches a general topic/creator
            if query:
                return ("search_youtube", {"query": query})

        # Google Searches (e.g. "search Python tutorials on Google", "google search Python tutorials")
        if "google" in text and any(k in text for k in ["search", "dhundo", "dhoondo", "look for", "find"]):
            query = text
            for phrase in [
                "open chrome and search for", "open chrome and search",
                "open google and search for", "open google and search",
                "search google for", "search for", "search on google for", "search on google",
                "google pe search karo", "google pe search kar do", "google pe search",
                "on google", "in google", "google par", "google pe", "google",
                "search", "please", "khol do and search", "khol do", "karo", "kar do"
            ]:
                query = query.replace(phrase, "").strip()
            query = query.strip(" :,.-")
            if query:
                return ("search_google", {"query": query})

        # Simple Open YouTube
        if any(text == p or text.startswith(p + " ") for p in ["open youtube", "launch youtube", "youtube khol", "youtube open", "go to youtube", "youtube kholo"]):
            return ("open_website", {"url": "https://www.youtube.com"})

        # Simple Open Google
        if any(text == p or text.startswith(p + " ") for p in ["open google", "launch google", "google khol", "google open", "go to google", "google kholo"]):
            return ("open_website", {"url": "https://www.google.com"})

        # Specific websites
        for prefix in ["open ", "launch ", "go to ", "khol do ", "khol "]:
            if text.startswith(prefix):
                target = text[len(prefix):].strip()
                for w in ["website", "site", "page", "please", "in a new tab", "in new tab"]:
                    target = target.replace(w, "").strip()
                if "." in target or target in ["storagge.in", "storagge", "github", "gmail", "chatgpt", "reddit", "wikipedia"]:
                    return ("open_website", {"url": target})

        # Open desktop applications
        for prefix in ["open ", "launch ", "start ", "khol ", "khol do ", "open karo "]:
            if text.startswith(prefix) or prefix in text:
                parts = text.split(prefix, 1)
                app = parts[1].strip()
                for w in ["please", "app", "application", "karo", "kar do", "ko", "me"]:
                    app = app.replace(w, "").strip()
                if app in ["chrome", "notepad", "calculator", "calc", "paint", "explorer", "vscode", "vs code", "code"]:
                    return ("open_app", {"app_name": app})

        # Local file searches
        for kw in ["find", "search for", "locate", "look for", "dhundo", "dhoondo"]:
            if kw in text and any(w in text for w in ["file", "folder", "project", "mera", "meri", "my"]):
                parts = text.split(kw, 1)
                query = parts[1].strip() if len(parts) > 1 else ""
                for w in ["my", "project", "folder", "file", "please", "karo", "kar do", "ko"]:
                    query = query.replace(w, "").strip()
                if query:
                    return ("search_files", {"query": query})
                elif "project" in text:
                    return ("search_files", {"query": "ANDRO"})

        # Git commands
        if "git status" in text or "check git status" in text or "status check" in text or "check status" in text:
            return ("git_status", {})
        if "git add" in text or "stage changes" in text or "stage my changes" in text or "stage all" in text:
            return ("git_add", {})
        if text.startswith("commit "):
            msg = user_input[len("commit "):].strip()
            return ("git_commit", {"message": msg})
        if "git push" in text or "push to github" in text or "push changes" in text or "push my changes" in text or "push kar do" in text:
            return ("git_push", {})

        return (None, {})

    def process_input(self, user_input: str, trigger_push_confirmation=None):
        """Process user input with high-accuracy tool routing and Ollama chat."""
        user_input = user_input.strip()
        if not user_input:
            return

        # 1. First check high-precision intent router for explicit actions
        direct_tool, direct_args = self._parse_direct_intent(user_input)
        if direct_tool:
            self.execute_tool(direct_tool, direct_args, trigger_push_confirmation)
            return

        # 2. Otherwise pass to Ollama with tools schema
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

            # Conversational response
            content = getattr(message, "content", None) or ""
            if content:
                self.messages.append({
                    "role": "assistant",
                    "content": content,
                })
                self.andro_say(content)
            else:
                self.andro_say("I'm here to help! What would you like to do?")

        except Exception as error:
            error_str = str(error)
            if "connection" in error_str.lower() or "connect" in error_str.lower():
                msg = "Ollama is not running or unreachable. Please ensure Ollama is started with model 'qwen3:8b'."
            else:
                msg = f"AI Error: {error_str}"
            self.console.print(f"\n[bold red]❌ {msg}[/bold red]\n")
            speak(msg)
