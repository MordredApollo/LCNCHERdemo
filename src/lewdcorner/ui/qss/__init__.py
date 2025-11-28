"""
QSS Theme management
"""
from pathlib import Path

THEMES_DIR = Path(__file__).parent


def load_theme(theme_name: str = "dark") -> str:
    """
    Load QSS theme by name
    
    Args:
        theme_name: "dark" or "light"
        
    Returns:
        QSS stylesheet string
    """
    theme_file = THEMES_DIR / f"{theme_name}_theme.qss"
    
    if not theme_file.exists():
        # Fallback to dark theme
        theme_file = THEMES_DIR / "dark_theme.qss"
    
    try:
        with open(theme_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Failed to load theme {theme_name}: {e}")
        return ""


def get_available_themes() -> list:
    """Get list of available theme names"""
    return ["dark", "light"]
