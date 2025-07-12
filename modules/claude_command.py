"""
Claude Command Builder - Handle Claude command construction and MCP configuration
"""

import json
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def build_claude_command(settings: Dict, project: Dict, project_key: str = None) -> str:
    """Build Claude command with project context and MCP configuration"""
    cmd_parts = [settings["claude_command"]]
    
    # Add model specification
    cmd_parts.append('--model "sonnet"')
    
    # Add MCP configuration from file (universal access)
    mcp_config_file = Path("/home/bpeeters/MEGA/manager/config/mcp_config.json")
    if mcp_config_file.exists():
        cmd_parts.append(f"--mcp-config {mcp_config_file}")
        cmd_parts.append("--strict-mcp-config")
    else:
        print(f"Warning: MCP config file not found: {mcp_config_file}")
    
    # Add project directory with validation
    project_dir = project.get("directory")
    if project_dir:
        project_dir_path = Path(project_dir)
        if project_dir_path.exists() and project_dir_path.is_dir():
            cmd_parts.append(f'--add-dir {shlex.quote(project_dir)}')
        else:
            print(f"Warning: Project directory does not exist: {project_dir}")
            print(f"Skipping --add-dir flag for non-existent directory")
    
    # Ensure task file exists before building command
    _ensure_task_file_exists(project, project_key)
    
    # Build system prompt from template  
    system_prompt = _build_system_prompt_from_template(project, project_key)
    
    # Add the system prompt with proper shell escaping
    cmd_parts.append(f'--append-system-prompt {shlex.quote(system_prompt)}')
    
    # Build and add initial message
    initial_message = _build_initial_message_from_template(project, project_key)
    cmd_parts.append(shlex.quote(initial_message))
    
    return " ".join(cmd_parts)


def _build_system_prompt_from_template(project: Dict, project_key: str = None) -> str:
    """Build system prompt content from template file"""
    # Get project details
    if not project_key:
        project_key = project.get("key", "unknown")
    
    # Load system prompt template
    prompt_file = Path("/home/bpeeters/MEGA/manager/config/system_prompt_template.md")
    if not prompt_file.exists():
        return f"System prompt template file not found: {prompt_file}"
    
    template = prompt_file.read_text()
    
    # Load project context
    context_file = Path("/home/bpeeters/MEGA/manager/config/contexts") / f"context_{project_key}.md"
    if context_file.exists():
        context_content = context_file.read_text()
    else:
        context_content = f"Context file not found: {context_file}"
    
    # Get task file path
    task_file_path = f"tasks/task_{project_key}.md"
    
    # Get current date for daily log
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Fill template with project data
    return template.format(
        project_name=project['name'],
        category=project.get('category', 'General'),
        directory=project['directory'],
        todoist_project=project.get('todoist_project', 'Inbox'),
        task_file_path=task_file_path,
        current_date=current_date,
        context_content=context_content
    )


def validate_mcp_servers(mcp_servers: List[str]) -> List[str]:
    """Validate that MCP servers exist in the system"""
    # This could be expanded to check actual MCP server availability
    # For now, just return the list as-is
    return mcp_servers


def _ensure_task_file_exists(project: Dict, project_key: str = None) -> str:
    """Ensure task file exists for the project"""
    if not project_key:
        project_key = project.get("key", "unknown")
    
    # Create tasks directory if it doesn't exist
    tasks_dir = Path("/home/bpeeters/MEGA/manager/tasks")
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task file if it doesn't exist
    task_file = tasks_dir / f"task_{project_key}.md"
    if not task_file.exists():
        task_file.write_text(f"# {project['name']} - Task Notes\n")
    
    # Return the relative path for the system prompt
    return f"tasks/task_{project_key}.md"


def _build_initial_message_from_template(project: Dict, project_key: str = None) -> str:
    """Build initial message from template including task file content"""
    if not project_key:
        project_key = project.get("key", "unknown")
    
    # Load message template
    template_file = Path("/home/bpeeters/MEGA/manager/config/claude_message_template.md")
    if not template_file.exists():
        # Fallback if template doesn't exist
        return f"Starting new session for {project['name']}. Task file: tasks/task_{project_key}.md"
    
    template = template_file.read_text()
    
    # Get task file content
    task_file_path = f"tasks/task_{project_key}.md"
    task_file_full = Path("/home/bpeeters/MEGA/manager") / task_file_path
    
    if task_file_full.exists():
        task_file_content = task_file_full.read_text().strip()
    else:
        task_file_content = "(Task file not found - will be created)"
    
    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Fill template with data
    return template.format(
        project_name=project['name'],
        category=project.get('category', 'General'),
        directory=project.get('directory', 'N/A'),
        task_file_path=task_file_path,
        task_file_content=task_file_content,
        current_date=current_date
    )


def get_context_files(project: Dict, project_key: str = None) -> List[Path]:
    """Get the context file for a project"""
    if not project_key:
        project_key = project.get("key", "unknown")
    
    context_file = Path("/home/bpeeters/MEGA/manager/config/contexts") / f"context_{project_key}.md"
    
    if context_file.exists():
        return [context_file]
    else:
        return []
