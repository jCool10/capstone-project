"""Base query engine."""

import logging
from abc import abstractmethod
from typing import Any, List, Optional

from src.callbacks.callback_manager import CallbackManager

logger = logging.getLogger(__name__)


class BaseEngine:
    """Base query engine."""

    def __init__(
        self, 
        callback_manager: Optional[CallbackManager],
    ) -> None:
        self.callback_manager = callback_manager or CallbackManager([])

    @abstractmethod
    def run_engine(self):
        pass

    @abstractmethod
    async def arun_engine(self):
        pass