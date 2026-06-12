"""
Extracts human-readable conversation titles from brain artifacts.

This module is UI-agnostic — it performs file I/O only and returns data.
"""

from __future__ import annotations

import os
import re
import platform

from .constants import MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, TITLE_ARTIFACT_FILES, OVERVIEW_SUBPATH


class ArtifactParser:
    """Extracts human-readable conversation titles from brain artifacts."""

    @staticmethod
    def extract_title(conv_uuid: str, brain_dir: str) -> str | None:
        """
        Attempts to extract a human-readable title from the brain artifacts
        for a given conversation UUID.

        Fallback Sequence:
          1. First Markdown heading (#) in task.md / implementation_plan.md / walkthrough.md
          2. First strictly meaningful line in .system_generated/logs/overview.txt
          3. None (Caller will generate a timestamp-based fallback string)
        """
        target_dir = os.path.join(brain_dir, conv_uuid)
        if not os.path.isdir(target_dir):
            return None

        for artifact_file in TITLE_ARTIFACT_FILES:
            filepath = os.path.join(target_dir, artifact_file)
            if os.path.isfile(filepath):
                title = ArtifactParser._read_first_heading(filepath)
                if title:
                    return title

        overview_path = os.path.join(target_dir, OVERVIEW_SUBPATH)
        if os.path.isfile(overview_path):
            try:
                with open(overview_path, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        clean = line.strip()
                        if clean and not clean.startswith("#") and len(clean) > MIN_TITLE_LENGTH:
                            return clean[:MAX_TITLE_LENGTH]
            except OSError:
                pass

        return None

    @staticmethod
    def _read_first_heading(filepath: str) -> str | None:
        """Extracts the first Markdown heading (# ...) from a file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        title = stripped.lstrip("#").strip()
                        if title:
                            return title[:MAX_TITLE_LENGTH]
        except OSError:
            pass
        return None

    @staticmethod
    def infer_workspace_from_brain(conv_uuid: str, brain_dir: str) -> str | None:
        """
        Heuristically scans brain files and logs to infer the developer's workspace path
        matching the registered workspaces in the IDE's workspaceStorage.
        """
        from .environment import EnvironmentResolver
        import json
        import urllib.parse

        # 1. Discover all registered workspaces on the system
        db_path = EnvironmentResolver.get_antigravity_db_path()
        workspaces = []
        user_dir = os.path.dirname(os.path.dirname(db_path))
        ws_storage = os.path.join(user_dir, "workspaceStorage")
        if os.path.isdir(ws_storage):
            import glob
            for ws_json in glob.glob(os.path.join(ws_storage, "*", "workspace.json")):
                try:
                    with open(ws_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    folder = data.get("folder")
                    if folder and folder.startswith("file:///"):
                        path = folder[len("file:///"):]
                        if not path.startswith("/") and not (len(path) >= 2 and path[1] == ":"):
                            path = "/" + path
                        path = urllib.parse.unquote(path)
                        workspaces.append(os.path.abspath(path))
                except Exception:
                    pass

        target_dir = os.path.join(brain_dir, conv_uuid)
        overview_path = os.path.join(target_dir, ".system_generated", "logs", "overview.txt")
        
        # Read content from overview.txt first if it exists, or fall back to md files
        content = ""
        if os.path.isfile(overview_path):
            try:
                with open(overview_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                pass
        
        if not content:
            # Fallback: read any md files
            content_parts = []
            try:
                for name in os.listdir(target_dir):
                    if name.endswith(".md") and not name.startswith("."):
                        with open(os.path.join(target_dir, name), "r", encoding="utf-8", errors="ignore") as f:
                            content_parts.append(f.read())
                content = "\n".join(content_parts)
            except OSError:
                pass

        if not content or not workspaces:
            return None

        # Count occurrences of each workspace path in the content
        matched_counts = {ws: 0 for ws in workspaces}
        for ws in workspaces:
            matched_counts[ws] = content.count(ws)

        # Ignore parent workspaces if a more specific child workspace is matched
        for ws_parent in workspaces:
            for ws_child in workspaces:
                if ws_child != ws_parent and (ws_child.startswith(ws_parent + "/") or ws_child.startswith(ws_parent + "\\")):
                    if matched_counts.get(ws_child, 0) > 0:
                        matched_counts[ws_parent] = 0
                        break

        # Ignore home directory if more specific workspace is matched
        home = os.path.expanduser("~")
        if home in matched_counts and len(matched_counts) > 1:
            if any(v > 0 for k, v in matched_counts.items() if k != home):
                matched_counts[home] = 0

        best_ws = None
        best_count = 0
        for ws, count in matched_counts.items():
            if count > best_count:
                best_count = count
                best_ws = ws
            elif count == best_count and best_ws is not None:
                if len(ws) > len(best_ws):
                    best_ws = ws

        return best_ws
