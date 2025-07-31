import msgpack
import msgpack_numpy as m
m.patch()

from Pyro5.api import Daemon
import Pyro5.api
from FileBrowserServer import fileBrowser

Pyro5.config.SERIALIZER = "msgpack"

daemon = Daemon()
service = fileBrowser()
uri = daemon.register(service)
print("URI: " + str(uri))

daemon.requestLoop()
