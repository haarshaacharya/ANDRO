import os
import re
import subprocess
import webbrowser
import urllib.parse
import urllib.request
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

    if "." in url:
        return f"https://{url}"

    return f"https://www.{url}.com"


def open_browser(url: str):
    """Instantly open a URL in Google Chrome using Profile 1 (or default browser fallback)."""
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
    """Open a website or domain in Google Chrome (Profile 1)."""
    full_url = normalize_url(url)
    return open_browser(full_url)


def open_youtube():
    """Open YouTube in Google Chrome (Profile 1)."""
    return open_browser("https://www.youtube.com")


def open_google():
    """Open Google in Google Chrome (Profile 1)."""
    return open_browser("https://www.google.com")


def search_google(query: str):
    """Search Google for a query in Google Chrome (Profile 1) instantaneously."""
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Please provide a query to search on Google.",
        }

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}"
    result = open_browser(search_url)
    if result["success"]:
        result["message"] = f"Searched Google for '{query}' in Chrome ({CHROME_PROFILE})."
    return result


def search_youtube(query: str):
    """Search YouTube for a query in Google Chrome (Profile 1) instantaneously."""
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Please provide a query to search on YouTube.",
        }

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    result = open_browser(search_url)
    if result["success"]:
        result["message"] = f"Searched YouTube for '{query}' in Chrome ({CHROME_PROFILE})."
    return result


def _fast_resolve_youtube_first_video(query: str):
    """Ultra-fast sub-second resolver for YouTube search result to first video URL."""
    try:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=1.2) as response:
            html = response.read().decode("utf-8", errors="ignore")
            # Extract video ID
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if video_ids:
                # Extract video title
                title_match = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"', html)
                video_title = title_match.group(1) if title_match else query
                return f"https://www.youtube.com/watch?v={video_ids[0]}", video_title
    except Exception:
        pass
    return None, query


def play_first_video(query: str = ""):
    """Instantaneously search YouTube and play the top video in Chrome (Profile 1)."""
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Please specify what video or topic you would like to play on YouTube.",
        }

    # Fast sub-second video URL extraction
    video_url, video_title = _fast_resolve_youtube_first_video(query)

    if not video_url:
        # Fallback to search results URL directly if quick fetch failed
        encoded_query = urllib.parse.quote_plus(query)
        video_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    # Open immediately in user's Chrome Profile 1 (< 0.5s total time!)
    result = open_browser(video_url)

    if result.get("success"):
        return {
            "success": True,
            "message": f"Playing '{video_title}' on YouTube in Chrome ({CHROME_PROFILE}).",
            "video_title": video_title,
            "url": video_url,
        }
    return result
