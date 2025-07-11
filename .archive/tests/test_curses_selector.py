#!/usr/bin/env python3
"""
Test Curses-based project selector
Run with: python3 test_curses_selector.py
"""

import curses
import sys
from typing import Optional, Dict, List

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

class CursesProjectSelector:
    """Curses-based project selector"""
    
    def __init__(self, projects: Dict):
        self.projects = projects
        self.project_keys = list(projects.keys())
        self.current_selection = 0
        self.selected_project = None
    
    def draw_menu(self, stdscr):
        """Draw the project selection menu"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = "🤖 Claude Manager - Select Project Focus"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Instructions
        instructions = "Use ↑/↓ arrows to navigate, Enter to select, Esc/q to exit"
        stdscr.addstr(2, (width - len(instructions)) // 2, instructions)
        
        # Draw projects
        start_y = 4
        for i, key in enumerate(self.project_keys):
            project = self.projects[key]
            
            # Status indicator
            status = "✓" if project.get("valid", True) else "✗"
            
            # Main project line
            project_line = f"{status} {project['name']}"
            
            # Tags line
            tags_str = ", ".join(project.get("tags", []))
            tags_line = f"   Tags: {tags_str}" if tags_str else ""
            
            # Directory line
            dir_line = f"   Directory: {project['directory']}"
            
            # Calculate colors
            if i == self.current_selection:
                # Highlighted item
                attr = curses.A_REVERSE | curses.A_BOLD
                tag_attr = curses.A_REVERSE
            else:
                # Normal item
                attr = curses.A_BOLD if project.get("valid", True) else curses.A_DIM
                tag_attr = curses.A_DIM
            
            # Draw the project item
            y_pos = start_y + i * 4
            if y_pos < height - 2:
                stdscr.addstr(y_pos, 2, project_line, attr)
                if tags_line and y_pos + 1 < height - 2:
                    stdscr.addstr(y_pos + 1, 2, tags_line, tag_attr)
                if y_pos + 2 < height - 2:
                    stdscr.addstr(y_pos + 2, 2, dir_line, tag_attr)
        
        # Draw exit option
        exit_y = start_y + len(self.project_keys) * 4
        if exit_y < height - 2:
            exit_attr = curses.A_REVERSE | curses.A_BOLD if self.current_selection == len(self.project_keys) else curses.A_NORMAL
            stdscr.addstr(exit_y, 2, "Exit", exit_attr)
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Main selector loop"""
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable special keys
        
        # Color setup (if available)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
        
        max_selection = len(self.project_keys)  # includes exit option
        
        while True:
            self.draw_menu(stdscr)
            
            # Get user input
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                # Move up
                self.current_selection = (self.current_selection - 1) % (max_selection + 1)
            elif key == curses.KEY_DOWN:
                # Move down
                self.current_selection = (self.current_selection + 1) % (max_selection + 1)
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key
                # Select current item
                if self.current_selection < len(self.project_keys):
                    self.selected_project = self.project_keys[self.current_selection]
                break
            elif key in [27, ord('q'), ord('Q')]:  # Escape or q
                # Exit
                break
            elif key == curses.KEY_RESIZE:
                # Handle terminal resize
                continue
        
        return self.selected_project

def curses_select_project(projects: Dict) -> Optional[str]:
    """Use curses to select a project with arrow keys"""
    try:
        selector = CursesProjectSelector(projects)
        return curses.wrapper(selector.run)
    except Exception as e:
        print(f"Error with curses selection: {e}")
        return None

def main():
    print("🧪 Testing Curses Project Selector")
    print("=" * 40)
    
    try:
        # Test curses availability
        curses.wrapper(lambda stdscr: None)
        print("✓ Curses is available")
    except Exception as e:
        print(f"✗ Curses is not available: {e}")
        sys.exit(1)
    
    print("\nStarting curses selector...")
    print("(Use arrow keys to navigate, Enter to select, Esc/q to exit)")
    input("Press Enter to continue...")
    
    selected_project = curses_select_project(SAMPLE_PROJECTS)
    
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