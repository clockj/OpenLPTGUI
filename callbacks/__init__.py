from ._contourExtraction import ContourExtraction
from ._opencvCalib import OpencvCalib
from ._polyCalib import PolyCalib
from ._vsc import Vsc
from ._lptImgProcess import LptCreateImgFile, LptImgProcess

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.opencvCalib = OpencvCalib()
        self.polyCalib = PolyCalib()
        self.vsc = Vsc()
        self.lptCreateImgFile = LptCreateImgFile()
        self.lptImgProcess = LptImgProcess()
        