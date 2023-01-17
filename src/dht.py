from network import Address
from typing import List

from ipaddress import ip_address
import http.client, json

from logger import LOG


class DHT:
    def get_peers(self, hash: str) -> List[Address]:
        raise NotImplementedError()


class MockDHT(DHT):
    def __init__(self, address: Address, timeout: int = 5, *args, **kwargs) -> None:
        super(MockDHT, self).__init__(*args, **kwargs)
        self.address, self.timeout = address, timeout
        self.default_peers = []
        self.success_post_message = "OK"

    def get_peers(self, hash: str) -> List[Address]:
        conn = http.client.HTTPConnection(str(self.address), timeout = self.timeout)
        LOG.info("Open connection for {}".format(self.address))

        try:
            destination_path = f"/peers?hash={hash}"
            LOG.info("Send request to {}{}".format(self.address, destination_path))
            conn.request("GET", destination_path)

        except http.client.socket.timeout as err:
            LOG.info("Request timeout on {}{}".format(self.address, destination_path))
            return self.default_peers

        except ConnectionRefusedError as err:
            LOG.info("Request failed {}".format(err))
            return self.default_peers

        response = conn.getresponse()

        if not response.status == http.client.OK:
            LOG.info("Bad request. Response status {}".format(response.status))
            return self.default_peers

        content = response.read().decode()
        peers = [
            Address(ip_address(peer.get("host", "0.0.0.0")), int(peer.get("port", 0))) 
            for peer in json.loads(content)
        ]

        LOG.info("Found {} peers".format("\n".join(peers)))
        LOG.info("Close connection for {}".format(self.address))
        conn.close()
        return peers

    def add_peers(self, peers: List[Address], hash: str) -> None:
        conn = http.client.HTTPConnection(str(self.address))
        LOG.info("Open connection for {}".format(self.address))

        def post(peer_address: Address) -> http.client.HTTPResponse:
            try:
                destination_path = f"/peers?host={peer_address.host}&port={peer_address.port}&hash={hash}"
                LOG.info("Send request to {}{}".format(self.address, destination_path))
                conn.request("POST", destination_path)

            except http.client.socket.timeout as err:
                LOG.info("Request timeout on {}{}".format(self.address, destination_path))
                return http.client.HTTPResponse(status = http.client.REQUEST_TIMEOUT)

            except ConnectionRefusedError as err:
                LOG.info("Request failed {}".format(err))
                return http.client.HTTPResponse(status = http.client.BAD_REQUEST)

            response = conn.getresponse()
            return response
        
        for peer_address in peers:
            response = post(peer_address)
            content = response.read().decode()

            if not response.status == http.client.OK or content != self.success_post_message:
                LOG.info("Peer {} not added".format(peer_address))

        LOG.info("Close connection for {}".format(self.address))
        conn.close()
