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
    
    # Build the message content
    message_parts = []
    
    # Add project intro
    if not project_key:
        project_key = project.get("key", "unknown")
    
    category = project.get('category', 'General')
    todoist_project = project.get('todoist_project', 'Inbox')
    
    intro_msg = f"You are now in {project['name']} mode. "
    intro_msg += f"Category: {category}. "
    intro_msg += f"Working directory: {project['directory']}. "
    intro_msg += f"Todoist project: {todoist_project}."
    message_parts.append(intro_msg)
    
    # Add general Claude Manager guidelines
    general_guidelines = Path("/home/bpeeters/MEGA/manager/config/general_guidelines.md")
    if general_guidelines.exists():
        guidelines_content = general_guidelines.read_text()
        message_parts.append("\n=== Claude Manager Guidelines ===")
        message_parts.append(guidelines_content)
    
    # Add project-specific context
    context_file = Path("/home/bpeeters/MEGA/manager/config/contexts") / f"context_{project_key}.md"
    if context_file.exists():
        context_content = context_file.read_text()
        message_parts.append("\n=== Project Context ===")
        message_parts.append(context_content)
    else:
        message_parts.append(f"\n=== Project Context ===")
        message_parts.append(f"Context file not found: {context_file}")
    
    # Combine all message parts
    full_message = "\n".join(message_parts)
    
    # Add the message to command
    cmd_parts.append(f'"{full_message}"')
    
    return " ".join(cmd_parts)


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