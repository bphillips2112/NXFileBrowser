"""
NXFileRemote
the wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import os
from Pyro5.api import Proxy
import numpy as np
from nexusformat.nexus import NXFile

def message(msg):
    print("pyro client: " + str(msg))

class NXFileRemote(NXFile):
    def __init__(self, name, uri, hostname=None):
        message("proxy connect")
        proxy = Proxy(uri)
        message("proxy init")
        proxy._pyroTimeout = 20.0

        result = proxy.initfile(name)
        if result is not True:
            raise RuntimeError(f"Remote file initialization failed: {result}")

        message("file init")
        self._file = proxy
        self._filename = name
        self._mode = 'r'
        self.hostname = hostname
        self.nxpath = "/"  # Optional default path context

    def __repr__(self):
        return f'<NXFileRemote "{os.path.basename(self._filename)}" (mode {self._mode})>'

    def __getitem__(self, key):
        return self._file.getitem(self._filename, key)

    def __setitem__(self, key, value):
        # print(f"key: {key}")
        # print(f"type key: {type(key)}")
        # print(f"value: {value}")
        # print(f"type value: {type(value)}")
        return self._file.setitem(self._filename, key, value)

    def __delitem__(self, key):
        #print(f"filename: {self._filename}")
        #print(f"key: {key}")
        #print(f"type filename: {type(self._filename)}, type key: {type(key)}")
        return self._file.delitem(self._filename, key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def open(self, **kwds):
        return self

    def close(self):
        pass

    def get(self, key):
        return self._file.getitem(self._filename, key)

    def readvalue(self, path, idx=()):
        result = self._file.getvalue(self._filename, path, idx=idx)

        #if isinstance(value, _StreamResultIterator):
        #        value = list(value)

        return result

    def readvalues(self, attrs=None):
        return self._file.readvalues(self._filename, self.nxpath, attrs)

    def writevalue(self, path, value, idx=()):
        return self._file.setvalue(self._filename, path, value, idx=idx)
    
    #def update_data(self, name, value, path):
    #    return self._file.update_data(self._filename, name, value, path)
    
    def create_group(self, path):
        return self._file.create_group(self._filename, path)

    def update(self, item, path=None):
        if path:
            self.nxpath = path
        elif hasattr(item, "nxgroup"):
            self.nxpath = item.nxgroup.nxpath
        return self._file.update(self._filename, item, self.nxpath)

    def readfile(self):
        print("before nxfileremote")
        print("type of self._file" + str(type(self._file)))
        self.tree = self._file.tree(self._filename)
        print("after nxfileremote")
        #self.tree._file = self
        #self.tree._filename = self.filename
        return self.tree

    def file(self):
        raise AttributeError("remote nxfile does not have a local hdf5 file")
    
    def __del__(self):
        pass

    def is_open(self):
        return True

    @property
    def filename(self):
        return self._filename

    def _getmode(self):
        return self._mode

    def _setmode(self, mode):
        if mode in ('rw', 'r+'):
            self._mode = 'rw'
        else:
            self._mode = 'r'
        self._file.setmode(self._filename, self._mode)

    mode = property(_getmode, _setmode, doc="Read/write mode of remote file")

def nxloadremote(filename, uri, hostname=None):
    with NXFileRemote(filename, uri, hostname=hostname) as f:
        tree = f.readfile()
    return tree
