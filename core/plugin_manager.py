import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from aiogram.types import Message
from core.plugin_base import BasePlugin, PluginResponse

logger = logging.getLogger("PluginManager")

class PluginManager:
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or (Path(__file__).resolve().parent.parent / "plugins")
        self.plugins: List[BasePlugin] = []

    def load_plugins(self) -> None:
        """Plugins papkasidagi barcha pluginlarni dinamik ravishda yuklaydi"""
        self.plugins.clear()
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return

        for py_file in self.plugins_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_name = f"plugins.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                # Modul ichidagi BasePlugin vorislarini topish
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                    ):
                        plugin_instance = attr()
                        self.plugins.append(plugin_instance)
                        logger.info(f"Plugin yuklandi: [{plugin_instance.name}] ({module_name})")
            except Exception as e:
                logger.error(f"Plugin yuklashda xatolik ({module_name}): {e}", exc_info=True)

        # Prioritet bo'yicha saralash (kichik son = yuqori ustunlik)
        self.plugins.sort(key=lambda p: p.priority)
        logger.info(f"Jami {len(self.plugins)} ta plugin faollashtirildi.")

    async def startup(self) -> None:
        """Barcha pluginlarning on_startup metodini chaqirish"""
        for plugin in self.plugins:
            try:
                await plugin.on_startup()
            except Exception as e:
                logger.error(f"Plugin startup xatosi [{plugin.name}]: {e}")

    async def shutdown(self) -> None:
        """Barcha pluginlarning on_shutdown metodini chaqirish"""
        for plugin in self.plugins:
            try:
                await plugin.on_shutdown()
            except Exception as e:
                logger.error(f"Plugin shutdown xatosi [{plugin.name}]: {e}")

    async def process_message(self, message: Message, context: Dict[str, Any]) -> Optional[PluginResponse]:
        """
        Xabarni navbatdagi mos pluginga yuboradi.
        Birinchi mos kelgan va qayta ishlagan plugin javobini qaytaradi.
        """
        for plugin in self.plugins:
            try:
                if await plugin.can_handle(message, context):
                    logger.info(f"Xabar [{plugin.name}] pluginiga yo'naltirildi.")
                    resp = await plugin.handle(message, context)
                    if resp and resp.handled:
                        return resp
            except Exception as e:
                logger.error(f"Plugin xatosi [{plugin.name}]: {e}", exc_info=True)

        return None
