import socket
import sys

from typing import Union
from ipaddress import ip_address
from network import NetworkOptions, Address


class Client:
    """Client part for bot message sending functions"""
    def __init__(self, network_options: NetworkOptions) -> None:
        self._network_options = network_options
    
    def send_message(self, message: str) -> Union[str, None]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((
                self._network_options.address.host, 
                self._network_options.address.port)
            )
            sock.sendall(bytes(message, self._network_options.encoding))
            received = self._receive(sock)

        return received

    def direct_answer(self, socket: socket.socket, message: str) -> Union[str, None]:
        socket.sendall(bytes(message, self._network_options.encoding))
        return self._receive(socket)

    def change_destination(self, address: Address) -> None:
        self._network_options.address = address

    def _receive(self, socket: socket.socket) -> Union[str, None]:
        return str(socket.recv(
            self._network_options.buffer_size), self._network_options.encoding)


if __name__ == "__main__":

    """ Client as script, does not affect on work with the bot, 
        only needed for debugging """

    host, port, msg = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    network_options = NetworkOptions(
        path = None,
        address = Address(ip_address(host), port),
        buffer_size = 1024,
        encoding = "utf-8"
    )

    received = Client(network_options).send_message(msg)
    print("Sent:     {}".format(msg))
    print("Received: {}".format(received))
