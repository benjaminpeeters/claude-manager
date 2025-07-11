"""
Category Selector - Two-step Textual interface for category and project selection
"""

import sys
from typing import Optional, Dict, List, Tuple

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Vertical
    from textual.widgets import Header, Footer, ListView, ListItem, Label
    from textual.binding import Binding
    from textual.reactive import reactive
except ImportError:
    print("❌ Textual not available. Install with: pip install textual")
    sys.exit(1)

class CategorySelectorApp(App):
    """Two-step Textual app for category and project selection"""
    
    CSS = """
    ListView {
        height: 1fr;
        margin: 1;
    }
    
    .category-item, .project-item {
        padding: 1;
        margin: 0 1;
    }
    
    .item-name {
        text-style: bold;
    }
    
    .item-valid {
        color: $success;
    }
    
    .item-invalid {
        color: $error;
    }
    
    .item-description {
        color: $text-muted;
        text-style: italic;
    }
    
    .item-directory {
        color: $text-muted;
    }
    
    .special-option {
        color: $warning;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "back_or_quit", "Back/Quit"),
        Binding("enter", "select", "Select"),
        Binding("space", "select", "Select"),
    ]
    
    selected_project: reactive[Optional[str]] = reactive(None)
    current_step: reactive[str] = reactive("category")  # "category" or "project"
    current_category: reactive[Optional[str]] = reactive(None)
    
    def __init__(self, projects: Dict):
        super().__init__()
        self.projects = projects
        self.categories = self._get_categories()
        self.selected_project = None
        self.current_step = "category"
        self.current_category = None
    
    def _get_categories(self) -> Dict[str, List[str]]:
        """Group projects by category (supports comma-separated categories)"""
        categories = {}
        for project_key, project in self.projects.items():
            category_str = project.get("category", "General")
            
            # Handle comma-separated categories
            project_categories = [cat.strip() for cat in category_str.split(",")]
            
            for category in project_categories:
                if category not in categories:
                    categories[category] = []
                categories[category].append(project_key)
        return categories
    
    def compose(self) -> ComposeResult:
        """Compose the app layout"""
        yield Header()
        yield Container(id="main_container")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted"""
        self._update_view()
    
    def watch_current_step(self, step: str) -> None:
        """Called when current_step changes"""
        self._update_view()
    
    def watch_current_category(self, category: str) -> None:
        """Called when current_category changes"""
        if self.current_step == "project":
            self._update_view()
    
    def _update_view(self) -> None:
        """Update the view content"""
        try:
            main_container = self.query_one("#main_container")
            main_container.remove_children()
            content = self._create_current_view()
            main_container.mount(content)
            
            # Set focus on the new ListView
            try:
                list_view = self.query_one("#selection_list", ListView)
                list_view.focus()
            except Exception:
                pass
        except Exception:
            pass
    
    def _create_current_view(self) -> Container:
        """Create the current view based on step"""
        if self.current_step == "category":
            return self._create_category_view()
        else:
            return self._create_project_view()
    
    def _create_category_view(self) -> Container:
        """Create category selection view"""
        items = []
        
        # Add categories
        for category in sorted(self.categories.keys()):
            if category != "General":  # General will be added separately
                project_count = len(self.categories[category])
                content = Vertical(
                    Label(f"📁 {category}", classes="item-name item-valid"),
                    Label(f"{project_count} project{'s' if project_count != 1 else ''}", classes="item-description"),
                    classes="category-item"
                )
                items.append(ListItem(content, id=f"cat_{category}"))
        
        # Add General category
        if "General" in self.categories:
            project_count = len(self.categories["General"])
            content = Vertical(
                Label("📋 General", classes="item-name item-valid"),
                Label(f"{project_count} project{'s' if project_count != 1 else ''}", classes="item-description"),
                classes="category-item"
            )
            items.append(ListItem(content, id="cat_General"))
        
        # Add Exit option
        exit_content = Vertical(
            Label("🚪 Exit", classes="item-name special-option"),
            Label("Close Claude Manager", classes="item-description"),
            classes="category-item"
        )
        items.append(ListItem(exit_content, id="exit"))
        
        return Container(
            Label("🤖 Claude Manager - Select Category", classes="item-name"),
            ListView(*items, id="selection_list"),
            id="view_container"
        )
    
    def _create_project_view(self) -> Container:
        """Create project selection view"""
        items = []
        category_projects = self.categories.get(self.current_category, [])
        
        # Add projects in current category
        for project_key in sorted(category_projects):
            project = self.projects[project_key]
            
            # Check if project directory exists for validation
            from pathlib import Path
            is_valid = Path(project["directory"]).exists()
            status = "✓" if is_valid else "✗"
            status_class = "item-valid" if is_valid else "item-invalid"
            
            # Get todoist project
            todoist_project = project.get("todoist_project", "No Todoist project")
            
            content = Vertical(
                Label(f"{status} {project['name']}", classes=f"item-name {status_class}"),
                Label(f"Directory: {project['directory']}", classes="item-directory"),
                Label(f"Todoist: {todoist_project}", classes="item-description"),
                classes="project-item"
            )
            items.append(ListItem(content, id=project_key))
        
        # Add General option (if not already in General category)
        if self.current_category != "General" and "General" in self.categories:
            general_content = Vertical(
                Label("📋 General Tasks", classes="item-name special-option"),
                Label("Switch to general tasks", classes="item-description"),
                classes="project-item"
            )
            items.append(ListItem(general_content, id="general_direct"))
        
        # Add Back option
        back_content = Vertical(
            Label("⬅️  Back to Categories", classes="item-name special-option"),
            Label("Return to category selection", classes="item-description"),
            classes="project-item"
        )
        items.append(ListItem(back_content, id="back"))
        
        # Add Exit option
        exit_content = Vertical(
            Label("🚪 Exit", classes="item-name special-option"),
            Label("Close Claude Manager", classes="item-description"),
            classes="project-item"
        )
        items.append(ListItem(exit_content, id="exit"))
        
        return Container(
            Label(f"🤖 Claude Manager - {self.current_category} Projects", classes="item-name"),
            ListView(*items, id="selection_list"),
            id="view_container"
        )
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection"""
        if event.item and event.item.id:
            self._handle_selection(str(event.item.id))
    
    def action_select(self) -> None:
        """Handle Enter key selection"""
        try:
            list_view = self.query_one("#selection_list", ListView)
            if list_view.highlighted_child and list_view.highlighted_child.id:
                selection_id = str(list_view.highlighted_child.id)
                self._handle_selection(selection_id)
            elif hasattr(list_view, 'index') and list_view.index is not None:
                # Fallback: use index to get selection
                children = list(list_view.children)
                if 0 <= list_view.index < len(children):
                    child = children[list_view.index]
                    if hasattr(child, 'id') and child.id:
                        self._handle_selection(str(child.id))
        except Exception as e:
            # Debug: print error (this will show in terminal after exit)
            pass
    
    def _handle_selection(self, selection_id: str):
        """Handle a selection based on current step"""
        # Debug info (will be printed to terminal after exit)
        debug_info = f"Selection: {selection_id}, Step: {self.current_step}, Category: {self.current_category}"
        
        if selection_id == "exit":
            self.exit(None)
        elif selection_id == "back":
            self._go_back()
        elif selection_id == "general_direct":
            # Direct selection of general from project view
            if "general" in self.projects:
                self.selected_project = "general"
                self.exit("general")
        elif self.current_step == "category":
            if selection_id.startswith("cat_"):
                category = selection_id[4:]  # Remove "cat_" prefix
                self._go_to_projects(category)
        else:  # project step
            if selection_id in self.projects:
                self.selected_project = selection_id
                self.exit(selection_id)
            else:
                # Debug: selection not found in projects
                available_projects = list(self.projects.keys())
                self.app.bell()  # Audio feedback for failed selection
    
    def _go_to_projects(self, category: str):
        """Navigate to project selection for a category"""
        self.current_category = category
        self.current_step = "project"
        # The watch_current_step method will handle the view update
    
    def _go_back(self):
        """Go back to category selection"""
        self.current_step = "category"
        self.current_category = None
        # The watch_current_step method will handle the view update
    
    def action_back_or_quit(self) -> None:
        """Handle Escape key - back or quit"""
        if self.current_step == "project":
            self._go_back()
        else:
            self.exit(None)
    
    def action_quit(self) -> None:
        """Handle quit action"""
        self.exit(None)

def select_project_with_categories(projects: Dict) -> Optional[str]:
    """Use Textual to select a project with category navigation"""
    try:
        app = CategorySelectorApp(projects)
        return app.run()
    except Exception as e:
        print(f"Error with category selection: {e}")
        return None

def main():
    """Test the category selector"""
    # Sample projects for testing
    sample_projects = {
        "remind": {
            "name": "REMIND Model",
            "category": "PIK",
            "directory": "/home/bpeeters/remind",
            "todoist_project": "PIK Research"
        },
        "msg": {
            "name": "MSG Model",
            "category": "PIK", 
            "directory": "/home/bpeeters/msg",
            "todoist_project": "PIK Research"
        },
        "damage_paper": {
            "name": "Damage Capital Paper",
            "category": "Publications",
            "directory": "/home/bpeeters/damage_capital",
            "todoist_project": "Publications"
        },
        "scibatoo": {
            "name": "Scibatoo Platform",
            "category": "Projects",
            "directory": "/home/bpeeters/scibatoo",
            "todoist_project": "Side Projects"
        },
        "claude_manager": {
            "name": "Claude Manager",
            "category": "Flows",
            "directory": "/home/bpeeters/MEGA/manager",
            "todoist_project": "Productivity Tools"
        },
        "health": {
            "name": "Health & Wellness",
            "category": "Life",
            "directory": "/home/bpeeters/MEGA",
            "todoist_project": "Health & Fitness"
        },
        "general": {
            "name": "General Tasks",
            "category": "General",
            "directory": "/home/bpeeters/MEGA",
            "todoist_project": "Inbox"
        }
    }
    
    print("🧪 Testing Category Selector")
    selected = select_project_with_categories(sample_projects)
    if selected:
        print(f"Selected project: {selected}")
    else:
        print("No project selected")

if __name__ == "__main__":
    main()