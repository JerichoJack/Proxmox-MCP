# core/event_dispatcher.py
import asyncio
from typing import List
from core.utils import setup_logger

logger = setup_logger()


class EventDispatcher:
    """
    Receives normalized events from input modules and dispatches to enabled output modules.
    Responsible for asynchronously sending notifications to all configured output channels.
    """

    def __init__(self, notifiers: List):
        self.notifiers = notifiers or []
        logger.info(f"EventDispatcher initialized with {len(self.notifiers)} notifier(s).")

    async def dispatch(self, title: str, message: str, **kwargs):
        """
        Dispatch a message event to all enabled notifiers.
        Each notifier must implement an async send(title, message, **kwargs) method.
        """
        if not self.notifiers:
            logger.warning("No notifiers configured — event dispatch skipped.")
            return

        tasks = []
        for notifier in self.notifiers:
            try:
                tasks.append(asyncio.create_task(notifier.send(title, message, **kwargs)))
            except Exception as e:
                logger.error(f"Failed to schedule event for notifier {notifier.__class__.__name__}: {e}")

        if tasks:
            try:
                await asyncio.gather(*tasks)
                logger.info(f"Dispatched event '{title}' to {len(tasks)} notifier(s).")
            except Exception as e:
                logger.error(f"Error during event dispatch: {e}")


# Optional test when run directly
if __name__ == "__main__":
    import asyncio
    from modules.output.gotify_notifier import GotifyNotifier

    async def test_dispatcher():
        gotify = GotifyNotifier("https://gotify.example.com", "abcd1234")
        dispatcher = EventDispatcher([gotify])
        await dispatcher.dispatch("Test Event", "This is a test message", node="pve-main")

    asyncio.run(test_dispatcher())
