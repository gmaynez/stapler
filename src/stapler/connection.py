# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Stapler Contributors

"""Blender socket connection manager for Stapler.

This module handles the TCP socket connection to Blender, sending commands
and receiving responses.
"""

from __future__ import annotations

import json
import logging
import os
import socket
from dataclasses import dataclass
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


@dataclass
class BlenderConnection:
    """Manages connection to Blender addon socket server."""

    host: str
    port: int
    sock: socket.socket | None = None

    def connect(self) -> bool:
        """Connect to the Blender addon socket server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {e}")
            self.sock = None
            return False

    def disconnect(self) -> None:
        """Disconnect from the Blender addon."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {e}")
            finally:
                self.sock = None

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """Receive the complete response, potentially in multiple chunks.

        Args:
            sock: The socket to receive from
            buffer_size: Size of receive buffer

        Returns:
            bytes: The complete response data

        Raises:
            Exception: If connection is closed or response is incomplete
        """
        chunks: list[bytes] = []
        # Use a consistent timeout value that matches the addon's timeout
        sock.settimeout(15.0)  # Match the addon's timeout

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if not chunks:  # If we haven't received anything yet, this is an error
                            raise Exception("Connection closed before receiving any data")
                        break

                    chunks.append(chunk)

                    # Check if we've received a complete JSON object
                    try:
                        data = b"".join(chunks)
                        json.loads(data.decode("utf-8"))
                        # If we get here, it parsed successfully
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {e}")
                    raise  # Re-raise to be handled by the caller
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {e}")
            raise

        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b"".join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError as e:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received") from e
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a command to Blender and return the response.

        Args:
            command_type: The type of command to send
            params: Optional parameters for the command

        Returns:
            dict: The result from Blender

        Raises:
            ConnectionError: If not connected to Blender
            Exception: For various communication errors
        """
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {"type": command_type, "params": params or {}}

        try:
            # Log the command being sent
            logger.info(f"Sending command: {command_type} with params: {params}")

            # Send the command
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            logger.info("Command sent, waiting for response...")

            # Set a timeout for receiving - use the same timeout as in receive_full_response
            self.sock.settimeout(15.0)  # Match the addon's timeout

            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")

            response = json.loads(response_data.decode("utf-8"))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request") from None
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {e}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {e}")
            # Try to log what was received
            if "response_data" in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {e}") from e
        except Exception as e:
            logger.error(f"Error communicating with Blender: {e}")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            self.sock = None
            raise Exception(f"Communication error with Blender: {e}") from e


# Global connection instance
_blender_connection: BlenderConnection | None = None


def get_blender_connection() -> BlenderConnection:
    """Get or create a persistent Blender connection.

    Returns:
        BlenderConnection: The active connection instance

    Raises:
        Exception: If unable to connect to Blender
    """
    global _blender_connection

    # If we have an existing connection, check if it's still valid
    if _blender_connection is not None:
        try:
            # Simple ping to check connection
            _blender_connection.send_command("get_scene_info")
            return _blender_connection
        except Exception as e:
            # Connection is dead, close it and create a new one
            logger.warning(f"Existing connection is no longer valid: {e}")
            try:
                _blender_connection.disconnect()
            except Exception:
                pass
            _blender_connection = None

    # Create a new connection if needed
    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", str(DEFAULT_PORT)))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception("Could not connect to Blender. Make sure the Blender addon is running.")
        logger.info("Created new persistent connection to Blender")

    return _blender_connection

