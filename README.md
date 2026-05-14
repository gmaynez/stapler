# Stapler - Modern Blender MCP Integration

**Stapler** connects Blender to AI assistants like Claude through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), enabling AI-driven 3D modeling, scene inspection, and automation.

> **Note:** Stapler is a modernized fork of [blender-mcp](https://github.com/ahujasid/blender-mcp) by Siddharth Ahuja, completely rewritten with Python 3.13+, official MCP SDK, and focused on core Blender functionality.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

## Features

- 🎨 **Scene Inspection** - Get detailed information about Blender scenes and objects with collection hierarchy
- 📸 **Viewport Screenshots** - Capture and analyze the 3D viewport
- 🔧 **Object Queries** - Retrieve transform, materials, modifiers, constraints, and bounding box data
- 💻 **Code Execution** - Run Python code directly in Blender
- 🚀 **Modern Architecture** - Built with Python 3.13+ and official MCP SDK
- 🧹 **Focused & Clean** - Only core Blender functionality, no external services
- 📚 **API Documentation** - Access Blender Python API docs and examples via MCP resources
- 🎯 **Viewport Navigation** - Focus viewport on specific objects
- 🖼️ **Quick Rendering** - Generate thumbnail previews of scenes

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

Stapler provides 8 core tools to Claude:

#### 1. `get_objects_summary`

Get a summary of all objects in the current Blender scene with collection hierarchy.

**Example:**
> "What objects are in the current scene and how are they organized?"

**Parameters:**
- `include_hidden` - Whether to include hidden objects (default: false)

**Returns:**
- Scene name
- Collection hierarchy with objects
- Object counts by type
- Material count

#### 2. `get_object_detail_summary`

Get detailed information about a specific object.

**Example:**
> "Tell me about the Cube object including its modifiers"

**Parameters:**
- `name` - Name of the object to query

**Returns:**
- Transform data (location, rotation, scale)
- Object type
- Materials
- Mesh data (vertex/edge/polygon counts)
- Modifiers and constraints
- Parent/children relationships
- Collection membership
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

#### 5. `jump_to_view3d_object_by_name`

Focus the 3D viewport on a specific object.

**Example:**
> "Focus on the Camera object"

**Parameters:**
- `name` - Name of the object to focus on

**Returns:**
- Success status
- Object location

#### 6. `get_screenshot_of_window_as_json`

Get a JSON description of the Blender window layout.

**Example:**
> "What panels are open in the current Blender window?"

**Returns:**
- Window dimensions
- All areas with their types and sizes
- Active and selected objects in 3D viewports
- Active property panels

#### 7. `render_thumbnail_to_path`

Render a quick thumbnail preview of the current scene.

**Example:**
> "Render a quick preview of the current scene"

**Parameters:**
- `output_path` - Where to save the thumbnail
- `width` - Thumbnail width (default: 256)
- `height` - Thumbnail height (default: 256)

**Returns:**
- PNG image of the rendered thumbnail

### MCP Resources

Stapler provides 2 MCP resources for accessing Blender documentation:

#### 1. `blender://api/{identifier}`

Access Blender Python API documentation.

**Example:**
> "Show me the documentation for bpy.types.ShaderNodeBsdfPrincipled"

**Parameters:**
- `identifier` - Module or class name (e.g., `bpy.types.ShaderNodeBsdfPrincipled`)
- Use `*` for pattern matching (e.g., `bpy.types.*`)

**Returns:**
- RST documentation content
- List of matching modules for wildcard patterns

#### 2. `blender://examples/{name}`

Access Python code examples from Blender documentation.

**Example:**
> "Show me an example of using bpy.app.handlers"

**Parameters:**
- `name` - Example name (e.g., `bpy.app.handlers.0`)

**Returns:**
- Python code example
- List of available examples for a module

### Example Interactions

**Scene Exploration:**
```
You: What's in the current scene?
Claude: [Uses get_objects_summary]
        There's a default scene with 3 objects in 1 collection: Camera, Cube, and Light...
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

**Navigation:**
```
You: Focus on the Camera
Claude: [Uses jump_to_view3d_object_by_name]
        I've focused the viewport on the Camera...
```

**API Documentation:**
```
You: How do I create a material with Python?
Claude: [Accesses blender://api/bpy.types.Material]
        Here's the documentation for bpy.types.Material...
```

## Development

### Project Structure

```
stapler/
├── src/stapler/
│   ├── __init__.py           # Package initialization
│   ├── server.py             # FastMCP server implementation
│   ├── connection.py         # Blender socket connection
│   ├── data/                 # Bundled documentation
│   │   ├── api/              # Blender Python API docs (RST)
│   │   └── examples/         # Python code examples
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
- ✅ 8 MCP tools (up from 4)
- ✅ MCP resources for API documentation and examples
- ✅ Collection hierarchy support
- ✅ Object modifiers and constraints info
- ✅ Viewport navigation tools
- ✅ Quick thumbnail rendering

## Comparison with Official Blender MCP

| Feature | Stapler | Official Blender MCP |
|---------|---------|---------------------|
| Blender Version | 4.0+ | 5.1+ |
| Python | 3.13+ | Blender's Python |
| MCP SDK | FastMCP | Custom |
| Tools | 8 | 19 |
| Resources | 2 (API docs, examples) | ❌ |
| Background Execution | ❌ | ✅ |
| Installation | `uv` | `.mcpb` bundle |

**Stapler is ideal for:**
- Users on Blender 4.x/5.0
- Claude Desktop users
- Quick setup without Blender Lab dependencies
- Access to API documentation via MCP resources

**Official MCP is better for:**
- Blender 5.1+ users
- Complex file analysis tasks
- Background Blender process execution

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
