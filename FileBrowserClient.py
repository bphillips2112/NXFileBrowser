import msgpack_numpy as m; m.patch()
import Pyro5.api
import shutil
from pathlib import Path
from nexusformat.nexus import NXgroup, NXfield
from nxfileremote import NXFileRemote, nxloadremote
import numpy as np
import Pyro5.errors
import sys
import logging
logging.basicConfig()  # or your own sophisticated setup
logging.getLogger("Pyro5").setLevel(logging.DEBUG)
logging.getLogger("Pyro5.core").setLevel(logging.DEBUG)
# ... set level of other logger names as desired ...


Pyro5.config.SERIALIZER = "msgpack"

#create browser object
#uri=input("Enter server URI: ").strip()
if len(sys.argv) == 1:
        uri = raw_input("Enter URI: ")
elif len(sys.argv) == 2:
        uri = sys.argv[1] 
else:
        print("usage: client.py <URI>")
        exit(1)
Browser = Pyro5.api.Proxy(uri)

#set current path to working dir
current_path = Path.cwd()
remote_nx = None
b=True

while b:
        print("\nCurrent dir: %s" % current_path)
        entries = Browser.list_directory(str(current_path))

        #create command line in loop
        command = input(">> ").strip()

        #change directory
        if command.startswith("cd "):
                _, new_dir = command.split(maxsplit=1)
                new_dir = str(new_dir)
                result = Browser.change_directory(str(current_path), new_dir)
                if isinstance(result, str) and result != "Invalid directory":
                        current_path = Path(result)
                else:
                        print(result)

        #list directory
        elif command.startswith("ls"):
                command_parts = command.split(maxsplit=1)
                if len(command_parts) == 1:
                        path = current_path
                else:
                        path = command_parts[1]

                entries = Browser.list_directory(str(path))
                if isinstance(entries, str):
                        print(entries)
                else:
                        for name, is_dir in entries:
                                print(f"{'[DIR]' if is_dir else '[FILE]'} {name}")

        #move directory
        elif command.startswith("mv "):
                _, old_dir, new_dir = command.split(maxsplit=2)
                result = Browser.move_directory(old_dir, new_dir)
                print(result)

        #make directory
        elif command.startswith("mkdir "):
                _, name = command.split(maxsplit=1)
                name = str(name)
                result = Browser.make_directory(str(current_path), name)
                print(result)

        #remove file or directory
        elif command.startswith("rm "):
                _, path = command.split(maxsplit=1)
                result = Browser.remove(path)
                print(result)

        #create file in current directory
        elif command.startswith("touch "):
                _, name = command.split(maxsplit=1)
                result = Browser.make_file(name)
                print(result)

        #copy file or directory
        elif command.startswith("cp "):
                _, file, new_file = command.split(maxsplit=2)
                file, new_file = str(file), str(new_file)
                result = Browser.copy(file, new_file)
                print(result)

        #read and open file
        elif command.startswith("open "):
                _, file = command.split(maxsplit=1)
                opened_file = Browser.open(file)
                print(opened_file)

        elif command.startswith("search "):
                parts = command.split(maxsplit=2)
                pattern = parts[1]
                suffix = parts[2] if len(parts) > 2 else None
                list = Browser.search(str(current_path), pattern, suffix)
                if isinstance(list, str):
                        print(list)
                else:
                        for entries in list:
                        	print(entries)

        elif command.startswith("nxinit "):
                parts = command.split(maxsplit=1)
                file = parts[1]
                path = Path(file)
                if path.exists() and len(parts) == 2:
                        try:
                                remote_nx = NXFileRemote(file, uri)
                                print(f"Nexus file '{file}' initialized.")
                        except Exception as e:
                                remote_nx = None
                                print(f"initialization failed: {e}")
                else:
                        print(f"{file} does not exist or wrong number of args (takes 1)")

        elif command.startswith("nxgetitem "):
                parts = command.split(maxsplit=1)
                key = parts[1]
                path = Path(key)
                if True and (len(parts) == 2):
                        if remote_nx:
                                try:
                                        result = remote_nx.get(key)
                                        print(result)
                                except Exception as e:
                                        print(f"failed to get item: {type(e)} - {e}")
                        else:
                                print("no nexus file initialized")
                else: 
                        print(f"{key} is not a valid key or wrong number of args (takes 1)")

        elif command.startswith("nxgetvalue "):
                if remote_nx:
                        try:
                                parts = command.split()
                                path = parts[1]
                                path_test = Path(path)
                                if True:
                                        if len(parts) > 2:
                                                idx = tuple(map(int, parts[2:]))
                                        else:
                                                idx = ()

                                        result = remote_nx.readvalue(path, idx=idx)
                                        print("value", result)
                                else:
                                        print(f"{path} does not exist")
                        except Exception as e:
                                print(f"error retrieving vlaue: {e}")
                else:
                        print("no nexus file initialized")

        elif command.startswith("nxsetitem "):
                parts = command.split(maxsplit=2)
                key = parts[1]
                value = parts[2]
                path = Path(key)
                if True and len(parts) == 3:
                        if remote_nx and (remote_nx._getmode()=="rw" or remote_nx._getmode()=="w"):
                                try:
                                        parsed = eval(value, {__builtins__: {}}, {})
                                except Exception:
                                        parsed = value
                                try:
                                        result = remote_nx.__setitem__(key, parsed)
                                        print(result)
                                except Exception as e:
                                        print(f"failed to set item: {type(e)} - {e}")
                        else:
                                print("no nexus file initialized or file not set to write")
                else:
                        print(f"{key} is nota valid key or wrong number of args (takes 2)")

        elif command.startswith("nxsetvalue "):
                parts = command.split(maxsplit=2)
                path = parts[1]
                value = parts[2]
                path_test = Path(path)
                if True and len(parts) == 3:
                        if remote_nx:
                                result = eval(value)
                                remote_nx.writevalue(path, value)
                                print(result)
                        else:
                                print("no nexus file initialized")
                else:
                        print(f"{path} does not exist or wrong number of args (takes 2)")

        # elif command.startswith("nxreadvalues "):
        #         _, path  = command.split(maxsplit=1)
        #         path_test = Path(path)
        #         if True:
        #                 if remote_nx:
        #                         remote_nx.nxpath = path
        #                         result = remote_nx.readvalues(path)
        #                         print(result)
        #                 else:
        #                         print("no nexus file initialized")
        #         else:
        #                 print(f"{path} does not exist")


        elif command.startswith("nxupdate"):
                parts = command.split(maxsplit=2)
                item = parts[1]
                path = parts[2]
                if True and len(parts) == 3:
                        if remote_nx:
                                try:
                                        remote_nx.update(item, path)
                                        print("file updated")
                                except Exception as e:
                                        print(f"error during update: {type(e)} - {e}")
                        else:
                                print("no nexus file initialized")
                else:
                        print(f"{path} does not exist or wrong number of args (takes 2)")

        elif command.startswith("nxdelitem "):
                parts = command.split(maxsplit=1)
                path = parts[1]
                path_test = Path(path)
                if True and len(parts) == 2:
                        if remote_nx and (remote_nx._getmode()=="rw" or remote_nx._getmode()=="w"):
                                del remote_nx[path]
                                print("item deleted")
                        else:
                                print("no nexus file initialized or file not set to write")
                else:
                        print(f"{path} does not exist or wrong number of args (takes 1)")

        elif command.startswith("nxtree"):
                if remote_nx:
                        print("type: " + str(type(remote_nx)))
                        try:
                                tree = remote_nx.readfile()
                                #tree = remote_nx.tree()
                                #tree = nxloadremote(remote_nx.filename, uri)
                                print(tree)
                                #print("nxtree call")
                        except Exception:
                                print("exception")
                                print("".join(Pyro5.errors.get_pyro_traceback()))
                else:
                        print("no nexus file initialized")

        elif command.startswith("nxfilename"):
                if remote_nx:
                        print(remote_nx.filename)
                else:
                        print("no nexus file initialized")

        elif command.startswith("nxsetmode"):
                parts = command.split(maxsplit=1)
                mode = parts[1]
                if len(parts) == 2:
                        if remote_nx:
                                try:
                                        remote_nx._setmode(mode)
                                        print("set mode")
                                except Exception as e:
                                        print(f"set mode failed: {e}")
                        else:
                                print("no nexus file initialized")
                else:
                        print("wrong number of args (takes 1)")

        elif command.startswith("nxgetmode"):
                if remote_nx:
                        result = remote_nx.mode
                        print(f"mode: {result}")
                else:
                        print("No nexus file initialized")

        elif command == "exit":
                b=False
                
        else:
                print("Unknown command.")

