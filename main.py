# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Stapler entry point.

This module provides the main entry point for running the Stapler MCP server.
"""

from stapler.server import main as server_main


def main():
    """Entry point for the stapler package."""
    server_main()


if __name__ == "__main__":
    main()
