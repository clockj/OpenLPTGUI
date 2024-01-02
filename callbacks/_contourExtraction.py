import dearpygui.dearpygui as dpg
import cv2
import os.path
import random
import numpy as np
import pandas as pd
from ._texture import Texture
from ._blocks import Blocks
from ._imageProcessing import ImageProcessing

class ContourExtraction:

    def __init__(self) -> None:

        self.filePath = None
        self.imageProcessing = ImageProcessing()
        self.contourTableEntry = []
        self.contourCenters = []
        self.exportFilePath = None
        self.exportFileName = None
        self.exportSelectPath = None
        self.exportSelectFileName = None
        
        self.exportCenterFilePath = None
        self.exportCenterFileName = None
        
        self.toggleDrawContoursFlag = True
        
        # Coordinate system 
        # image: (row,col)  
        #        0 -->
        #        |
        #        v
        # cv2: (col, row)
        # dpg mouse: (x,y)
        #        ^
        #        |
        #        0 -->
        self.selectAxisFlag = False
        self.selectAxisTag = None 
        self.selectAxisID = None
        self.selectAxisCount = 0
        self.height = 1 
        self.width = 1
        self.axis = np.zeros(shape=(2,4)) #         x1,y1,x2,y2
                                          # axis 1 
                                          # axis 2
        self.ptXYID = None
        self.centerExport = None # WorldX,WorldY,WorldZ,Row,Col,ImgX,ImgY
                                          
    def extractContour(self, sender=None, app_data=None):

        globalThresholdSelectedFlag = dpg.get_value('globalThresholdingCheckbox')
        adaptativeThresholdSelectedFlag = dpg.get_value('adaptativeThresholdingCheckbox')
        adaptativeGaussianThresholdSelectedFlag = dpg.get_value('adaptativeGaussianThresholdingCheckbox')
        otsuBinarizationFlag = dpg.get_value('otsuBinarization')

        if globalThresholdSelectedFlag == False and adaptativeThresholdSelectedFlag == False and adaptativeGaussianThresholdSelectedFlag == False and otsuBinarizationFlag == False:
            dpg.configure_item('nonBinary', show=True)
            return

        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.height = image.shape[0]
        self.width = image.shape[1]

        approximationMode = None
        value = dpg.get_value('approximationModeListbox')
        if value == 'None':
            approximationMode = cv2.CHAIN_APPROX_NONE
        elif value == 'Simple':
            approximationMode = cv2.CHAIN_APPROX_SIMPLE
        elif value == 'TC89_L1':
            approximationMode = cv2.CHAIN_APPROX_TC89_L1
        elif value == 'TC89_KCOS':
            approximationMode = cv2.CHAIN_APPROX_TC89_KCOS

        areaMin = dpg.get_value("regionSizeMin")**2
        areaMax = dpg.get_value("regionSizeMax")**2
        if areaMin > areaMax:
            dpg.configure_item('errRange', show=True)
            return
        cnts, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, approximationMode)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        contours = ()
        for c in cnts:
            area = cv2.contourArea(c)
            if area >= areaMin and area <= areaMax:
                contours += (c,)

        self.removeContour()

        thicknessValue = dpg.get_value('contourThicknessSlider')
        self.contourCenters = np.zeros(shape=(len(contours),2))
        for idx, contour in enumerate(contours):
            contourColor = (random.randint(0,255),random.randint(0,255),random.randint(0,255), 255)
            contourColorBGR = (contourColor[2], contourColor[1], contourColor[0])
            
            area = cv2.contourArea(contour)
            (col,row),radius = cv2.minEnclosingCircle(contour)
            centerX = col
            centerY = self.height - row
            self.contourCenters[idx,0] = centerX
            self.contourCenters[idx,1] = centerY
            self.contourTableEntry.append(
                {
                    'id': idx,
                    'centerX': centerX,
                    'centerY': centerY, 
                    'area': area,
                    'radius': radius,   
                    'color': contourColorBGR,
                    'cntColRow': contour,
                    'cntCol': [x[0][0] for x in contour],
                    'cntRow': [x[0][1] for x in contour],
                }
            )
            center = (int(col),int(row))
            radius = int(radius)
            cv2.circle(image,center,3,(0,0,255),-1)
            cv2.circle(image,center,radius,contourColorBGR,thicknessValue) 
            # cv2.drawContours(image, contour, -1, contourColor, thicknessValue)

        self.contourTableEntry = list(sorted(self.contourTableEntry, key=lambda x: x['radius'], reverse=True))

        dpg.add_separator(tag='separator1', parent='ContourExtractionParent')
        dpg.add_button(tag='toggleDrawContoursButton', width=-1, label='Hide All Contours', parent='ContourExtractionParent', callback=self.toggleDrawContours)
        dpg.add_separator(tag='separator2', parent='ContourExtractionParent')
        dpg.add_button(tag='removeExtractContour', width=-1, label='Remove Contour', parent='ContourExtractionParent', callback=self.removeContour)
        dpg.add_separator(tag='separator3', parent='ContourExtractionParent')
        dpg.add_button(tag='exportSelectedContours', width=-1, label='Export Selected Contours as Files', parent='ContourExtractionParent', callback=self.exportSelectedButtonCall)
        dpg.add_separator(tag='separator4', parent='ContourExtractionParent')
        with dpg.table(tag='ContourExtractionTable', header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, parent='ContourExtractionParent'):

            dpg.add_table_column(label="Id", width_fixed=True)
            dpg.add_table_column(label="Color", width_fixed=True)
            dpg.add_table_column(label="Visible", width_fixed=True)
            dpg.add_table_column(label="Center: (x,y)", width_fixed=True)
            dpg.add_table_column(label="Area", width_fixed=True)
            dpg.add_table_column(label="Export Contour", width_fixed=True)

            for contourEntry in self.contourTableEntry:
                with dpg.table_row():
                    for j in range(6):
                        if j == 0:
                            dpg.add_text(contourEntry['id'])
                        if j == 1:
                            dpg.add_color_button(default_value=contourEntry['color'])
                        if j == 2:
                            dpg.add_checkbox(tag='checkboxContourId' + str(contourEntry['id']), callback= lambda sender, app_data: self.redrawContours(), default_value=True)
                        if j == 3:
                            centerX = contourEntry["centerX"]
                            centerY = contourEntry["centerY"]
                            dpg.add_text(f"({centerX},{centerY})")
                        if j == 4:
                            dpg.add_text(contourEntry['area'])
                        if j == 5:
                            dpg.add_button(label='Export Individual Contour', tag="exportContour" + str(contourEntry['id']), callback=self.exportButtonCall)

        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)
        
        dpg.configure_item('Extract Plane Coordinate', show=True)

    def createAxis(self, sender=None, app_data=None):
        if self.selectAxisFlag:
            if self.selectAxisCount < 2:
                pos = dpg.get_plot_mouse_pos()
                self.selectAxisCount += 1
                self.axis[self.selectAxisID, 2*(self.selectAxisCount-1)] = pos[0]
                self.axis[self.selectAxisID, 2*(self.selectAxisCount-1)+1] = pos[1]
                
                text = f'Point {self.selectAxisCount}: ({pos[0]:.2f},{pos[1]:.2f})'
                dpg.set_value(self.selectAxisTag + f'Pt{self.selectAxisCount}', text)
                
                image = self.imageProcessing.blocks[Blocks.findContour.value]['output']
                pt = (int(pos[0]), self.height-int(pos[1]))
                cv2.drawMarker(image, pt, (0,0,255), markerType=cv2.MARKER_CROSS, 
                                markerSize=10, thickness=1)
                if self.selectAxisCount == 2:
                    pt1 = (int(self.axis[self.selectAxisID,0]), int(self.height-self.axis[self.selectAxisID,1]))
                    pt2 = (int(self.axis[self.selectAxisID,2]), int(self.height-self.axis[self.selectAxisID,3]))
                    cv2.line(image, pt1, pt2, color=(0,0,255), thickness=2)
                self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
                Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)
            else:
                self.selectAxisCount = 0
                self.selectAxisFlag = False
        pass
    
    def selectAxis(self, sender=None, app_data=None):    
        if self.selectAxisFlag and self.selectAxisTag != sender:
            dpg.configure_item('errAxis')
        else:
            self.selectAxisFlag = True
            self.selectAxisTag = sender
            self.selectAxisID = int(sender[-1]) - 1

    def extractPoints(self, sender=None, app_data=None):
        # get left axis 
        xIDMin = dpg.get_value('Axis1')
        yIDMin = dpg.get_value('Axis1_Min')
        yIDMax = dpg.get_value('Axis1_Max')
        
        x1,y1,x2,y2 = self.axis[0,:]
        pt1 = np.array([x1,y1])
        vecY = np.array([x2-x1,y2-y1]) / (yIDMax-yIDMin)
        
        # get bottom axis
        if yIDMin != dpg.get_value('Axis2'):
            dpg.configure_item('errYMin')
            return
        if xIDMin != dpg.get_value('Axis2_Min'):
            dpg.configure_item('errXMin')
            return
        xIDMax = dpg.get_value('Axis2_Max')
        
        x1,y1,x2,y2 = self.axis[1,:]
        pt2 = np.array([x1,y1])
        vecX = np.array([x2-x1,y2-y1]) / (xIDMax-xIDMin)

        
        # find idex matching
        centers = self.contourCenters[np.logical_not(np.isnan(self.contourCenters[:,0])),:]
        ncenter = centers.shape[0]
        self.ptXYID = np.zeros(shape=(ncenter,4))
        self.ptXYID[:,0:2] = centers
        self.ptXYID[:,2:4] = None
        threshold = min(np.sum(np.square(vecX)),
                        np.sum(np.square(vecY))) / 4
        ptRef = (pt1+pt2) / 2
        
        nx = xIDMax - xIDMin + 1
        ny = yIDMax - yIDMin + 1
        for i in range(0,nx):
            addX = vecX * i 
            for j in range(0,ny):
                addY = vecY * j
                add = addX + addY 
                ptGrid = ptRef + add
                
                diff = np.sum(np.square(centers - ptGrid), axis=1)
                id = np.argmin(diff)
                
                if diff[id] < threshold:
                    self.ptXYID[id, 2] = xIDMin + i
                    self.ptXYID[id, 3] = yIDMin + j
        # plot idex 
        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()
        
        for i in range(ncenter):
            if not np.isnan(self.ptXYID[i,2]):  
                center = (int(self.ptXYID[i,0]),int(self.height-self.ptXYID[i,1])) # convert into cv2 coordinate
                cv2.circle(image,center,3,(0,0,255),-1)
                
                text = f'({self.ptXYID[i,2]},{self.ptXYID[i,3]})'
                txtpos = (center[0]+5, center[1]-5)
                cv2.putText(image, text, txtpos, fontScale = 0.3, fontFace=cv2.FONT_HERSHEY_SIMPLEX, color = (250,0,0))
        
        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)
        
        dpg.configure_item('Extract World Coordinate', show=True)
        pass
    
    def extractWorldCoordinate(self, sender=None, app_data=None):
        imgAxisXTag = dpg.get_value('imgAxisX')
        imgAxisYTag = dpg.get_value('imgAxisY')
        
        if imgAxisXTag == imgAxisYTag:
            dpg.configure_item('errImgAxis', show=True)
            return
        
        imgAxisX = 0
        if imgAxisXTag == 'y':
            imgAxisX = 1
        elif imgAxisXTag == 'z':
            imgAxisX = 2
        
        imgAxisY = 1
        if imgAxisYTag == 'x':
            imgAxisY = 0
        elif imgAxisYTag == 'z':
            imgAxisY = 2
        
        imgAxisZ = 3 - imgAxisX - imgAxisY
        
        centers = self.ptXYID[np.logical_not(np.isnan(self.ptXYID[:,2])),:] # ImgX,ImgY,ImgXID,ImgYID
        self.centerExport = np.zeros(shape=(centers.shape[0],7)) # WorldX,WorldY,WorldZ,Row,Col,ImgX,ImgY
        
        unit = dpg.get_value('dist')
        self.centerExport[:,imgAxisX] = centers[:,2] * unit
        self.centerExport[:,imgAxisY] = centers[:,3] * unit
        self.centerExport[:,imgAxisZ] = dpg.get_value('Axis3')
        self.centerExport[:,3] = centers[:,0]
        self.centerExport[:,4] = self.height - centers[:,1]
        self.centerExport[:,5] = centers[:,0]
        self.centerExport[:,6] = centers[:,1]
        
        dpg.configure_item('exportCenters', show=True)
        pass 
    
    def openCentersDirectorySelector(self, sender=None, app_data=None): 
        dpg.configure_item('directoryFolderexportCenters', show=True)
        pass
    
    def selectCentersFolder(self, sender=None, app_data=None):
        self.exportCenterFilePath = app_data['file_path_name']
        self.exportCenterFileName = dpg.get_value('inputCenterNameText') + '.csv'
        filePath = os.path.join(self.exportCenterFilePath, self.exportCenterFileName)

        dpg.set_value('centerFileName', 'File Name: ' + self.exportCenterFileName)
        dpg.set_value('centerPathName', 'Complete Path Name: ' + filePath)
        pass
    
    def exportCentersToFile(self, sender=None, app_data=None):
        if self.exportCenterFilePath is None:
            dpg.configure_item("exportCentersError", show=True)
            return
        
        df = pd.DataFrame(self.centerExport, columns=['WorldX','WorldY','WorldZ','Row','Col','ImgX','ImgY'])
        df.to_csv(os.path.join(self.exportCenterFilePath, self.exportCenterFileName),index=False)
        
        dpg.configure_item("exportCenters", show=False)
        pass
    
    def toggleDrawContours(self, sender = None, app_data = None):
        self.toggleDrawContoursFlag = not self.toggleDrawContoursFlag
        if self.toggleDrawContoursFlag:
            dpg.configure_item('toggleDrawContoursButton', label="Hide All Contours")
            self.showAllContours()
        else:
            dpg.configure_item('toggleDrawContoursButton', label="Show All Contours")
            self.hideAllContours()
        pass

    def removeContour(self, sender=None, app_data=None):
        self.hideAllContours()
        dpg.delete_item('separator1')
        dpg.delete_item('removeExtractContour')
        dpg.delete_item('ContourExtractionTable')
        dpg.delete_item('toggleDrawContoursButton')
        dpg.delete_item('separator2')
        dpg.delete_item('exportAllContours')
        dpg.delete_item('exportSelectedContours')
        dpg.delete_item('separator3')
        dpg.delete_item('separator4')
        # dpg.configure_item('contourExportOption', enabled=False)
        self.contourTableEntry = []
        self.showContourFlag = True
        pass

    def redrawContours(self):
        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()

        thicknessValue = dpg.get_value('contourThicknessSlider')

        for entry in self.contourTableEntry:
            drawContour = dpg.get_value('checkboxContourId' + str(entry['id']))
            if drawContour:
                centerX = entry['centerX']
                centerY = entry['centerY']
                self.contourCenters[entry['id'],0] = centerX
                self.contourCenters[entry['id'],1] = centerY
                radius = entry['radius']
                
                center = (int(centerX),int(self.height-centerY)) # convert into cv2 coordinate
                radius = int(radius)
                cv2.circle(image,center,3,(0,0,255),-1)
                cv2.circle(image,center,radius,(entry['color'][2], entry['color'][1], entry['color'][0]),thicknessValue) 
                # cv2.drawContours(image, entry['data'], -1, (entry['color'][2], entry['color'][1], entry['color'][0]), thicknessValue)
            else:
                self.contourCenters[entry['id'],:] = None

        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)

    def hideAllContours(self, sender = None, app_data = None):
        for entry in self.contourTableEntry:
            dpg.set_value('checkboxContourId' + str(entry['id']), False)
        self.redrawContours()

    def showAllContours(self, sender = None, app_data = None):
        for entry in self.contourTableEntry:
            dpg.set_value('checkboxContourId' + str(entry['id']), True)
        self.redrawContours()

    def selectFolder(self, sender=None, app_data=None):

        self.exportFilePath = app_data['file_path_name']

        self.exportFileName = dpg.get_value('inputContourNameText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportPathName', 'Complete Path Name: ' + filePath)

        pass

    def openDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputContourId') != '' and dpg.get_value('inputContourNameText') != '':
            dpg.configure_item('directorySelectorFileDialog', show=True)

    def openExportSelectedDirectorySelector(self, sender=None, app_data=None):
        if dpg.get_value('inputSelectedContourNameText') != '':
            dpg.configure_item('directoryFolderExportSelected', show=True)
        
    def selectExportAllFolder(self, sender=None, app_data=None):
        self.exportSelectPath = app_data['file_path_name']
        self.exportSelectFileName = dpg.get_value('inputSelectedContourNameText')
        filesPath = os.path.join(self.exportSelectPath, self.exportSelectFileName + '-<id>.txt')

        dpg.set_value('exportSelectedFileName', 'File Name: ' + self.exportSelectFileName + '-<id>.txt')
        dpg.set_value('exportSelectedPathName', 'Complete Path Name: ' + filesPath)
        pass

    def exportButtonCall(self, sender, app_data=None):
        auxId = sender[13:]
        dpg.set_value('inputContourNameText', '')
        dpg.set_value('contourIdExportText', 'Contour ID: ' + auxId)
        dpg.set_value('exportFileName', 'File Name: ')
        dpg.set_value('exportPathName', 'Complete Path Name: ')
        self.exportFileName = None
        self.exportFilePath = None
        dpg.configure_item('exportContourWindow', show=True)
        pass

    def exportSelectedButtonCall(self, sender=None, app_data=None):
        dpg.set_value('inputSelectedContourNameText', '')
        dpg.set_value('exportSelectedFileName', 'File Default Name: ')
        dpg.set_value('exportSelectedPathName', 'Complete Path Name: ')

        self.exportSelectPath = None
        self.exportSelectFileName = None

        dpg.configure_item('exportSelectedContourWindow', show=True)
        pass

    def exportSelectedContourToFile(self, sender=None, app_data=None):
        if self.exportSelectPath is None:
            dpg.configure_item("exportSelectedContourError", show=True)
            return

        dpg.configure_item("exportSelectedContourError", show=False)
        selectedContours = []
        for entry in self.contourTableEntry:
            if dpg.get_value('checkboxContourId' + str(entry['id'])) == True:
                selectedContours.append(entry)

        for selectedContour in selectedContours:
            self.exportContourToFile(selectedContour['id'], os.path.join(self.exportSelectPath, self.exportSelectFileName + '_' + str(selectedContour['id'])) + '.txt')
        self.exportFilePath = None
        self.exportFileName = None
        dpg.configure_item('exportSelectedContourWindow', show=False)
        pass

    def exportIndividualContourToFile(self, sender=None, app_data=None):
        if self.exportFilePath is None:
            dpg.configure_item("exportContourError", show=True)
            return

        dpg.configure_item("exportContourError", show=False)
        auxId = int(dpg.get_value("contourIdExportText")[12:])
        self.exportContourToFile(auxId, os.path.join(self.exportFilePath, self.exportFileName))
        dpg.configure_item('exportContourWindow', show=False)
        pass

    def exportContourToFile(self, auxId, path):
        for i in self.contourTableEntry:
            if i["id"] == auxId:
                entry = i
                break
        xarray = entry["contourX"]
        yarray = entry["contourY"]

        dx = 1
        dy = 1
        xmin = min(xarray)
        ymin = min(yarray)
        xmax = max(xarray)
        ymax = max(yarray)
        nx = round((xmax - xmin)/dx) + 1
        ny = round((ymax - ymin)/dy) + 1
        xarray.append(xarray[0])
        yarray.append(yarray[0])
        self.export_coords_mesh(path, xarray, yarray, nx, ny, xmin, ymin, xmax, ymax, dx, dy)
        pass
    
    def export_coords_mesh(self, path, x, y, nx, ny, xmin, ymin, xmax, ymax, dx, dy):
        x = x[::-1]
        y = y[::-1]
        content = ''
        content = content + str(nx) + " " + str(ny) + "\n"
        content = content + str(xmin) + " " + str(ymin) + "\n"
        content = content + str(xmax) + " " + str(ymax) + "\n"
        content = content + str(dx) + " " + str(dy) + "\n"
        try:
            with open(path, "w") as dataFile:
                content += self.converte_pointArray_to_string(x,y)
                dataFile.write(content)
        except:
            print('Path does not exist for mesh export')
            return
        
    def converte_pointArray_to_string(self, x, y):
        content = ''
        i = 0
        while i < len(x):
            content = content + str(x[i]) + " " + str(y[i]) + "\n"
            i += 1
        return content