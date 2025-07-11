"""
Claude Command Builder - Handle Claude command construction and MCP configuration
"""

import json
from pathlib import Path
from typing import Dict, List
from .context_discovery import discover_project_context


def build_claude_command(settings: Dict, project: Dict, project_key: str = None) -> str:
    """Build Claude command with project context and MCP configuration"""
    cmd_parts = [settings["claude_command"]]
    
    # Add MCP configuration from file (universal access)
    mcp_config_file = Path("/home/bpeeters/MEGA/manager/config/mcp_config.json")
    if mcp_config_file.exists():
        cmd_parts.append(f"--mcp-config {mcp_config_file}")
        cmd_parts.append("--strict-mcp-config")
    else:
        print(f"Warning: MCP config file not found: {mcp_config_file}")
    
    # Add the manager's Claude instructions
    manager_claude_md = Path("/home/bpeeters/MEGA/manager/CLAUDE.md")
    if manager_claude_md.exists():
        cmd_parts.append(f"@{manager_claude_md}")
    
    # Auto-discover and add context files using @ syntax
    all_context_files = discover_project_context(project, project_key)
    
    for context_file_path in all_context_files:
        context_path = Path(context_file_path)
        if context_path.exists():
            cmd_parts.append(f"@{context_path}")
    
    # Add initial message about the project
    category = project.get('category', 'General')
    todoist_project = project.get('todoist_project', 'Inbox')
    
    intro_msg = f"You are now in {project['name']} mode. "
    intro_msg += f"Category: {category}. "
    intro_msg += f"Working directory: {project['directory']}. "
    intro_msg += f"Todoist project: {todoist_project}."
    cmd_parts.append(f'"{intro_msg}"')
    
    return " ".join(cmd_parts)


def validate_mcp_servers(mcp_servers: List[str]) -> List[str]:
    """Validate that MCP servers exist in the system"""
    # This could be expanded to check actual MCP server availability
    # For now, just return the list as-is
    return mcp_servers


def get_context_files(project: Dict, project_key: str = None) -> List[Path]:
    """Get all context files for a project, including auto-discovered ones"""
    all_context_files = discover_project_context(project, project_key)
    return [Path(f) for f in all_context_files if Path(f).exists()]