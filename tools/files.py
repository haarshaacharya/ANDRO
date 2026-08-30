from pathlib import Path

USER_HOME = Path.home()

SEARCH_FOLDERS = [
    USER_HOME / "OneDrive" / "Attachments" / "Desktop",
    USER_HOME / "Documents",
    USER_HOME / "Downloads",
]

IGNORE_FOLDERS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".idea",
    ".next",
    "dist",
    "build",
}


def find_files(query: str, max_results: int = 20):
    """Search files and folders intelligently."""

    query = query.lower().strip()

    exact_matches = []
    starts_with_matches = []
    contains_matches = []

    for folder in SEARCH_FOLDERS:

        if not folder.exists():
            continue

        try:
            for path in folder.rglob("*"):

                # Ignore unnecessary folders
                if any(
                    part.lower() in IGNORE_FOLDERS
                    for part in path.parts
                ):
                    continue

                name = path.name.lower()

                result = {
                    "name": path.name,
                    "path": str(path),
                    "type": "folder" if path.is_dir() else "file"
                }

                if name == query:
                    exact_matches.append(result)

                elif name.startswith(query):
                    starts_with_matches.append(result)

                elif query in name:
                    contains_matches.append(result)

        except (PermissionError, OSError):
            continue

    # If exact matches exist, return ONLY them
    if exact_matches:
        return exact_matches[:max_results]

    # Otherwise return ranked partial matches
    results = starts_with_matches + contains_matches

    return results[:max_results]