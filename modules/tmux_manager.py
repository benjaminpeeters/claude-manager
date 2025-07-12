"""
Tmux Manager - Handle all tmux session, window, and pane operations
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from .debug_logger import get_debug_logger


class TmuxManager:
    """Manages tmux sessions, windows, and panes for Claude Manager"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.session_name = settings["tmux_session_name"]
        self.debug_logger = get_debug_logger()
    
    def _run_tmux_command(self, command: list, log_success: bool = True) -> subprocess.CompletedProcess:
        """Run a tmux command with debug logging"""
        result = subprocess.run(command, capture_output=True, text=True)
        
        if log_success or result.returncode != 0:
            self.debug_logger.log_tmux_command(
                command, result.returncode, result.stdout, result.stderr
            )
        
        return result
    
    def session_exists(self) -> bool:
        """Check if the tmux session exists"""
        result = self._run_tmux_command([
            "tmux", "has-session", "-t", self.session_name
        ], log_success=False)
        return result.returncode == 0
    
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
    
    def _create_window_safe(self, window_name: str, session_target: str = None, insert_left: bool = False) -> Optional[str]:
        """Safely create a window and return reliable target string"""
        if session_target is None:
            session_target = self.session_name
            
        # Create window and get index for reliable targeting
        if insert_left:
            # Use -b flag to insert before the first window (leftmost position)
            target_args = ["-b", "-t", f"{session_target}:^"]
        else:
            # Use -a flag to append after last window (default behavior)
            target_args = ["-a", "-t", session_target]
        
        result = self._run_tmux_command([
            "tmux", "new-window"] + target_args + [
            "-n", window_name, "-c", "/home/bpeeters/MEGA/manager",
            "-d", "-P", "-F", "#{window_index}"
        ])
        
        if result.returncode != 0:
            print(f"Error creating named window '{window_name}': {result.stderr}")
            # Try without name as fallback
            result = self._run_tmux_command([
                "tmux", "new-window"] + target_args + [
                "-c", "/home/bpeeters/MEGA/manager", "-d",
                "-P", "-F", "#{window_index}"
            ])
            if result.returncode != 0:
                print(f"Failed to create window: {result.stderr}")
                return None
        
        window_index = result.stdout.strip()
        if not window_index:
            print("Warning: Could not determine window index")
            return None
            
        # Use index-based targeting for reliability
        window_target = f"{session_target}:{window_index}"
        
        # Verify window exists
        verify_result = self._run_tmux_command([
            "tmux", "display-message", "-t", window_target, "-p", "#{window_name}"
        ], log_success=False)
        
        if verify_result.returncode != 0:
            print(f"Warning: Could not verify window {window_target}")
            return None
            
        return window_target

    def _verify_window_ready(self, window_target: str, max_retries: int = 5) -> bool:
        """Verify that a window is ready for operations"""
        for attempt in range(max_retries):
            result = self._run_tmux_command([
                "tmux", "display-message", "-t", window_target, "-p", "#{window_id}"
            ], log_success=False)
            
            if result.returncode == 0 and result.stdout.strip():
                return True
                
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Progressive delay
                
        return False

    def create_window(self, project: Dict, project_key: str) -> Optional[str]:
        """Create a new tmux window and return the window target"""
        session_exists = self.session_exists()
        
        if session_exists:
            # Add a new window to existing session
            window_name = self.get_unique_window_name(project_key)
            print(f"Creating new window '{window_name}' in existing session '{self.session_name}'...")
            return self._create_window_safe(window_name, insert_left=True)
        else:
            # Create new session with named first window
            window_name = self.get_unique_window_name(project_key)
            print(f"Creating new session '{self.session_name}' with window '{window_name}'...")
            result = self._run_tmux_command([
                "tmux", "new-session", "-d", "-s", self.session_name,
                "-n", window_name, "-c", "/home/bpeeters/MEGA/manager"
            ])
            if result.returncode != 0:
                print(f"Failed to create session: {result.stderr}")
                return None
            return f"{self.session_name}:0"  # First window is always index 0
    
    def setup_standard_project_layout(self, window_target: str, project: Dict, project_key: str):
        """Setup standard 2-pane layout for project window: task file (left) | claude (right)"""
        print(f"Setting up standard project layout: {window_target}")
        
        # Split vertically (left | right)
        result = self._run_tmux_command([
            "tmux", "split-window", "-h", "-t", window_target,
            "-c", "/home/bpeeters/MEGA/manager"
        ])
        
        if result.returncode != 0:
            print(f"Error creating vertical split: {result.stderr}")
            return False
        
        # Setup left pane with task file
        self.setup_task_file_pane(window_target, project, "0", project_key)
        
        # Setup right pane with claude
        self.setup_claude_pane(window_target, project, "1", project_key)
        
        # Select claude pane as active
        subprocess.run([
            "tmux", "select-pane", "-t", f"{window_target}.1"
        ])
        
        return True
    
    def setup_notes_pane(self, window_target: str, project: Dict, pane_id: str, project_key: str = None):
        """Setup the notes pane (top-left) - opens project-specific task file"""
        # Get project key
        if not project_key:
            project_key = project.get("key", "unknown")
        
        # Create tasks directory if it doesn't exist
        tasks_dir = Path("/home/bpeeters/MEGA/manager/tasks")
        tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Open project-specific task file
        task_file = tasks_dir / f"task_{project_key}.md"
        
        # Create task file if it doesn't exist
        if not task_file.exists():
            task_file.write_text(
                f"# {project['name']} - Task Notes\n\n"
                f"Project: {project.get('name', 'Unknown')}\n"
                f"Category: {project.get('category', 'General')}\n"
                f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"## Current Tasks\n\n\n"
                f"## Notes\n\n\n"
            )
        
        # Open in editor
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            f"{self.settings['editor']} {task_file}", "Enter"
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
                # Use the window target directly, it's already in the correct format
                subprocess.run(["tmux", "attach-session", "-t", window_target])
        else:
            print(f"New session created: {self.session_name}")
            print(f"Attaching to session...")
            subprocess.run(["tmux", "attach-session", "-t", self.session_name])
    
    def create_ccusage_window(self) -> Optional[str]:
        """Create ccusage window in the mngr session"""
        if not self.session_exists():
            print("Error: mngr session doesn't exist")
            return None
            
        print("Creating ccusage window...")
        result = subprocess.run([
            "tmux", "new-window", "-a", "-t", self.session_name,
            "-n", "ccusage", "-c", "/home/bpeeters/MEGA/manager",
            "-d", self.settings["ccusage_command"]
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating ccusage window: {result.stderr}")
            return None
            
        # Small delay to ensure window is ready
        time.sleep(0.1)
        return f"{self.session_name}:ccusage"
    
    def create_log_window(self) -> Optional[str]:
        """Create daily log window in the mngr session"""
        if not self.session_exists():
            print("Error: mngr session doesn't exist")
            return None
            
        # Create logs directory if it doesn't exist
        logs_dir = Path("/home/bpeeters/MEGA/manager/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daily log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = logs_dir / f"{today}.md"
        
        if not log_file.exists():
            log_file.write_text(f"# Daily Log - {today}\n\n")
        
        print("Creating log window...")
        result = subprocess.run([
            "tmux", "new-window", "-a", "-t", self.session_name,
            "-n", "mngr-log", "-c", "/home/bpeeters/MEGA/manager",
            "-d", f"{self.settings['editor']} {log_file}"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating log window: {result.stderr}")
            return None
            
        # Small delay to ensure window is ready
        time.sleep(0.1)
        return f"{self.session_name}:mngr-log"
    
    def create_project_window(self, project: Dict, project_key: str) -> Optional[str]:
        """Create a project window with task file and claude instance"""
        if not self.session_exists():
            print("Error: mngr session doesn't exist")
            return None
            
        window_name = f"cc-mngr-{project_key}"
        print(f"Creating project window '{window_name}'...")
        
        # Use the safe window creation method
        window_target = self._create_window_safe(window_name)
        if not window_target:
            self.debug_logger.log_window_creation("project", window_name, False, "Failed to create window")
            return None
            
        print(f"Successfully created window: {window_target}")
        self.debug_logger.log_window_creation("project", window_name, True)
        
        # Verify window is ready before proceeding
        if not self._verify_window_ready(window_target):
            print("Warning: Window not ready for operations")
            return None
        
        # Setup two-pane layout (vertical split)
        if not self.setup_project_window_layout(window_target, project, project_key):
            print("Failed to setup project window layout")
            return None
        
        return window_target
    
    def setup_project_window_layout(self, window_target: str, project: Dict, project_key: str):
        """Setup two-pane layout for project window: task file (left) | claude (right)"""
        return self.setup_standard_project_layout(window_target, project, project_key)
    
    def setup_task_file_pane(self, window_target: str, project: Dict, pane_id: str, project_key: str):
        """Setup task file pane (same as notes pane but renamed for clarity)"""
        self.setup_notes_pane(window_target, project, pane_id, project_key)
    
    def rename_current_window(self, new_name: str) -> bool:
        """Rename the current tmux window"""
        try:
            result = subprocess.run([
                "tmux", "rename-window", new_name
            ], capture_output=True, text=True, check=True)
            print(f"Renamed current window to: {new_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error renaming window: {e.stderr}")
            return False
    
    def clear_current_window(self):
        """Clear all panes in current window and reset to single pane"""
        debug_logger = get_debug_logger()
        
        try:
            debug_logger.log("Starting window clear process", "CLEAR")
            
            # Kill all panes except pane 0
            debug_logger.log("Getting list of panes", "CLEAR")
            result = self._run_tmux_command([
                "tmux", "list-panes", "-F", "#{pane_index}"
            ])
            
            if result.returncode != 0:
                debug_logger.log("Failed to list panes", "ERROR", {"stderr": result.stderr})
                raise subprocess.CalledProcessError(result.returncode, "list-panes", result.stderr)
            
            pane_indices = result.stdout.strip().split('\n')
            debug_logger.log(f"Found panes: {pane_indices}", "CLEAR")
            
            # Kill extra panes
            for pane_idx in pane_indices:
                if pane_idx and pane_idx != "0":
                    debug_logger.log(f"Killing pane {pane_idx}", "CLEAR")
                    kill_result = self._run_tmux_command([
                        "tmux", "kill-pane", "-t", f".{pane_idx}"
                    ])
                    if kill_result.returncode != 0:
                        debug_logger.log(f"Failed to kill pane {pane_idx}", "WARNING", {
                            "stderr": kill_result.stderr
                        })
            
            # Clear the remaining pane content
            debug_logger.log("Clearing remaining pane content", "CLEAR")
            # For Scenario 3, we don't send C-c because claude-manager is running in this pane
            # and would interrupt itself. Just clear the screen.
            clear_result = self._run_tmux_command([
                "tmux", "send-keys", "-t", ".0", "clear", "Enter"
            ])
            
            if clear_result.returncode != 0:
                debug_logger.log("Failed to clear pane content", "WARNING", {
                    "stderr": clear_result.stderr
                })
            
            debug_logger.log("Window clear process completed", "CLEAR")
            print("Cleared current window")
            
        except Exception as e:
            debug_logger.log("Exception in clear_current_window", "ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"Error clearing window: {e}")
            raise
    
    def setup_current_window_as_project(self, project: Dict, project_key: str):
        """Transform current window into a project window"""
        debug_logger = get_debug_logger()
        
        try:
            debug_logger.log("Starting window transformation", "TRANSFORM", {
                "project_key": project_key,
                "project_name": project.get("name", "Unknown")
            })
            
            # Clear existing content with better user feedback
            print("   → Preparing to transform current window...")
            print("   → This will clear the current window and set up your project workspace")
            print("   → Please wait, do not interrupt...")
            debug_logger.log("About to clear current window", "TRANSFORM")
            
            try:
                self.clear_current_window()
                debug_logger.log("Window cleared successfully", "TRANSFORM")
                print("   ✅ Window cleared successfully")
            except Exception as e:
                debug_logger.log("Error clearing window", "ERROR", {"error": str(e)})
                print(f"   ❌ Error clearing window: {e}")
                return None
            
            # Rename window
            window_name = f"cc-mngr-{project_key}"
            print(f"   → Renaming window to {window_name}...")
            debug_logger.log(f"About to rename window to {window_name}", "TRANSFORM")
            
            try:
                if not self.rename_current_window(window_name):
                    print("   ⚠️  Warning: Could not rename window")
                    debug_logger.log("Window rename failed but continuing", "WARNING")
                else:
                    debug_logger.log("Window renamed successfully", "TRANSFORM")
            except Exception as e:
                debug_logger.log("Error renaming window", "ERROR", {"error": str(e)})
                print(f"   ⚠️  Error renaming window: {e}")
            
            # Get current window target
            debug_logger.log("Getting window target", "TRANSFORM")
            
            try:
                result = self._run_tmux_command([
                    "tmux", "display-message", "-p", "#{session_name}:#{window_name}"
                ], log_success=False)
                
                if result.returncode != 0:
                    debug_logger.log("Window name targeting failed, trying index", "TRANSFORM")
                    # Fallback to index-based targeting
                    result = self._run_tmux_command([
                        "tmux", "display-message", "-p", "#{session_name}:#{window_index}"
                    ], log_success=False)
                
                if result.returncode != 0:
                    debug_logger.log("Both targeting methods failed", "ERROR", {
                        "return_code": result.returncode,
                        "stderr": result.stderr
                    })
                    print(f"   ❌ Error getting window target: {result.stderr}")
                    return None
                    
                window_target = result.stdout.strip()
                debug_logger.log(f"Got window target: {window_target}", "TRANSFORM")
                print(f"   → Setting up project layout...")
                
                # Verify window is ready before proceeding
                if not self._verify_window_ready(window_target):
                    debug_logger.log("Window not ready for layout setup", "ERROR")
                    print(f"   ❌ Window not ready for operations")
                    return None
                
                # Setup project layout
                print(f"   → Creating project layout (task file + Claude instance)...")
                debug_logger.log("About to setup project layout", "TRANSFORM")
                try:
                    success = self.setup_standard_project_layout(window_target, project, project_key)
                    if success:
                        debug_logger.log("Project layout setup completed", "TRANSFORM")
                        print(f"   ✅ Project layout created successfully")
                    else:
                        debug_logger.log("Project layout setup failed", "ERROR")
                        print(f"   ❌ Error setting up layout")
                        return None
                except Exception as e:
                    debug_logger.log("Error setting up project layout", "ERROR", {"error": str(e)})
                    print(f"   ❌ Error setting up layout: {e}")
                    return None
                
                debug_logger.log("Window transformation completed successfully", "TRANSFORM")
                return window_target
                
            except Exception as e:
                debug_logger.log("Exception in window targeting", "ERROR", {
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                print(f"   ❌ Error getting window target: {e}")
                return None
                
        except Exception as e:
            debug_logger.log("Exception in setup_current_window_as_project", "ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"   ❌ Error setting up window: {e}")
            return None