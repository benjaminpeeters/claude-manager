#!/usr/bin/env python3
"""
Test FZF-based project selector
Run with: python3 test_fzf_selector.py
"""

import subprocess
import sys
from typing import Optional, Dict, List

# Sample project data
SAMPLE_PROJECTS = {
    "pik_research": {
        "name": "PIK Research (REMIND/MSGM)",
        "directory": "/home/bpeeters/remind",
        "tags": ["research", "pik", "remind"]
    },
    "personal_dev": {
        "name": "Personal Development",
        "directory": "/home/bpeeters/personal",
        "tags": ["personal", "habits"]
    },
    "chinese_learning": {
        "name": "Chinese Learning",
        "directory": "/home/bpeeters/chinese",
        "tags": ["learning", "chinese"]
    },
    "general_tasks": {
        "name": "General Tasks",
        "directory": "/home/bpeeters/MEGA",
        "tags": ["general", "tasks"]
    }
}

def fzf_select_project(projects: Dict) -> Optional[str]:
    """Use FZF to select a project with arrow keys"""
    try:
        # Prepare the project list for FZF
        project_lines = []
        project_keys = list(projects.keys())
        
        for key in project_keys:
            project = projects[key]
            # Format: "key: Project Name [tag1,tag2]"
            tags_str = ",".join(project.get("tags", []))
            line = f"{key}: {project['name']} [{tags_str}]"
            project_lines.append(line)
        
        # Add exit option
        project_lines.append("EXIT: Exit Claude Manager")
        
        # Create FZF command
        fzf_cmd = [
            "fzf",
            "--prompt=Select Project: ",
            "--header=Use arrows to navigate, Enter to select, Esc to exit",
            "--height=40%",
            "--border",
            "--ansi",
            "--reverse"
        ]
        
        # Run FZF
        result = subprocess.run(
            fzf_cmd,
            input="\n".join(project_lines),
            text=True,
            capture_output=True
        )
        
        if result.returncode != 0:
            return None
        
        # Parse the selected line
        selected_line = result.stdout.strip()
        if not selected_line:
            return None
        
        # Extract the project key
        selected_key = selected_line.split(":")[0]
        
        if selected_key == "EXIT":
            return None
        
        return selected_key if selected_key in projects else None
        
    except Exception as e:
        print(f"Error with FZF selection: {e}")
        return None

def main():
    print("🧪 Testing FZF Project Selector")
    print("=" * 40)
    
    # Test FZF availability
    try:
        subprocess.run(["fzf", "--version"], capture_output=True, check=True)
        print("✓ FZF is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FZF is not available")
        sys.exit(1)
    
    print("\nStarting FZF selector...")
    print("(Use arrow keys to navigate, Enter to select, Esc to exit)")
    
    selected_project = fzf_select_project(SAMPLE_PROJECTS)
    
    if selected_project:
        project_info = SAMPLE_PROJECTS[selected_project]
        print(f"\n✓ Selected project: {selected_project}")
        print(f"  Name: {project_info['name']}")
        print(f"  Directory: {project_info['directory']}")
        print(f"  Tags: {', '.join(project_info['tags'])}")
    else:
        print("\n↩ No project selected (cancelled)")

if __name__ == "__main__":
    main()