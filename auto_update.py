#!/usr/bin/env python3

import sys
import os
import subprocess
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Configure logging
LOG_FILE = "./update_repo.log"

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler(LOG_FILE)
console_handler = logging.StreamHandler()

# Create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def run_command(command: List[str]) -> None:
    """Run a shell command and handle exceptions."""
    try:
        subprocess.run(command, check=True)
        logger.info(f"Command succeeded: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed ({e.returncode}): {' '.join(command)}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        sys.exit(1)


def main() -> None:
    # Load environment variables from .env file
    dotenv_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    dotenv_exists: bool = os.path.exists(dotenv_path)
    if dotenv_exists:
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment variables from {dotenv_path}")
    else:
        logger.info(f".env file not found at {dotenv_path}")

    # Retrieve environment variables
    repo_url: Optional[str] = os.environ.get("REPO_URL")
    target_dir: Optional[str] = os.environ.get("TARGET_DIR")
    pip_command_suffix: Optional[str] = (
        os.environ.get("PIP_COMMAND_SUFFIX")
        if os.environ.get("PIP_COMMAND_SUFFIX")
        else None
    )

    if not repo_url:
        logger.error("Environment variable REPO_URL is not set.")
        sys.exit(1)

    if not target_dir:
        # Use the directory containing the script
        target_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"No TARGET_DIR provided. Using script directory: {target_dir}")
    else:
        logger.info(f"Using TARGET_DIR from environment: {target_dir}")

    # Ensure target directory exists
    if not os.path.isdir(target_dir):
        logger.info(f"Creating target directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)

    # Clone the repository if the .git directory doesn't exist
    git_dir = os.path.join(target_dir, ".git")
    if not os.path.isdir(git_dir):
        logger.info("Cloning repository...")
        run_command(["git", "clone", repo_url, target_dir])
    else:
        logger.info("Repository already cloned.")

    # Navigate to the target directory
    try:
        os.chdir(target_dir)
    except FileNotFoundError:
        logger.error(f"Target directory not found: {target_dir}")
        sys.exit(1)

    # Execute Git and Docker Compose commands
    logger.info("Resetting repository...")
    run_command(["git", "reset", "--hard"])

    logger.info("Pulling latest changes...")
    run_command(["git", "pull", "origin", "main"])

    logger.info("Loading pip library changes...")

    cmd: List[str] = ["pip3", "install", "-r", "requirements.txt"]
    if pip_command_suffix:
        cmd += pip_command_suffix.split(" ")
    run_command(cmd)

    logger.info("Stopping Docker Compose services...")
    run_command(["docker-compose", "down"])

    logger.info("Starting Docker Compose services...")
    run_command(["docker-compose", "up", "-d", "--build"])


if __name__ == "__main__":
    main()
