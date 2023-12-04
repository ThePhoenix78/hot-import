from hot_import import HotImport

import test_import
from test_import import say_hello, lol

import time


mods = HotImport([test_import, say_hello, lol])
test_import = mods.get_module(test_import)


def add():
    myClass.a += 1
    print(myClass)


while True:
    print(lol())
    print(say_hello())
    print(test_import.baba())
    time.sleep(1)
