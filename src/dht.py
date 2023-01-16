from network import Address
from typing import List
from uuid import UUID

import http.client, urllib.parse, json
from ipaddress import ip_address


class DHT:
    def __init__(self, address: Address) -> None:
        self.address = address

    def get_peers(self, hash: UUID) -> List[Address]:
        conn = http.client.HTTPConnection(str(self.address))
        params = urllib.parse.urlencode({'@hash': hash})
        conn.request("GET", "peers", params)
        response = conn.getresponse()

        if not response.status == 200:
            print("Peers not found")
            return []

        content = response.read().decode()
        peers = [
            Address(ip_address(peer["host"]), int(peer["port"])) 
            for peer in json.load(content)
        ]

        conn.close()
        return peers

    def add_peers(self, peers: List[Address], hash: UUID) -> None:
        conn = http.client.HTTPConnection(str(self.address))
        for address in peers:
            params = urllib.parse.urlencode({
                '@host': address.host, '@port': address.port, 'hash': hash})
            conn.request("POST", params)

            response = conn.getresponse()
            content = response.read().decode()
            if not response.status == 200 or content != "OK":
                print("Peer {} not added".format(address))

        conn.close()
