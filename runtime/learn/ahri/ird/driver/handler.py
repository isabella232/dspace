import digi
import digi.on as on


# validation
@on.attr
def h():
    ...


# intent back-prop
@on.mount
def h():
    ...


# status
@on.mount
def h():
    ...


# intent
@on.mount
@on.control
def h():
    ...
    

if __name__ == '__main__':
    digi.run()
