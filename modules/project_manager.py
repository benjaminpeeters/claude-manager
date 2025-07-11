"""
Project Manager - Handle project selection and configuration
"""

from typing import Dict, Optional, List
from pathlib import Path


class ProjectManager:
    """Manages project selection and validation"""
    
    def __init__(self, projects: Dict):
        self.projects = projects
    
    def select_project(self) -> Optional[str]:
        """Interactive project selection using category-based Textual interface"""
        try:
            from .category_selector import select_project_with_categories
            return select_project_with_categories(self.projects)
        except ImportError:
            print("Warning: Textual not available, falling back to number selection")
            return self._fallback_select_project()
    
    def _fallback_select_project(self) -> Optional[str]:
        """Fallback project selection using numbers (original method)"""
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
    
    def validate_project(self, project_key: str) -> bool:
        """Validate that a project configuration is valid"""
        if project_key not in self.projects:
            return False
        
        project = self.projects[project_key]
        
        # Check required fields
        required_fields = ["name", "directory"]
        for field in required_fields:
            if field not in project:
                print(f"Project '{project_key}' missing required field: {field}")
                return False
        
        # Check if directory exists
        project_dir = Path(project["directory"])
        if not project_dir.exists():
            print(f"Project directory does not exist: {project_dir}")
            return False
        
        return True
    
    def get_project_info(self, project_key: str) -> Dict:
        """Get project information with validation"""
        if not self.validate_project(project_key):
            raise ValueError(f"Invalid project: {project_key}")
        
        return self.projects[project_key]
    
    def list_projects(self) -> None:
        """Print list of available projects"""
        print("\nAvailable projects:")
        for key, project in self.projects.items():
            status = "✓" if self.validate_project(key) else "✗"
            print(f"  {status} {key}: {project.get('name', 'Unknown')}")
    
    def get_project_category(self, project_key: str) -> str:
        """Get category for a project"""
        if project_key not in self.projects:
            return "General"
        return self.projects[project_key].get("category", "General")
    
    def get_project_todoist(self, project_key: str) -> str:
        """Get Todoist project for a project"""
        if project_key not in self.projects:
            return "Inbox"
        return self.projects[project_key].get("todoist_project", "Inbox")
    
    def get_project_mcp_access(self, project_key: str) -> List[str]:
        """Get MCP servers for a project - all projects now use todoist-mcp"""
        # All projects now have universal todoist-mcp access
        return ["todoist-mcp"]