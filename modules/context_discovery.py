"""
Context Discovery - Auto-discover context files for projects (like chinese/laoshi pattern)
"""

from pathlib import Path
from typing import List, Dict
import glob

class ContextDiscovery:
    """Discover context files automatically for projects"""
    
    def __init__(self, project_directory: str):
        self.project_dir = Path(project_directory)
        self.mega_dir = Path("/home/bpeeters/MEGA")
    
    def discover_context_files(self, project_key: str, manual_context: List[str] = None) -> List[str]:
        """
        Discover context files from context file and auto-discovery
        
        Args:
            project_key: Project key to find context file
            manual_context: List of manually specified context files (legacy)
            
        Returns:
            List of all context files (context + from context + auto-discovered)
        """
        context_files = []
        
        # Add project context file first (always first)
        context_file = self._get_context_file(project_key)
        if context_file and context_file.exists():
            context_files.append(str(context_file))
        
        # Read context files from context file
        context_context = self._read_context_from_context_file(context_file)
        for context_file_path in context_context:
            resolved_path = self._resolve_context_path(context_file_path)
            if resolved_path and resolved_path.exists():
                context_files.append(str(resolved_path))
        
        # Add manual context files (for backward compatibility)
        if manual_context:
            for context_file in manual_context:
                resolved_path = self._resolve_context_path(context_file)
                if resolved_path and resolved_path.exists() and str(resolved_path) not in context_files:
                    context_files.append(str(resolved_path))
        
        # Auto-discover additional context files
        auto_discovered = self._auto_discover_files()
        
        # Add auto-discovered files that aren't already included
        existing_paths = set(context_files)
        for auto_file in auto_discovered:
            if str(auto_file) not in existing_paths:
                context_files.append(str(auto_file))
        
        return context_files
    
    def _resolve_context_path(self, context_file: str) -> Path:
        """Resolve context file path relative to MEGA directory"""
        if context_file.startswith('/'):
            return Path(context_file)
        else:
            return self.mega_dir / context_file
    
    def _auto_discover_files(self) -> List[Path]:
        """Auto-discover context files in project directory"""
        discovered_files = []
        
        # Check if we're in a subdirectory of MEGA
        try:
            # Try to get relative path from MEGA directory
            rel_path = self.project_dir.relative_to(self.mega_dir)
            search_dir = self.project_dir
        except ValueError:
            # Project is outside MEGA directory, search from project root
            search_dir = self.project_dir
        
        # 1. Look for .ai directory (like chinese/laoshi pattern)
        ai_dir = search_dir / ".ai"
        if ai_dir.exists():
            discovered_files.extend(self._discover_ai_directory(ai_dir))
        
        # 2. Look for common documentation files
        doc_patterns = [
            "CLAUDE.md", "README.md", "docs/README.md",
            "docs/*.md", "documentation/*.md",
            "notes/*.md", "notes/**/*.md"
        ]
        
        for pattern in doc_patterns:
            discovered_files.extend(self._find_files_by_pattern(search_dir, pattern))
        
        # 3. Look for project-specific configuration/context files
        config_patterns = [
            "*.md", "config/*.md", "context/*.md"
        ]
        
        for pattern in config_patterns:
            discovered_files.extend(self._find_files_by_pattern(search_dir, pattern))
        
        # Remove duplicates and sort
        unique_files = list(set(discovered_files))
        unique_files.sort()
        
        return unique_files
    
    def _discover_ai_directory(self, ai_dir: Path) -> List[Path]:
        """Discover files in .ai directory (like chinese/laoshi)"""
        discovered = []
        
        # Common .ai subdirectories to include
        ai_subdirs = [
            "docs", "cache", "progress", "reference", 
            "modes", "dev", "logs", "context"
        ]
        
        for subdir in ai_subdirs:
            subdir_path = ai_dir / subdir
            if subdir_path.exists():
                # Add all markdown files in subdirectory
                md_files = list(subdir_path.glob("*.md"))
                discovered.extend(md_files)
                
                # Also check for nested markdown files
                nested_md = list(subdir_path.glob("**/*.md"))
                discovered.extend(nested_md)
        
        # Also check for files directly in .ai
        direct_files = list(ai_dir.glob("*.md"))
        discovered.extend(direct_files)
        
        return discovered
    
    def _find_files_by_pattern(self, search_dir: Path, pattern: str) -> List[Path]:
        """Find files matching a glob pattern"""
        try:
            if "**" in pattern:
                # Recursive pattern
                matches = list(search_dir.glob(pattern))
            else:
                # Non-recursive pattern
                matches = list(search_dir.glob(pattern))
            
            # Filter to only include files (not directories)
            return [m for m in matches if m.is_file()]
        except Exception:
            return []
    
    def get_context_summary(self, context_files: List[str]) -> Dict:
        """Get summary information about discovered context files"""
        summary = {
            "total_files": len(context_files),
            "manual_files": 0,
            "auto_discovered": 0,
            "categories": {
                "ai_directory": 0,
                "documentation": 0,
                "notes": 0,
                "config": 0,
                "other": 0
            }
        }
        
        for file_path in context_files:
            path = Path(file_path)
            
            # Categorize file
            if ".ai" in path.parts:
                summary["categories"]["ai_directory"] += 1
            elif any(name in path.name.lower() for name in ["readme", "claude", "doc"]):
                summary["categories"]["documentation"] += 1
            elif "notes" in path.parts:
                summary["categories"]["notes"] += 1
            elif any(name in path.parts for name in ["config", "context"]):
                summary["categories"]["config"] += 1
            else:
                summary["categories"]["other"] += 1
        
        return summary
    
    def _get_context_file(self, project_key: str) -> Path:
        """Get the context file path for a project"""
        context_dir = Path("/home/bpeeters/MEGA/manager/config/contexts")
        return context_dir / f"context_{project_key}.md"
    
    def _read_context_from_context_file(self, context_file: Path) -> List[str]:
        """Read context files list from context file"""
        if not context_file or not context_file.exists():
            return []
        
        try:
            content = context_file.read_text()
            context_files = []
            
            # Look for Context Files section
            in_context_section = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('## Context Files'):
                    in_context_section = True
                    continue
                elif line.startswith('##') and in_context_section:
                    # End of context section
                    break
                elif in_context_section and line.startswith('- `') and line.endswith('`'):
                    # Extract file path from markdown list item
                    file_path = line[3:-1]  # Remove "- `" and "`"
                    context_files.append(file_path)
            
            return context_files
            
        except Exception:
            return []

def discover_project_context(project: Dict, project_key: str = None) -> List[str]:
    """
    Main function to discover context files for a project
    
    Args:
        project: Project configuration dictionary
        project_key: Project key for finding summary file
        
    Returns:
        List of context file paths
    """
    discovery = ContextDiscovery(project["directory"])
    manual_context = project.get("claude_context", [])
    
    # Use project_key if provided, otherwise try to infer from project
    if not project_key:
        project_key = project.get("key", "unknown")
    
    return discovery.discover_context_files(project_key, manual_context)

def main():
    """Test context discovery"""
    # Test with current claude-manager project
    test_project = {
        "directory": "/home/bpeeters/MEGA/manager",
        "claude_context": ["CLAUDE.md", "README.md"]
    }
    
    print("🧪 Testing Context Discovery")
    print(f"Project directory: {test_project['directory']}")
    print(f"Manual context: {test_project['claude_context']}")
    print()
    
    discovery = ContextDiscovery(test_project["directory"])
    context_files = discovery.discover_context_files(test_project["claude_context"])
    
    print(f"Discovered {len(context_files)} context files:")
    for i, file_path in enumerate(context_files, 1):
        exists = "✓" if Path(file_path).exists() else "✗"
        print(f"  {i:2d}. {exists} {file_path}")
    
    print()
    summary = discovery.get_context_summary(context_files)
    print("Summary:")
    print(f"  Total files: {summary['total_files']}")
    print(f"  Categories:")
    for category, count in summary['categories'].items():
        if count > 0:
            print(f"    {category}: {count}")

if __name__ == "__main__":
    main()