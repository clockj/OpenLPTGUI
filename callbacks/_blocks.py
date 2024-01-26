import enum

class Blocks(enum.Enum):
    __order__ = 'importImage invertImage setAreaColor histogramEqualization brightnessAndContrast averageBlur gaussianBlur medianBlur grayscale laplacian sobel globalThresholding adaptativeMeanThresholding adaptativeGaussianThresholding otsuBinarization findContour'
    importImage = 0
    invertImage = 1
    setAreaColor = 2
    histogramEqualization = 3
    brightnessAndContrast = 4
    averageBlur = 5
    gaussianBlur = 6
    medianBlur = 7
    grayscale = 8
    laplacian = 9
    sobel = 10
    globalThresholding = 11
    adaptativeMeanThresholding = 12
    adaptativeGaussianThresholding = 13
    otsuBinarization = 14
    findContour = 15