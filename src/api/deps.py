"""
API dependency injection.

FastAPI's Depends() pattern for shared dependencies.
This keeps route functions clean and testable.
"""

from typing import Annotated

from fastapi import Depends

from src.core.config import Settings, get_settings


# Type alias for settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]
