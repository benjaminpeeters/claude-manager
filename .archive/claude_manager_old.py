#!/usr/bin/env python3
"""
Claude Manager - Personal AI Assistant/Coach
Integrates with Todoist, monitors progress, and provides intelligent support
"""

import os
import sys
import yaml
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Base paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MEGA_DIR = Path("/home/bpeeters/MEGA")


class ClaudeManager:
    def __init__(self):
        self.projects = self.load_projects()
        self.settings = self.load_settings()
        self.current_project = None
        
    def load_projects(self) -> Dict:
        """Load project configurations from projects.yaml"""
        projects_file = CONFIG_DIR / "projects.yaml"
        if projects_file.exists():
            with open(projects_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return self.get_default_projects()
    
    def load_settings(self) -> Dict:
        """Load general settings from settings.yaml"""
        settings_file = CONFIG_DIR / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return self.get_default_settings()
    
    def get_default_projects(self) -> Dict:
        """Default project configurations - empty by default"""
        return {}
    
    def get_default_settings(self) -> Dict:
        """Default general settings"""
        return {
            "tmux_session_name": "mngr",
            "editor": "nvim",
            "claude_command": "claude",
            "ccusage_command": "ccusage blocks --live -t 150000",
            "pane_heights": {
                "top": 80,  # percentage
                "bottom": 20
            },
            "auto_save_interval": 300,  # seconds
            "monitoring": {
                "track_deep_work": True,
                "track_habits": True,
                "track_todoist": True
            }
        }
    
    def get_unique_window_name(self, session_name: str, project_key: str) -> str:
        """Generate a unique window name with incremental numbering if needed"""
        base_name = f"cc-mngr-{project_key}"
        
        # Get existing window names
        result = subprocess.run([
            "tmux", "list-windows", "-t", session_name, "-F", "#{window_name}"
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
    
    def select_project(self) -> Optional[str]:
        """Interactive project selection"""
        print("\n🤖 Claude Manager - Select Project Focus\n")
        print("Available projects:")
        
        project_keys = list(self.projects.keys())
        for i, key in enumerate(project_keys, 1):
            project = self.projects[key]
            print(f"  {i}. {project['name']}")
        
        print(f"  {len(project_keys) + 1}. Exit")
        
        while True:
            try:
                choice = input("\nSelect project (number): ").strip()
                choice_num = int(choice)
                
                if choice_num == len(project_keys) + 1:
                    return None
                elif 1 <= choice_num <= len(project_keys):
                    return project_keys[choice_num - 1]
                else:
                    print("Invalid choice. Please try again.")
            except (ValueError, EOFError, KeyboardInterrupt):
                return None
    
    def setup_tmux_session(self, project_key: str):
        """Setup tmux session with three panes"""
        project = self.projects[project_key]
        session_name = self.settings["tmux_session_name"]
        
        # Check if session exists
        session_exists = subprocess.run([
            "tmux", "has-session", "-t", session_name
        ], capture_output=True).returncode == 0
        
        if session_exists:
            # Add a new window to existing session with smart naming
            window_name = self.get_unique_window_name(session_name, project_key)
            print(f"Creating new window '{window_name}' in existing session '{session_name}'...")
            
            # Let tmux automatically assign the next available window index
            result = subprocess.run([
                "tmux", "new-window", "-t", session_name,
                "-n", window_name, "-c", project["directory"],
                "-d"  # Don't make it the active window
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error creating named window: {result.stderr}")
                print("Trying with auto-generated name...")
                # Alternative: let tmux auto-generate window name and index
                result = subprocess.run([
                    "tmux", "new-window", "-t", session_name,
                    "-c", project["directory"], "-d"
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Failed to create window: {result.stderr}")
                    return
                # Get the window that was just created
                window_list = subprocess.run([
                    "tmux", "list-windows", "-t", session_name, "-F", "#{window_index}"
                ], capture_output=True, text=True)
                if window_list.returncode == 0:
                    # Get the highest window index (the one just created)
                    window_indices = [int(x) for x in window_list.stdout.strip().split('\n') if x.strip()]
                    latest_window = max(window_indices)
                    window_target = f"{session_name}:{latest_window}"
                    print(f"Created window at index {latest_window}")
                else:
                    print("Could not determine new window index")
                    return
            else:
                window_target = f"{session_name}:{window_name}"
                print(f"Successfully created window: {window_target}")
        else:
            # Create new session with named first window
            window_name = self.get_unique_window_name(session_name, project_key)
            print(f"Creating new session '{session_name}' with window '{window_name}'...")
            subprocess.run([
                "tmux", "new-session", "-d", "-s", session_name,
                "-n", window_name, "-c", project["directory"]
            ])
            window_target = f"{session_name}:{window_name}"
        
        # Setup the three-pane layout (consolidated function)
        self.setup_window_layout(window_target, project)
        
        print(f"✨ Claude Manager setup complete!")
        
        # Automatic switching/attaching
        if session_exists:
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
                subprocess.run(["tmux", "attach-session", "-t", f"{session_name}:{window_target.split(':')[1]}"])
        else:
            print(f"New session created: {session_name}")
            print(f"Attaching to session...")
            subprocess.run(["tmux", "attach-session", "-t", session_name])
    
    def setup_window_layout(self, window_target: str, project: Dict):
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
            "-c", project["directory"]
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in vertical split: {result.stderr}")
            return
        
        # Now split the left column horizontally to create buffer (top) and ccusage (bottom)
        print("Creating horizontal split in left column...")
        result = subprocess.run([
            "tmux", "split-window", "-v", "-t", f"{window_target}.0",
            "-p", str(self.settings["pane_heights"]["bottom"]),
            "-c", project["directory"]
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
        self.setup_notes_pane(window_target, project, "0")
        
        print("Setting up monitoring pane...")
        self.setup_monitoring_pane(window_target, "1")
        
        print("Setting up claude pane...")
        self.setup_claude_pane(window_target, project, "2")
    
    def setup_notes_pane(self, window_target: str, project: Dict, pane_id: str):
        """Setup the notes pane (top-left)"""
        notes_path = MEGA_DIR / project["notes_file"]
        
        # Create notes file if it doesn't exist
        if not notes_path.exists():
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(f"# {project['name']} Notes\n\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        # Open in editor
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            f"{self.settings['editor']} {notes_path}", "Enter"
        ])
    
    def setup_claude_pane(self, window_target: str, project: Dict, pane_id: str):
        """Setup the Claude pane (top-right)"""
        # Build Claude command with context
        claude_cmd = self.build_claude_command(project)
        
        # Send command to pane
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            claude_cmd, "Enter"
        ])
    
    def setup_monitoring_pane(self, window_target: str, pane_id: str):
        """Setup the monitoring pane (bottom)"""
        subprocess.run([
            "tmux", "send-keys", "-t", f"{window_target}.{pane_id}",
            self.settings["ccusage_command"], "Enter"
        ])
    
    def build_claude_command(self, project: Dict) -> str:
        """Build Claude command with project context and MCP configuration"""
        cmd_parts = [self.settings["claude_command"]]
        
        # Add MCP configuration
        mcp_servers = project.get("mcp_access", [])
        if mcp_servers:
            # Create MCP config JSON for the specified servers
            mcp_config = {}
            for server in mcp_servers:
                mcp_config[server] = {}  # Let it use default configuration
            
            # Add MCP config as JSON string
            import json
            mcp_config_str = json.dumps({"mcpServers": mcp_config})
            cmd_parts.append(f"--mcp-config '{mcp_config_str}'")
            cmd_parts.append("--strict-mcp-config")
        
        # Add the manager's Claude instructions
        manager_claude_md = BASE_DIR / "CLAUDE.md"
        if manager_claude_md.exists():
            cmd_parts.append(f"@{manager_claude_md}")
        
        # Add context files using @ syntax
        for context_file in project.get("claude_context", []):
            context_path = MEGA_DIR / context_file
            if "*" in context_file:
                # Handle wildcards
                for path in context_path.parent.glob(context_path.name):
                    if path.is_file():
                        cmd_parts.append(f"@{path}")
            elif context_path.exists():
                cmd_parts.append(f"@{context_path}")
        
        # Add initial message about the project
        intro_msg = f"You are now in {project['name']} mode. "
        intro_msg += f"Working directory: {project['directory']}. "
        intro_msg += f"Focus areas: {', '.join(project.get('tags', []))}."
        cmd_parts.append(f'"{intro_msg}"')
        
        return " ".join(cmd_parts)
    
    def save_project_configs(self):
        """Save current project configurations"""
        with open(CONFIG_DIR / "projects.yaml", 'w') as f:
            yaml.dump(self.projects, f, default_flow_style=False)
    
    def save_settings(self):
        """Save current settings"""
        with open(CONFIG_DIR / "settings.yaml", 'w') as f:
            yaml.dump(self.settings, f, default_flow_style=False)
    
    def run(self):
        """Main execution flow"""
        # Ensure config files exist
        if not (CONFIG_DIR / "projects.yaml").exists():
            print("\nNo projects.yaml found. Creating an example configuration...")
            self.create_example_config()
            print(f"Please edit {CONFIG_DIR / 'projects.yaml'} to add your projects.")
            return
        
        if not (CONFIG_DIR / "settings.yaml").exists():
            self.save_settings()
        
        # Check if we have any projects
        if not self.projects:
            print("\nNo projects configured.")
            print(f"Please edit {CONFIG_DIR / 'projects.yaml'} to add your projects.")
            return
        
        # Select project
        project_key = self.select_project()
        if not project_key:
            print("\nExiting Claude Manager.")
            return
        
        self.current_project = project_key
        print(f"\n✨ Starting {self.projects[project_key]['name']}...\n")
        
        # Setup tmux session/window
        self.setup_tmux_session(project_key)
    
    def create_example_config(self):
        """Create an example projects.yaml file"""
        example_projects = {
            "example_project": {
                "name": "Example Project",
                "directory": str(MEGA_DIR),
                "notes_file": "notes/example.md",
                "claude_context": [
                    "notes/example.md"
                ],
                "mcp_access": ["todoist-mcp"],
                "tags": ["example"]
            }
        }
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_DIR / "projects.yaml", 'w') as f:
            f.write("# Claude Manager Projects Configuration\n")
            f.write("# Add your projects below following this structure:\n\n")
            yaml.dump(example_projects, f, default_flow_style=False)
            f.write("\n# Add more projects as needed\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude Manager - Personal AI Assistant")
    parser.add_argument("--project", "-p", help="Project key to start directly")
    parser.add_argument("--list", "-l", action="store_true", help="List available projects")
    
    args = parser.parse_args()
    
    manager = ClaudeManager()
    
    if args.list:
        print("\nAvailable projects:")
        for key, project in manager.projects.items():
            print(f"  {key}: {project['name']}")
        return
    
    if args.project:
        if args.project in manager.projects:
            manager.current_project = args.project
            print(f"\n✨ Starting {manager.projects[args.project]['name']}...\n")
            manager.setup_tmux_session(args.project)
        else:
            print(f"Error: Project '{args.project}' not found.")
            print("Use --list to see available projects.")
    else:
        manager.run()


if __name__ == "__main__":
    main()