from inspect import getmembers, getfile, ismethod, getsource

import importlib, types

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import sys, os

import time, shutil


class Mod:
    def __init__(self, functions: dict, name: str):
        for key, value in functions.items():
            setattr(self, key, value)

        setattr(self, "__name__", name)

    def ___update___(self, functions: dict, name: str):
        for key, value in functions.items():
            setattr(self, key, value)

        setattr(self, "__name__", name)


class Module(FileSystemEventHandler):
    def __init__(self, module, event_handler, auto_update: bool = True):
        # self.base_module = importlib.import_module(module.__name__)
        self.module = None
        self.auto_update = auto_update

        self.functions_mods = {}
        self.functions = {}
        self._call_event = event_handler

        if not callable(module):
            self.module_name = module.__name__
            self.module_path = os.path.abspath(module.__file__).replace("\\", "/").rsplit("/", 1)[0]
            self.base_module = module
        else:
            self.module_name = module.__module__.rsplit(".", 1)[0]
            self.module_path = getfile(module).replace("\\", "/").rsplit("/", 1)[0]
            self.base_module = importlib.import_module(self.module_name)

        self.build_informations()
        self.build_functions()

    def build_informations(self):
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
                self.functions = {**self.functions, **self.functions_mods[mod]}
        else:
            if not new_mod:
                new_mod = importlib.import_module(specific_module)

            dico = getmembers(new_mod)
            mod = specific_module.rsplit(".", 1)[-1]
            self.functions_mods[mod] = {dico[i][0]: dico[i][1] for i in range(len(dico))}
            self.functions = {**self.functions, **self.functions_mods[mod]}

        if self.auto_update and self.module:
            self.module.___update___(self.functions, self.module_name)

        else:
            self.module = Mod(self.functions, self.module_name)

    def import_code(self, code, module_name):
        module = types.ModuleType(module_name)
        exec(code, module.__dict__)
        return module

    def on_modified(self, event):
        # old_module = self.module
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

        self._call_event(self.module)


class HotImport():
    def __init__(self, modules: list = [], auto_update: bool = True, globals=None):
        self.modules_importer = {}
        caller_module = sys._getframe(1).f_globals["__name__"]
        self.modules_importer[caller_module] = sys.modules[caller_module]

        self.globals = globals
        self.modules = []
        self.functions = {}

        self.observer = Observer()
        self.callback_function = None
        self.ignore = [
            "__builtins__", "__cached__", "__file__",
            "__loader__", "__name__", "__package__",
            "__spec__", "__path__", "__doc__"
        ]

        observed = []

        for module in modules:
            caller_module = None

            if not callable(module):
                pat = os.path.abspath(module.__file__).replace("\\", "/").rsplit("/", 1)[0]
                caller_module = sys._getframe(1).f_globals[module.__name__]
            else:
                pat = getfile(module).replace("\\", "/").rsplit("/", 1)[0]
                name = module.__module__.rsplit(".", 1)[0]
                self.functions[f"{name}.{module.__name__}"] = module
                caller_module = sys._getframe(1).f_globals[name]

            if pat not in observed:
                event_handler = self.add_handler(Module(module, event_handler=self.call_event, auto_update=auto_update))
                self.observer.schedule(event_handler, path=pat, recursive=True)
                observed.append(pat)

                if caller_module:
                    self.modules_importer[caller_module.__name__] = sys.modules[caller_module.__name__]

        self.observer.start()

    def add_handler(self, handler: Module):
        self.modules.append(handler)
        return handler

    def get_module(self, module: str):
        if not isinstance(module, str):
            module = module.__name__

        for mod in self.modules:
            if mod.module_name == module:
                return mod.module

    def get_function(self, function: str):
        for mod in self.modules:
            if mod.functions.get(function.__name__):
                return mod.functions.get(function.__name__)

    def join_observer(self):
        self.observer.join()

    def stop_observer(self):
        self.observer.stop()

    def call_event(self, module):
        self.module_on_update(module)

        if self.callback_function:
            self.callback_function(module)

    def on_update(self, callback: callable = None):
        def add_debug(func):
            self.callback_function = func
            return func

        if callable(callback):
            return add_debug(callback)

        return add_debug

    def module_on_update(self, module):
        """
        updated = False
        for k, v in self.modules_importer.items():
            if k == module.__name__:
                for new_name, new_var in module.__dict__.items():
                    # if new_name not in self.ignore:
                    mod =  self.modules_importer.get("__main__")

                    print(vars(mod))
                    vars(mod)[new_name] = new_var
        """
        for k, v in self.functions.items():
            if k.startswith(f"{module.__name__}."):
                new_name = k.rsplit(".", 1)[-1]
                mod = self.modules_importer.get("__main__")
                self.functions[k] = getattr(module, new_name)
                vars(mod)[new_name] = self.functions[k]
                # print(self.functions[k])

        """
        # self.globals[new_name] = self.functions[k]
        for old_name in vars(self.module_importer).keys():
            old_func = old_name.split(".")[-1]
            for new_name, new_var in vars(module).items():
                if old_func == new_name:
                    vars(self.module_importer)[new_name] = new_var
        """
