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
        conn.request("GET", f"/peers?hash={hash}")
        response = conn.getresponse()

        if not response.status == 200:
            print("Peers not found")
            return []

        content = response.read().decode()
        peers = [
            Address(ip_address(peer["host"]), int(peer["port"])) 
            for peer in json.loads(content)
        ]

        conn.close()
        return peers

    def add_peers(self, peers: List[Address], hash: UUID) -> None:
        conn = http.client.HTTPConnection(str(self.address))
        for address in peers:
            conn.request("POST", f"/peers?host={address.host}&port={address.port}&hash={hash}")

            response = conn.getresponse()
            content = response.read().decode()
            if not response.status == 200 or content != "OK":
                print("Peer {} not added".format(address))

        conn.close()
