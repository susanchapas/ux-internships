#!/usr/bin/env python3
"""Create the admin account. Run once: python create_admin.py"""

import sys
import getpass
from auth import register_user
from models import Role


def main():
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    if not all([username, email, password]):
        sys.exit("All fields required")
    try:
        user = register_user(username, email, password, role=Role.admin)
        print(f"Admin '{user.username}' created (id={user.id})")
    except Exception as e:
        sys.exit(f"Failed: {e}")


if __name__ == "__main__":
    main()
