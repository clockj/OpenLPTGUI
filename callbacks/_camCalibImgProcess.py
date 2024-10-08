import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import pydicom
import os.path
from ._blocks import Blocks
from ._texture import Texture

class CamCalibImageProcess:
    def __init__(self) -> None:

        self.filePath = None
        self.fileName = None
        self.exportImageFilePath = None
        self.currentTab = None
        
        self.height = None
        self.width = None

        self.startPos = None
        self.endPos = None
        
        self.blocks = [
            {
                'method': self.importImage,
                'name': self.importImage.__name__,
                'status': True,
                'output': None,
                'tab': 'Processing'
            },
            # {
            #     'method': self.invertImage,
            #     'name': self.invertImage.__name__,
            #     'status': False,
            #     'output': None,
            #     'tab': 'Filtering'  
            # },
            {
                'method': self.setAreaColor,
                'name': self.setAreaColor.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering',
                'isFirst': True
            },
            {
                'method': self.histogramEqualization,
                'name': self.histogramEqualization.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.brightnessAndContrast,
                'name': self.brightnessAndContrast.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.averageBlur,
                'name': self.averageBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.gaussianBlur,
                'name': self.gaussianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.medianBlur,
                'name': self.medianBlur.__name__,
                'status': False,
                'output': None,
                'tab': 'Filtering'
            },
            {
                'method': self.grayscale,
                'name': self.grayscale.__name__,
                'status': True,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.globalThresholding,
                'name': self.globalThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptativeMeanThresholding,
                'name': self.adaptativeMeanThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.adaptativeGaussianThresholding,
                'name': self.adaptativeGaussianThresholding.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.otsuBinarization,
                'name': self.otsuBinarization.__name__,
                'status': False,
                'output': None,
                'tab': 'Thresholding'
            },
            {
                'method': self.findContour,
                'name': self.findContour.__name__,
                'status': True,
                'output': None,
                'tab': 'ContourExtraction'
            },
        ]


    def executeQuery(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def executeQueryFromNext(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
                continue
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def toggleAndExecuteQuery(self, methodName, sender = None, app_data = None):
        self.toggleEffect(methodName, sender, app_data)
        if dpg.get_value(sender) is True:
            self.executeQuery(methodName)
        else:
            if methodName == 'setAreaColor':
                self.blocks[self.getIdByMethod(methodName)]['isFirst'] = True
            self.retrieveFromLastActive(methodName, sender, app_data)
            self.executeQueryFromNext(methodName)
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass

    def getIdByMethod(self, methodName):
        id = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                return id
            id += 1

    def retrieveFromLastActive(self, methodName, sender = None, app_data = None):
        self.blocks[self.getIdByMethod(methodName)]['output'] = self.blocks[self.getLastActiveBeforeMethod(methodName)]['output'].copy()
        # Texture.updateTexture(self.blocks[self.getIdByMethod(methodName)]['tab'], self.blocks[self.getIdByMethod(methodName)]['output'])
        Texture.updateTexture(self.blocks[self.getIdByMethod(methodName)]['tab'], np.flipud(self.blocks[self.getIdByMethod(methodName)]['output']))

    def getLastActiveBeforeMethod(self, methodName):
        lastActiveIndex = 0
        lastActive = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                break
            if entry['status'] is True:
                lastActiveIndex = lastActive 
            lastActive += 1
        return lastActiveIndex

    def openImage(self, filePath):
        # Check if image is .dcm or .dicom or other format
        if filePath.endswith('.dcm') or filePath.endswith('.dicom'):
            return self.openDicom(filePath)
        return self.openOtherImage(filePath)

    def openDicom(self, filePath):
        ds = pydicom.dcmread(filePath)
        pixelArray = ds.pixel_array
        _, encodedImage = cv2.imencode('.jpg', pixelArray)
        numpyarray = cv2.imdecode(encodedImage, cv2.IMREAD_COLOR)
        return numpyarray
    
    def openOtherImage(self, filePath):
        stream = open(filePath, "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        bgrImage = cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)
        return bgrImage

    def openFile(self, sender = None, app_data = None):
        self.filePath = app_data['file_path_name']
        self.fileName = app_data['file_name']

        if os.path.isfile(self.filePath) is False:
            dpg.configure_item('noPath', show=True)
            return

        dpg.set_value("brightnessSlider",0)
        dpg.set_value("contrastSlider",1)
        dpg.set_value("averageBlurSlider",1)
        # dpg.set_value("gaussianBlurSlider",1)
        dpg.set_value("medianBlurSlider",1)
        dpg.set_value("globalThresholdSlider",127)
        
        try:
            dpg.get_item_callback("removeExtractContour")()
        except:
            pass
        self.uncheckAllTags()
        for entry in self.blocks[1:-1]:
            if entry['name'] != self.grayscale.__name__:
                entry['status'] = False
        self.executeQuery('importImage')
        self.enableAllTags()
        pass

    def cancelImportImage(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_id")
        pass

    def toggleEffect(self, methodName, sender = None, app_data = None):
        for entry in self.blocks:
            if entry['name'] == methodName:
                entry['status'] = dpg.get_value(sender)
        pass

    def importImage(self, sender = None, app_data = None):
        self.blocks[Blocks.importImage.value]['output'] = self.openImage(self.filePath)

        # Texture.createAllTextures(self.blocks[Blocks.importImage.value]['output'])
        Texture.createAllTextures(np.flipud(self.blocks[Blocks.importImage.value]['output']))

        dpg.set_value('file_name_text', 'File Name: ' + self.fileName)
        dpg.set_value('file_path_text', 'File Path: ' + self.filePath)

        shape = self.blocks[Blocks.importImage.value]['output'].shape
        self.height = shape[0]
        self.width = shape[1]

        dpg.set_value('imgWidth', 'Width: ' + str(shape[1]) + 'px')
        dpg.set_value('imgHeight', 'Height: ' + str(shape[0]) + 'px')

        dpg.configure_item("exportImageAsFileProcessingGroup", show=True)
        dpg.configure_item("exportImageAsFileFilteringGroup", show=True)
        dpg.configure_item("exportImageAsFileThresholdingGroup", show=True)
    
    def invertImage(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('invertImage')]['output']
        image = cv2.bitwise_not(image)
        self.blocks[Blocks.invertImage.value]['output'] = image
        # Texture.updateTexture(self.blocks[Blocks.invertImage.value]['tab'], image)
        Texture.updateTexture(self.blocks[Blocks.invertImage.value]['tab'], np.flipud(image))
    
    def setAreaColor(self, sender=None, app_data=None):
        if self.blocks[Blocks.setAreaColor.value]['isFirst']:
            img = self.blocks[self.getLastActiveBeforeMethod('setAreaColor')]['output'].copy()
            self.blocks[Blocks.setAreaColor.value]['isFirst'] = False
            self.blocks[Blocks.setAreaColor.value]['output'] = img
        else:
            img = self.blocks[Blocks.setAreaColor.value]['output']
        
            region = dpg.get_plot_query_area(plot="FilteringPlotParent") 
            
            color = dpg.get_value('areaColorPicker')
            if color == 'White':
                color = [255, 255, 255]
            else:
                color = [0, 0, 0]
                     
            colMin = max(int(region[0]), 0)   
            colMax = min(int(region[1]), self.width-1)
            # rowMin = max(int(self.height - region[3]), 0)
            # rowMax = min(int(self.height - region[2]), self.height-1)
            rowMin = max(int(region[2]), 0)
            rowMax = min(int(region[3]), self.height-1)
            
            if rowMin != rowMax or colMin != colMax:
                img[rowMin:rowMax, colMin:colMax, 0] = int(color[2])
                img[rowMin:rowMax, colMin:colMax, 1] = int(color[1])
                img[rowMin:rowMax, colMin:colMax, 2] = int(color[0])
            
            self.blocks[Blocks.setAreaColor.value]['output'] = img
            # Texture.updateTexture(self.blocks[Blocks.setAreaColor.value]['tab'], img)
            Texture.updateTexture(self.blocks[Blocks.setAreaColor.value]['tab'], np.flipud(img))
        
    def histogramEqualization(self, sender=None, app_data=None):

        img_yuv = cv2.cvtColor(self.blocks[self.getLastActiveBeforeMethod('histogramEqualization')]['output'], cv2.COLOR_BGR2YUV)
        img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
        dst = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        self.blocks[Blocks.histogramEqualization.value]['output'] = dst
        # Texture.updateTexture(self.blocks[Blocks.histogramEqualization.value]['tab'], dst)
        Texture.updateTexture(self.blocks[Blocks.histogramEqualization.value]['tab'], np.flipud(dst))

    def brightnessAndContrast(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('brightnessAndContrast')]['output']
        alpha = dpg.get_value('contrastSlider')
        beta = dpg.get_value('brightnessSlider')
        outputImage = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        self.blocks[Blocks.brightnessAndContrast.value]['output'] = outputImage
        # Texture.updateTexture(self.blocks[Blocks.brightnessAndContrast.value]['tab'], outputImage)
        Texture.updateTexture(self.blocks[Blocks.brightnessAndContrast.value]['tab'], np.flipud(outputImage))

    def averageBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('averageBlur')]['output']

        kernelSize = (2 * dpg.get_value('averageBlurSlider')) - 1
        kernel = np.ones((kernelSize,kernelSize),np.float32)/(kernelSize*kernelSize)
        dst = cv2.filter2D(image,-1,kernel)

        self.blocks[Blocks.averageBlur.value]['output'] = dst
        # Texture.updateTexture(self.blocks[Blocks.averageBlur.value]['tab'], dst)
        Texture.updateTexture(self.blocks[Blocks.averageBlur.value]['tab'], np.flipud(dst))

    def gaussianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('gaussianBlur')]['output']

        sigma = dpg.get_value('gaussianBlurSlider')
        kernelSize = (2 * int(np.ceil(sigma))) + 1
        dst = cv2.GaussianBlur(image, (kernelSize,kernelSize), sigma)

        self.blocks[Blocks.gaussianBlur.value]['output'] = dst
        # Texture.updateTexture(self.blocks[Blocks.gaussianBlur.value]['tab'], dst)
        Texture.updateTexture(self.blocks[Blocks.gaussianBlur.value]['tab'], np.flipud(dst))

    def medianBlur(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('medianBlur')]['output']
        kernel = (2 * dpg.get_value('medianBlurSlider')) - 1

        median = cv2.medianBlur(image, kernel)

        self.blocks[Blocks.medianBlur.value]['output'] = median
        # Texture.updateTexture(self.blocks[Blocks.medianBlur.value]['tab'], median)
        Texture.updateTexture(self.blocks[Blocks.medianBlur.value]['tab'], np.flipud(median))

    def grayscale(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('grayscale')]['output'].copy()

        grayMask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image[:, :, 0] = grayMask
        image[:, :, 1] = grayMask
        image[:, :, 2] = grayMask

        self.blocks[Blocks.grayscale.value]['output'] = image
        # Texture.updateTexture(self.blocks[Blocks.grayscale.value]['tab'], image)
        Texture.updateTexture(self.blocks[Blocks.grayscale.value]['tab'], np.flipud(image))

    def globalThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('globalThresholding')]['output']
        threshold = dpg.get_value('globalThresholdSlider')

        thresholdMode = cv2.THRESH_BINARY 
        invertFlag = dpg.get_value('invertGlobalThresholding')
        if invertFlag:
            thresholdMode = cv2.THRESH_BINARY_INV

        (T, threshInv) = cv2.threshold(image, threshold, 255, thresholdMode)

        self.blocks[Blocks.globalThresholding.value]['output'] = threshInv
        # Texture.updateTexture(self.blocks[Blocks.globalThresholding.value]['tab'], threshInv)
        Texture.updateTexture(self.blocks[Blocks.globalThresholding.value]['tab'], np.flipud(threshInv))

    def adaptativeMeanThresholding(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeMeanThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptativeMeanThresholding.value]['output'] = image
        # Texture.updateTexture(self.blocks[Blocks.adaptativeMeanThresholding.value]['tab'], image)
        Texture.updateTexture(self.blocks[Blocks.adaptativeMeanThresholding.value]['tab'], np.flipud(image))

    def adaptativeGaussianThresholding(self, sender=None, app_data=None):

        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeGaussianThresholding')]['output'].copy()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshInv = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
        image = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)

        self.blocks[Blocks.adaptativeGaussianThresholding.value]['output'] = image
        # Texture.updateTexture(self.blocks[Blocks.adaptativeGaussianThresholding.value]['tab'], image)
        Texture.updateTexture(self.blocks[Blocks.adaptativeGaussianThresholding.value]['tab'], np.flipud(image))

    def otsuBinarization(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('adaptativeGaussianThresholding')]['output'].copy()
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, threshInv = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshInv = cv2.cvtColor(threshInv, cv2.COLOR_GRAY2BGR)


        self.blocks[Blocks.otsuBinarization.value]['output'] = threshInv
        # Texture.updateTexture(self.blocks[Blocks.otsuBinarization.value]['tab'], threshInv)
        Texture.updateTexture(self.blocks[Blocks.otsuBinarization.value]['tab'], np.flipud(threshInv))

    def findContour(self, sender=None, app_data=None):

        if self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'] is None:
            return

        image = self.blocks[self.getLastActiveBeforeMethod('findContour')]['output'].copy()
        # Texture.updateTexture(self.blocks[Blocks.findContour.value]['tab'], image)
        Texture.updateTexture(self.blocks[Blocks.findContour.value]['tab'], np.flipud(image))

    def exportImage(self, sender = None, app_data = None, tab = None):

        dpg.set_value('exportImageFileName', 'File Name: ')
        dpg.set_value('exportImageFilePath', 'Complete Path Name: ')
        dpg.set_value('imageNameExportAsFile', '')
        self.exportImageFilePath = None
        self.currentTab = tab
        dpg.configure_item('exportImageAsFile', show=True)
        pass

    def exportImageDirectorySelector(self, sender = None, app_data = None):
        imageName = dpg.get_value('imageNameExportAsFile')
        if imageName == '':
            return
        dpg.configure_item('exportImageAsFile', show=True)
        dpg.configure_item('exportImageDirectorySelector', show=True)
        pass

    def exportImageSelectDirectory(self, sender = None, app_data = None):
        exportImageFileName = dpg.get_value('imageNameExportAsFile')
        exportImageFilePath = app_data['file_path_name']
        self.exportImageFilePath = os.path.join(exportImageFilePath, exportImageFileName + '.jpg')
        dpg.set_value('exportImageFileName', 'File Name: ' + exportImageFileName + '.jpg')
        dpg.set_value('exportImageFilePath', 'File Path: ' + self.exportImageFilePath)
        pass

    def exportImageAsFile(self, sender = None, app_data = None):
        if self.exportImageFilePath is None:
            dpg.configure_item("exportImageError", show=True)
            return

        dpg.configure_item("exportImageError", show=False)

        lastTabIndex = {
            'Processing': Blocks.histogramEqualization.name,
            'Filtering': Blocks.grayscale.name,
            'Thresholding': Blocks.findContour.name,
        }
        path = self.exportImageFilePath
        image = self.blocks[self.getLastActiveBeforeMethod(lastTabIndex[self.currentTab])]['output']
        cv2.imwrite(path, image)
        dpg.configure_item('exportImageAsFile', show=False)

    def enableAllTags(self):
        checkboxes = [
            'setAreaColorCheckbox',
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptativeThresholdingCheckbox',
            'adaptativeGaussianThresholdingCheckbox',
            'otsuBinarization',
            'extractContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=True)
        pass

    def disableAllTags(self):
        checkboxes = [
            'setAreaColorCheckbox',
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptativeThresholdingCheckbox',
            'adaptativeGaussianThresholdingCheckbox',
            'otsuBinarization',
            'extractContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.configure_item(checkbox, enabled=False)
        pass

    def uncheckAllTags(self):
        checkboxes = [
            'setAreaColorCheckbox',
            'histogramCheckbox',
            'brightnessAndContrastCheckbox',
            'averageBlurCheckbox',
            'gaussianBlurCheckbox',
            'medianBlurCheckbox',
            'globalThresholdingCheckbox',
            'invertGlobalThresholding',
            'adaptativeThresholdingCheckbox',
            'adaptativeGaussianThresholdingCheckbox',
            'otsuBinarization',
            'extractContourButton',
            'exportImageAsFileProcessing',
            'exportImageAsFileFiltering',
            'exportImageAsFileThresholding'
        ]
        for checkbox in checkboxes:
            dpg.set_value(checkbox, False)
        
            
    # help window 
    def helpMaskArea(self, sender=None, app_data=None):
        dpg.set_value("filteringTab_helpText", "Select the area you want to remove by dragging the left mouse button over the image.")
        dpg.configure_item("filteringTab_help", show=True)
    
    def helpRemoveNoise(self, sender=None, app_data=None):
        dpg.set_value("filteringTab_helpText", "Choose some of the blurring method for removing noise of the image.")
        dpg.configure_item("filteringTab_help", show=True)