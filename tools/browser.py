import subprocess
import webbrowser
import urllib.parse
from pathlib import Path
from tools.system import find_chrome, CHROME_PROFILE

KNOWN_DOMAINS = {
    "youtube": "https://www.youtube.com",
    "youtube.com": "https://www.youtube.com",
    "google": "https://www.google.com",
    "google.com": "https://www.google.com",
    "storagge.in": "https://storagge.in",
    "storagge": "https://storagge.in",
    "github": "https://github.com",
    "github.com": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
}


def normalize_url(url: str) -> str:
    """Normalize a website name or URL to a valid full URL."""
    url = url.strip().lower()

    if url in KNOWN_DOMAINS:
        return KNOWN_DOMAINS[url]

    if url.startswith("http://") or url.startswith("https://"):
        return url

    # If it contains a dot (e.g. storagge.in, example.org)
    if "." in url:
        return f"https://{url}"

    # Default to .com domain
    return f"https://www.{url}.com"


def open_browser(url: str):
    """Open a URL in Google Chrome using Profile 1 (or default browser fallback)."""
    chrome_path = find_chrome()

    if chrome_path:
        try:
            cmd = [chrome_path, f"--profile-directory={CHROME_PROFILE}", url]
            subprocess.Popen(cmd)
            return {
                "success": True,
                "message": f"Opened {url} in Chrome ({CHROME_PROFILE}) successfully.",
                "url": url,
            }
        except Exception as error:
            # Fallback to standard webbrowser module
            webbrowser.open(url)
            return {
                "success": True,
                "message": f"Opened {url} in default browser (Chrome fallback: {error}).",
                "url": url,
            }

    # Fallback to standard webbrowser if Chrome path is not found
    try:
        webbrowser.open(url)
        return {
            "success": True,
            "message": f"Opened {url} in default browser.",
            "url": url,
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Could not open browser: {error}",
            "url": url,
        }


def open_website(url: str):
    """Open a website or domain in the browser."""
    full_url = normalize_url(url)
    return open_browser(full_url)


def search_google(query: str):
    """Search Google for a query in the browser."""
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Please provide a query to search on Google."
        }

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}"
    result = open_browser(search_url)
    if result["success"]:
        result["message"] = f"Searched Google for '{query}'."
    return result


def search_youtube(query: str):
    """Search YouTube for a query in the browser."""
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Please provide a query to search on YouTube."
        }

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    result = open_browser(search_url)
    if result["success"]:
        result["message"] = f"Searched YouTube for '{query}'."
    return result
