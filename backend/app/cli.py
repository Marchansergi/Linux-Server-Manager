"""Administrative commands.

Usage:
    python -m app.cli create-user <username>
    python -m app.cli set-password <username>

Passwords are always read interactively so they never appear in shell
history or process listings.
"""

import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.config import SettingsError, load_settings
from app.db import create_db_engine, init_db
from app.services.auth import UserExistsError, UserNotFoundError, create_user, set_password


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        raise ValueError("Passwords do not match")
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("create-user", "create a dashboard user"),
        ("set-password", "change a user's password and revoke their sessions"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("username")
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
        engine = create_db_engine(settings.database_url)
        init_db(engine)
        password = _prompt_password()
        with Session(engine) as db:
            if args.command == "create-user":
                create_user(db, args.username, password)
                print(f"User '{args.username}' created.")
            else:
                set_password(db, args.username, password)
                print(f"Password for '{args.username}' updated; existing sessions revoked.")
    except (SettingsError, ValueError, UserExistsError, UserNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
