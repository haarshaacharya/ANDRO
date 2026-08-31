import json
import re
import time
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
from tools.desktop import (
    type_text,
    press_key,
    keyboard_shortcut,
    take_screenshot,
    mouse_click,
    mouse_move,
)
from tools.vision import analyze_screen
from tools.git_tools import (
    is_git_repository,
    git_status,
    git_add_all,
    git_commit,
    git_push,
)


SYSTEM_PROMPT = """You are ANDRO, a powerful and intelligent personal AI assistant, multi-step computer agent, and screen vision assistant.

You help the user with programming, projects, computer tasks, files, desktop applications, web browser automation, desktop automation (typing text, keys, shortcuts, screenshots, mouse control), Smart Screen Vision analysis, and Git operations.
You can understand English as well as Hindi / Hinglish phrasing (e.g. "Chrome khol do", "Mera project dhundo", "YouTube pe Techno Gamerz search karo", "Techno Gamerz play karo", "Notepad me hello likho", "Enter dabao", "Screen par kya hai", "Is error ko explain karo").

TOOL ROUTING PRIORITY RULES:
1. If the user asks about the screen or visual contents (e.g. "What is on my screen?", "Analyze my screen", "Screen par kya hai?", "Is error ko explain karo"), call `analyze_screen`.
2. If the user asks to type text (e.g. "Type hello in Notepad", "Type Hello World", "likho Hello"), call `type_text`.
3. If the user asks to press a key (e.g. "Press Enter", "Press Escape", "Enter dabao"), call `press_key`.
4. If the user asks for a keyboard shortcut (e.g. "Press Ctrl L", "Shortcut Ctrl C", "Ctrl V dabao"), call `keyboard_shortcut`.
5. If the user asks for a screenshot (e.g. "Take a screenshot", "Screenshot lo"), call `take_screenshot`.
6. If the user asks to move the mouse or click (e.g. "Move mouse to 500 400", "Click", "Double click"), call `mouse_move` or `mouse_click`.
7. If the user asks to play a video or search YouTube and play (e.g. "Open YouTube, search Techno Gamerz and play the first video", "Play Techno Gamerz on YouTube", "Techno Gamerz play karo"), call `play_youtube_video`.
8. If the user asks to search YouTube (e.g. "search Techno Gamerz", "search Techno Gamerz on YouTube"), call `search_youtube`.
9. If the user asks to search Google (e.g. "Search Python tutorials on Google"), call `search_google`.
10. Only call `open_website` if the user ONLY wants to open a domain/website without searching or playing (e.g. "Open Storagge.in", "Open YouTube", "Open Google").
11. If the user asks to open an application (e.g. "Open Chrome", "Open Calculator", "Open Notepad"), call `open_app`.
12. If the user asks to search files/folders (e.g. "Find my ANDRO project", "Mera project dhundo"), call `search_files`.
13. For Git operations, call `git_status`, `git_add`, `git_commit`, or `git_push`.
14. For general conversation or programming questions, respond directly and concisely without calling any tool.

Safety note: Never perform destructive actions automatically. Git push requires explicit confirmation.

Always be concise, friendly, and helpful.
"""

# Ollama Tool Definitions
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Capture the current screen on demand and visually analyze active windows, text, messages, or error dialogs (e.g. 'What is on my screen?', 'Explain this error', 'Screen par kya hai').",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Specific question or focus area for visual analysis (e.g. 'explain the visible error message').",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type or paste text into the currently active window or application (e.g. 'Type hello in Notepad', 'Type Hello world').",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The exact text to type into the focused window.",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key safely (e.g. 'enter', 'esc', 'escape', 'tab', 'space', 'backspace', 'up', 'down', 'f5').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key name to press (e.g. 'enter', 'escape', 'tab', 'space').",
                    }
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_shortcut",
            "description": "Execute a keyboard shortcut combination (e.g. 'ctrl+c', 'ctrl+v', 'ctrl+l', 'ctrl+n', 'alt+tab', 'ctrl+w').",
            "parameters": {
                "type": "object",
                "properties": {
                    "shortcut": {
                        "type": "string",
                        "description": "The shortcut combination to press (e.g. 'ctrl+c', 'ctrl+l', 'ctrl+v').",
                    }
                },
                "required": ["shortcut"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture the full screen and save as a timestamped image in Pictures/ANDRO_Screenshots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional custom filename for the screenshot.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Click the mouse at the current position (e.g. 'left', 'right', 'double click').",
            "parameters": {
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "description": "Mouse button: 'left', 'right', or 'middle'. Default is 'left'.",
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of clicks: 1 for single click, 2 for double click.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Move the mouse cursor smoothly to screen coordinates (x, y).",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "The X screen coordinate.",
                    },
                    "y": {
                        "type": "integer",
                        "description": "The Y screen coordinate.",
                    }
                },
                "required": ["x", "y"],
            },
        },
    },
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
    """Intelligent Multi-Step AI Agent for ANDRO with planning, screen vision, and computer automation."""

    def __init__(self, project_path: Path, console: Console, model: str = "qwen3:8b"):
        self.project_path = project_path
        self.console = console
        self.model = model
        self.stop_requested = False
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def stop(self):
        """Emergency stop handler to abort the active multi-step task immediately."""
        self.stop_requested = True

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
        if self.stop_requested:
            return False

        # ---------------------------------
        # 1. SMART SCREEN VISION
        # ---------------------------------
        if tool_name == "analyze_screen":
            prompt = args.get("prompt") or ""
            self.console.print("\n[yellow]👁️ ANDRO is capturing and analyzing screen...[/yellow]")
            result = analyze_screen(prompt)
            if result.get("success"):
                self.console.print(f"\n[bold green]🖥️ Screen Analysis:[/bold green]\n{result['message']}\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 2. TYPE TEXT
        # ---------------------------------
        elif tool_name == "type_text":
            text_to_type = args.get("text") or ""
            text_to_type = str(text_to_type)
            if not text_to_type:
                self.andro_say("What text would you like me to type?")
                return True

            self.console.print(f"\n[yellow]⌨️ ANDRO is typing text: '{text_to_type}'[/yellow]")
            result = type_text(text_to_type)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 3. PRESS KEY
        # ---------------------------------
        elif tool_name == "press_key":
            key = args.get("key") or ""
            key = str(key).strip()
            if not key:
                self.andro_say("Which key should I press?")
                return True

            self.console.print(f"\n[yellow]⌨️ ANDRO is pressing key: '{key}'[/yellow]")
            result = press_key(key)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 4. KEYBOARD SHORTCUT
        # ---------------------------------
        elif tool_name == "keyboard_shortcut":
            shortcut = args.get("shortcut") or ""
            shortcut = str(shortcut).strip()
            if not shortcut:
                self.andro_say("Which shortcut should I press?")
                return True

            self.console.print(f"\n[yellow]⌨️ ANDRO is pressing shortcut: '{shortcut}'[/yellow]")
            result = keyboard_shortcut(shortcut)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 5. TAKE SCREENSHOT
        # ---------------------------------
        elif tool_name == "take_screenshot":
            filename = args.get("filename") or ""
            self.console.print("\n[yellow]📸 ANDRO is capturing screenshot...[/yellow]")
            result = take_screenshot(filename)
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak("Screenshot taken and saved successfully.")
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 6. MOUSE CLICK
        # ---------------------------------
        elif tool_name == "mouse_click":
            button = args.get("button") or "left"
            clicks = args.get("clicks") or 1
            result = mouse_click(button=button, clicks=int(clicks))
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 7. MOUSE MOVE
        # ---------------------------------
        elif tool_name == "mouse_move":
            x = args.get("x") or 0
            y = args.get("y") or 0
            result = mouse_move(int(x), int(y))
            if result.get("success"):
                self.console.print(f"\n[bold green]✅ ANDRO: {result['message']}[/bold green]\n")
                speak(result["message"])
            else:
                self.console.print(f"\n[bold red]❌ ANDRO: {result['message']}[/bold red]\n")
                speak(result["message"])
            return True

        # ---------------------------------
        # 8. FILE SEARCH
        # ---------------------------------
        elif tool_name == "search_files":
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
        # 9. OPEN APPLICATION
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
        # 10. PLAY FIRST YOUTUBE VIDEO
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
        # 11. YOUTUBE SEARCH
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
        # 12. GOOGLE SEARCH
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
        # 13. OPEN WEBSITE / URL
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
        # 14. GIT STATUS
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
        # 15. GIT ADD
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
        # 16. GIT COMMIT
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
        # 17. GIT PUSH
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

    def _decompose_multi_step(self, user_input: str) -> list:
        """Decompose compound multi-step commands into ordered executable actions."""
        text = user_input.lower().strip()

        # Multi-Step Example: "Open Notepad and type Hello from ANDRO" / "Notepad kholo aur hello likho"
        if ("open notepad" in text or "notepad khol" in text) and any(k in text for k in ["type ", "likho ", "write "]):
            # Extract text to type
            type_part = ""
            for kw in ["type ", "likho ", "write "]:
                if kw in text:
                    type_part = user_input[text.index(kw) + len(kw):].strip()
                    break
            if type_part:
                return [
                    {"tool": "open_app", "args": {"app_name": "notepad"}, "title": "Opening Notepad"},
                    {"tool": "_wait", "args": {"seconds": 0.8}, "title": "Waiting for Notepad window"},
                    {"tool": "type_text", "args": {"text": type_part}, "title": f"Typing text '{type_part}'"},
                ]

        # Multi-Step Example: "Open Chrome, search Python tutorials, then open YouTube and search Techno Gamerz"
        if ("open chrome" in text or "chrome" in text) and "open youtube" in text and ("search" in text or "play" in text):
            # Extract queries
            steps = []
            if "search" in text and "python" in text:
                steps.append({"tool": "search_google", "args": {"query": "Python tutorials"}, "title": "Searching Python tutorials on Google"})
            if "techno gamerz" in text:
                if "play" in text:
                    steps.append({"tool": "play_youtube_video", "args": {"query": "Techno Gamerz"}, "title": "Searching YouTube and playing Techno Gamerz"})
                else:
                    steps.append({"tool": "search_youtube", "args": {"query": "Techno Gamerz"}, "title": "Searching Techno Gamerz on YouTube"})
            if steps:
                return steps

        # Multi-Step Example: "Take a screenshot and tell me what is on my screen" / "Screenshot lo aur explain karo"
        if ("screenshot" in text or "screen" in text) and any(k in text for k in ["tell me", "explain", "kya hai", "analyze", "problem", "error"]):
            return [
                {"tool": "analyze_screen", "args": {"prompt": user_input}, "title": "Analyzing screen contents and errors"},
            ]

        return []

    def execute_multi_step_plan(self, plan: list, trigger_push_confirmation=None) -> bool:
        """Execute an ordered multi-step plan with live step-by-step progress tracking."""
        self.stop_requested = False
        total_steps = len(plan)
        self.console.print(f"\n[bold magenta]🧠 ANDRO is planning the task ({total_steps} steps)...[/bold magenta]\n")

        for index, step in enumerate(plan, start=1):
            if self.stop_requested:
                self.console.print("\n[bold yellow]🛑 Task stopped by user.[/bold yellow]\n")
                self.andro_say("Current task stopped.")
                self.stop_requested = False
                return True

            tool_name = step.get("tool")
            args = step.get("args", {})
            title = step.get("title", f"Step {index}")

            self.console.print(f"[bold cyan]Step {index}/{total_steps}: {title}...[/bold cyan]")

            if tool_name == "_wait":
                time.sleep(args.get("seconds", 0.5))
            else:
                self.execute_tool(tool_name, args, trigger_push_confirmation)

            self.console.print(f"[bold green]✅ Completed Step {index}/{total_steps}[/bold green]\n")

        self.console.print("[bold green]🎉 Task completed successfully.[/bold green]\n")
        return True

    def _parse_direct_intent(self, user_input: str) -> tuple:
        """High-precision sub-millisecond intent detector for unambiguous commands."""
        text = user_input.lower().strip()

        # Exit commands
        if text in ["exit", "quit", "bye"]:
            return ("exit", {})

        # Emergency Stop commands
        if text in ["stop andro", "stop", "ruk jao", "ruko"]:
            self.stop()
            return ("stop", {})

        # Screen Vision commands (e.g. "What is on my screen?", "Screen par kya hai?", "Analyze my screen", "Is error ko explain karo")
        vision_triggers = [
            "what is on my screen", "what's on my screen", "what is on screen",
            "screen par kya hai", "screen pe kya hai", "analyze my screen",
            "analyze the screen", "screen dekho", "what does this error mean",
            "what is wrong on my screen", "is error ko explain karo",
            "explain this error", "screen par kya problem hai", "screen vision"
        ]
        if any(t in text for t in vision_triggers):
            return ("analyze_screen", {"prompt": user_input})

        # Screenshot commands
        if any(k in text for k in ["take a screenshot", "take screenshot", "capture screen", "screenshot lo", "screenshot le lo", "screenshot"]):
            return ("take_screenshot", {})

        # Type text commands (e.g. "Type hello in Notepad", "Type Hello World", "likho hello")
        if text.startswith("type ") or text.startswith("likho ") or " me likho " in text or " mein likho " in text:
            cleaned = user_input
            for prefix in ["Type ", "type ", "likho ", "Likho "]:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):]
                    break
            for suffix_word in [" in notepad", " in chrome", " in editor", " me", " mein"]:
                if cleaned.lower().endswith(suffix_word):
                    cleaned = cleaned[:-len(suffix_word)]
            cleaned = cleaned.strip(" :\"'")
            if cleaned:
                return ("type_text", {"text": cleaned})

        # Key press commands (e.g. "Press Enter", "Enter dabao", "Press Escape", "Press Tab")
        key_matches = {
            "enter": ["press enter", "enter dabao", "hit enter", "press return"],
            "escape": ["press escape", "press esc", "esc dabao", "escape dabao"],
            "tab": ["press tab", "tab dabao"],
            "space": ["press space", "space dabao", "space bar"],
            "backspace": ["press backspace", "backspace dabao"],
            "delete": ["press delete", "delete dabao"],
            "f5": ["press f5", "refresh page", "page refresh karo", "f5 dabao"],
        }
        for key, triggers in key_matches.items():
            if any(text == t or text.startswith(t + " ") for t in triggers):
                return ("press_key", {"key": key})

        # Keyboard shortcuts (e.g. "Press Ctrl L", "Press Ctrl+C", "Shortcut Ctrl V", "Ctrl L dabao")
        if "ctrl" in text or "alt" in text or "shortcut" in text:
            m = re.search(r'(ctrl|alt|shift|win)[\s\+\-]+([a-z0-9]+)', text)
            if m:
                shortcut_str = f"{m.group(1)}+{m.group(2)}"
                return ("keyboard_shortcut", {"shortcut": shortcut_str})

        # Mouse click commands
        if text in ["click", "click karo", "left click", "mouse click"]:
            return ("mouse_click", {"button": "left", "clicks": 1})
        if text in ["double click", "double click karo", "2 bar click"]:
            return ("mouse_click", {"button": "left", "clicks": 2})
        if text in ["right click", "right click karo"]:
            return ("mouse_click", {"button": "right", "clicks": 1})

        # Mouse move commands (e.g. "Move mouse to 500 400", "Move cursor to 500 400")
        if "mouse" in text or "cursor" in text:
            m = re.search(r'(\d+)[,\s]+(\d+)', text)
            if m:
                return ("mouse_move", {"x": int(m.group(1)), "y": int(m.group(2))})

        # YouTube video playback & compound search-and-play commands
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
        """Process user input with multi-step planning, high-accuracy tool routing, and Ollama chat."""
        user_input = user_input.strip()
        if not user_input:
            return

        self.stop_requested = False

        # 1. Check for compound multi-step tasks (STEP 12)
        multi_step_plan = self._decompose_multi_step(user_input)
        if multi_step_plan:
            self.execute_multi_step_plan(multi_step_plan, trigger_push_confirmation)
            return

        # 2. Check high-precision direct intent router
        direct_tool, direct_args = self._parse_direct_intent(user_input)
        if direct_tool:
            if direct_tool == "stop":
                self.andro_say("Current task stopped.")
                return
            self.execute_tool(direct_tool, direct_args, trigger_push_confirmation)
            return

        # 3. Otherwise pass to Ollama with tools schema
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
                    if self.stop_requested:
                        self.andro_say("Current task stopped.")
                        return

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
