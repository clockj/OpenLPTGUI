from ._contourExtraction import ContourExtraction
from ._opencvCalib import OpencvCalib
from ._polyCalib import PolyCalib
from ._lptImgProcess import LptCreateImgFile, LptImgProcess
from ._lptRun import LptRun
from ._vsc import Vsc

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.opencvCalib = OpencvCalib()
        self.polyCalib = PolyCalib()
        
        self.lptCreateImgFile = LptCreateImgFile()
        self.lptImgProcess = LptImgProcess()
        
        self.lptRun = LptRun()
        
        self.vsc = Vsc()
        