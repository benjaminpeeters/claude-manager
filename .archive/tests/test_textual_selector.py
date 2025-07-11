#!/usr/bin/env python3
"""
Test Textual-based project selector
Run with: python3 test_textual_selector.py
"""

import sys
from typing import Optional, Dict

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Vertical
    from textual.widgets import Header, Footer, ListView, ListItem, Label
    from textual.binding import Binding
    from textual.reactive import reactive
except ImportError:
    print("❌ Textual not available. Install with: pip install textual")
    sys.exit(1)

# Sample project data
SAMPLE_PROJECTS = {
    "pik_research": {
        "name": "PIK Research (REMIND/MSGM)",
        "directory": "/home/bpeeters/remind",
        "tags": ["research", "pik", "remind"],
        "valid": True
    },
    "personal_dev": {
        "name": "Personal Development",
        "directory": "/home/bpeeters/personal",
        "tags": ["personal", "habits"],
        "valid": True
    },
    "chinese_learning": {
        "name": "Chinese Learning",
        "directory": "/home/bpeeters/chinese",
        "tags": ["learning", "chinese"],
        "valid": False  # Example of invalid project
    },
    "general_tasks": {
        "name": "General Tasks",
        "directory": "/home/bpeeters/MEGA",
        "tags": ["general", "tasks"],
        "valid": True
    }
}

class ProjectSelectorApp(App):
    """Textual app for project selection"""
    
    CSS = """
    ListView {
        height: 1fr;
        margin: 1;
    }
    
    .project-item {
        padding: 1;
        margin: 0 1;
    }
    
    .project-name {
        text-style: bold;
    }
    
    .project-valid {
        color: $success;
    }
    
    .project-invalid {
        color: $error;
    }
    
    .project-tags {
        color: $text-muted;
        text-style: italic;
    }
    
    .project-directory {
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        ("enter", "select", "Select"),
    ]
    
    selected_project: reactive[Optional[str]] = reactive(None)
    
    def __init__(self, projects: Dict):
        super().__init__()
        self.projects = projects
        self.project_keys = list(projects.keys())
        self.selected_project = None
    
    def compose(self) -> ComposeResult:
        """Compose the app layout"""
        yield Header()
        yield Container(
            Label("🤖 Claude Manager - Select Project Focus", classes="project-name"),
            ListView(
                *[self.create_project_item(key) for key in self.project_keys],
                id="project_list"
            ),
            id="main_container"
        )
        yield Footer()
    
    def create_project_item(self, project_key: str) -> ListItem:
        """Create a list item for a project"""
        project = self.projects[project_key]
        
        # Status indicator
        status = "✓" if project.get("valid", True) else "✗"
        status_class = "project-valid" if project.get("valid", True) else "project-invalid"
        
        # Format tags
        tags_str = ", ".join(project.get("tags", []))
        
        # Create the item content
        content = Vertical(
            Label(f"{status} {project['name']}", classes=f"project-name {status_class}"),
            Label(f"Directory: {project['directory']}", classes="project-directory"),
            Label(f"Tags: {tags_str}", classes="project-tags") if tags_str else Label(""),
            classes="project-item"
        )
        
        return ListItem(content, id=project_key)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection"""
        if event.item and event.item.id:
            self.selected_project = str(event.item.id)
            self.exit(self.selected_project)
    
    def action_select(self) -> None:
        """Handle Enter key selection"""
        list_view = self.query_one("#project_list", ListView)
        if list_view.highlighted_child:
            project_key = list_view.highlighted_child.id
            if project_key:
                self.selected_project = str(project_key)
                self.exit(self.selected_project)
    
    def action_quit(self) -> None:
        """Handle quit action"""
        self.exit(None)

def textual_select_project(projects: Dict) -> Optional[str]:
    """Use Textual to select a project with arrow keys"""
    try:
        app = ProjectSelectorApp(projects)
        return app.run()
    except Exception as e:
        print(f"Error with Textual selection: {e}")
        return None

def main():
    print("🧪 Testing Textual Project Selector")
    print("=" * 40)
    
    try:
        from textual import __version__
        print(f"✓ Textual is available (v{__version__})")
    except ImportError:
        print("✗ Textual is not available")
        sys.exit(1)
    
    print("\nStarting Textual selector...")
    print("(Use arrow keys to navigate, Enter to select, Esc/q to exit)")
    
    selected_project = textual_select_project(SAMPLE_PROJECTS)
    
    if selected_project:
        project_info = SAMPLE_PROJECTS[selected_project]
        print(f"\n✓ Selected project: {selected_project}")
        print(f"  Name: {project_info['name']}")
        print(f"  Directory: {project_info['directory']}")
        print(f"  Tags: {', '.join(project_info['tags'])}")
        print(f"  Valid: {'Yes' if project_info.get('valid', True) else 'No'}")
    else:
        print("\n↩ No project selected (cancelled)")

if __name__ == "__main__":
    main()