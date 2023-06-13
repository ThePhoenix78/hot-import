from easy_import import EasyImport
from easy_terminal import terminal

import test_import


mods = EasyImport([test_import], auto_update=True)

test_import = mods.get_module(test_import)

# print(mods.modules[1].sub_modules)


@mods.on_update()
def on_update(module):
    name = module.module_name
    print(f"\nUpdated : {name}")


myClass = test_import.TestClass(10)


@terminal()
def hello():
    print(test_import.say_hello())
    print(test_import.hello)


@terminal()
def baba():
    print(test_import.baba())


@terminal()
def show_class():
    print(myClass)


@terminal()
def add():
    myClass.a += 1
    print(myClass)


# mods.stop_observer()
# mods.join_observer()
