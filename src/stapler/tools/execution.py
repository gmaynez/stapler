# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Code execution tool for Stapler.

This module provides functionality to execute arbitrary Python code
in Blender's context.
"""

from __future__ import annotations

# Tool implementation is in server.py using @mcp.tool() decorator

# Safety notice: This tool executes code directly in Blender.
# Users should be aware of security implications.
EXECUTION_WARNING = """
WARNING: execute_blender_code runs arbitrary Python code in Blender.
Only execute code from trusted sources. Always save your work before
executing code that modifies the scene.
"""

