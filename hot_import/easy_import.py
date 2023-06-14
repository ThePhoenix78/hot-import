from easy_events import EasyEvents, Parameters
from inspect import getmembers

import importlib, types

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import sys, os

import time, shutil


class Mod:
    def __init__(self, functions: dict):
        for key, value in functions.items():
            setattr(self, key, value)

    def ___update___(self, functions: dict):
        for key, value in functions.items():
            setattr(self, key, value)


class Module(FileSystemEventHandler):
    def __init__(self, module, event_handler, auto_update: bool = True):
        self.base_module = module
        self.module_name = self.base_module.__name__

        self.module = None
        self.auto_update = auto_update

        self.functions_mods = {}
        self.functions = {}

        self._call_event = event_handler

        self.build_informations()
        self.build_functions()

    def build_informations(self, module=None):
        if not module:
            module = self.base_module

        self.module_path = os.path.abspath(self.base_module.__file__).replace("\\", "/").rsplit("/", 1)[0]
        self.sub_modules = [elem.replace(".pyw", "").replace(".py", "") for elem in os.listdir(self.module_path) if ".py" in elem]
        self.sub_modules_full = os.listdir(self.module_path)

    def build_functions(self, module=None, specific_module=None, new_mod=None):
        if not module:
            module = self.base_module

        if not specific_module:
            for mod in self.sub_modules:
                new_mod = importlib.import_module(f"{module.__name__}.{mod}")
                dico = getmembers(new_mod)
                self.functions_mods[mod] = {dico[i][0]: dico[i][1] for i in range(len(dico))}
                self.functions = {**self.functions, **{dico[i][0]: dico[i][1] for i in range(len(dico))}}
        else:
            if not new_mod:
                new_mod = importlib.import_module(specific_module)

            dico = getmembers(new_mod)
            mod = specific_module.rsplit(".", 1)[-1]
            self.functions_mods[mod] = {dico[i][0]: dico[i][1] for i in range(len(dico))}
            self.functions = {**self.functions, **{dico[i][0]: dico[i][1] for i in range(len(dico))}}

        if not self.module:
            self.module = Mod(self.functions)

        elif self.auto_update:
            self.module.___update___(self.functions)

        else:
            self.module = Mod(self.functions)

    def get_function(self, function: str):
        return self.functions.get(function)

    def import_code(self, code, module_name):
        module = types.ModuleType(module_name)
        exec(code, module.__dict__)
        return module

    def on_modified(self, event):
        full_pat = event.src_path.replace("\\", "/")

        lib_pat = full_pat.rsplit("/", 1)[0]

        file_name = full_pat.rsplit("/", 1)[-1]
        mod_name = file_name.rsplit(".", 1)[0]

        if f"/{self.module_name}/" not in full_pat:
            return

        if not event.is_directory and (event.src_path.endswith('.py') or event.src_path.endswith('.pyw')):
            sucess = False

            with open(full_pat, "r") as f:
                memory_file = f.read()

            try:
                new_mod = self.import_code(memory_file, mod_name)
                self.build_functions(specific_module=f"{lib_pat}.{mod_name}", new_mod=new_mod)
                sucess = True
            except Exception as e:
                pass

            if not sucess:
                try:
                    temp = f"{time.time()}".replace(".", "_")
                    shutil.copytree(lib_pat, temp)

                    try:
                        new_mod = importlib.import_module(temp)
                        self.build_functions(new_mod, specific_module=f"{temp}.{mod_name}", new_mod=new_mod)
                    except Exception as e:
                        pass

                    shutil.rmtree(temp)
                    sucess = True
                except Exception as e:
                    pass

        self._call_event(self)


class EasyImport(EasyEvents):
    def __init__(self, modules: list = [], auto_update: bool = True):
        EasyEvents.__init__(self, str_only=False, default_event=False)
        self.modules = []
        self.observer = Observer()

        for module in modules:
            event_handler = self.add_handler(Module(module, event_handler=self.call_event, auto_update=auto_update))
            pat = os.path.abspath(module.__file__).replace("\\", "/").rsplit("/", 1)[0]

            self.observer.schedule(event_handler, path=pat, recursive=True)

        self.observer.start()

    def add_handler(self, handler: Module):
        self.modules.append(handler)
        return handler

    def get_object(self, object: str):
        for elem in gc.get_objects():
            if isinstance(elem, dict) and object in str(elem):
                val = elem.get(object)
                if "<easy_import" in str(val):
                    return val

    def update(self, old_value, new_value):
        pass

    def get_module(self, module: str):
        if not isinstance(module, str):
            module = module.__name__

        for mod in self.modules:
            if mod.module_name == module:
                return mod.module

    def join_observer(self):
        self.observer.join()

    def stop_observer(self):
        self.observer.stop()

    def call_event(self, module):
        data = Parameters("on_update")

        for key, value in module.__dict__.items():
            setattr(data, key, value)

        self.trigger(data, event_type="on_update")

    def on_update(self, callback: callable = None):
        def add_debug(func):
            self.add_event(callback=func, aliases="on_update", event_type="on_update")
            return func

        if callable(callback):
            return add_debug(callback)

        return add_debug
