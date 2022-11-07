from unittest import TestCase

from typing import Optional

from command import ChildCommand
from storage import InMemoryStorage
from client import NetworkClient

from network import Address, NetworkOptions
from ipaddress import ip_address


class MockClient(NetworkClient):
    def __init__(self, *args, **kwargs) -> None:
        self.sent_messages = 0
        super(MockClient, self).__init__(*args, **kwargs)

    def send_message(self, message: str) -> Optional[str]:
        self.sent_messages += 1


class ChildCommandTestCase(TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()
        self.child = Address(ip_address("8.8.8.8"), 8)

        options = NetworkOptions(
            path = None, address = None, buffer_size = 1024, encoding = "utf-8"
        )

        self.client = MockClient(options)

    def test_command_is_redirected_to_all_childs(self) -> None:
        ChildCommand(self.storage, self.child, self.client).execute()
        self.assertEqual(self.client.sent_messages, 0)

        ChildCommand(self.storage, self.child, self.client).execute()
        self.assertEqual(self.client.sent_messages, 1)

    def test_command_adds_child_to_storage(self) -> None:
        for _ in range(2):
            ChildCommand(self.storage, self.child, self.client).execute()
        self.assertSetEqual(self.storage.get_childs(), {self.child, })
