#!/usr/bin/env python3
"""
Create all missing summary files for existing projects
"""

import yaml
from pathlib import Path

def create_summary_file(project_key: str, project_info: dict, summaries_dir: Path):
    """Create a summary file for a project"""
    summary_path = summaries_dir / f"summary_{project_key}.md"
    
    if summary_path.exists():
        print(f"⏭️  Skipping {project_key} - summary already exists")
        return
    
    # Determine common context files based on category
    context_files = []
    category = project_info.get('category', 'General')
    
    if category == "PIK":
        context_files = [
            "notes/work/notes_pik.md",
            "notes/work/notes_gams.md",
            "notes/work/notes_remind.md"
        ]
    elif category == "Publications":
        context_files = [
            "papers/manuscript.md",
            "papers/literature_review.md",
            "papers/notes.md"
        ]
    elif category == "Projects":
        context_files = [
            "docs/README.md",
            "docs/development.md",
            "project/notes.md"
        ]
    elif category == "Flows":
        context_files = [
            "README.md",
            "docs/usage.md",
            "notes/development.md"
        ]
    elif category == "Life":
        context_files = [
            "notes/monitoring/habits.md",
            "notes/life/goals.md",
            "notes/personal/notes.md"
        ]
    elif category == "General":
        context_files = [
            "notes/buffer.md",
            "notes/monitoring/pipeline.md",
            "notes/monitoring/habits.md",
            "notes/monitoring/goalsLT.md"
        ]
    
    # Generate content
    content = f"""# {project_info['name']} - Summary

## Overview

{project_info.get('description', f"Project summary for {project_info['name']}.")}

## Project Details

- **Category**: {project_info['category']}
- **Directory**: `{project_info['directory']}`
- **Todoist Project**: {project_info['todoist_project']}

## Key Information

<!-- Add key information about this project here -->

## Context Files

"""
    
    for file_path in context_files:
        content += f"- `{file_path}`\n"
    
    content += """
## Notes

<!-- Add project-specific notes here -->

---
*This file serves as the main summary and context guide for Claude Manager.*
*It is automatically loaded when this project is selected.*
"""
    
    # Write the file
    try:
        with open(summary_path, 'w') as f:
            f.write(content)
        print(f"✅ Created summary for {project_key}")
    except Exception as e:
        print(f"❌ Failed to create summary for {project_key}: {e}")

def main():
    """Create all missing summary files"""
    config_dir = Path("/home/bpeeters/MEGA/manager/config")
    projects_file = config_dir / "projects.yaml"
    summaries_dir = config_dir / "summaries"
    
    # Ensure summaries directory exists
    summaries_dir.mkdir(exist_ok=True)
    
    # Load projects
    try:
        with open(projects_file, 'r') as f:
            projects = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ Failed to load projects: {e}")
        return
    
    print(f"📁 Creating summary files in {summaries_dir}")
    print(f"📋 Found {len(projects)} projects")
    print()
    
    for project_key, project_info in projects.items():
        create_summary_file(project_key, project_info, summaries_dir)
    
    print()
    print(f"🎉 Summary creation complete!")
    print(f"📁 Check {summaries_dir} for all summary files")

if __name__ == "__main__":
    main()