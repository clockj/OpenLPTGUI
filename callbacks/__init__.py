from ._contourExtraction import ContourExtraction
from ._opencvCalib import opencvCalib

class Callbacks:
    def __init__(self) -> None:
        self.contourExtraction = ContourExtraction()
        self.imageProcessing = self.contourExtraction.imageProcessing
        self.opencvCalib = opencvCalib()