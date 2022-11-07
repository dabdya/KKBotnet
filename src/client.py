import socket
import sys

from typing import Optional, Union
from abc import ABC, abstractmethod

from ipaddress import ip_address
from network import NetworkOptions, Address


class NetworkClient(ABC): 
    def __init__(self, network_options: NetworkOptions) -> None:
        self.network_options = network_options

    def change_destination(self, address: Address) -> None:
        self.network_options.address = address

    @abstractmethod
    def send_message(self, message: str) -> Optional[str]:
        pass


class SocketClient(NetworkClient):

    def send_message(self, message: str) -> Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((
                self.network_options.address.host, self.network_options.address.port)
            )
            sock.sendall(bytes(message, self.network_options.encoding))
            return self.receive(sock)

    def direct_message(self, socket: socket.socket, message: str) -> Optional[str]:
        socket.sendall(bytes(message, self.network_options.encoding))
        return self.receive(socket)

    def receive(self, socket: socket.socket) -> Optional[str]:
        received = socket.recv(self.network_options.buffer_size)
        return str(received, self.network_options.encoding)


if __name__ == "__main__":

    host, port, msg = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    network_options = NetworkOptions(
        path = None,
        address = Address(ip_address(host), port),
        buffer_size = 1024,
        encoding = "utf-8"
    )

    received = SocketClient(network_options).send_message(msg)
    print("Sent:     {}".format(msg))
    print("Received: {}".format(received))
