"""
Config Manager - Handle configuration loading, saving, and defaults
"""

import yaml
from pathlib import Path
from typing import Dict


class ConfigManager:
    """Manages configuration files and settings"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.projects_file = config_dir / "projects.yaml"
        self.settings_file = config_dir / "settings.yaml"
    
    def load_projects(self) -> Dict:
        """Load project configurations from projects.yaml"""
        if self.projects_file.exists():
            with open(self.projects_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def load_settings(self) -> Dict:
        """Load general settings from settings.yaml"""
        if self.settings_file.exists():
            with open(self.settings_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return self.get_default_settings()
    
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
    
    def save_projects(self, projects: Dict):
        """Save project configurations"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.projects_file, 'w') as f:
            yaml.dump(projects, f, default_flow_style=False)
    
    def save_settings(self, settings: Dict):
        """Save settings configuration"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False)
    
    def create_example_config(self):
        """Create an example projects.yaml file"""
        example_projects = {
            "example_project": {
                "name": "Example Project",
                "category": "Projects",
                "directory": "/home/bpeeters/MEGA",
                "todoist_project": "Example Project"
            },
            "general": {
                "name": "General Tasks",
                "category": "General",
                "directory": "/home/bpeeters/MEGA",
                "todoist_project": "Inbox"
            }
        }
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.projects_file, 'w') as f:
            f.write("# Claude Manager Projects Configuration - New Schema\n")
            f.write("# Categories: PIK, Publications, Projects, Flows, Life, General\n")
            f.write("# Context files are in config/contexts/\n")
            f.write("# Context files are specified in individual context files\n\n")
            yaml.dump(example_projects, f, default_flow_style=False)
            f.write("\n# Add more projects as needed\n")
            f.write("# Available categories: PIK, Publications, Projects, Flows, Life, General\n")
    
    def ensure_config_files_exist(self) -> bool:
        """Ensure configuration files exist, return True if projects exist"""
        # Create settings if missing
        if not self.settings_file.exists():
            self.save_settings(self.get_default_settings())
        
        # Check projects file
        if not self.projects_file.exists():
            print("\nNo projects.yaml found. Creating an example configuration...")
            self.create_example_config()
            print(f"Please edit {self.projects_file} to add your projects.")
            return False
        
        return True
    
    def get_config_info(self) -> Dict:
        """Get information about configuration files"""
        return {
            "config_dir": str(self.config_dir),
            "projects_file": str(self.projects_file),
            "settings_file": str(self.settings_file),
            "projects_exists": self.projects_file.exists(),
            "settings_exists": self.settings_file.exists()
        }