"""
Tmux Manager - Handle all tmux session, window, and pane operations
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class TmuxManager:
    """Manages tmux sessions, windows, and panes for Claude Manager"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.session_name = settings["tmux_session_name"]
    
    def session_exists(self) -> bool:
        """Check if the tmux session exists"""
        return subprocess.run([
            "tmux", "has-session", "-t", self.session_name
        ], capture_output=True).returncode == 0
    
    def get_unique_window_name(self, project_key: str) -> str:
        """Generate a unique window name with incremental numbering if needed"""
        base_name = f"cc-mngr-{project_key}"
        
        # Get existing window names
        result = subprocess.run([
            "tmux", "list-windows", "-t", self.session_name, "-F", "#{window_name}"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # If we can't get window list, just return base name
            return base_name
            
        existing_names = set(result.stdout.strip().split('\n'))
        
        # If base name doesn't exist, use it
        if base_name not in existing_names:
            return base_name
            
        # Otherwise, find the next available number
        counter = 1
        while f"{base_name}-{counter}" in existing_names:
            counter += 1
            
        return f"{base_name}-{counter}"
    
    def create_window(self, project: Dict, project_key: str) -> Optional[str]:
        """Create a new tmux window and return the window target"""
        session_exists = self.session_exists()
        
        if session_exists:
            # Add a new window to existing session with smart naming
            window_name = self.get_unique_window_name(project_key)
            print(f"Creating new window '{window_name}' in existing session '{self.session_name}'...")
            
            # Let tmux automatically assign the next available window index
            result = subprocess.run([
                "tmux", "new-window", "-t", self.session_name,
                "-n", window_name, "-c", "/home/bpeeters/MEGA/manager",
                "-d"  # Don't make it the active window
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error creating named window: {result.stderr}")
                print("Trying with auto-generated name...")
                # Alternative: let tmux auto-generate window name and index
                result = subprocess.run([
                    "tmux", "new-window", "-t", self.session_name,
                    "-c", "/home/bpeeters/MEGA/manager", "-d"
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Failed to create window: {result.stderr}")
                    return None
                # Get the window that was just created
                window_list = subprocess.run([
                    "tmux", "list-windows", "-t", self.session_name, "-F", "#{window_index}"
                ], capture_output=True, text=True)
                if window_list.returncode == 0:
                    # Get the highest window index (the one just created)
                    window_indices = [int(x) for x in window_list.stdout.strip().split('\n') if x.strip()]
                    latest_window = max(window_indices)
                    window_target = f"{self.session_name}:{latest_window}"
                    print(f"Created window at index {latest_window}")
                else:
                    print("Could not determine new window index")
                    return None
            else:
                window_target = f"{self.session_name}:{window_name}"
                print(f"Successfully created window: {window_target}")
        else:
            # Create new session with named first window
            window_name = self.get_unique_window_name(project_key)
            print(f"Creating new session '{self.session_name}' with window '{window_name}'...")
            subprocess.run([
                "tmux", "new-session", "-d", "-s", self.session_name,
                "-n", window_name, "-c", "/home/bpeeters/MEGA/manager"
            ])
            window_target = f"{self.session_name}:{window_name}"
        
        return window_target
    
    def setup_window_layout(self, window_target: str, project: Dict, project_key: str = None):
        """Setup the three-pane layout for a window"""
        print(f"Setting up panes in window: {window_target}")
        
        # Create the desired layout:
        # buffer  | claude-manager |
        # --------|                | 
        # ccusage |                |
        
        # First split vertically to create left and right columns
        print("Creating vertical split for left/right columns...")
        result = subprocess.run([
            "tmux", "split-window", "-h", "-t", window_target,
            "-c", "/home/bpeeters/MEGA/manager"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in vertical split: {result.stderr}")
            return
        
        # Now split the left column horizontally to create buffer (top) and ccusage (bottom)
        print("Creating horizontal split in left column...")
        result = subprocess.run([
            "tmux", "split-window", "-v", "-t", f"{window_target}.0",
            "-p", str(self.settings["pane_heights"]["bottom"]),
            "-c", "/home/bpeeters/MEGA/manager"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in horizontal split: {result.stderr}")
            return
        
        print("Layout created successfully!")
        
        # Now we have:
        # Pane 0: top-left (buffer/notes)
        # Pane 1: bottom-left (ccusage)
        # Pane 2: right side (claude)
        
        # Setup each pane
        print("Setting up notes pane...")
        self.setup_notes_pane(window_target, project, "0", project_key)
        
        print("Setting up monitoring pane...")
        self.setup_monitoring_pane(window_target, "1")
        
        print("Setting up claude pane...")
        self.setup_claude_pane(window_target, project, "2", project_key)
        
        # Select the Claude pane as the active pane
        subprocess.run([
            "tmux", "select-pane", "-t", f"{window_target}.2"
        ])
    
    def setup_notes_pane(self, window_target: str, project: Dict, pane_id: str, project_key: str = None):
        """Setup the notes pane (top-left) - opens buffer.md"""
        # Always open the general buffer file for quick notes
        notes_path = Path("/home/bpeeters/MEGA/notes/buffer.md")
        
        # Create buffer file if it doesn't exist
        if not notes_path.exists():
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(f"# Quick Notes Buffer\n\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        # Open in editor
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            f"{self.settings['editor']} {notes_path}", "Enter"
        ])
    
    def setup_claude_pane(self, window_target: str, project: Dict, pane_id: str, project_key: str = None):
        """Setup the Claude pane (right side)"""
        # Import here to avoid circular imports
        from .claude_command import build_claude_command
        
        # Build Claude command with context
        claude_cmd = build_claude_command(self.settings, project, project_key)
        
        # Send command to pane
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            claude_cmd, "Enter"
        ])
    
    def setup_monitoring_pane(self, window_target: str, pane_id: str):
        """Setup the monitoring pane (bottom-left)"""
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            self.settings["ccusage_command"], "Enter"
        ])
    
    def auto_attach_or_switch(self, window_target: str, session_existed: bool):
        """Handle automatic attach or window switching"""
        if session_existed:
            print(f"New window created: {window_target}")
            # Check if we're already in a tmux session
            current_session = os.environ.get("TMUX_PANE")
            if current_session:
                # We're inside tmux, just select the window
                print(f"Switching to new window...")
                subprocess.run(["tmux", "select-window", "-t", window_target])
            else:
                # We're outside tmux, attach to session and select window
                print(f"Attaching to session and switching to window...")
                subprocess.run(["tmux", "attach-session", "-t", f"{self.session_name}:{window_target.split(':')[1]}"])
        else:
            print(f"New session created: {self.session_name}")
            print(f"Attaching to session...")
            subprocess.run(["tmux", "attach-session", "-t", self.session_name])