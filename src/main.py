import btdht, binascii, dotenv, random, os, time, logging


from dht import DHT

import socketserver, threading

from argparse import ArgumentParser, Namespace
from typing import Iterable, Optional
from ipaddress import ip_address
from functools import partial
from pathlib import Path

from storage import BaseStorage, InMemoryStorage
from network import NetworkOptions, Address
from client import SocketClient
from bot import Bot


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """For asynchronous request processing"""
    pass


def notify_port_changed(network_options: NetworkOptions, storage: BaseStorage) -> None:
    parent = storage.get_parent()
    client = SocketClient(network_options)
    # TODO: dodelat'


def init_parent(self_network_options: NetworkOptions, bootstrap_wait_sec: float) -> Optional[Address]:
    tracker_address = Address(ip_address("51.250.96.145"), 3000)
    dht = DHT(tracker_address)

    file_hash = os.environ.get("FILE_HASH", str())
    peers = dht.get_peers(file_hash)

    if not peers: return
    random.shuffle(peers)
    
    for host, port in peers:
        parent_address = Address(ip_address(host), max(0, int(port)))
        parent_options = NetworkOptions(
            path = None,
            address = parent_address,
            buffer_size = network_options.buffer_size,
            encoding = network_options.encoding
        )
        client = SocketClient(parent_options)
        try:
            received = client.send_message(
                f"INIT:{self_network_options.address.host}:{self_network_options.address.port}"
            )
        except TimeoutError as err:
            continue
        if received == "OK":
            return parent_address


def configure_server(network_options: NetworkOptions, bot_storage: BaseStorage) -> ThreadedTCPServer:
    bot = partial(Bot, bot_storage, network_options)
    server = ThreadedTCPServer((
        network_options.address.host, network_options.address.port), bot
    )

    if not network_options.address.port:
        network_options.change_port(server.server_address[1])

    return server


def run_server(server: ThreadedTCPServer) -> None:
    with server:
        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.start()
        print("Server startup on {}".format(network_options.address))
        server_thread.join()


def parse_args() -> Namespace:
    parser = ArgumentParser(add_help = False)
    parser.add_argument(
        "-m", "--master", action = "store_true"
    )
    parser.add_argument("-p","--port")
    return parser.parse_args()


def load_environment(file: Path) -> None:
    dotenv.load_dotenv(file)


if __name__ == "__main__":

    load_environment(file = Path("../environment.env"))
    args = parse_args()
    port_shift = int(os.environ.get("PORT_SHIFT", 0))   
    
    network_options = NetworkOptions(
        path = Path("data/network_options.json"),
        address = Address(ip_address("0.0.0.0"), int(args.port) - port_shift),
        buffer_size = 1024,
        encoding = "utf-8"
    )

    storage = InMemoryStorage()
    server = configure_server(network_options, bot_storage = storage)

    if not args.master:
        parent = init_parent(network_options, bootstrap_wait_sec = 90)
        if not parent:
            print("Parent not found")
            
            # TODO: handle case when parent was not found
        else:
            storage.change_parent(parent)
            print(parent)

    try:
        run_server(server)
    except OSError as err:
        network_options.change_port(new_port = 0)
        notify_port_changed(network_options, storage)
        server = configure_server(network_options, bot_storage = storage)
        run_server(server)
