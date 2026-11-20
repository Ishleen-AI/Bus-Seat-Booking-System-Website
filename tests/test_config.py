import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_production_requires_strong_secrets():
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env.pop("SECRET_KEY", None)
    env.pop("ADMIN_PASSWORD", None)

    result = subprocess.run(
        [sys.executable, "-c", "import config"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Production requires SECRET_KEY" in result.stderr


def test_production_uses_secure_session_cookies():
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["SECRET_KEY"] = "s" * 32
    env["ADMIN_PASSWORD"] = "p" * 16

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from config import Config; print(Config.SESSION_COOKIE_SECURE)",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "True"
