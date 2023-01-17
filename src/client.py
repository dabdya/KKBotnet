import socket, sys

from typing import Optional
from ipaddress import ip_address
from network import NetworkOptions, Address

from OpenSSL.crypto import sign, load_privatekey,FILETYPE_PEM


class NetworkClient: 
    def __init__(self, destination_network_options: NetworkOptions) -> None:
        self.destination_network_options = destination_network_options

    def change_destination(self, address: Address) -> None:
        self.destination_network_options.address = address

    def send_message(self, message: str) -> Optional[str]:
        raise NotImplementedError()


class SocketClient(NetworkClient):
    def send_message(self, message: str) -> Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((
                self.destination_network_options.address.host, 
                self.destination_network_options.address.port)
            )
            fkey = open("./key.pem")
            key = fkey.read()
            fkey.close()
            pkey = load_privatekey(FILETYPE_PEM,key)

            signed_data = sign(pkey, message, "sha256")

            sock.sendall(bytes(message, self.destination_network_options.encoding) + bytes("@","utf-8")+bytes(signed_data))
            return self.receive(sock)

    def direct_message(self, socket: socket.socket, message: str) -> Optional[str]:
        socket.sendall(bytes(message, self.destination_network_options.encoding))
        return self.receive(socket)

    def receive(self, socket: socket.socket) -> Optional[str]:
        received = socket.recv(self.destination_network_options.buffer_size)
        return str(received, self.destination_network_options.encoding)


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
