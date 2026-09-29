import getpass
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cli
from app.db import User, create_db_engine
from app.security import verify_password


@pytest.fixture
def database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite:///{tmp_path / 'data' / 'cli.db'}"
    monkeypatch.setenv("LSM_DATABASE_URL", url)
    return url


def _answer_prompts(monkeypatch: pytest.MonkeyPatch, *answers: str) -> None:
    replies = iter(answers)
    monkeypatch.setattr(getpass, "getpass", lambda _prompt: next(replies))


def _stored_hash(database_url: str, username: str) -> str | None:
    with Session(create_db_engine(database_url)) as db:
        return db.scalar(select(User.password_hash).where(User.username == username))


def test_create_user(database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _answer_prompts(monkeypatch, "cli password 123", "cli password 123")
    assert cli.main(["create-user", "admin"]) == 0
    stored = _stored_hash(database_url, "admin")
    assert stored is not None and verify_password("cli password 123", stored)


def test_set_password(database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _answer_prompts(monkeypatch, *["first password 1"] * 2, *["second password 2"] * 2)
    assert cli.main(["create-user", "admin"]) == 0
    assert cli.main(["set-password", "admin"]) == 0
    stored = _stored_hash(database_url, "admin")
    assert stored is not None and verify_password("second password 2", stored)


@pytest.mark.parametrize(
    ("argv", "answers", "message"),
    [
        (["create-user", "admin"], ("one password 123", "two password 123"), "do not match"),
        (["create-user", "admin"], ("short", "short"), "between 12"),
        (["create-user", "bad name"], ("good password 12",) * 2, "Username"),
        (["set-password", "ghost"], ("good password 12",) * 2, "does not exist"),
    ],
)
def test_errors_exit_with_status_1(
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    answers: tuple[str, ...],
    message: str,
) -> None:
    _answer_prompts(monkeypatch, *answers)
    assert cli.main(argv) == 1
    assert message in capsys.readouterr().err


def test_invalid_settings_exit_with_status_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LSM_SESSION_TTL_MINUTES", "not-a-number")
    assert cli.main(["create-user", "admin"]) == 1
    assert "Invalid configuration" in capsys.readouterr().err
