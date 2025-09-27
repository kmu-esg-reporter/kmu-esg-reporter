"""Base page class for UI components."""

from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session


class BasePage(ABC):
    """Base class for all UI pages."""
    
    def __init__(self):
        self.db_session: Optional[Session] = None
        self.company_id: Optional[int] = None
    
    @abstractmethod
    async def render(self, db_session: Session, company_id: Optional[int] = None) -> None:
        """Render the page content. Must be implemented by subclasses."""
        self.db_session = db_session
        self.company_id = company_id
        
        
# from abc import ABC, abstractmethod
# from typing import Optional
# from sqlalchemy.orm import Session
# from nicegui import ui, app

# class MediaBreakpoints:
#     def __init__(self):
#         self.xs = 0
#         self.sm = 576
#         self.md = 768
#         self.lg = 992
#         self.xl = 1200

# class ScreenSize:
#     def __init__(self):
#         self.width = None
#         self.breakpoint = None
#         self.media = MediaBreakpoints()

#     async def set_breakpoint(self):
#         screen_width = app.storage.user.get("screen_width", None)
#         # screen_width = None
#         if screen_width is None:
#             self.width = await ui.run_javascript("window.screen.width;", timeout=10)
#             self.width = int(self.width)
#             app.storage.user['screen_width'] = self.width
#             self.breakpoint = self.tailwind_breakpoints()
#         else:
#             self.width = screen_width
#             self.breakpoint = self.tailwind_breakpoints()

#     def is_breakpoint(self, breakpoint):
#         return self.breakpoint == breakpoint

#     def tailwind_breakpoints(self):
#         if self.width < 768:
#             return "sm"
#         elif self.width < 1024:
#             return "md"
#         elif self.width < 1280:
#             return "lg"
#         elif self.width < 1536:
#             return "xl"
#         else:
#             return "2xl"

# class BasePage(ABC):
#     """Base class for all UI pages with responsive support."""
    
#     def __init__(self):
#         self.db_session: Optional[Session] = None
#         self.company_id: Optional[int] = None
#         self.screen_size = ScreenSize()
#         self._is_mobile = False
#         self._is_desktop = False
        
#     async def initialize_responsive(self):
#         """Initialize screen size detection and set responsive flags."""
#         await self.screen_size.set_breakpoint()
#         self._is_mobile = self.screen_size.is_breakpoint("sm")
#         self._is_desktop = not self._is_mobile
        
#     @property
#     def is_mobile(self) -> bool:
#         """Check if current screen is mobile."""
#         return self._is_mobile
        
#     @property
#     def is_desktop(self) -> bool:
#         """Check if current screen is desktop."""
#         return self._is_desktop
        
#     def get_responsive_classes(self, mobile_classes: str = "", desktop_classes: str = "") -> str:
#         """Get appropriate classes based on screen size."""
#         if self.is_mobile and mobile_classes:
#             return mobile_classes
#         elif self.is_desktop and desktop_classes:
#             return desktop_classes
#         return ""
    
#     def apply_responsive_classes(self, element, mobile_classes: str = "", desktop_classes: str = ""):
#         """Apply responsive classes to a UI element."""
#         if self.is_mobile and mobile_classes:
#             element.classes(add=mobile_classes)
#         elif self.is_desktop and desktop_classes:
#             element.classes(add=desktop_classes)
            
#     @abstractmethod
#     async def render(self, db_session: Session, company_id: Optional[int] = None) -> None:
#         """Render the page content. Must be implemented by subclasses."""
#         self.db_session = db_session
#         self.company_id = company_id
#         await self.initialize_responsive()  # 렌더링 전에 반응형 초기화
