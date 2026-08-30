import subprocess
from pathlib import Path


def run_git(args, project_path):
    """Run a git command inside a project folder."""

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Git is not installed or not available in PATH."
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Git command timed out."
        }

    except Exception as error:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(error)
        }


def is_git_repository(project_path):
    """Check whether a folder is a Git repository."""

    project_path = Path(project_path)

    if not project_path.exists():
        return False

    result = run_git(
        ["rev-parse", "--is-inside-work-tree"],
        str(project_path)
    )

    return result["success"] and result["stdout"] == "true"


def git_status(project_path):
    """Get the Git status of a project."""

    if not is_git_repository(project_path):
        return {
            "success": False,
            "message": "This folder is not a Git repository."
        }

    result = run_git(["status", "--short"], project_path)

    if not result["success"]:
        return {
            "success": False,
            "message": result["stderr"]
        }

    status = result["stdout"]

    if not status:
        status = "Working tree is clean."

    return {
        "success": True,
        "message": status
    }


def git_add_all(project_path):
    """Stage all changes in a Git repository."""

    if not is_git_repository(project_path):
        return {
            "success": False,
            "message": "This folder is not a Git repository."
        }

    result = run_git(["add", "."], project_path)

    if result["success"]:
        return {
            "success": True,
            "message": "All changes staged successfully."
        }

    return {
        "success": False,
        "message": result["stderr"]
    }


def git_commit(project_path, message):
    """Create a Git commit."""

    if not is_git_repository(project_path):
        return {
            "success": False,
            "message": "This folder is not a Git repository."
        }

    result = run_git(
        ["commit", "-m", message],
        project_path
    )

    if result["success"]:
        return {
            "success": True,
            "message": result["stdout"]
        }

    return {
        "success": False,
        "message": result["stderr"]
    }


def git_push(project_path):
    """Push commits to the configured remote."""

    if not is_git_repository(project_path):
        return {
            "success": False,
            "message": "This folder is not a Git repository."
        }

    result = run_git(["push"], project_path)

    if result["success"]:
        return {
            "success": True,
            "message": result["stdout"] or "Push completed successfully."
        }

    return {
        "success": False,
        "message": result["stderr"]
    }