# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Object information tool for Stapler.

This module provides functionality to retrieve detailed information
about specific objects in the Blender scene.
"""

from __future__ import annotations

from typing import TypedDict


class MeshInfo(TypedDict, total=False):
    """Type definition for mesh data.

    Attributes:
        vertices: Number of vertices
        edges: Number of edges
        polygons: Number of polygons/faces
    """

    vertices: int
    edges: int
    polygons: int


class ObjectInfo(TypedDict, total=False):
    """Type definition for object information returned from Blender.

    Attributes:
        name: Object name
        type: Object type (MESH, CAMERA, LIGHT, etc.)
        location: World location [x, y, z]
        rotation: Euler rotation [x, y, z]
        scale: Scale [x, y, z]
        visible: Whether object is visible
        materials: List of material names
        mesh: Mesh data (if object is a mesh)
        world_bounding_box: Axis-aligned bounding box [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    """

    name: str
    type: str
    location: list[float]
    rotation: list[float]
    scale: list[float]
    visible: bool
    materials: list[str]
    mesh: MeshInfo
    world_bounding_box: list[list[float]]


# Tool implementation is in server.py using @mcp.tool() decorator

