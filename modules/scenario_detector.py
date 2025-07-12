"""
Scenario Detection Module for Claude Manager

Detects the current tmux environment and determines which of three scenarios
the claude-manager is being launched in:
1. Outside tmux, no mngr session exists
2. Outside tmux, mngr session exists  
3. Inside tmux (any session)
"""

import os
import subprocess
import re
from typing import Optional, Tuple
from .tmux_manager import TmuxManager


class ScenarioDetector:
    """Detects and analyzes the current tmux environment for scenario routing."""
    
    def __init__(self, tmux_manager: TmuxManager):
        self.tmux_manager = tmux_manager
        
    def detect_scenario(self) -> str:
        """
        Detect which of the three scenarios we're in.
        
        Returns:
            str: One of 'outside_tmux_no_session', 'outside_tmux_has_session', 'inside_tmux'
        """
        if not self._is_inside_tmux():
            # Outside tmux - check if mngr session exists
            if self.tmux_manager.session_exists():
                return "outside_tmux_has_session"
            else:
                return "outside_tmux_no_session"
        else:
            # Inside tmux
            return "inside_tmux"
    
    def _is_inside_tmux(self) -> bool:
        """Check if currently running inside a tmux session."""
        return bool(os.environ.get("TMUX_PANE"))
    
    def get_current_window_name(self) -> Optional[str]:
        """
        Get the name of the current tmux window if inside tmux.
        
        Returns:
            Optional[str]: Window name or None if not in tmux or error
        """
        if not self._is_inside_tmux():
            return None
            
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#{window_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_current_session_name(self) -> Optional[str]:
        """
        Get the name of the current tmux session if inside tmux.
        
        Returns:
            Optional[str]: Session name or None if not in tmux or error
        """
        if not self._is_inside_tmux():
            return None
            
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#{session_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def is_claude_manager_window(self, window_name: Optional[str] = None) -> bool:
        """
        Check if the given window (or current window) is a claude-manager window.
        
        Args:
            window_name: Window name to check. If None, checks current window.
            
        Returns:
            bool: True if window follows claude-manager naming pattern
        """
        if window_name is None:
            window_name = self.get_current_window_name()
            
        if not window_name:
            return False
            
        # Check for cc-mngr-{project-key} pattern (optionally with counter)
        pattern = r"^cc-mngr-[a-zA-Z0-9_]+(-\d+)?$"
        return bool(re.match(pattern, window_name))
    
    def extract_project_from_window(self, window_name: Optional[str] = None) -> Optional[str]:
        """
        Extract project key from a claude-manager window name.
        
        Args:
            window_name: Window name to parse. If None, uses current window.
            
        Returns:
            Optional[str]: Project key or None if not a claude-manager window
        """
        if window_name is None:
            window_name = self.get_current_window_name()
            
        if not window_name or not self.is_claude_manager_window(window_name):
            return None
            
        # Extract project key from cc-mngr-{project-key} or cc-mngr-{project-key}-{counter}
        match = re.match(r"^cc-mngr-([a-zA-Z0-9_]+)(?:-\d+)?$", window_name)
        if match:
            return match.group(1)
        return None
    
    def get_mngr_session_windows(self) -> list[str]:
        """
        Get list of all window names in the mngr session.
        
        Returns:
            list[str]: List of window names, empty if session doesn't exist
        """
        if not self.tmux_manager.session_exists():
            return []
            
        try:
            result = subprocess.run(
                ["tmux", "list-windows", "-t", self.tmux_manager.session_name, "-F", "#{window_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            return [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
    
    def get_claude_manager_windows(self) -> list[str]:
        """
        Get list of all claude-manager windows in the mngr session.
        
        Returns:
            list[str]: List of claude-manager window names
        """
        all_windows = self.get_mngr_session_windows()
        return [w for w in all_windows if self.is_claude_manager_window(w)]
    
    def has_ccusage_window(self) -> bool:
        """
        Check if the mngr session has a ccusage window.
        
        Returns:
            bool: True if ccusage window exists
        """
        windows = self.get_mngr_session_windows()
        return "ccusage" in windows
    
    def has_log_window(self) -> bool:
        """
        Check if the mngr session has a log window.
        
        Returns:
            bool: True if mngr-log window exists
        """
        windows = self.get_mngr_session_windows()
        return "mngr-log" in windows
    
    def get_scenario_info(self) -> dict:
        """
        Get comprehensive information about the current scenario.
        
        Returns:
            dict: Detailed scenario information for debugging
        """
        scenario = self.detect_scenario()
        current_window = self.get_current_window_name()
        current_session = self.get_current_session_name()
        
        info = {
            "scenario": scenario,
            "inside_tmux": self._is_inside_tmux(),
            "mngr_session_exists": self.tmux_manager.session_exists(),
            "current_session": current_session,
            "current_window": current_window,
            "is_claude_manager_window": self.is_claude_manager_window(current_window),
            "extracted_project": self.extract_project_from_window(current_window),
        }
        
        if scenario in ["outside_tmux_has_session", "inside_tmux"]:
            info.update({
                "mngr_windows": self.get_mngr_session_windows(),
                "claude_manager_windows": self.get_claude_manager_windows(),
                "has_ccusage_window": self.has_ccusage_window(),
                "has_log_window": self.has_log_window(),
            })
            
        return info