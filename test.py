from hot_import import HotImport

import test_import
from test_import import say_hello

from test_import import TestClass as TC

import time

t = TC()
mods = HotImport([test_import])

def hello():
    print(say_hello())


def baba():
    print(test_import.baba())


while True:
    print("say_hello : ", hello(), hello)
    print("say_hello : ", baba(), baba)
    print(TC.test(t))
    time.sleep(1)

# mods.stop_observer()
# mods.join_observer()
