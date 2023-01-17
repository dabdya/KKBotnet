from typing import Union, Optional
from ipaddress import ip_address
from socketserver import BaseRequestHandler

from logger import LOG

from client import SocketClient
from OpenSSL.crypto import verify,load_certificate,FILETYPE_PEM
from storage import BaseStorage
from network import NetworkOptions, Address
from command import Command, InitCommand, CommandParser


class Bot(BaseRequestHandler):
    """ This class acts as a socket request handler. For each connection, 
        a new instance of the class is created, so in the constructor 
        you need to pass a storage where you can find childs and parents """

    def __init__(self, storage: BaseStorage, options: NetworkOptions, *args, **kwargs) -> None:
        self.storage, self.options = storage, options
        self.parent_requried_message = "Only parent commands are executed"
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        """Contains the request processing flow"""
        client_address = Address(
            host = ip_address(self.client_address[0]),
            port = int(self.client_address[1])
        )
        LOG.info("New request from {}".format(client_address))

        raw_data = self.request.recv(self.options.buffer_size).strip()
        
        cert = open("./cert.pem")
        raw_cert = cert.read()
        load_cert = load_certificate(FILETYPE_PEM, raw_cert)
        data = raw_data.decode(encoding = self.options.encoding)
        print(data)
        message, signed_data = data.split("@")
        print(data.split("@"))
        try:
            verify(load_cert, signed_data.encode(self.options.encoding), message, "sha256")
        except Exception as err:
            LOG.info("Failed to verify. Exit")
            return

        LOG.info("Trying extract command from request data")
        command = self.get_command(raw_data, self.options.encoding)

        if not command:
            LOG.info("Received unsupported command `{}`. Closing connection".format(command))
            SocketClient(self.options).direct_message(
                socket = self.request, message = "Unsupported command"
            )
            return

        is_command_already_execute: bool = self.storage.is_command_hashed(command)
        if is_command_already_execute:
            LOG.info("Command `{}` already executed. Closing connection".format(command))
            SocketClient(self.options).direct_message(
                socket = self.request, message = "Command is already executed"
            )
            return

        LOG.info("Hashing `{}` command".format(command))
        self.storage.add_hash_command(command)

        parent = self.storage.get_parent()
    
        if parent is not None:
            LOG.info("Extracted {} parent from storage".format(parent))
            if parent.host != client_address.host:
                LOG.info("Parent {} does not match with client {}".format(parent, client_address))
                SocketClient(self.options).direct_message(
                    socket = self.request, message = self.parent_requried_message
                )
                return
        else:
            LOG.info("Parent is empty because master mode enabled")

        if not isinstance(command, InitCommand):
            LOG.info("Forwarding command `{}` to childs".format(command))
            self.forward_command(command)

        LOG.info("Executing command `{}`".format(command))
        execute_result = self.execute_command(command)

        LOG.info("Sending backward report to {}".format(client_address))
        self.backward_report(execute_result)

    def get_command(self, raw_data: bytes, encoding: str) -> Union[Command, None]:
        """Tries parse command and returns it"""
        data = raw_data.decode(encoding = encoding)
        command = CommandParser.get_command(
            data, self.storage, self.options, delimiter = " ")
        LOG.info("Extracted command `{}`".format(command))
        return command

    def execute_command(self, command: Command) -> str:
        """Executes command and returns result"""
        return command.execute()

    def forward_command(self, command: Command) -> None:
        """Send a command to each child in the storage"""
        client = SocketClient(self.options)
        for child in self.storage.get_childs():
            LOG.info("Proccessing child {}".format(child))
            client.change_destination(child)

            response = client.send_message(str(command))
            LOG.info("Child response is `{}`".format(response))
            
            parent = self.storage.get_parent()
            if parent:
                LOG.info(
                    "Sending backward report from child {} to {}".format(child, parent))
                self.backward_report(response)

            if response == self.parent_requried_message:
                LOG.info("Deleting child {} because parent request failed".format(child))
                self.storage.delete_child(child)

    def backward_report(self, report: str) -> None:
        """Send a command result to each parent"""
        SocketClient(self.options).direct_message(socket = self.request, message = report)
