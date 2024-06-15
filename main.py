from interface import Interface
from callbacks import Callbacks
import ctypes

class App:
    def __init__(self) -> None:
        self.interface = Interface(Callbacks())


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    app = App()