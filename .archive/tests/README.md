# Dynamic Project Selection Tests

This directory contains test scripts for different dynamic project selection methods.

## Test Scripts

### 1. FZF Selector (`test_fzf_selector.py`)
- **Requirements**: `fzf` command-line tool
- **Features**: Fast fuzzy finding, type-to-filter, arrow navigation
- **Usage**: `python3 test_fzf_selector.py`

### 2. Textual Selector (`test_textual_selector.py`)  
- **Requirements**: `textual` Python library
- **Features**: Rich TUI, project details, validation status
- **Usage**: `python3 test_textual_selector.py`

### 3. Curses Selector (`test_curses_selector.py`)
- **Requirements**: Built-in `curses` module
- **Features**: Basic but functional, always available
- **Usage**: `python3 test_curses_selector.py`

### 4. Integration Example (`test_integration.py`)
- **Requirements**: claude-manager modules
- **Features**: Shows how to integrate with ProjectManager
- **Usage**: `python3 test_integration.py`

## Quick Test Commands

```bash
# Test FZF (if available)
python3 test_fzf_selector.py

# Test Textual (if installed)
python3 test_textual_selector.py

# Test Curses (always available)
python3 test_curses_selector.py

# Test integration with all methods
python3 test_integration.py
```

## Installation Requirements

```bash
# For FZF method
sudo apt install fzf  # or: brew install fzf

# For Textual method  
pip install textual

# Curses is built-in to Python
```

## Comparison

| Method   | Speed | Features | Dependencies | Reliability |
|----------|-------|----------|--------------|-------------|
| FZF      | ⭐⭐⭐⭐⭐ | ⭐⭐⭐      | fzf          | ⭐⭐⭐⭐⭐       |
| Textual  | ⭐⭐⭐⭐  | ⭐⭐⭐⭐⭐    | textual      | ⭐⭐⭐⭐        |
| Curses   | ⭐⭐⭐    | ⭐⭐⭐      | None         | ⭐⭐⭐⭐⭐       |

## Recommendation

1. **FZF** for speed and simplicity
2. **Textual** for rich interface and features
3. **Curses** as reliable fallback