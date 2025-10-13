# core/event_listener.py
class EventListener:
    """
    Central orchestrator for all input modules (event ingestion).
    """
    def __init__(self, config, callback):
        self.config = config
        self.callback = callback  # Function to process new events
        self.listeners = []

    def register_listener(self, listener):
        """Register a BaseListener-derived input module."""
        self.listeners.append(listener)

    async def start_all(self):
        """Start all registered listeners."""
        for listener in self.listeners:
            await listener.start()

    async def stop_all(self):
        """Stop all registered listeners."""
        for listener in self.listeners:
            await listener.stop()
