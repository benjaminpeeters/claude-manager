"""
Claude Command Builder - Handle Claude command construction and MCP configuration
"""

import json
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
            cmd_parts.append(f'--add-dir "{project_dir}"')
        else:
            print(f"Warning: Project directory does not exist: {project_dir}")
            print(f"Skipping --add-dir flag for non-existent directory")
    
    # Build system prompt from template
    system_prompt = _build_system_prompt_from_template(project, project_key)
    
    # Add the system prompt
    cmd_parts.append(f'--append-system-prompt "{system_prompt}"')
    
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
    
    # Fill template with project data
    return template.format(
        project_name=project['name'],
        category=project.get('category', 'General'),
        directory=project['directory'],
        todoist_project=project.get('todoist_project', 'Inbox'),
        context_content=context_content
    )


def validate_mcp_servers(mcp_servers: List[str]) -> List[str]:
    """Validate that MCP servers exist in the system"""
    # This could be expanded to check actual MCP server availability
    # For now, just return the list as-is
    return mcp_servers


def get_context_files(project: Dict, project_key: str = None) -> List[Path]:
    """Get the context file for a project"""
    if not project_key:
        project_key = project.get("key", "unknown")
    
    context_file = Path("/home/bpeeters/MEGA/manager/config/contexts") / f"context_{project_key}.md"
    
    if context_file.exists():
        return [context_file]
    else:
        return []
