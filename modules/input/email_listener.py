# modules/email_listener.py
import asyncio
import email
import imaplib
from core.config import MCPConfig

class EmailListener:
    """
    Polls an IMAP mailbox for Proxmox event notifications.
    Supports standalone, clustered, and mixed lab topologies.
    """

    def __init__(self, config: MCPConfig, event_callback):
        """
        :param config: MCPConfig instance
        :param event_callback: async function to handle parsed email events
        """
        self.config = config
        self.event_callback = event_callback
        self._running = False

    async def _poll_mailbox(self, node_label: str):
        """
        Poll the configured mailbox for new messages.
        Node label is used for tagging events (e.g., 'pve-main', 'pbs-main').
        """
        server = self.config._get_list("EVENT_EMAIL_IMAP_SERVER")
        port = self.config._get_int("EVENT_EMAIL_IMAP_PORT", 993)
        username = self.config._get_list("EVENT_EMAIL_USERNAME")[0]
        password = self.config._get_list("EVENT_EMAIL_PASSWORD")[0]
        folder = self.config._get_list("EVENT_EMAIL_FOLDER")[0] or "INBOX"
        interval = self.config.email_poll_interval

        while self._running:
            try:
                imap = imaplib.IMAP4_SSL(server, port)
                imap.login(username, password)
                imap.select(folder)
                status, messages = imap.search(None, 'UNSEEN')
                if status != "OK":
                    await asyncio.sleep(interval)
                    continue

                for num in messages[0].split():
                    res, msg_data = imap.fetch(num, "(RFC822)")
                    if res != "OK":
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    subject = msg.get("subject", "")
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    event = {
                        "node": node_label,
                        "subject": subject,
                        "body": body,
                    }

                    await self.event_callback(node_label, event)
                    imap.store(num, '+FLAGS', '\\Seen')

                imap.logout()
            except Exception as e:
                print(f"[Email] Error polling mailbox for node {node_label}: {e}")
            await asyncio.sleep(interval)

    async def start(self):
        """Start email polling for all nodes that have email alerts configured."""
        if not self.config.event_email_enabled:
            print("[Email] Email listener is disabled in config.")
            return

        self._running = True
        self._tasks = []

        # Poll once per node defined in PVE/PBS
        for node in self.config.pve_nodes + self.config.pbs_nodes:
            task = asyncio.create_task(self._poll_mailbox(node))
            self._tasks.append(task)

        print(f"[Email] Email listener started for nodes: {', '.join(self.config.pve_nodes + self.config.pbs_nodes)}")

    async def stop(self):
        """Stop email polling."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        print("[Email] Email listener stopped.")
