# Stapler - Modern Blender MCP Integration

**Stapler** connects Blender to AI assistants like Claude through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), enabling AI-driven 3D modeling, scene inspection, and automation.

> **Note:** Stapler is a modernized fork of [blender-mcp](https://github.com/ahujasid/blender-mcp) by Siddharth Ahuja, completely rewritten with Python 3.13+, official MCP SDK, and focused on core Blender functionality.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

## Features

- 🎨 **Scene Inspection** - Get detailed information about Blender scenes and objects
- 📸 **Viewport Screenshots** - Capture and analyze the 3D viewport
- 🔧 **Object Queries** - Retrieve transform, materials, and bounding box data
- 💻 **Code Execution** - Run Python code directly in Blender
- 🚀 **Modern Architecture** - Built with Python 3.13+ and official MCP SDK
- 🧹 **Focused & Clean** - Only core Blender functionality, no external services

## Architecture

Stapler consists of two components:

1. **MCP Server** (`src/stapler/`) - Implements the MCP protocol using FastMCP
2. **Blender Addon** (`blender_addon/stapler_addon.py`) - Socket server inside Blender

```
┌─────────────────┐         MCP Protocol         ┌──────────────────┐
│                 │ ◄──────────────────────────► │                  │
│  Claude / AI    │                               │  Stapler Server  │
│                 │                               │    (FastMCP)     │
└─────────────────┘                               └──────────────────┘
                                                           │
                                                   TCP Socket (9876)
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │     Blender      │
                                                  │  (Stapler Addon) │
                                                  └──────────────────┘
```

## Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **Blender 4.0+** - [Download](https://www.blender.org/download/)
- **uv** - [Install](https://docs.astral.sh/uv/getting-started/installation/)

### Installing uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation

### 1. Install the MCP Server

Clone the repository:

```bash
git clone https://github.com/gmaynez/stapler.git
cd stapler
```

Install dependencies with uv:

```bash
uv sync
```

### 2. Install the Blender Addon

1. Open Blender
2. Go to **Edit > Preferences > Add-ons**
3. Click **Install...** and select `blender_addon/stapler_addon.py`
4. Enable the addon by checking the box next to "Interface: Stapler MCP Integration"

### 3. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "stapler": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/stapler",
        "run",
        "stapler"
      ]
    }
  }
}
```

Replace `/absolute/path/to/stapler` with the actual path to your Stapler installation.

**Windows users:** Use forward slashes in the path, e.g., `C:/Users/YourName/stapler`

### 4. Configure Cursor (Optional)

For Cursor IDE integration, go to **Settings > MCP** and add:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "stapler": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/stapler",
        "run",
        "stapler"
      ]
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "stapler": {
      "command": "cmd",
      "args": [
        "/c",
        "uv",
        "--directory",
        "C:/path/to/stapler",
        "run",
        "stapler"
      ]
    }
  }
}
```

## Usage

### Starting the Connection

1. Open Blender
2. Press `N` to show the sidebar
3. Navigate to the **Stapler** tab
4. Click **"Connect to MCP Server"**
5. The server will start on port `9876` (default)

### Available Tools

Stapler provides 4 core tools to Claude:

#### 1. `get_scene_info`

Get comprehensive information about the current Blender scene.

**Example:**
> "What objects are in the current scene?"

**Returns:**
- Scene name
- Object count
- List of objects with names, types, and locations
- Material count

#### 2. `get_object_info`

Get detailed information about a specific object.

**Example:**
> "Tell me about the Cube object"

**Parameters:**
- `object_name` - Name of the object to query

**Returns:**
- Transform data (location, rotation, scale)
- Object type
- Materials
- Mesh data (vertex/edge/polygon counts)
- World-space bounding box

#### 3. `get_viewport_screenshot`

Capture a screenshot of the 3D viewport.

**Example:**
> "Show me a screenshot of the current view"

**Parameters:**
- `max_size` - Maximum dimension in pixels (default: 800)

**Returns:**
- PNG image of the viewport

#### 4. `execute_blender_code`

Execute Python code in Blender's context.

**Example:**
> "Create a UV sphere at the origin"

**Parameters:**
- `code` - Python code to execute

**⚠️ Warning:** This executes arbitrary code in Blender. Always save your work first.

### Example Interactions

**Scene Exploration:**
```
You: What's in the current scene?
Claude: [Uses get_scene_info]
        There's a default scene with 3 objects: Camera, Cube, and Light...
```

**Object Manipulation:**
```
You: Create a red sphere above the cube
Claude: [Uses execute_blender_code]
        I've created a red sphere at location (0, 0, 3)...
```

**Visual Inspection:**
```
You: Show me how it looks
Claude: [Uses get_viewport_screenshot]
        Here's the current viewport...
```

## Development

### Project Structure

```
stapler/
├── src/stapler/
│   ├── __init__.py           # Package initialization
│   ├── server.py             # FastMCP server implementation
│   ├── connection.py         # Blender socket connection
│   └── tools/                # Tool type definitions
│       ├── scene.py
│       ├── objects.py
│       ├── viewport.py
│       └── execution.py
├── blender_addon/
│   └── stapler_addon.py      # Blender addon
├── main.py                   # Entry point
├── pyproject.toml            # uv project configuration
└── README.md
```

### Running in Development Mode

Test the server with the MCP Inspector:

```bash
uv run mcp dev src/stapler/server.py
```

This opens an interactive inspector to test tools.

### Running Directly

```bash
uv run stapler
```

Or with Python:

```bash
uv run python main.py
```

## Troubleshooting

### Connection Issues

**Problem:** "Could not connect to Blender"

**Solutions:**
1. Make sure Blender is running
2. Ensure the Stapler addon is enabled
3. Click "Connect to MCP Server" in Blender's Stapler panel
4. Check that port 9876 is not blocked by firewall

### Port Already in Use

**Problem:** Port 9876 is already in use

**Solution:** Change the port in Blender's Stapler panel before connecting

### Claude Can't Find Tools

**Problem:** Claude says it doesn't have access to Blender tools

**Solutions:**
1. Restart Claude Desktop after editing the config file
2. Verify the config file path is correct
3. Check Claude's logs for MCP connection errors

### Screenshots Not Working

**Problem:** `get_viewport_screenshot` fails

**Solution:** Make sure you have at least one 3D viewport open in Blender

## Differences from blender-mcp

Stapler is a **significant rewrite** of the original blender-mcp:

### Removed
- ❌ PolyHaven integration (6 tools)
- ❌ Hyper3D Rodin integration (4 tools)
- ❌ Sketchfab integration (2 tools)
- ❌ API key management
- ❌ External service UI elements
- ❌ Complex prompt templates

### Added/Improved
- ✅ Python 3.13+ support
- ✅ Official MCP SDK with FastMCP
- ✅ Full uv package manager integration
- ✅ Modular architecture
- ✅ Modern type hints
- ✅ Better error handling
- ✅ ~71% code reduction (cleaner, more maintainable)
- ✅ GPL v3 license (required due to Blender Python API usage)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later).

See [LICENSE](LICENSE) file for details.

**Note:** This project uses the Blender Python API (`bpy`), which is GPL v3 licensed. 
Per GPL requirements, any software that uses GPL-licensed libraries must also be 
GPL licensed. This is why Stapler is GPL v3, even though the original blender-mcp 
was MIT licensed (MIT is GPL-compatible).

### Original Work Attribution

Stapler is a derivative work based on [blender-mcp](https://github.com/ahujasid/blender-mcp) by Siddharth Ahuja, licensed under the MIT License.

See [NOTICE](NOTICE) file for full attribution and changes made.

## Acknowledgments

- **Siddharth Ahuja** - Original blender-mcp creator
- **Anthropic** - For Claude and the Model Context Protocol
- **Model Context Protocol Team** - For the Python SDK
- **Blender Foundation** - For Blender

## Links

- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Blender Python API](https://docs.blender.org/api/current/)
- [uv Package Manager](https://docs.astral.sh/uv/)
- [Original blender-mcp](https://github.com/ahujasid/blender-mcp)

## Support

For issues and questions:

- **Issues:** [GitHub Issues](https://github.com/gmaynez/stapler/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmaynez/stapler/discussions)

---

**Made with 🖇️ by the Stapler community**
