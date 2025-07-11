#!/usr/bin/env python3
"""
Claude Manager - Personal AI Assistant/Coach
Integrates with Todoist, monitors progress, and provides intelligent support
"""

import argparse
from pathlib import Path

# Import modular components
from modules.config_manager import ConfigManager
from modules.project_manager import ProjectManager
from modules.tmux_manager import TmuxManager

# Base paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"


class ClaudeManager:
    """Main Claude Manager orchestrator"""
    
    def __init__(self):
        # Initialize configuration manager
        self.config_manager = ConfigManager(CONFIG_DIR)
        
        # Load configurations
        self.projects = self.config_manager.load_projects()
        self.settings = self.config_manager.load_settings()
        
        # Initialize managers
        self.project_manager = ProjectManager(self.projects)
        self.tmux_manager = TmuxManager(self.settings)
        
        self.current_project = None
    
    def run(self):
        """Main execution flow"""
        # Ensure config files exist
        if not self.config_manager.ensure_config_files_exist():
            return
        
        # Check if we have any projects
        if not self.projects:
            print("\nNo projects configured.")
            print(f"Please edit {CONFIG_DIR / 'projects.yaml'} to add your projects.")
            return
        
        # Select project
        project_key = self.project_manager.select_project()
        if not project_key:
            print("\nExiting Claude Manager.")
            return
        
        # Validate project
        if not self.project_manager.validate_project(project_key):
            print(f"\nProject '{project_key}' has configuration errors.")
            return
        
        self.current_project = project_key
        project = self.project_manager.get_project_info(project_key)
        
        print(f"\n✨ Starting {project['name']}...\n")
        
        # Setup tmux session/window
        self.setup_workspace(project_key, project)
    
    def setup_workspace(self, project_key: str, project: dict):
        """Setup the complete workspace for a project"""
        # Check if session exists before creating window
        session_existed = self.tmux_manager.session_exists()
        
        # Create tmux window
        window_target = self.tmux_manager.create_window(project, project_key)
        if not window_target:
            print("Failed to create tmux window.")
            return
        
        # Setup the three-pane layout
        self.tmux_manager.setup_window_layout(window_target, project, project_key)
        
        print(f"✨ Claude Manager setup complete!")
        
        # Handle automatic attach/switch
        self.tmux_manager.auto_attach_or_switch(window_target, session_existed)
    
    def list_projects(self):
        """List all available projects"""
        self.project_manager.list_projects()
    
    def get_config_info(self):
        """Get configuration information"""
        return self.config_manager.get_config_info()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude Manager - Personal AI Assistant")
    parser.add_argument("--project", "-p", help="Project key to start directly")
    parser.add_argument("--list", "-l", action="store_true", help="List available projects")
    parser.add_argument("--config-info", action="store_true", help="Show configuration information")
    parser.add_argument("--new", help="Create a new project interactively")
    
    args = parser.parse_args()
    
    try:
        manager = ClaudeManager()
        
        if args.config_info:
            info = manager.get_config_info()
            print("Configuration Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            return
        
        if args.new:
            # Create new project
            from modules.project_creator import create_project_interactive
            success = create_project_interactive(CONFIG_DIR, args.new)
            if success:
                print(f"\\n🎉 Project '{args.new}' created successfully!")
                print("You can now use it with: python3 claude_manager.py")
            return
        
        if args.list:
            manager.list_projects()
            return
        
        if args.project:
            if args.project in manager.projects:
                if not manager.project_manager.validate_project(args.project):
                    print(f"Error: Project '{args.project}' has configuration errors.")
                    return
                
                manager.current_project = args.project
                project = manager.project_manager.get_project_info(args.project)
                print(f"\n✨ Starting {project['name']}...\n")
                manager.setup_workspace(args.project, project)
            else:
                print(f"Error: Project '{args.project}' not found.")
                print("Use --list to see available projects.")
        else:
            manager.run()
            
    except KeyboardInterrupt:
        print("\n\nClaude Manager interrupted.")
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    main()
