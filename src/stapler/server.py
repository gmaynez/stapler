# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Stapler MCP Server - Blender integration through Model Context Protocol.

This module implements the MCP server using FastMCP, exposing core Blender
functionality through tools that can be accessed by MCP clients like Claude.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP, Image

from stapler.connection import BlenderConnection, get_blender_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ServerContext:
    """Application context for the MCP server."""

    connection: BlenderConnection | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage application lifecycle with connection management.

    Args:
        server: The FastMCP server instance

    Yields:
        ServerContext: Context containing the Blender connection
    """
    logger.info("Stapler MCP server starting up")
    context = ServerContext()

    try:
        # Try to connect to Blender on startup to verify it's available
        try:
            context.connection = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {e}")
            logger.warning("Make sure the Blender addon is running before using tools")

        yield context
    finally:
        # Clean up connection on shutdown
        if context.connection:
            logger.info("Disconnecting from Blender on shutdown")
            context.connection.disconnect()
        logger.info("Stapler MCP server shut down")


# Create the MCP server with lifespan support
mcp = FastMCP("Stapler", lifespan=app_lifespan)


@mcp.tool()
def get_scene_info(ctx: Context) -> str:
    """Get detailed information about the current Blender scene.

    Returns comprehensive scene data including object count, object names,
    types, and locations.

    Returns:
        str: JSON-formatted scene information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info from Blender: {e}")
        return f"Error getting scene info: {e}"


@mcp.tool()
def get_object_info(ctx: Context, object_name: str) -> str:
    """Get detailed information about a specific object in the Blender scene.

    Retrieves comprehensive data about an object including its transform,
    materials, mesh data, and world-space bounding box.

    Args:
        object_name: The name of the object to get information about

    Returns:
        str: JSON-formatted object information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_object_info", {"name": object_name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info from Blender: {e}")
        return f"Error getting object info: {e}"


@mcp.tool()
def get_viewport_screenshot(ctx: Context, max_size: int = 800) -> Image:
    """Capture a screenshot of the current Blender 3D viewport.

    Takes a screenshot of the active 3D viewport and returns it as an image.
    The image is automatically resized if larger than max_size.

    Args:
        max_size: Maximum size in pixels for the largest dimension (default: 800)

    Returns:
        Image: The screenshot as a PNG image
    """
    try:
        blender = get_blender_connection()

        # Create temp file path
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

        result = blender.send_command(
            "get_viewport_screenshot",
            {"max_size": max_size, "filepath": temp_path, "format": "png"},
        )

        if "error" in result:
            raise Exception(result["error"])

        if not os.path.exists(temp_path):
            raise Exception("Screenshot file was not created")

        # Read the file
        with open(temp_path, "rb") as f:
            image_bytes = f.read()

        # Delete the temp file
        os.remove(temp_path)

        return Image(data=image_bytes, format="png")

    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        raise Exception(f"Screenshot failed: {e}") from e


@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """Execute arbitrary Python code in Blender.

    Runs Python code in Blender's context, with access to the bpy module.
    Use this for operations not covered by other tools. Break complex
    operations into smaller chunks.

    WARNING: This executes code directly in Blender. Use with caution.

    Args:
        code: The Python code to execute

    Returns:
        str: Execution result or error message
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("execute_code", {"code": code})
        return f"Code executed successfully: {result.get('result', '')}"
    except Exception as e:
        logger.error(f"Error executing code: {e}")
        return f"Error executing code: {e}"


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

