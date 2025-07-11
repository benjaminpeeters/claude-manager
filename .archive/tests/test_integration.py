#!/usr/bin/env python3
"""
Test Integration Example - How to integrate dynamic selectors with ProjectManager
Run with: python3 test_integration.py
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict

# Add the parent directory to sys.path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules.project_manager import ProjectManager
    from modules.config_manager import ConfigManager
except ImportError:
    print("❌ Could not import claude-manager modules")
    sys.exit(1)

# Import our test selectors
from test_fzf_selector import fzf_select_project
from test_textual_selector import textual_select_project
from test_curses_selector import curses_select_project

class EnhancedProjectManager(ProjectManager):
    """Enhanced ProjectManager with dynamic selection options"""
    
    def __init__(self, projects: Dict):
        super().__init__(projects)
        self.selection_methods = {
            'fzf': self._fzf_select,
            'textual': self._textual_select,
            'curses': self._curses_select,
            'numbers': self._number_select  # Original method
        }
    
    def select_project_dynamic(self, method: str = 'auto') -> Optional[str]:
        """Select project using specified method with auto-fallback"""
        
        if method == 'auto':
            # Auto-detect best available method
            method = self._detect_best_method()
        
        if method not in self.selection_methods:
            print(f"Unknown selection method: {method}")
            method = 'numbers'  # Fallback to numbers
        
        print(f"Using selection method: {method}")
        
        try:
            return self.selection_methods[method]()
        except Exception as e:
            print(f"Error with {method} selection: {e}")
            if method != 'numbers':
                print("Falling back to number selection...")
                return self._number_select()
            return None
    
    def _detect_best_method(self) -> str:
        """Detect the best available selection method"""
        
        # Check for FZF (fastest and most reliable)
        try:
            import subprocess
            subprocess.run(['fzf', '--version'], capture_output=True, check=True)
            return 'fzf'
        except:
            pass
        
        # Check for Textual (most feature-rich)
        try:
            import textual
            return 'textual'
        except ImportError:
            pass
        
        # Check for Curses (built-in, always available)
        try:
            import curses
            return 'curses'
        except ImportError:
            pass
        
        # Fallback to numbers
        return 'numbers'
    
    def _fzf_select(self) -> Optional[str]:
        """FZF selection method"""
        return fzf_select_project(self.projects)
    
    def _textual_select(self) -> Optional[str]:
        """Textual selection method"""
        return textual_select_project(self.projects)
    
    def _curses_select(self) -> Optional[str]:
        """Curses selection method"""
        return curses_select_project(self.projects)
    
    def _number_select(self) -> Optional[str]:
        """Original number-based selection method"""
        return self.select_project()

def load_real_projects() -> Dict:
    """Load actual projects from config if available"""
    try:
        config_dir = Path(__file__).parent.parent / "config"
        config_manager = ConfigManager(config_dir)
        projects = config_manager.load_projects()
        if projects:
            return projects
    except:
        pass
    
    # Fallback to sample projects
    return {
        "pik_research": {
            "name": "PIK Research (REMIND/MSGM)",
            "directory": "/home/bpeeters/remind",
            "notes_file": "notes/work/notes_remind.md",
            "tags": ["research", "pik", "remind"]
        },
        "personal_dev": {
            "name": "Personal Development",
            "directory": "/home/bpeeters/personal",
            "notes_file": "notes/personal/habits.md",
            "tags": ["personal", "habits"]
        },
        "chinese_learning": {
            "name": "Chinese Learning",
            "directory": "/home/bpeeters/chinese",
            "notes_file": "notes/learning/chinese.md",
            "tags": ["learning", "chinese"]
        },
        "general_tasks": {
            "name": "General Tasks",
            "directory": "/home/bpeeters/MEGA",
            "notes_file": "notes/buffer.md",
            "tags": ["general", "tasks"]
        }
    }

def test_method(method_name: str, manager: EnhancedProjectManager):
    """Test a specific selection method"""
    print(f"\n🧪 Testing {method_name.upper()} method")
    print("-" * 40)
    
    try:
        selected = manager.select_project_dynamic(method_name)
        if selected:
            project_info = manager.get_project_info(selected)
            print(f"✓ Selected: {selected}")
            print(f"  Name: {project_info['name']}")
            print(f"  Directory: {project_info['directory']}")
            print(f"  Tags: {', '.join(project_info.get('tags', []))}")
        else:
            print("↩ No project selected")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🧪 Testing Integration with ProjectManager")
    print("=" * 50)
    
    # Load projects
    projects = load_real_projects()
    manager = EnhancedProjectManager(projects)
    
    print(f"Loaded {len(projects)} projects:")
    for key, project in projects.items():
        status = "✓" if manager.validate_project(key) else "✗"
        print(f"  {status} {key}: {project['name']}")
    
    # Test auto-detection
    print(f"\n🔍 Auto-detected best method: {manager._detect_best_method()}")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 50)
        print("Choose a selection method to test:")
        print("1. Auto-detect (recommended)")
        print("2. FZF")
        print("3. Textual")
        print("4. Curses")  
        print("5. Numbers (original)")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            test_method('auto', manager)
        elif choice == '2':
            test_method('fzf', manager)
        elif choice == '3':
            test_method('textual', manager)
        elif choice == '4':
            test_method('curses', manager)
        elif choice == '5':
            test_method('numbers', manager)
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()