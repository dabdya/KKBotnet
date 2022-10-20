from functools import partial
from pathlib import Path
from ipaddress import ip_address
import threading
import socketserver

from storage import BaseStorage, InMemoryStorage
from network import NetworkOptions, Address
from bot import Bot


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """For asynchronous request processing"""
    pass


def run_server(network_options: NetworkOptions, bot_storage: BaseStorage) -> None:
    bot = partial(Bot, bot_storage, network_options)

    with ThreadedTCPServer((
        network_options.address.host, network_options.address.port), bot) as server:

        if not network_options.address.port:
            network_options.change_port(server.server_address[1])

        print("Server startup on {}".format(network_options.address))

        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.start(); server_thread.join()


if __name__ == "__main__":

    network_options = NetworkOptions(
        path = Path("data/network_options.json"),
        address = Address(ip_address("0.0.0.0"), 0),
        buffer_size = 1024,
        encoding = "utf-8"
    )

    try:
        run_server(network_options, bot_storage = InMemoryStorage())
    except OSError as err:
        network_options.change_port(port = 0)
        run_server(network_options, bot_storage = InMemoryStorage())
        #TODO, in this rare case, all parents should be notified
