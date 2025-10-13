# modules/output/base.py
class BaseNotifier:
    def __init__(self, config, name="BaseNotifier"):
        self.config = config
        self.name = name

    async def send(self, title, message):
        raise NotImplementedError("send() must be implemented by subclass")

