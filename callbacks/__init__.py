from ._contourExtraction import ContourExtraction
from ._opencvCalib import OpencvCalib
from ._vsc import Vsc
from ._lptImgProcess import LptImgProcess

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.opencvCalib = OpencvCalib()
        self.vsc = Vsc()
        self.lptImgProcess = LptImgProcess()
        