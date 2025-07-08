import msgpack_numpy as m; m.patch()
import Pyro5.api
from Pyro5.api import expose, Daemon
import os
from pathlib import Path
from nexusformat.nexus import nxload, NXgroup, NXfield
import threading
import shutil
import sys
import time
import numpy as np

import logging
logging.basicConfig()  # or your own sophisticated setup
logging.getLogger("Pyro5").setLevel(logging.DEBUG)
logging.getLogger("Pyro5.core").setLevel(logging.DEBUG)
# ... set level of other logger names as desired ...

Pyro5.config.SERIALIZER = "msgpack"

#expose browser class
@expose
def msg(msg):
    print("pyro server: " + msg)

@expose
def msgv(m, v):
    msg(m + ": " + str(v))

@expose
def shutdown(self):
        msg("server shutdown")
        time.sleep(1)
        daemon.shutdown()

@expose
class fileBrowser(object):
        root = {}

        def list_directory(self, path):
                try:
                        path_obj = Path(path)
                        return [(entry.name, entry.is_dir()) for entry in path_obj.iterdir()]
                except FileNotFoundError:
                        return "directory not found"

        def change_directory(self, current_path, new_dir):
                new_path = Path(new_dir)
                if not new_path.is_absolute():
                        new_path = Path(current_path) / new_path

                new_path = new_path.resolve()
                if new_path.is_dir():
                        os.chdir(new_path)
                        return str(new_path)
                else:
                        return "Invalid directory"

        def move_directory(self, current_path, new_path):
                try:
                        print(f"attempting to move from '{current_path}' to '{new_path}'")
                        dest = shutil.move(str(current_path), str(new_path))
                        print(f"Directory moved to '{dest}'")
                except FileNotFoundError:
                        return f"FileNotFoundError: the directory '{current_path}' does not exist"

        def make_directory(self, current_path, name):
                new_path = Path(current_path) / name
                new_path.mkdir()

        def make_file(self, name):
                try:
                        path_obj = Path(name)
                        path_obj.touch(exist_ok=False)
                except FileExistsError:
                        return f" Error '{name}' already exists"

        def remove(self, path):
                path_obj = Path(path)
                if path_obj.is_file():
                        try:
                                path_obj.unlink()
                        except FileNotFoundError:
                                return f"FileNotFoundError: the directory '{path}' does not exist"

                if path_obj.is_dir():
                        try:
                                path_obj.rmdir
                        except FileNotFoundError:
                                return f"FileNotFoundError: the directory '{path}' does not exist"

        def copy(self, file, new_file):
                try:
                        shutil.copy(str(file), str(new_file))
                except FileNotFoundError:
                        return f"FileNotFoundError: the file '{file}' does not exist"

        def open(self, file):
                try:
                        path_obj = Path(file)
                        contents = path_obj.read_text(encoding='utf-8')
                        return contents
                except FileNotFoundError:
                        return f"FileNotFoundError: the file '{file}' does not exist"

        def search(self, current_dir, search_path, suffix=None):
                try:
                        my_dir = Path(current_dir)
                        my_list = my_dir.rglob(search_path)
                        if suffix:
                        	my_list = [entry for entry in my_list if entry.suffix == suffix]
                        return [str(entry) for entry in my_list]
                except FileNotFoundError:
                        return "directory not found"

        def initfile(self, name):
                msg("Initializing NXFileService: " + name)
                try:
                        msgv("opening", name)
                        self.root[name] = nxload(name)
                except Exception as e:
                        m = "Caught exception while opening: " + name + "\n" + \
                        "Exception msg: " + str(e)
                        msg(m)
                        return m
                return True

    # We cannot expose __getitem__ via Pyro
    # Cf. pyro-core mailing list, 7/20/2014

        def getitem(self, name, key):
                msgv("getitem", key)
                obj = self.root[name][key]

                result = {
                        "type":None,
                        "nxname": obj.nxname if obj.nxname is hasattr(obj, "nxname") else key,
                        "attrs": {}
                }
                if hasattr(obj, "attrs"):
                        result["attrs"] = {m: n.nxdata for m,n in obj.attrs.items()}

                if hasattr(obj, "nxdata"):
                        result["type"] = "NXfield"
                        val = obj.nxdata
                        result["value"] = val.tolist() if hasattr(val, "tolist") else val
                        result["dtype"] = str(obj.dtype)
                        result["shape"] = obj.shape

                elif hasattr(obj, "entries"):
                        result["type"] = "NXgroup"
                        result["keys"] = list(obj.entries.keys())
                        result["class"] = obj.nxclass
                else:
                        result["type"] = str(type(obj))
                        result["str"] = str(obj)
                
                return result

    # Two-step call sequence
        def getvalue(self, name, path, idx=()):
                msgv("getvalue", idx)
                try:
                        msg("get path: " + str(path))
                        t = self.root[name][path]
                        value = t.nxdata
                        #msgv('t', t)
                        msg("returning t")

                        if isinstance(idx, list):
                                idx = tuple(idx)

                        if idx and hasattr(value, "__getitem__"):
                                value = value[idx]
                        else:
                                print("cannot index")

                        return value
                except Exception as e:
                        print("EXCEPTION in getvalue(%s): " % idx + str(e))

        def setitem(self, name, key, value):
                msgv("setitem", key)
                self.root[name][key] = value

    # Two-step call sequence
        def setvalue(self, name, path, value, idx=()):
                msgv("setvalue", idx)
                try:
                        msg("set path: " + str(path))
                        obj = self.root[name][path]
                        data = obj.nxdata

                        if idx:
                                if hasattr(data, "__setitem__"):
                                        data[idx]=value
                                else:
                                        return f"cannot index scalar value at '{path}'"
                        else:
                                obj.nxdata = value

                        return f"value at '{path}' updated to '{value}'"

                except Exception as e:
                        print("EXCEPTION in getvalue(%s): " % idx + str(e))

        def readvalues(self, name, path, attrs):
                with self.root[name].nxfile as f:
                        f.nxpath = path
                        return f.readvalues(attrs)

        def update(self, name, item, path):
                with self.root[name].nxfile as f:
                        obj = self.root[name][path]
                        f.update(obj)

        
        def delitem(self, name, path):
                try:
                        del self.root[name][path]
                        with self.root[name].nxfile as f:
                                f.nxpath = path
                                del f[path]

                        return f"deleted {path}"
                except Exception as e:
                        print(f"Error deleting: {type(e)} - {e}")
                        return f"Error deleting: {type(e)} - {e}"
                
        def tree(self, name):
                print("before server")
                t = self.root[name].tree
                print("type: " + str(type(t)))
                print("after server")
                return t

        def filename(self, name):
                return self.root[name]._filename()

        def setmode(self, name, mode):
                 self.root[name]._mode = self.root[name]._file.mode = mode

        def exit(self, code):
                msg("Daemon Exiting")
                thread = threading.Thread(target=shutdown)
                thread=setDaemon(True)
                thread.start()
