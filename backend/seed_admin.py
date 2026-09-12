"""Secure interactive command for creating the first ADMIN user."""

import argparse
import getpass

from backend.auth import create_first_admin


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first CRM admin")
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name")
    parser.add_argument("--email", required=True)
    parser.add_argument("--phone")
    args = parser.parse_args()

    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")
    if not password or password != confirmation:
        raise SystemExit("Passwords are empty or do not match")
    try:
        user_id = create_first_admin(
            first_name=args.first_name,
            last_name=args.last_name,
            email=args.email,
            phone=args.phone,
            password=password,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f"Created ADMIN user with user_id={user_id}")


if __name__ == "__main__":
    main()
