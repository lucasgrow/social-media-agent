"""Self-contained, cross-platform local Cobalt provisioning.

Public API: is_running, ensure, start, stop, status. See server.py for details.
"""
from social_media_agent.cobalt.server import ensure, is_running, start, status, stop

__all__ = ["is_running", "ensure", "start", "stop", "status"]
