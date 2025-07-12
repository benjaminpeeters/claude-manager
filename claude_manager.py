#!/usr/bin/env python3
"""
Claude Manager - Personal AI Assistant/Coach
Integrates with Todoist, monitors progress, and provides intelligent support
"""

import argparse
from pathlib import Path

# Import modular components
from modules.config_manager import ConfigManager
from modules.project_manager import ProjectManager
from modules.tmux_manager import TmuxManager
from modules.scenario_detector import ScenarioDetector
from modules.debug_logger import get_debug_logger, log_debug

# Base paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"


class ClaudeManager:
    """Main Claude Manager orchestrator"""
    
    def __init__(self):
        # Initialize debug logger
        self.debug_logger = get_debug_logger(BASE_DIR)
        log_debug("Claude Manager initializing", "INIT")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager(CONFIG_DIR)
        
        # Load configurations
        try:
            self.projects = self.config_manager.load_projects()
            self.debug_logger.log_config_loading("projects", str(CONFIG_DIR / "projects.yaml"), True)
        except Exception as e:
            self.debug_logger.log_config_loading("projects", str(CONFIG_DIR / "projects.yaml"), False, str(e))
            raise
        
        try:
            self.settings = self.config_manager.load_settings()
            self.debug_logger.log_config_loading("settings", str(CONFIG_DIR / "settings.yaml"), True)
        except Exception as e:
            self.debug_logger.log_config_loading("settings", str(CONFIG_DIR / "settings.yaml"), False, str(e))
            raise
        
        # Initialize managers
        self.project_manager = ProjectManager(self.projects)
        self.tmux_manager = TmuxManager(self.settings)
        self.scenario_detector = ScenarioDetector(self.tmux_manager)
        
        self.current_project = None
        log_debug("Claude Manager initialization complete", "INIT", {
            "projects_count": len(self.projects),
            "session_name": self.settings.get("tmux_session_name", "unknown")
        })
    
    def run(self):
        """Main execution flow"""
        # Ensure config files exist
        if not self.config_manager.ensure_config_files_exist():
            return
        
        # Check if we have any projects
        if not self.projects:
            print("\nNo projects configured.")
            print(f"Please edit {CONFIG_DIR / 'projects.yaml'} to add your projects.")
            return
        
        # Detect scenario and route accordingly
        scenario = self.scenario_detector.detect_scenario()
        scenario_info = self.scenario_detector.get_scenario_info()
        
        # Log scenario detection
        self.debug_logger.log_scenario_detection(scenario, scenario_info)
        
        print(f"Detected scenario: {scenario}")
        
        if scenario == "outside_tmux_no_session":
            log_debug("Routing to scenario 1: outside_tmux_no_session", "ROUTING")
            self.handle_scenario_1()
        elif scenario == "outside_tmux_has_session":
            log_debug("Routing to scenario 2: outside_tmux_has_session", "ROUTING")
            self.handle_scenario_2()
        elif scenario == "inside_tmux":
            log_debug("Routing to scenario 3: inside_tmux", "ROUTING")
            self.handle_scenario_3()
        else:
            log_debug(f"Unknown scenario detected: {scenario}", "ERROR")
            print(f"Unknown scenario: {scenario}")
            return
    
    
    def handle_scenario_1(self, preset_project_key: str = None):
        """Handle Scenario 1: Outside tmux, no mngr session exists"""
        print("Scenario 1: Creating new mngr session with full setup")
        
        # Select project (or use preset)
        if preset_project_key:
            project_key = preset_project_key
            log_debug(f"Using preset project for scenario 1: {project_key}", "PROJECT")
        else:
            log_debug("Starting project selection for scenario 1", "PROJECT")
            project_key = self.project_manager.select_project()
        self.debug_logger.log_project_selection(project_key, list(self.projects.keys()))
        
        if not project_key:
            log_debug("No project selected, exiting scenario 1", "PROJECT")
            print("\nExiting Claude Manager.")
            return
        
        # Validate project
        if not self.project_manager.validate_project(project_key):
            print(f"\nProject '{project_key}' has configuration errors.")
            return
        
        project = self.project_manager.get_project_info(project_key)
        print(f"\n✨ Starting {project['name']} with full setup...\n")
        
        # Create new session (this will be completely new)
        self.tmux_manager.session_name = self.settings["tmux_session_name"]
        
        # Step 1: Create new session with temporary first window
        print("Creating new mngr session...")
        import subprocess
        result = subprocess.run([
            "tmux", "new-session", "-d", "-s", self.settings["tmux_session_name"],
            "-c", "/home/bpeeters/MEGA/manager"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to create session: {result.stderr}")
            return
        
        # Step 2: Create ccusage window (first window, will be index 1)
        print("Creating ccusage window...")
        ccusage_target = self.tmux_manager.create_ccusage_window()
        if not ccusage_target:
            print("Warning: Failed to create ccusage window")
        
        # Step 3: Create log window (second window, will be index 2)
        print("Creating log window...")
        log_target = self.tmux_manager.create_log_window()
        if not log_target:
            print("Warning: Failed to create log window")
        
        # Step 4: Create project window (third window, will be index 3)
        print("Creating project window...")
        project_target = self.tmux_manager.create_project_window(project, project_key)
        if not project_target:
            print("Failed to create project window.")
            return
        
        # Step 5: Remove the initial temporary window (index 0) - this will shift all indices down by 1
        # So final order will be: ccusage (0), log (1), project (2)
        subprocess.run(["tmux", "kill-window", "-t", f"{self.settings['tmux_session_name']}:0"])
        
        print(f"✨ Claude Manager setup complete!")
        
        # Step 6: Attach to session and focus on project window
        try:
            subprocess.run(["tmux", "attach-session", "-t", project_target])
        except Exception as e:
            print(f"Error attaching to session: {e}")
    
    def handle_scenario_2(self, preset_project_key: str = None):
        """Handle Scenario 2: Outside tmux, mngr session exists"""
        print("Scenario 2: Adding new window to existing mngr session")
        
        # Select project (or use preset)
        if preset_project_key:
            project_key = preset_project_key
            log_debug(f"Using preset project for scenario 2: {project_key}", "PROJECT")
        else:
            project_key = self.project_manager.select_project()
        if not project_key:
            print("\nExiting Claude Manager.")
            return
        
        # Validate project
        if not self.project_manager.validate_project(project_key):
            print(f"\nProject '{project_key}' has configuration errors.")
            return
        
        project = self.project_manager.get_project_info(project_key)
        print(f"\n✨ Starting {project['name']} in existing session...\n")
        
        # Create project window in existing session
        project_target = self.tmux_manager.create_project_window(project, project_key)
        if not project_target:
            print("Failed to create project window.")
            return
        
        print(f"✨ Project window created!")
        
        # Attach to session and switch to new project window
        try:
            import subprocess
            subprocess.run(["tmux", "attach-session", "-t", project_target])
        except Exception as e:
            print(f"Error attaching to session: {e}")
    
    def handle_scenario_3(self, preset_project_key: str = None):
        """Handle Scenario 3: Inside tmux (any session)"""
        print("Scenario 3: Transforming current window into project window")
        
        # Select project (or use preset)
        if preset_project_key:
            project_key = preset_project_key
            log_debug(f"Using preset project for scenario 3: {project_key}", "PROJECT")
        else:
            log_debug("Starting project selection for scenario 3", "PROJECT")
            project_key = self.project_manager.select_project()
        self.debug_logger.log_project_selection(project_key, list(self.projects.keys()))
        
        if not project_key:
            log_debug("No project selected, exiting scenario 3", "PROJECT")
            print("\nExiting Claude Manager.")
            return
        
        # Validate project
        if not self.project_manager.validate_project(project_key):
            log_debug(f"Project validation failed: {project_key}", "PROJECT")
            print(f"\nProject '{project_key}' has configuration errors.")
            return
        
        project = self.project_manager.get_project_info(project_key)
        print(f"\n✨ Transforming current window for {project['name']}...")
        log_debug(f"Starting window transformation for {project_key}", "WINDOW")
        
        # Show progress
        print("   → Clearing current window content...")
        
        # Transform current window
        try:
            log_debug("About to call setup_current_window_as_project", "SCENARIO3")
            window_target = self.tmux_manager.setup_current_window_as_project(project, project_key)
            log_debug(f"setup_current_window_as_project returned: {window_target}", "SCENARIO3")
            
            if not window_target:
                log_debug("Window transformation failed - returned None", "ERROR")
                print("❌ Failed to setup current window.")
                print("   Check debug logs for details.")
                return
            
            print(f"✨ Current window transformed into project workspace!")
            print(f"   Left pane: Task file (task_{project_key}.md)")
            print(f"   Right pane: Claude instance with {project['name']} context")
            log_debug(f"Successfully transformed window to {window_target}", "WINDOW")
            
        except Exception as e:
            log_debug(f"Exception in scenario 3 window transformation: {e}", "ERROR")
            self.debug_logger.log_error(e, "scenario 3 window transformation")
            print(f"❌ Error during window transformation: {e}")
            return
    
    def list_projects(self):
        """List all available projects"""
        self.project_manager.list_projects()
    
    def get_config_info(self):
        """Get configuration information"""
        return self.config_manager.get_config_info()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude Manager - Personal AI Assistant")
    parser.add_argument("--project", "-p", help="Project key to start directly")
    parser.add_argument("--list", "-l", action="store_true", help="List available projects")
    parser.add_argument("--config-info", action="store_true", help="Show configuration information")
    parser.add_argument("--new", help="Create a new project interactively")
    
    args = parser.parse_args()
    
    try:
        manager = ClaudeManager()
        
        if args.config_info:
            info = manager.get_config_info()
            print("Configuration Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            return
        
        if args.new:
            # Create new project
            from modules.project_creator import create_project_interactive
            success = create_project_interactive(CONFIG_DIR, args.new)
            if success:
                print(f"\\n🎉 Project '{args.new}' created successfully!")
                print("You can now use it with: python3 claude_manager.py")
            return
        
        if args.list:
            manager.list_projects()
            return
        
        if args.project:
            if args.project in manager.projects:
                if not manager.project_manager.validate_project(args.project):
                    print(f"Error: Project '{args.project}' has configuration errors.")
                    return
                
                manager.current_project = args.project
                project = manager.project_manager.get_project_info(args.project)
                print(f"\n✨ Starting {project['name']}...\n")
                
                # Use scenario-based handling for direct project specification
                scenario = manager.scenario_detector.detect_scenario()
                if scenario == "outside_tmux_no_session":
                    manager.handle_scenario_1(args.project)
                elif scenario == "outside_tmux_has_session":
                    manager.handle_scenario_2(args.project)
                elif scenario == "inside_tmux":
                    manager.handle_scenario_3(args.project)
                else:
                    print(f"Unknown scenario: {scenario}")
            else:
                print(f"Error: Project '{args.project}' not found.")
                print("Use --list to see available projects.")
        else:
            manager.run()
            
    except KeyboardInterrupt:
        print("\n\nClaude Manager interrupted.")
        log_debug("Claude Manager interrupted by user", "EXIT")
    except Exception as e:
        print(f"Error: {e}")
        # Log the error if we have a manager instance
        if 'manager' in locals():
            manager.debug_logger.log_error(e, "main execution")
        return 1
    finally:
        # Finalize debug logging if we have a manager instance
        if 'manager' in locals():
            manager.debug_logger.finalize()


if __name__ == "__main__":
    main()
