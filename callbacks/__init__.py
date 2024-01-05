from ._contourExtraction import ContourExtraction
from ._opencvCalib import OpencvCalib
from ._vsc import Vsc

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.OpencvCalib = OpencvCalib()
        self.Vsc = Vsc()