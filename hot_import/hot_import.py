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
    def __init__(self, module, event_handler: callable, auto_update: bool = True):
        # self.base_module = importlib.import_module(module.__name__)
        self.module = None
        self.auto_update: bool = auto_update

        self.functions_mods: dict = {}
        self.functions: dict = {}
        self._call_event: callable = event_handler

        if not callable(module):
            self.module_name: str = module.__name__
            self.module_path: str = os.path.abspath(module.__file__).replace("\\", "/").rsplit("/", 1)[0]
            self.base_module = module
        else:
            self.module_name: str = module.__module__.rsplit(".", 1)[0]
            self.module_path: str = getfile(module).replace("\\", "/").rsplit("/", 1)[0]
            self.base_module = importlib.import_module(self.module_name)

        self.build_informations()
        self.build_functions()

    def build_informations(self):
        self.sub_modules: list = [elem.replace(".pyw", "").replace(".py", "") for elem in os.listdir(self.module_path) if ".py" in elem]
        self.sub_modules_full: list = os.listdir(self.module_path)

    def build_functions(self, module=None, specific_module=None, new_mod=None):
        if not module:
            module = self.base_module

        if not specific_module:
            for mod in self.sub_modules:
                new_mod = importlib.import_module(f"{module.__name__}.{mod}")
                dico = getmembers(new_mod)
                self.functions_mods[mod]: dict = {dico[i][0]: dico[i][1] for i in range(len(dico))}
                self.functions: dict = {**self.functions, **self.functions_mods[mod]}
        else:
            if not new_mod:
                new_mod = importlib.import_module(specific_module)

            dico = getmembers(new_mod)
            mod: str = specific_module.rsplit(".", 1)[-1]
            self.functions_mods[mod]: dict = {dico[i][0]: dico[i][1] for i in range(len(dico))}
            self.functions: dict = {**self.functions, **self.functions_mods[mod]}

        if not self.module:
            self.module: Mod = Mod(self.functions, self.module_name)

        elif self.auto_update:
            self.module.___update___(self.functions, self.module_name)

        else:
            self.module: Mod = Mod(self.functions, self.module_name)

    def import_code(self, code, module_name):
        module = types.ModuleType(module_name)
        exec(code, module.__dict__)
        return module

    def on_modified(self, event):
        # old_module = self.module
        full_pat: str = event.src_path.replace("\\", "/")

        lib_pat: str = full_pat.rsplit("/", 1)[0]

        file_name: str = full_pat.rsplit("/", 1)[-1]
        mod_name: str = file_name.rsplit(".", 1)[0]

        if f"/{self.module_name}/" not in full_pat:
            return

        if not event.is_directory and (event.src_path.endswith('.py') or event.src_path.endswith('.pyw')):
            sucess: bool = False

            with open(full_pat, "r") as f:
                memory_file: str = f.read()

            try:
                new_mod = self.import_code(memory_file, mod_name)
                self.build_functions(specific_module=f"{lib_pat}.{mod_name}", new_mod=new_mod)
                sucess: bool = True
            except Exception:
                pass

            if not sucess:
                try:
                    temp: str = f"{time.time()}".replace(".", "_")
                    shutil.copytree(lib_pat, temp)

                    try:
                        new_mod = importlib.import_module(temp)
                        self.build_functions(new_mod, specific_module=f"{temp}.{mod_name}", new_mod=new_mod)
                    except Exception:
                        pass

                    shutil.rmtree(temp)
                    sucess: bool = True
                except Exception:
                    pass

        self._call_event(self.module)


class HotImport():
    def __init__(self, modules: list = [], auto_update: bool = True):
        self.modules: list = []
        self.functions: dict = {}
        self.observer: Observer = Observer()
        self.callback_function: callable = None
        observed: list = []
        caller_module = sys._getframe(1).f_globals["__name__"]
        self.module_importer = sys.modules[caller_module]

        for module in modules:
            if not callable(module):
                pat: str = os.path.abspath(module.__file__).replace("\\", "/").rsplit("/", 1)[0]

            else:
                pat: str = getfile(module).replace("\\", "/").rsplit("/", 1)[0]
                name: str = module.__module__.rsplit(".", 1)[0]
                self.functions[f"{name}.{module.__name__}"] = module

            if pat not in observed:
                event_handler = self.add_handler(Module(module, event_handler=self.call_event, auto_update=auto_update))
                self.observer.schedule(event_handler, path=pat, recursive=True)
                observed.append(pat)

        self.observer.start()

    def add_handler(self, handler: Module):
        self.modules.append(handler)
        return handler

    def get_module(self, module: str):
        if not isinstance(module, str):
            module: str = module.__name__

        for mod in self.modules:
            if mod.module_name == module:
                return mod.module

    def get_function(self, function: str):
        mod = self.get_module(function.__module__.rsplit(".", 1)[0])
        if mod:
            return getattr(mod, function.__name__)

    def join_observer(self):
        self.observer.join()

    def stop_observer(self):
        self.observer.stop()

    def call_event(self, module):
        # self.functions[f"{module.__module__}.{module.__name__}"] = module
        self.module_on_update(module)

        if self.callback_function:
            self.callback_function(module)

    def on_update(self, callback: callable = None):
        def add_debug(func: callable):
            self.callback_function: callable = func
            return func

        if callable(callback):
            return add_debug(callback)

        return add_debug

    def module_on_update(self, module:Mod):
        module_imported = sys.modules[module.__name__]

        for old_name, f in vars(module_imported).items():
            old_func: str = old_name.split(".")[-1]

            for new_name, new_val in vars(module).items():
                if old_func == new_name:
                    vars(module_imported)[new_name] = new_val

                    for main_var, main_val in vars(self.module_importer).items():
                        if main_val == f:
                            vars(self.module_importer)[main_var] = new_val

        # print(f"\nUpdated : {module.__name__}")
