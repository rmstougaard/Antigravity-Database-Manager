# Antigravity Database Manager (Patched Edition)

An enhanced and patched fork of the [original Antigravity-Database-Manager by Donald R. Johnson](https://github.com/ag-donald/Antigravity-Database-Manager).

This tool is designed to diagnose, check, and recover lost chat history in the Google Antigravity IDE. Wiping chat history is a common issue with the IDE's session manager, where internal SQLite index files (`state.vscdb`) are wiped on unclean shutdowns, restarts, or updates, while the raw conversation data files (`.pb`) remain intact on disk.

This patched edition resolves several critical bugs to ensure recovery is reliable, accurate, and compatible with more environments.

## Patched Improvements

*   **Generic Parent-Workspace Filtering**: Fixed a bug where conversations were mapped to generic parent directories (e.g., `/home/user/work`) instead of their specific sub-project directories (e.g., `/home/user/work/my-project`).
*   **POSIX URI Normalization**: Fixed path formatting to construct standard three-slash `file:///` URIs, ensuring the IDE registers the workspace paths correctly.
*   **Robust Process Detection**: Switched from `pgrep -f` to `pgrep -x` to avoid false positives matching the python script itself when warning about the active IDE process.
*   **Python Compatibility**: Lowered the minimum Python version requirement from 3.10 to 3.8+ to support standard enterprise Linux environments.

## Quickstart

1. **Close the Antigravity IDE completely** (mandatory, otherwise the IDE will overwrite your recovery changes upon shutdown).
2. Run the recovery script:
   ```bash
   python3 antigravity_database_manager.py recover
   ```
3. Reopen the IDE—your conversation history will be restored in the sidebar.

## Credits & License

*   Original tool by Donald R. Johnson at Agmercium.
*   Patches contributed by Rasmus Stougaard.
*   Licensed under **The Unlicense** (Public Domain).
