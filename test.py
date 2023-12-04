from hot_import import HotImport

import test_import
from test_import import say_hello

from test_import import TestClass

import time

mods = HotImport([test_import.say_hello])

def hello():
    print(say_hello())


def lol():
    print(test_import.lol())


def baba():
    print(test_import.baba())


while True:
    print("say_hello                : ", say_hello(), say_hello)
    print("test_import.say_hello    : ", test_import.say_hello(), test_import.say_hello)
    time.sleep(1)

# mods.stop_observer()
# mods.join_observer()
