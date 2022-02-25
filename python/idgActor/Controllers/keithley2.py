from importlib import reload

from idgActor.Controllers import keithley
reload(keithley)

class keithley2(keithley.keithley):
    EOL = '\n'
    pass