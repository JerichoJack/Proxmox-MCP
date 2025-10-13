# modules/input/base.py
class BaseListener:
    """
    Base class for all event ingestion modules.
    """
    async def start(self):
        raise NotImplementedError("Start method must be implemented in subclass.")

    async def stop(self):
        raise NotImplementedError("Stop method must be implemented in subclass.")