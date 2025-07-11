"""
Project Creator - Interactive creation of new projects with --new flag
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional

class ProjectCreator:
    """Handle creation of new projects interactively"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.projects_file = config_dir / "projects.yaml"
        self.contexts_dir = config_dir / "contexts"
        
        # Ensure contexts directory exists
        self.contexts_dir.mkdir(exist_ok=True)
        
        self.categories = ["PIK", "Publications", "Projects", "Flows", "Life", "General"]
    
    def create_new_project(self, project_name: str) -> bool:
        """
        Create a new project interactively
        
        Args:
            project_name: The name/key for the new project
            
        Returns:
            True if project was created successfully
        """
        print(f"\n🤖 Creating new project: {project_name}")
        print("=" * 50)
        
        # Load existing projects
        existing_projects = self._load_existing_projects()
        
        # Check if project already exists
        if project_name in existing_projects:
            print(f"❌ Project '{project_name}' already exists!")
            return False
        
        # Collect project information
        project_info = self._collect_project_info(project_name)
        if not project_info:
            print("❌ Project creation cancelled.")
            return False
        
        # Create context file
        context_content = self._generate_context_content(project_name, project_info)
        context_path = self.contexts_dir / f"context_{project_name}.md"
        
        try:
            with open(context_path, 'w') as f:
                f.write(context_content)
            print(f"✅ Created context file: {context_path}")
        except Exception as e:
            print(f"❌ Failed to create context file: {e}")
            return False
        
        # Add project to YAML
        try:
            existing_projects[project_name] = {
                "name": project_info["display_name"],
                "category": project_info["category"],
                "directory": project_info["directory"],
                "todoist_project": project_info["todoist_project"]
            }
            
            self._save_projects(existing_projects)
            print(f"✅ Added project to configuration")
            
        except Exception as e:
            print(f"❌ Failed to save project configuration: {e}")
            return False
        
        print(f"\n🎉 Project '{project_name}' created successfully!")
        print(f"📁 Context: {context_path}")
        print(f"📋 Category: {project_info['category']}")
        print(f"📌 Todoist: {project_info['todoist_project']}")
        
        return True
    
    def _load_existing_projects(self) -> Dict:
        """Load existing projects from YAML"""
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}
    
    def _save_projects(self, projects: Dict):
        """Save projects to YAML file"""
        with open(self.projects_file, 'w') as f:
            f.write("# Claude Manager Projects Configuration - New Schema\n")
            f.write("# Categories: PIK, Publications, Projects, Flows, Life, General\n")
            f.write("# All projects have universal todoist-mcp access\n")
            f.write("# Context files are in config/contexts/\n\n")
            yaml.dump(projects, f, default_flow_style=False, sort_keys=False)
    
    def _collect_project_info(self, project_name: str) -> Optional[Dict]:
        """Collect project information interactively"""
        try:
            # Display name
            display_name = input(f"Display name for '{project_name}' [default: {project_name.title()}]: ").strip()
            if not display_name:
                display_name = project_name.title()
            
            # Category
            print(f"\nAvailable categories: {', '.join(self.categories)}")
            category = self._get_category()
            if not category:
                return None
            
            # Directory
            directory = self._get_directory()
            if not directory:
                return None
            
            # Todoist project
            todoist_project = input("\\nTodoist project name [default: Inbox]: ").strip()
            if not todoist_project:
                todoist_project = "Inbox"
            
            # Context files
            context_files = self._get_context_files()
            
            # Context description
            context_description = input("\\nBrief description for context file: ").strip()
            if not context_description:
                context_description = f"Context and summary for {display_name}"
            
            return {
                "display_name": display_name,
                "category": category,
                "directory": directory,
                "todoist_project": todoist_project,
                "context_files": context_files,
                "context_description": context_description
            }
            
        except (KeyboardInterrupt, EOFError):
            print("\\n\\nCancelled by user.")
            return None
    
    def _get_category(self) -> Optional[str]:
        """Get category selection"""
        while True:
            try:
                print("\\nSelect category:")
                for i, cat in enumerate(self.categories, 1):
                    print(f"  {i}. {cat}")
                
                choice = input("\\nEnter category number: ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(self.categories):
                    return self.categories[choice_num - 1]
                else:
                    print("Invalid choice. Please try again.")
                    
            except (ValueError, KeyboardInterrupt, EOFError):
                return None
    
    def _get_directory(self) -> Optional[str]:
        """Get and validate project directory"""
        while True:
            try:
                directory = input("\\nProject directory path: ").strip()
                if not directory:
                    print("Directory path is required.")
                    continue
                
                # Expand home directory
                directory = str(Path(directory).expanduser())
                
                # Check if directory exists
                dir_path = Path(directory)
                if not dir_path.exists():
                    create = input(f"Directory doesn't exist. Create '{directory}'? [y/N]: ").strip().lower()
                    if create in ['y', 'yes']:
                        try:
                            dir_path.mkdir(parents=True, exist_ok=True)
                            print(f"✅ Created directory: {directory}")
                        except Exception as e:
                            print(f"❌ Failed to create directory: {e}")
                            continue
                    else:
                        continue
                
                return directory
                
            except (KeyboardInterrupt, EOFError):
                return None
    
    def _get_context_files(self) -> List[str]:
        """Get context files list"""
        context_files = []
        print("\\n📄 Context files (press Enter when done):")
        print("   Relative paths from /home/bpeeters/MEGA/")
        
        while True:
            try:
                file_path = input(f"   Context file {len(context_files) + 1} [Enter to finish]: ").strip()
                if not file_path:
                    break
                context_files.append(file_path)
            except (KeyboardInterrupt, EOFError):
                break
        
        return context_files
    
    def _generate_context_content(self, project_name: str, project_info: Dict) -> str:
        """Generate content for the context file"""
        context_section = ""
        if project_info["context_files"]:
            context_section = "\\n## Context Files\\n\\n"
            for file_path in project_info["context_files"]:
                context_section += f"- `{file_path}`\\n"
        
        content = f"""# {project_info['display_name']} - Context

## Overview

{project_info['context_description']}

## Project Details

- **Category**: {project_info['category']}
- **Directory**: `{project_info['directory']}`
- **Todoist Project**: {project_info['todoist_project']}

## Key Information

<!-- Add key information about this project here -->

{context_section}

## Notes

<!-- Add project-specific notes here -->

---
*This file serves as the main context and summary guide for Claude Manager.*
*It is automatically loaded when this project is selected.*
"""
        
        return content

def create_project_interactive(config_dir: Path, project_name: str) -> bool:
    """
    Main function to create a project interactively
    
    Args:
        config_dir: Configuration directory path
        project_name: Name of the project to create
        
    Returns:
        True if successful
    """
    creator = ProjectCreator(config_dir)
    return creator.create_new_project(project_name)

def main():
    """Test project creation"""
    from pathlib import Path
    
    config_dir = Path("/home/bpeeters/MEGA/manager/config")
    
    print("🧪 Testing Project Creator")
    print("=" * 30)
    
    test_project = "test_project"
    success = create_project_interactive(config_dir, test_project)
    
    if success:
        print(f"\\n✅ Successfully created project: {test_project}")
    else:
        print(f"\\n❌ Failed to create project: {test_project}")

if __name__ == "__main__":
    main()