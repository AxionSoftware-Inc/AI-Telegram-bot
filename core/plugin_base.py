from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from aiogram.types import Message

@dataclass
class PluginResponse:
    text: Optional[str] = None
    document_path: Optional[str] = None
    handled: bool = True

class BasePlugin(ABC):
    name: str = "BasePlugin"
    description: str = "Asosiy plugin shabloni"
    priority: int = 50  # Kichikroq son = yuqori prioritet

    async def on_startup(self) -> None:
        """Bot ishga tushganda bajariladigan bir martalik sozlama"""
        pass

    async def on_shutdown(self) -> None:
        """Bot to'xtaganda resurslarni tozalash"""
        pass

    @abstractmethod
    async def can_handle(self, message: Message, context: Dict[str, Any]) -> bool:
        """Xabar ushbu pluginga tegishli yoki yo'qligini tekshirish"""
        pass

    @abstractmethod
    async def handle(self, message: Message, context: Dict[str, Any]) -> Optional[PluginResponse]:
        """Xabarni qayta ishlash va javob qaytarish"""
        pass
