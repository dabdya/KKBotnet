from typing import Union
from ipaddress import ip_address
from socketserver import BaseRequestHandler


from client import SocketClient
from storage import BaseStorage
from network import NetworkOptions, Address
from command import Command, ConsoleCommand, ChildCommand


class Bot(BaseRequestHandler):
    """ This class acts as a socket request handler. For each connection, 
        a new instance of the class is created, so in the constructor 
        you need to pass a storage where you can find childs and parents """

    def __init__(self, storage: BaseStorage, options: NetworkOptions, *args, **kwargs) -> None:
        self.storage, self.options = storage, options
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        """Contains the request processing flow"""
        print(self.storage.get_childs())
        print(self.storage.get_parents())
        raw_data = self.request.recv(self.options.buffer_size).strip()
        command = self.get_command(raw_data, self.options.encoding)

        if not command:
            SocketClient(self.options).direct_message(
                socket = self.request, message = "Unsupported command"
            ); return

        client_address = Address(
            host = ip_address(self.client_address[0]), 
            port = int(self.client_address[1])
        )

        self.storage.add_parent(client_address)
        self.forward_command(command)
        self.backward_report(self.execute_command(command))

    def get_command(self, raw_data: bytes, encoding: str) -> Union[Command, None]:
        """Tries parse command and returns it"""
        data = raw_data.decode(encoding = encoding)

        if data.find("CONSOLE") >= 0:
            _, name, *args = data.split()
            return ConsoleCommand(name, tuple(args))

        elif data.find("ADD_CHILD") >= 0:
            _, host, port = data.split(":")
            child_address = Address(host = ip_address(host), port = int(port))
            return ChildCommand(self.storage, child_address, self.options)

    def execute_command(self, command: Command) -> str:
        """Executes command and returns result"""
        return command.execute()

    def forward_command(self, command: Command) -> None:
        """Send a command to each child in the storage"""
        client = SocketClient(self.options)
        for child in self.storage.get_childs():
            client.change_destination(child)
            client.send_message(str(command))

    def backward_report(self, report: str) -> None:
        """Send a command result to each parent"""
        SocketClient(self.options).direct_message(socket = self.request, message = report)
