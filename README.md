# **HOW TO USE?**

```py
import test_import
...
mods = HotImport([test_import]) # Update all the 'test_import' module
```

```py
from test_import import say_hello
... #                                                                                        
mods = HotImport([say_hello]) # Update only the 'test_import.say_hello' function and the 'say_hello' function
```
```py
from test_import import TestClass as TC
...
mods = HotImport([TC]) # Update all the 'TestClass' class and 'TC'
```

### Warning !
If you have : 
```py
t = TC()
```
Then after the update `t.function()` will be the old one, you can access the new version only by using `TC.function(t)`

## DISCLAIMER

This library is new and may contain some errors

Otherwise, have fun with it as long as you declare my work
