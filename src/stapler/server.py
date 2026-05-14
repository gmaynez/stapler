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
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP, Image

from stapler.connection import BlenderConnection, get_blender_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Data directory for bundled documentation
DATA_DIR = Path(__file__).parent / "data"
API_DOCS_DIR = DATA_DIR / "api"
EXAMPLES_DIR = DATA_DIR / "examples"


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
def get_objects_summary(ctx: Context, include_hidden: bool = False) -> str:
    """Get a summary of all objects in the current Blender scene with collection hierarchy.

    Returns the scene's collection hierarchy with object types, visibility,
    and counts. More structured than a flat object list.

    Args:
        include_hidden: Whether to include hidden objects (default: False)

    Returns:
        str: JSON-formatted objects summary with collection hierarchy
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_objects_summary", {"include_hidden": include_hidden})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting objects summary from Blender: {e}")
        return f"Error getting objects summary: {e}"


@mcp.tool()
def get_object_detail_summary(ctx: Context, name: str) -> str:
    """Get a detailed summary of a specific object in the Blender scene.

    Retrieves comprehensive data about an object including its transform,
    materials, mesh data, modifiers, constraints, parent/children relationships,
    collection membership, and world-space bounding box.

    Args:
        name: The name of the object to get information about

    Returns:
        str: JSON-formatted detailed object summary
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_object_detail_summary", {"name": name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object detail summary from Blender: {e}")
        return f"Error getting object detail summary: {e}"


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


@mcp.tool()
def jump_to_view3d_object_by_name(ctx: Context, name: str) -> str:
    """Focus the 3D viewport on a specific object by name.

    Sets the object as active and centers the viewport on it.
    Useful for navigating to specific objects in complex scenes.

    Args:
        name: The name of the object to focus on

    Returns:
        str: JSON-formatted result with object location
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("jump_to_view3d_object_by_name", {"name": name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error jumping to object: {e}")
        return f"Error jumping to object: {e}"


@mcp.tool()
def get_screenshot_of_window_as_json(ctx: Context) -> str:
    """Get a JSON description of the Blender window layout.

    Returns information about the window dimensions, all areas (panels),
    their types, sizes, and active objects. Useful for understanding the
    current UI layout without image processing.

    Returns:
        str: JSON-formatted window layout description
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_screenshot_of_window_as_json")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting window layout: {e}")
        return f"Error getting window layout: {e}"


@mcp.tool()
def render_thumbnail_to_path(ctx: Context, output_path: str, width: int = 256, height: int = 256) -> Image:
    """Render a quick thumbnail preview of the current scene.

    Renders a low-quality thumbnail suitable for quick previews.
    Temporarily overrides render settings for speed, then restores them.

    Args:
        output_path: File path where the thumbnail will be saved
        width: Thumbnail width in pixels (default: 256)
        height: Thumbnail height in pixels (default: 256)

    Returns:
        Image: The rendered thumbnail as a PNG image
    """
    try:
        blender = get_blender_connection()

        result = blender.send_command(
            "render_thumbnail_to_path",
            {"output_path": output_path, "width": width, "height": height}
        )

        if "error" in result:
            raise Exception(result["error"])

        if not os.path.exists(output_path):
            raise Exception("Thumbnail file was not created")

        # Read the file
        with open(output_path, "rb") as f:
            image_bytes = f.read()

        return Image(data=image_bytes, format="png")

    except Exception as e:
        logger.error(f"Error rendering thumbnail: {e}")
        raise Exception(f"Thumbnail render failed: {e}") from e


# MCP Resources for documentation access

@mcp.resource("blender://api/{identifier}")
def get_python_api_docs(identifier: str) -> str:
    """Get Blender Python API documentation for a module or class.

    Returns RST documentation content for the specified identifier.
    Use '*' at the end for pattern matching (e.g., 'bpy.types.*').

    Args:
        identifier: Module or class name (e.g., 'bpy.types.ShaderNodeBsdfPrincipled')

    Returns:
        str: RST documentation content
    """
    try:
        # Handle wildcard patterns
        if identifier.endswith("*"):
            prefix = identifier[:-1]
            matching_files = []
            for rst_file in API_DOCS_DIR.glob("*.rst"):
                if rst_file.stem.startswith(prefix.rstrip(".")):
                    matching_files.append(rst_file.stem)
            if matching_files:
                return f"Matching modules: {', '.join(sorted(matching_files))}"
            return f"No modules found matching '{identifier}'"

        # Look for exact file match
        rst_file = API_DOCS_DIR / f"{identifier}.rst"
        if rst_file.exists():
            return rst_file.read_text(encoding="utf-8")

        # Try with dots replaced by underscores
        rst_file = API_DOCS_DIR / f"{identifier.replace('.', '_')}.rst"
        if rst_file.exists():
            return rst_file.read_text(encoding="utf-8")

        # Search in all RST files for the identifier
        results = []
        for rst_file in API_DOCS_DIR.glob("*.rst"):
            content = rst_file.read_text(encoding="utf-8")
            if identifier in content:
                results.append(rst_file.stem)

        if results:
            return f"Identifier '{identifier}' found in: {', '.join(sorted(results))}"

        return f"Documentation not found for '{identifier}'. Available files: {', '.join(sorted([f.stem for f in API_DOCS_DIR.glob('*.rst')]))}"

    except Exception as e:
        logger.error(f"Error reading API docs: {e}")
        return f"Error reading API docs: {e}"


@mcp.resource("blender://examples/{name}")
def get_python_example(name: str) -> str:
    """Get a Python code example for Blender.

    Returns Python code examples from the Blender documentation.

    Args:
        name: Example name (e.g., 'bpy.app.handlers.0' or 'bmesh.ops.1')

    Returns:
        str: Python code example
    """
    try:
        # Handle wildcard patterns
        if name.endswith("*"):
            prefix = name[:-1]
            matching_files = []
            for py_file in EXAMPLES_DIR.glob("*.py"):
                if py_file.stem.startswith(prefix.rstrip(".")):
                    matching_files.append(py_file.stem)
            if matching_files:
                return f"Matching examples: {', '.join(sorted(matching_files))}"
            return f"No examples found matching '{name}'"

        # Look for exact file match
        py_file = EXAMPLES_DIR / f"{name}.py"
        if py_file.exists():
            return py_file.read_text(encoding="utf-8")

        # Try common patterns
        for pattern in [f"{name}.0.py", f"{name}.1.py", f"{name}.2.py"]:
            py_file = EXAMPLES_DIR / pattern
            if py_file.exists():
                return py_file.read_text(encoding="utf-8")

        # List available examples for this module
        matching = list(EXAMPLES_DIR.glob(f"{name}*"))
        if matching:
            return f"Available examples: {', '.join(sorted([f.stem for f in matching]))}"

        return f"Example not found for '{name}'. Available: {', '.join(sorted([f.stem for f in EXAMPLES_DIR.glob('*.py')]))}"

    except Exception as e:
        logger.error(f"Error reading example: {e}")
        return f"Error reading example: {e}"


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

