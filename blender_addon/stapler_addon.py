# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Stapler - Blender MCP Integration Addon

This addon creates a socket server in Blender to communicate with the
Stapler MCP server, enabling AI-driven control of Blender.

Author: Stapler Contributors
License: GPL-3.0-or-later (required due to use of Blender Python API)
Based on: blender-mcp by Siddharth Ahuja (MIT)
"""

import bpy
import json
import mathutils
import socket
import tempfile
import threading
import time
import traceback
import os
import io
from contextlib import redirect_stdout
from bpy.props import IntProperty, BoolProperty

bl_info = {
    "name": "Stapler MCP Integration",
    "author": "Stapler Contributors",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Stapler",
    "description": "Connect Blender to AI through the Model Context Protocol",
    "category": "Interface",
}


class StaplerMCPServer:
    """Socket server for receiving MCP commands from Stapler."""

    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def start(self) -> None:
        """Start the socket server."""
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"Stapler server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {e}")
            self.stop()

    def stop(self) -> None:
        """Stop the socket server."""
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except Exception:
                pass
            self.server_thread = None

        print("Stapler server stopped")

    def _server_loop(self) -> None:
        """Main server loop in a separate thread."""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client, args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {e}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client: socket.socket) -> None:
        """Handle connected client."""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b""

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode("utf-8"))
                        buffer = b""

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode("utf-8"))
                                except Exception:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {e}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e),
                                    }
                                    client.sendall(
                                        json.dumps(error_response).encode("utf-8")
                                    )
                                except Exception:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break
        except Exception as e:
            print(f"Error in client handler: {e}")
        finally:
            try:
                client.close()
            except Exception:
                pass
            print("Client handler stopped")

    def execute_command(self, command: dict) -> dict:
        """Execute a command in the main Blender thread."""
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {e}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command: dict) -> dict:
        """Internal command execution with proper context."""
        cmd_type = command.get("type")
        params = command.get("params", {})

        handlers = {
            "get_objects_summary": self.get_objects_summary,
            "get_object_detail_summary": self.get_object_detail_summary,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "jump_to_view3d_object_by_name": self.jump_to_view3d_object_by_name,
            "get_screenshot_of_window_as_json": self.get_screenshot_of_window_as_json,
            "render_thumbnail_to_path": self.render_thumbnail_to_path,
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print("Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {e}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def get_objects_summary(self, include_hidden: bool = False) -> dict:
        """Get a summary of all objects with collection hierarchy."""
        try:
            print("Getting objects summary...")

            def get_collection_hierarchy(collection, include_hidden):
                """Recursively get collection hierarchy."""
                objects = []
                for obj in collection.objects:
                    if not include_hidden and obj.hide_get():
                        continue
                    objects.append({
                        "name": obj.name,
                        "type": obj.type,
                        "visible": not obj.hide_get(),
                    })

                children = {}
                for child_collection in collection.children:
                    child_data = get_collection_hierarchy(child_collection, include_hidden)
                    if child_data["objects"] or child_data["children"]:
                        children[child_collection.name] = child_data

                return {
                    "objects": objects,
                    "children": children,
                }

            scene = bpy.context.scene
            hierarchy = get_collection_hierarchy(scene.collection, include_hidden)

            # Count totals
            def count_objects(node):
                total = len(node["objects"])
                for child in node["children"].values():
                    total += count_objects(child)
                return total

            def count_collections(node):
                total = 1  # Count self
                for child in node["children"].values():
                    total += count_collections(child)
                return total

            total_objects = count_objects(hierarchy)
            total_collections = count_collections(hierarchy) - 1  # Exclude scene collection

            result = {
                "scene": scene.name,
                "collections": hierarchy["children"],
                "scene_objects": hierarchy["objects"],
                "total_objects": total_objects,
                "total_collections": total_collections,
                "materials_count": len(bpy.data.materials),
            }

            print(f"Objects summary collected: {total_objects} objects in {total_collections} collections")
            return result
        except Exception as e:
            print(f"Error in get_objects_summary: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj: bpy.types.Object) -> list[list[float]]:
        """Get the world-space axis-aligned bounding box of an object."""
        if obj.type != "MESH":
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [[*min_corner], [*max_corner]]

    def get_object_detail_summary(self, name: str) -> dict:
        """Get detailed summary of a specific object."""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": not obj.hide_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box

        # Add material slots
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        # Add mesh data if applicable
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        # Add modifiers
        obj_info["modifiers"] = [mod.name for mod in obj.modifiers]

        # Add constraints
        obj_info["constraints"] = [con.name for con in obj.constraints]

        # Add parent/children
        obj_info["parent"] = obj.parent.name if obj.parent else None
        obj_info["children"] = [child.name for child in obj.children]

        # Add collection membership
        obj_info["collections"] = [col.name for col in obj.users_collection]

        return obj_info

    def jump_to_view3d_object_by_name(self, name: str) -> dict:
        """Focus the 3D viewport on a specific object."""
        try:
            obj = bpy.data.objects.get(name)
            if not obj:
                raise ValueError(f"Object not found: {name}")

            # Set as active object
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # Find the 3D viewport area
            area = None
            for a in bpy.context.screen.areas:
                if a.type == "VIEW_3D":
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            # Focus viewport on the object
            with bpy.context.temp_override(area=area, selected_objects=[obj]):
                bpy.ops.view3d.view_selected()

            return {
                "success": True,
                "object": obj.name,
                "location": [obj.location.x, obj.location.y, obj.location.z],
            }
        except Exception as e:
            print(f"Error in jump_to_view3d_object_by_name: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def get_screenshot_of_window_as_json(self) -> dict:
        """Get a JSON description of the Blender window layout."""
        try:
            screen = bpy.context.screen
            window = bpy.context.window_manager.windows[0]

            areas = []
            for area in screen.areas:
                area_info = {
                    "type": area.type,
                    "x": area.x,
                    "y": area.y,
                    "width": area.width,
                    "height": area.height,
                }

                # Add context-specific info based on area type
                if area.type == "VIEW_3D":
                    # Get active and selected objects
                    with bpy.context.temp_override(area=area):
                        active_obj = bpy.context.view_layer.objects.active
                        selected = [obj.name for obj in bpy.context.selected_objects]
                        area_info["active_object"] = active_obj.name if active_obj else None
                        area_info["selected_objects"] = selected

                elif area.type == "PROPERTIES":
                    # Get active property panel
                    if hasattr(area.spaces, 'active') and hasattr(area.spaces.active, 'context'):
                        area_info["active_panel"] = area.spaces.active.context

                areas.append(area_info)

            # Find active area
            active_area = None
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    active_area = "VIEW_3D"
                    break
            if not active_area and areas:
                active_area = areas[0]["type"]

            result = {
                "window_width": window.width,
                "window_height": window.height,
                "areas": areas,
                "active_area": active_area,
                "screen_name": screen.name,
            }

            print(f"Window layout collected: {len(areas)} areas")
            return result
        except Exception as e:
            print(f"Error in get_screenshot_of_window_as_json: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def render_thumbnail_to_path(
        self, output_path: str, width: int = 256, height: int = 256
    ) -> dict:
        """Render a quick thumbnail preview of the current scene."""
        try:
            # Save current render settings
            scene = bpy.context.scene
            render = scene.render

            old_width = render.resolution_x
            old_height = render.resolution_y
            old_percentage = render.resolution_percentage
            old_samples = None
            old_use_denoising = None

            # Check if Cycles is the active engine
            if render.engine == 'CYCLES':
                old_samples = scene.cycles.samples
                old_use_denoising = scene.cycles.use_denoising
                scene.cycles.samples = 1  # Minimum samples for speed
                scene.cycles.use_denoising = False

            try:
                # Override render settings for thumbnail
                render.resolution_x = width
                render.resolution_y = height
                render.resolution_percentage = 100

                # Render
                bpy.ops.render.render(write_still=True)

                # Get the rendered image
                render_result = bpy.data.images.get("Render Result")
                if render_result:
                    render_result.save_render(output_path)
                    bpy.data.images.remove(render_result)

                return {
                    "success": True,
                    "filepath": output_path,
                    "width": width,
                    "height": height,
                }
            finally:
                # Restore original render settings
                render.resolution_x = old_width
                render.resolution_y = old_height
                render.resolution_percentage = old_percentage
                if render.engine == 'CYCLES':
                    if old_samples is not None:
                        scene.cycles.samples = old_samples
                    if old_use_denoising is not None:
                        scene.cycles.use_denoising = old_use_denoising

        except Exception as e:
            print(f"Error in render_thumbnail_to_path: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def get_viewport_screenshot(
        self, max_size: int = 800, filepath: str = None, format: str = "png"
    ) -> dict:
        """Capture a screenshot of the current 3D viewport."""
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            # Find the active 3D viewport
            area = None
            for a in bpy.context.screen.areas:
                if a.type == "VIEW_3D":
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            # Take screenshot with proper context override
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            # Load and resize if needed
            img = bpy.data.images.load(filepath)
            width, height = img.size

            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)

                # Set format and save
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height

            # Cleanup Blender image data
            bpy.data.images.remove(img)

            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath,
            }

        except Exception as e:
            return {"error": str(e)}

    def execute_code(self, code: str) -> dict:
        """Execute arbitrary Blender Python code."""
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}

            # Capture stdout during execution, and return it as result
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {e}") from e


# Blender UI Panel
class STAPLER_PT_Panel(bpy.types.Panel):
    """Stapler control panel in the 3D View sidebar."""

    bl_label = "Stapler MCP"
    bl_idname = "STAPLER_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Stapler"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "stapler_port")

        if not scene.stapler_server_running:
            layout.operator("stapler.start_server", text="Connect to MCP Server")
        else:
            layout.operator("stapler.stop_server", text="Disconnect from MCP Server")
            layout.label(text=f"Running on port {scene.stapler_port}")


# Operator to start the server
class STAPLER_OT_StartServer(bpy.types.Operator):
    """Start the Stapler server to connect with MCP clients."""

    bl_idname = "stapler.start_server"
    bl_label = "Connect to MCP"
    bl_description = "Start the Stapler server to connect with MCP clients"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if not hasattr(bpy.types, "stapler_server") or not bpy.types.stapler_server:
            bpy.types.stapler_server = StaplerMCPServer(port=scene.stapler_port)

        # Start the server
        bpy.types.stapler_server.start()
        scene.stapler_server_running = True

        return {"FINISHED"}


# Operator to stop the server
class STAPLER_OT_StopServer(bpy.types.Operator):
    """Stop the Stapler server connection."""

    bl_idname = "stapler.stop_server"
    bl_label = "Stop MCP Connection"
    bl_description = "Stop the connection to MCP clients"

    def execute(self, context):
        scene = context.scene

        # Stop the server if it exists
        if hasattr(bpy.types, "stapler_server") and bpy.types.stapler_server:
            bpy.types.stapler_server.stop()
            del bpy.types.stapler_server

        scene.stapler_server_running = False

        return {"FINISHED"}


# Registration functions
def register():
    """Register the addon."""
    bpy.types.Scene.stapler_port = IntProperty(
        name="Port",
        description="Port for the Stapler server",
        default=9876,
        min=1024,
        max=65535,
    )

    bpy.types.Scene.stapler_server_running = BoolProperty(
        name="Server Running", default=False
    )

    bpy.utils.register_class(STAPLER_PT_Panel)
    bpy.utils.register_class(STAPLER_OT_StartServer)
    bpy.utils.register_class(STAPLER_OT_StopServer)

    print("Stapler addon registered")


def unregister():
    """Unregister the addon."""
    # Stop the server if it's running
    if hasattr(bpy.types, "stapler_server") and bpy.types.stapler_server:
        bpy.types.stapler_server.stop()
        del bpy.types.stapler_server

    bpy.utils.unregister_class(STAPLER_PT_Panel)
    bpy.utils.unregister_class(STAPLER_OT_StartServer)
    bpy.utils.unregister_class(STAPLER_OT_StopServer)

    del bpy.types.Scene.stapler_port
    del bpy.types.Scene.stapler_server_running

    print("Stapler addon unregistered")


if __name__ == "__main__":
    register()

