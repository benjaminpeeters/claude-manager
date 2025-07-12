"""
Debug Logger for Claude Manager

Creates timestamped debug logs in .ai/logs/ directory when debug mode is enabled.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback


class DebugLogger:
    """Handles debug logging for claude-manager"""
    
    def __init__(self, base_dir: Path, enable_debug: bool = None):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / ".ai" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if debug mode is enabled
        if enable_debug is None:
            # Check environment variable or default to enabled for now
            enable_debug = os.environ.get("CLAUDE_MANAGER_DEBUG", "1").lower() in ["1", "true", "yes"]
        
        self.debug_enabled = enable_debug
        self.log_file: Optional[Path] = None
        self.start_time = datetime.now()
        
        if self.debug_enabled:
            self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Create timestamped debug log file"""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"debug_{timestamp}.md"
        
        # Write initial header
        with open(self.log_file, 'w') as f:
            f.write(f"# Claude Manager Debug Log\n\n")
            f.write(f"**Started**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Command**: {' '.join(sys.argv)}\n")
            f.write(f"**Working Dir**: {os.getcwd()}\n")
            f.write(f"**Environment**:\n")
            f.write(f"- TMUX_PANE: {os.environ.get('TMUX_PANE', 'Not set')}\n")
            f.write(f"- TMUX: {os.environ.get('TMUX', 'Not set')}\n")
            f.write(f"- USER: {os.environ.get('USER', 'Unknown')}\n\n")
    
    def log(self, message: str, category: str = "INFO", details: Optional[Dict[str, Any]] = None):
        """Log a message with optional details"""
        if not self.debug_enabled or not self.log_file:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        
        with open(self.log_file, 'a') as f:
            f.write(f"## [{timestamp}] {category}: {message}\n\n")
            
            if details:
                f.write("**Details**:\n")
                for key, value in details.items():
                    f.write(f"- {key}: {value}\n")
                f.write("\n")
    
    def log_scenario_detection(self, scenario: str, info: Dict[str, Any]):
        """Log scenario detection details"""
        self.log(
            f"Detected scenario: {scenario}",
            "SCENARIO",
            info
        )
    
    def log_tmux_command(self, command: list, result_code: int, stdout: str = "", stderr: str = ""):
        """Log tmux command execution"""
        details = {
            "command": " ".join(command),
            "return_code": result_code,
            "stdout": stdout.strip() if stdout else "(empty)",
            "stderr": stderr.strip() if stderr else "(empty)"
        }
        
        category = "TMUX_SUCCESS" if result_code == 0 else "TMUX_ERROR"
        self.log(f"Tmux command executed", category, details)
    
    def log_project_selection(self, selected_project: Optional[str], available_projects: list):
        """Log project selection details"""
        details = {
            "selected": selected_project or "None",
            "available": available_projects,
            "total_count": len(available_projects)
        }
        self.log("Project selection completed", "PROJECT", details)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with traceback"""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        self.log(f"Error occurred: {str(error)}", "ERROR", details)
    
    def log_window_creation(self, window_type: str, window_name: str, success: bool, error_msg: str = ""):
        """Log window creation attempts"""
        details = {
            "window_type": window_type,
            "window_name": window_name,
            "success": success,
            "error_message": error_msg
        }
        
        category = "WINDOW_SUCCESS" if success else "WINDOW_ERROR"
        self.log(f"Window creation: {window_name}", category, details)
    
    def log_config_loading(self, config_type: str, file_path: str, success: bool, error_msg: str = ""):
        """Log configuration loading"""
        details = {
            "config_type": config_type,
            "file_path": file_path,
            "file_exists": Path(file_path).exists(),
            "success": success,
            "error_message": error_msg
        }
        
        category = "CONFIG_SUCCESS" if success else "CONFIG_ERROR"
        self.log(f"Config loading: {config_type}", category, details)
    
    def finalize(self):
        """Write final summary to log"""
        if not self.debug_enabled or not self.log_file:
            return
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        with open(self.log_file, 'a') as f:
            f.write(f"## Session Summary\n\n")
            f.write(f"**Ended**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duration**: {duration.total_seconds():.2f} seconds\n")
            f.write(f"**Log file**: {self.log_file}\n")


# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None


def get_debug_logger(base_dir: Path = None) -> DebugLogger:
    """Get or create the global debug logger instance"""
    global _debug_logger
    
    if _debug_logger is None:
        if base_dir is None:
            # Default to current working directory
            base_dir = Path.cwd()
        _debug_logger = DebugLogger(base_dir)
    
    return _debug_logger


def log_debug(message: str, category: str = "INFO", details: Optional[Dict[str, Any]] = None):
    """Convenience function for debug logging"""
    logger = get_debug_logger()
    logger.log(message, category, details)