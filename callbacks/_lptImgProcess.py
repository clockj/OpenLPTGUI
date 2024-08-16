import dearpygui.dearpygui as dpg
import numpy as np
import cv2
import os
import re
from ._texture import Texture
import enum
from multiprocessing import Pool
import itertools

class Blocks(enum.Enum):
    __order__ = 'importImg invertImg removeBkg brightnessAndContrast imAdjust labvision'
    importImg = 0
    invertImg = 1
    removeBkg = 2
    brightnessAndContrast = 3
    imAdjust = 4
    labvision = 5


class LptImgProcess:
    def __init__(self) -> None:
        # import
        self.camName = []
        self.imgFileName = []
        self.imgFilePath = []
        self.nFrame = []
        
        self.height = None
        self.width = None
        
        # image maximum intensity dictionary 
        self.imgBitDepth = {'uint8':255, 'uint16':65535, 'uint32':4294967295}
        
        # block 
        self.blocks = [
            {
                'method': self.importImg,
                'name': self.importImg.__name__,
                'status': True,
                'output': None,
            },
            {
                'method': self.invertImg,
                'name': self.invertImg.__name__,
                'status': False,
                'output': None,  
            },
            {
                'method': self.removeBkg,
                'name': self.removeBkg.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.brightnessAndContrast,
                'name': self.brightnessAndContrast.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.imAdjust,
                'name': self.imAdjust.__name__,
                'status': False,
                'output': None,
            },
            {
                'method': self.labvision,
                'name': self.labvision.__name__,
                'status': False,
                'output': None,
            },
        ]
        
        # checkbox
        self.checkboxes = [
            'lptInvertImgCheckbox',
            'lptRemoveBkgCheckbox',
            'lptBrightnessAndContrastCheckbox',
            'lptImAdjustCheckbox',
            'lptLabvisionCheckbox'
        ]
        
        # export 
        self.exportFolderPath = None

    def enableAllTags(self):
        for checkbox in self.checkboxes:
            dpg.configure_item(checkbox, enabled=True, )

    def disableAllTags(self):
        for checkbox in self.checkboxes:
            dpg.configure_item(checkbox, enabled=False)

    def uncheckAllTags(self):
        for checkbox in self.checkboxes:
            dpg.set_value(checkbox, False)
    
    def openImgFile(self, sender=None, app_data=None):
        selections = app_data['selections']
        if len(selections) == 0:
            dpg.set_value('noLptImgPathText', 'No image path file is selected!')
            dpg.configure_item('noLptImgPath', show=True)
            return
        
        self.imgFilePath = []
        self.imgFileName = []
        self.camName = []
        self.nFrame = []
        idx = 0
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noLptImgPath', show=True)
                dpg.add_text('Wrong path:', parent='noLptImgPath')
                dpg.add_text(values, parent='noLptImgPath')
                return
            self.imgFilePath.append(values)
            with open(values, 'r') as f:
                lines = f.readlines()
                self.nFrame.append(len(lines))
            self.imgFileName.append(keys)
            self.camName.append('cam' + str(idx+1))
            idx += 1
        
        # configurate listbox for selecting sample image 
        dpg.configure_item('lptImgShowID', items=self.camName)
        dpg.configure_item('lptImgFrameID', max_value=max(self.nFrame)-1)
        dpg.configure_item('lptImgFrameRangeEnd', max_value=max(self.nFrame)-1, default_value=max(self.nFrame)-1)
        self.importImg()
        
        # enable all tags
        self.enableAllTags()
        
        # update output table
        for tag in dpg.get_item_children('lptImgFileTable')[1]:
            dpg.delete_item(tag)
            
        for i in range(len(self.imgFileName)):
            with dpg.table_row(parent='lptImgFileTable'):
                dpg.add_text(self.camName[i])
                dpg.add_text(self.imgFileName[i])
                dpg.add_text(str(self.nFrame[i]) + f', ID: 0~{self.nFrame[i]-1}')
                dpg.add_text(self.imgFilePath[i])

    def cancelImgImportFile(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_imgprocess")

    def importImg(self, sender = None, app_data = None):
        # load image path 
        camName = dpg.get_value('lptImgShowID')
        camID = self.camName.index(camName)
        frameID = dpg.get_value('lptImgFrameID')
        with open(self.imgFilePath[camID], 'r') as f:
            lines = f.readlines()
            imgPath = lines[frameID].replace('\n','')
        
        self.blocks[Blocks.importImg.value]['output'] = cv2.imread(imgPath, cv2.IMREAD_ANYDEPTH)
        shape = self.blocks[Blocks.importImg.value]['output'].shape
        self.height = shape[0]
        self.width = shape[1]
        
        # update sample image
        Texture.createTexture('lptImgProcess', np.flipud(self.blocks[Blocks.importImg.value]['output']))
        
        # uncheck all selected effects 
        self.uncheckAllTags()
                
        # update background subtraction frame number
        dpg.configure_item('lptRemoveBkgFrameNum', default_value=min(1000, self.nFrame[camID]))
        if self.nFrame[camID] < 1000:
            dpg.configure_item('lptRemoveBkgFrameStep', default_value=1)
        
        # update imadjust slider 
        maxIntensity = self.imgBitDepth[self.blocks[Blocks.importImg.value]['output'].dtype.name]
        dpg.configure_item('lptImAdjustRange', max_value=maxIntensity, default_value=maxIntensity)
        
        # update labvision filter size slider
        dpg.configure_item('lptFilterSizeSlider', max_value=min(self.height, self.width))

        dpg.set_value('lptImgSampleName', 'Sample Image: ' + imgPath.split(os.sep)[-1])
        dpg.set_value('lptImgSampleSize', '(Height, Width) = (' + str(self.height) + ', ' + str(self.width) + ')')
     
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
    
    def toggleEffect(self, methodName, sender = None, app_data = None):
        for entry in self.blocks:
            if entry['name'] == methodName:
                entry['status'] = dpg.get_value(sender)
    
    def executeQuery(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
    
    def executeQueryFromNext(self, methodName):
        executeFlag = 0
        for entry in self.blocks:
            if executeFlag == 0 and entry['name'] == methodName:
                executeFlag = 1
                continue
            if executeFlag == 1 and entry['status'] is True:
                entry['method']()
    
    def getIdByMethod(self, methodName):
        id = 0
        for entry in self.blocks:
            if entry['name'] == methodName:
                return id
            id += 1
    
    def retrieveFromLastActive(self, methodName, sender = None, app_data = None):
        self.blocks[self.getIdByMethod(methodName)]['output'] = self.blocks[self.getLastActiveBeforeMethod(methodName)]['output'].copy()
        Texture.updateTexture('lptImgProcess', np.flipud(self.blocks[self.getIdByMethod(methodName)]['output']))
        
    def toggleAndExecuteQuery(self, methodName, sender = None, app_data = None):
        self.toggleEffect(methodName, sender, app_data)
        if dpg.get_value(sender) is True:
            if methodName == 'removeBkg':
                return
            self.executeQuery(methodName)
        else:
            self.retrieveFromLastActive(methodName, sender, app_data)
            self.executeQueryFromNext(methodName)
    
    def invertImg(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('invertImg')]['output']
        invertFlag = dpg.get_value('lptInvertImgCheckbox')
       
        if invertFlag is True:
            outputImage = self.invertImgfunc(image)
        else:
            outputImage = image
            
        self.blocks[Blocks.invertImg.value]['output'] = outputImage
        Texture.updateTexture('lptImgProcess', np.flipud(outputImage))
    
    def invertImgfunc(self, image):
        return cv2.bitwise_not(image)
     
    def removeBkg(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('removeBkg')]['output']
        
        camName = dpg.get_value('lptImgShowID')
        camID = self.camName.index(camName)    
        nFrameBkg = dpg.get_value('lptRemoveBkgFrameNum')
        frameStep = dpg.get_value('lptRemoveBkgFrameStep')
        
        bkg = self.getBkgfunc(image, nFrameBkg, frameStep, camID)
        outputImage = self.removeBkgfunc(image, bkg)
        
        self.blocks[Blocks.removeBkg.value]['output'] = outputImage
        Texture.updateTexture('lptImgProcess', np.flipud(outputImage))
    
    def removeBkgfunc(self, image, bkg):        
        outputImage = image - bkg
        # outputImage = bkg - image
        outputImage = np.maximum(outputImage, np.zeros(outputImage.shape))
        outputImage = np.minimum(outputImage, self.imgBitDepth[image.dtype.name]*np.ones(outputImage.shape))
        outputImage = image.dtype.type(outputImage)
        return outputImage
    
    def getBkgfunc(self, image, nFrameBkg, frameStep, camID):
        # get background image
        # bkg: float
        bkg = np.zeros(image.shape, dtype=np.float32)
        num = 0
        for i in range(0, nFrameBkg, frameStep):
            with open(self.imgFilePath[camID], 'r') as f:
                lines = f.readlines()
                imgPath = lines[i].replace('\n','')
            bkg += cv2.imread(imgPath, cv2.IMREAD_ANYDEPTH)
            num += 1
        bkg = bkg / num
        return bkg
    
    def brightnessAndContrast(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('brightnessAndContrast')]['output']
        alpha = dpg.get_value('lptContrastSlider')
        beta = dpg.get_value('lptBrightnessSlider')
        
        outputImage = self.brightnessAndContrastfunc(image, alpha, beta)
        
        self.blocks[Blocks.brightnessAndContrast.value]['output'] = outputImage
        Texture.updateTexture('lptImgProcess', np.flipud(outputImage))
    
    def brightnessAndContrastfunc(self, image, alpha, beta):
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    
    def imAdjust(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('imAdjust')]['output']
        imadjustRange = dpg.get_value('lptImAdjustRange')
        
        outputImage = self.imAdjustfunc(image, imadjustRange)
        
        self.blocks[Blocks.imAdjust.value]['output'] = outputImage
        Texture.updateTexture('lptImgProcess', np.flipud(outputImage))
    
    def imAdjustfunc(self, image, range):
        outputImage = (image - np.min(image)) / (np.max(image) - np.min(image)) * range
        outputImage = image.dtype.type(outputImage)
        return outputImage
    
    def labvision(self, sender=None, app_data=None):
        image = self.blocks[self.getLastActiveBeforeMethod('labvision')]['output']
        sigma = dpg.get_value('lptGaussianBlurSlider')
        kernelSize = dpg.get_value('lptFilterSizeSlider')
        
        outputImage = self.labvisionfunc(image, sigma, kernelSize)
        
        self.blocks[Blocks.labvision.value]['output'] = outputImage
        Texture.updateTexture('lptImgProcess', np.flipud(outputImage))
    
    def labvisionfunc(self, image, sigma, kernelSize):
        # subtrack sliding minimum
        a = image.astype(np.float32)
        b = cv2.erode(a, np.ones((3,3)))
        c = a - b
        b = cv2.erode(c, np.ones((3,3)))
        c = c - b

        # Gaussian smoothing filter
        blur_kernelSize = 2 * int(np.ceil(2 * sigma)) + 1
        d = cv2.GaussianBlur(c, (blur_kernelSize,blur_kernelSize), sigma)

        # image normalization
        # kernelSize = 101
        kernel = 1/(kernelSize**2) * np.ones((kernelSize,kernelSize))
        e = cv2.filter2D(d,-1, kernel, borderType=cv2.BORDER_CONSTANT)

        f = a - e

        # outputImage = f
        # # sharpen the image
        outputImage = self.unsharpMask(f)
        outputImage = np.maximum(outputImage, np.zeros(outputImage.shape))
        outputImage = np.minimum(outputImage, self.imgBitDepth[image.dtype.name]*np.ones(outputImage.shape))
        outputImage = image.dtype.type(outputImage)
        
        return outputImage
    
    def unsharpMask(self, image, sigma=1.0, amount=1.0, threshold=0):
        "Return a sharpened version of the image, using an unsharp mask."
        kernelSize = 2 * int(np.ceil(2 * sigma)) + 1
        blurred = cv2.GaussianBlur(image, (kernelSize,kernelSize), sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)
        return sharpened
    
    def selectFolder(self, sender=None, app_data=None):
        self.exportFolderPath = app_data['file_path_name']
        dpg.set_value('lptImgOutputFolder', 'Folder: ' + self.exportFolderPath)
    
    def cancelSelectFolder(self, sender=None, app_data=None):
        dpg.hide_item("lptImgOutputDialog")
    
    def runBatch(self, sender=None, app_data=None):
        dpg.set_value('lptImgExportStatus', 'Status: --')
        
        # create sub folder
        for i in range(len(self.imgFileName)):
            subFolderPath = os.path.join(self.exportFolderPath, self.camName[i])
            if os.path.isdir(subFolderPath) is False:
                os.mkdir(subFolderPath)
        
        # get all parameters
        invertFlag = dpg.get_value('lptInvertImgCheckbox')
        removeBkgFlag = dpg.get_value('lptRemoveBkgCheckbox')
        brightnessAndContrastFlag = dpg.get_value('lptBrightnessAndContrastCheckbox')
        imAdjustFlag = dpg.get_value('lptImAdjustCheckbox')
        labvisionFlag = dpg.get_value('lptLabvisionCheckbox')
        
        nFrameBkg = dpg.get_value('lptRemoveBkgFrameNum')
        frameStep = dpg.get_value('lptRemoveBkgFrameStep')
        alpha = dpg.get_value('lptContrastSlider')
        beta = dpg.get_value('lptBrightnessSlider')
        imadjustRange = dpg.get_value('lptImAdjustRange')
        sigma = dpg.get_value('lptGaussianBlurSlider')
        kernelSize = dpg.get_value('lptFilterSizeSlider')
        
        params = {
            'invertFlag': invertFlag,
            'removeBkgFlag': removeBkgFlag,
            'brightnessAndContrastFlag': brightnessAndContrastFlag,
            'imAdjustFlag': imAdjustFlag,
            'labvisionFlag': labvisionFlag,
            'nFrameBkg': nFrameBkg,
            'frameStep': frameStep,
            'alpha': alpha,
            'beta': beta,
            'imadjustRange': imadjustRange,
            'sigma': sigma,
            'kernelSize': kernelSize,
            'bkg': None,
        }
        
        # run batch
        nThreads = dpg.get_value('lptImgThreadNum')
        frame_start = dpg.get_value('lptImgFrameRangeStart')
        frame_end = dpg.get_value('lptImgFrameRangeEnd')
        for camID in range(len(self.imgFileName)):
            with open(self.imgFilePath[camID], 'r') as f:
                lines = f.readlines()
                nFrame = len(lines)
                
                if nFrame < frame_end:
                    frame_end = nFrame
                    print(f'Warning: {self.camName[camID]} has less than {frame_end} frames!')
            
            # get background image
            if removeBkgFlag is True:
                img = cv2.imread(lines[0].replace('\n',''), cv2.IMREAD_ANYDEPTH)
                bkg = self.getBkgfunc(img, nFrameBkg, frameStep, camID)
                params['bkg'] = bkg
            
            with Pool(nThreads) as pool:
                pool.starmap(self.batchTask, zip(itertools.repeat(camID), list(range(frame_start, frame_end+1)), itertools.repeat(params)))
        
        print('Batch processing finished!')
        dpg.set_value('lptImgExportStatus', 'Status: Finish!')
        
    def batchTask(self, camID, frameID, params):        
        with open(self.imgFilePath[camID], 'r') as f:
            lines = f.readlines()
            imgPath = lines[frameID].replace('\n','')
            imgName = imgPath.split(os.sep)[-1]
            
        # read image
        image = cv2.imread(imgPath, cv2.IMREAD_ANYDEPTH)
        
        # invert image
        if params['invertFlag'] is True:
            image = self.invertImgfunc(image)
        
        # remove background
        if params['removeBkgFlag'] is True:
            image = self.removeBkgfunc(image, params['bkg'])
        
        # brightness and contrast
        if params['brightnessAndContrastFlag'] is True:
            image = self.brightnessAndContrastfunc(image, params['alpha'], params['beta'])
        
        # imadjust
        if params['imAdjustFlag'] is True:
            image = self.imAdjustfunc(image, params['imadjustRange'])
        
        # labvision
        if params['labvisionFlag'] is True:
            image = self.labvisionfunc(image, params['sigma'], params['kernelSize'])
        
        # save image
        exportPath = os.path.join(self.exportFolderPath, self.camName[camID], imgName)
        cv2.imwrite(exportPath, image)
        
    
    def helpImportImgFile(self, sender=None, app_data=None):
        dpg.set_value('lptImgProcess_helpText', '1. Image path file contains the path to all images. \n\n2. Multiple image path files can be imported. \n\n3. Image path files should have the same prefix ending with number. The order of number should be the same as the camera files.')
        dpg.configure_item('lptImgProcess_help', show=True)


class LptCreateImgFile:
    def __init__(self) -> None:
        self.mainFolder = None 
        self.imgFolderList = []
        self.nameFormat = None 
        
        self.outputFolder = None
    
    def openFolder(self, sender=None, app_data=None):
        self.mainFolder = app_data['file_path_name']
        
        # List all items in the parent directory
        all_items = os.listdir(self.mainFolder)

        # Filter out only directories
        self.imgFolderList = [item for item in all_items if os.path.isdir(os.path.join(self.mainFolder, item))]
        
        # Print the list of folders and its corresponding name 
        for tag in dpg.get_item_children('lptCreateImgfileTable')[1]:
            dpg.delete_item(tag)
         
        for i in range(len(self.imgFolderList)):
            folder = self.imgFolderList[i]
            with dpg.table_row(parent='lptCreateImgfileTable'):
                dpg.add_text('cam'+str(i+1))
                dpg.add_text(os.path.join(self.mainFolder, folder))
        
    def cancelImportFolder(self, sender=None, app_data=None):
        dpg.hide_item("file_dialog_createImgfile")
    
    def selectOutputFolder(self, sender=None, app_data=None):
        self.outputFolder = app_data['file_path_name']
        dpg.set_value('lptImgFileOutputFolder', 'Output Folder: ' + self.outputFolder)
    
    def createImgFiles(self, sender=None, app_data=None):
        if self.outputFolder is None:
            dpg.set_value('lptImgProcessCreate_noPathText', 'No output folder is selected!')
            dpg.configure_item('lptImgProcessCreate_noPath', show=True)
            return
        
        # get parameters
        nameSuffix = dpg.get_value('lptImgNameSuffix')
        frameStart = dpg.get_value('lptImgFileFrameStart')
        frameEnd = dpg.get_value('lptImgFileFrameEnd')
        
        # create image files
        for i in range(len(self.imgFolderList)):
            imgFolder = os.path.join(self.mainFolder, self.imgFolderList[i])
            
            # find all img files in the folder
            imgFiles = self.findImgFiles(imgFolder, nameSuffix)
            frameEnd_use = min(frameEnd, len(imgFiles)-1)
            
            with open(os.path.join(self.outputFolder, 'cam{:d}ImageNames.txt'.format(i+1)), 'w') as f:
                for j in range(frameStart, frameEnd_use+1):
                    f.write(imgFiles[j] + '\n')
        
        dpg.set_value('lptImgFileExportStatus', 'Export Image File Status: Finish (ID: {:d}~{:d})!'.format(frameStart, frameEnd_use))
        
    def getFileNumber(self, filename):
        # Extract numbers from the filename using a regular expression
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else float('inf')

    def findImgFiles(self, folder_path, suffix):
        files = []
        
        # Collect all files with the given suffix
        for file in os.listdir(folder_path):
            if file.endswith(suffix):
                files.append(file)
        
        # Sort the files based on the extracted numeric value
        sorted_files = sorted(files, key=self.getFileNumber)
        
        # Return the sorted file paths
        return [os.path.join(folder_path, file) for file in sorted_files]
    
    
    def helpSelectFolder(self, sender=None, app_data=None):
        dpg.set_value('lptImgProcessCreate_helpText', '1. Select the main folder containing all camera folders. \n\n2. The camera folders should have the same prefix ending with number. \n\n3. The order of number should be the same as the camera files.')
        dpg.configure_item('lptImgProcessCreate_help', show=True)