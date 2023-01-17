from typing import Union
from pathlib import Path
import json
from ipaddress import ip_address, IPv4Address, IPv6Address

from logger import LOG


class Address:
    """Incapsulates bot location"""
    def __init__(self, host: Union[IPv4Address, IPv6Address], port: int) -> None:
        self._host, self.port = host, port

    @property
    def host(self) -> str:
        return str(self._host)

    @host.setter
    def host(self, value):
        self._host = ip_address(value)
    
    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, obj: object) -> bool:  
        if not obj: 
            return False          
        return self.host == obj.host and self.port == obj.port

    def __str__(self) -> str:
        return "{}:{}".format(self._host, self.port)

    def __repr__(self) -> str:
        return str(self)


class NetworkOptions:
    def __init__(
        self, address: Union[Address, None], buffer_size: int, encoding: str) -> None:
        self.address = address
        self.buffer_size, self.encoding = buffer_size, encoding

    def try_load_from_file(self, path: Path) -> None:
        LOG.info("Trying load network options from {}".format(path))
        if not path.exists():
            LOG.info("Path {} not exists. Creating new file".format(path))
            path.parent.mkdir(parents = True, exist_ok = True)
            path.touch()

            options = {
                "host": str(self.address.host),
                "port": self.address.port,
                "buffer_size": self.buffer_size,
                "encoding": self.encoding
            }

            with open(path, "w") as options_file:
                json.dump(options, options_file)
            LOG.info("Network options saved in {}".format(path))
            LOG.info("Saved port is {}".format(self.address.port))
        
        else:
            with open(path, "r") as options_file:
                options = json.load(options_file)
                port = int(options.get("port", 0))
                LOG.info("Network options loaded from {}".format(path))
                LOG.info("Existing port is {}".format(port))

                if not self.address.port:
                    LOG.info("New port is not specified. Set existing port {}".format(port))
                    self.address.port = port

                if self.address.port != port:
                    LOG.info(
                        "New port {} is specified. Try change existsing port".format(self.address.port))
                    ok = self.change_port(path, self.address.port)
                    if not ok:
                        LOG.info("Server will use existing port {}".format(port))
                        self.address.port = port

    def change_port(self, path: Path, new_port: int) -> bool:
        if new_port <= 0 or new_port >= 65536:
            LOG.info("Invalid port {}. Existing port will not changed".format(new_port))
            return False

        with open(path, "r") as option_file:
            options = json.load(option_file)
            options["port"] = new_port

        with open(path, "w") as option_file:
            json.dump(options, option_file)

        self.address.port = options["port"]
        LOG.info("Port successfully changed. New port is {}".format(self.address.port))

        return True
