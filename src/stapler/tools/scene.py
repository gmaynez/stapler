# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Scene information tool for Stapler.

This module provides functionality to retrieve comprehensive information
about the current Blender scene.
"""

from __future__ import annotations

from typing import TypedDict


class SceneInfo(TypedDict, total=False):
    """Type definition for scene information returned from Blender.

    Attributes:
        name: Scene name
        object_count: Total number of objects in the scene
        objects: List of object data (name, type, location)
        materials_count: Total number of materials
    """

    name: str
    object_count: int
    objects: list[dict[str, str | list[float]]]
    materials_count: int


# Tool implementation is in server.py using @mcp.tool() decorator

