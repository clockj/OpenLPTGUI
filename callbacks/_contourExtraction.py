import dearpygui.dearpygui as dpg
import cv2
import os.path
import random
import numpy as np
import pandas as pd
from ._texture import Texture
from ._blocks import Blocks
from ._camCalibImgProcess import CamCalibImageProcess

class ContourExtraction:

    def __init__(self) -> None:

        self.filePath = None
        self.imageProcessing = CamCalibImageProcess()
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
        # cv2: (col, row) image_x: col, image_y: row
        # dpg mouse: (x,y)
        #        ^
        #        |
        #        0 -->
        self.selectCornersFlag = False
        self.selectCornersTag = None
        self.selectCornersCount = 0
        self.height = 1 
        self.width = 1
        self.corners = np.zeros(shape=(4,2)) #    MouseX,MouseY
                                             # BL
                                             # TL
                                             # TR
                                             # BR
        self.ptXYID = None
        self.centerExport = None # WorldX,WorldY,WorldZ,Row,Col,MouseX,MouseY
                                          
    def extractContour(self, sender=None, app_data=None):

        globalThresholdSelectedFlag = dpg.get_value('globalThresholdingCheckbox')
        adaptativeThresholdSelectedFlag = dpg.get_value('adaptativeThresholdingCheckbox')
        adaptativeGaussianThresholdSelectedFlag = dpg.get_value('adaptativeGaussianThresholdingCheckbox')
        otsuBinarizationFlag = dpg.get_value('otsuBinarization')

        # if globalThresholdSelectedFlag == False and adaptativeThresholdSelectedFlag == False and adaptativeGaussianThresholdSelectedFlag == False and otsuBinarizationFlag == False:
        #     dpg.configure_item('nonBinary', show=True)
        #     return

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
        # cnts, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, approximationMode)
        cnts, _ = cv2.findContours(image, cv2.RETR_LIST, approximationMode)
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
        if self.selectCornersFlag:
            if self.selectCornersCount < 4:
                pos = dpg.get_plot_mouse_pos()
                self.corners[self.selectCornersCount, 0] = pos[0]
                self.corners[self.selectCornersCount, 1] = pos[1]
                
                tag = self.selectCornersTag + str(self.selectCornersCount+1)
                text = dpg.get_value(tag).replace('--', f'({pos[0]:.2f},{pos[1]:.2f})')
                dpg.set_value(tag, text)
                
                image = self.imageProcessing.blocks[Blocks.findContour.value]['output']
                pt = (int(pos[0]), self.height-int(pos[1]))
                cv2.drawMarker(image, pt, (0,0,255), markerType=cv2.MARKER_CROSS, 
                               markerSize=10, thickness=1)
                
                self.selectCornersCount += 1
                if self.selectCornersCount == 4:
                    pts = self.corners.copy()
                    pts[:,1] = self.height - pts[:,1]
                    pts = np.reshape(pts.astype(np.int32), (-1,1,2))
                    cv2.polylines(image, [pts], True, color=(0,0,255), thickness=2)
                
                self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
                Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)
            else:
                self.selectCornersCount = 0
                self.selectCornersFlag = False

    def selectCorners(self, sender=None, app_data=None):
        if self.selectCornersFlag and self.selectCornersTag != sender:
            dpg.configure_item('errCorners')
        else:
            self.selectCornersFlag = True
            self.selectCornersTag = sender
    
    def extractPoints(self, sender=None, app_data=None):        
        # get axix id 
        BottomID = dpg.get_value('AxisID_Bottom')
        TopID = dpg.get_value('AxisID_Top')
        LeftID = dpg.get_value('AxisID_Left')
        RightID = dpg.get_value('AxisID_Right')
        
        # get sign for axis id 
        signX = np.sign(RightID-LeftID)
        signY = np.sign(TopID-BottomID)
        
        # get number of grids on each axis
        nx = int(abs(RightID-LeftID)) + 1
        ny = int(abs(TopID-BottomID)) + 1
        
        # get axis vectors
        ptBL = self.corners[0,:]
        ptTL = self.corners[1,:]
        ptTR = self.corners[2,:]
        ptBR = self.corners[3,:]
        leftVec = (ptTL - ptBL) / (TopID - BottomID)
        rightVec = (ptTR - ptBR) / (TopID - BottomID)
        topVec = (ptTR - ptTL) / (RightID - LeftID)
        bottomVec = (ptBR - ptBL) / (RightID - LeftID)
        
        # set threshold 
        threshold = min(np.linalg.norm(leftVec), 
                        np.linalg.norm(rightVec), 
                        np.linalg.norm(topVec), 
                        np.linalg.norm(bottomVec)) / 2
        threshold = threshold**2
        
        # find idex matching
        # centers = self.contourCenters[np.logical_not(np.isnan(self.contourCenters[:,0])),:]
        centers = self.contourCenters
        ncenter = centers.shape[0]
        self.ptXYID = np.zeros(shape=(ncenter,4))
        self.ptXYID[:,0:2] = centers
        self.ptXYID[:,2:4] = None
        
        # find axis points
        axisThreshold = dpg.get_value('axisThreshold')
        leftAxisPoints, axisPtID = self.findAxisPoints([ptBL, ptTL], centers, axisThreshold, 'y')
        if len(axisPtID) != ny:
            dpg.configure_item('errAxisPoints', show=True)
            dpg.add_text(f'Left Axis Points: {len(axisPtID)}', parent='errAxisPoints')
            dpg.add_text(str(leftAxisPoints), parent='errAxisPoints')
            return
        self.ptXYID[axisPtID,2] = LeftID
        self.ptXYID[axisPtID,3] = np.array(list(range(BottomID, TopID+1*signY, signY)), dtype=np.int32)

        rightAxisPoints, axisPtID = self.findAxisPoints([ptBR, ptTR], centers, axisThreshold, 'y')
        if len(axisPtID) != ny:
            dpg.configure_item('errAxisPoints', show=True)
            dpg.add_text(f'Right Axis Points: {len(axisPtID)}', parent='errAxisPoints')
            dpg.add_text(str(rightAxisPoints), parent='errAxisPoints')
            return
        self.ptXYID[axisPtID,2] = RightID
        self.ptXYID[axisPtID,3] = np.array(list(range(BottomID, TopID+1*signY, signY)), dtype=np.int32)
        
        topAxisPoints, axisPtID = self.findAxisPoints([ptTL, ptTR], centers, axisThreshold, 'x')
        if len(axisPtID) != nx:
            dpg.configure_item('errAxisPoints', show=True)
            dpg.add_text(f'Top Axis Points: {len(axisPtID)}', parent='errAxisPoints')
            dpg.add_text(str(topAxisPoints), parent='errAxisPoints')
            return
        self.ptXYID[axisPtID,2] = np.array(list(range(LeftID, RightID+1*signX, signX)), dtype=np.int32)
        self.ptXYID[axisPtID,3] = TopID
        
        bottomAxisPoints, axisPtID = self.findAxisPoints([ptBL, ptBR], centers, axisThreshold, 'x')
        if len(axisPtID) != nx:
            dpg.configure_item('errAxisPoints', show=True)
            dpg.add_text(f'Bottom Axis Points: {len(axisPtID)}', parent='errAxisPoints')
            dpg.add_text(str(bottomAxisPoints), parent='errAxisPoints')
            return
        self.ptXYID[axisPtID,2] = np.array(list(range(LeftID, RightID+1*signX, signX)), dtype=np.int32)
        self.ptXYID[axisPtID,3] = BottomID
        
        # find internal points
        for i in range(1,nx-1):
            for j in range(1,ny-1):
                # compute horizontal line
                pt1 = leftAxisPoints[j]
                pt2 = rightAxisPoints[j]
                vec = pt2 - pt1
                vec /= np.linalg.norm(vec)
                lineX = [pt1, vec]
                
                # compute vertical line
                pt1 = bottomAxisPoints[i]
                pt2 = topAxisPoints[i]
                vec = pt2 - pt1
                vec /= np.linalg.norm(vec)
                lineY = [pt1, vec]

                # compute cross point
                ptGrid = self.findCrossPoint(lineX, lineY)
                
                # find closest contour center
                diff = np.sum(np.square(centers - ptGrid), axis=1)
                id = np.argmin(diff)
                
                if diff[id] < threshold:
                    self.ptXYID[id, 2] = LeftID + i * signX
                    self.ptXYID[id, 3] = BottomID + j * signY
                    
        # plot idex 
        image = self.imageProcessing.blocks[self.imageProcessing.getLastActiveBeforeMethod('findContour')]['output'].copy()
        
        for i in range(ncenter):
            if not np.isnan(self.ptXYID[i,2]):  
                center = (int(self.ptXYID[i,0]),int(self.height-self.ptXYID[i,1])) # convert into cv2 coordinate
                cv2.circle(image,center,3,(0,0,255),-1)
                
                text = f'({int(self.ptXYID[i,2])},{int(self.ptXYID[i,3])})'
                txtpos = (center[0]+5, center[1]-5)
                cv2.putText(image, text, txtpos, fontScale = 0.3, fontFace=cv2.FONT_HERSHEY_SIMPLEX, color = (250,0,0))
        
        self.imageProcessing.blocks[Blocks.findContour.value]['output'] = image
        Texture.updateTexture(self.imageProcessing.blocks[Blocks.findContour.value]['tab'], image)
        
        dpg.configure_item('Extract World Coordinate', show=True)
    
    def findCrossPoint(self, line1, line2):
        pt1, vec1 = line1
        pt2, vec2 = line2
        lambda1 = (vec2[1] * (pt2[0] - pt1[0]) + vec2[0] * (pt1[1] - pt2[1])) / (vec1[0] * vec2[1] - vec1[1] * vec2[0])
        ptCross = pt1 + lambda1 * vec1
        return ptCross
    
    def findPointLineDistance(self, pt, line):
        pt1, vec = line
        diff = pt - pt1
        diffMag = np.sqrt(np.sum(np.square(diff), axis=1))
        vec2 = diff / np.reshape(diffMag, (-1,1))
        cosTheta = np.dot(vec2, vec)
        sinTheta = np.sqrt(1 - cosTheta**2)
        return sinTheta * diffMag
    
    def findAxisPoints(self, axisBoundary, centers, threshold, axisName): 
        pt1, pt2 = axisBoundary       
        lineVec = pt2 - pt1
        lineVec /= np.linalg.norm(lineVec)
        
        # calculate distance from each contour center to the line
        distance = self.findPointLineDistance(centers, [pt1, lineVec])
        
        
        if axisName == 'x':
            axisPtID = np.where((distance < threshold) & (centers[:,0] > pt1[0] - threshold) & (centers[:,0] < pt2[0] + threshold))[0]
            
            axisPoints = np.reshape(centers[axisPtID,:], (-1,2))
            x = axisPoints[:,0]
            id = np.argsort(x)
            
        elif axisName == 'y':
            axisPtID = np.where((distance < threshold) & (centers[:,1] > pt1[1] - threshold) & (centers[:,1] < pt2[1] + threshold))[0]
            
            axisPoints = np.reshape(centers[axisPtID,:], (-1,2))
            y = axisPoints[:,1]
            id = np.argsort(y)
            
        axisPoints = axisPoints[id,:]
        axisPtID = axisPtID[id]
        
        return list(axisPoints), axisPtID
    
    def extractWorldCoordinate(self, sender=None, app_data=None):
        mouseAxisXTag = dpg.get_value('mouseAxisX')
        mouseAxisYTag = dpg.get_value('mouseAxisY')
        
        if mouseAxisXTag == mouseAxisYTag:
            dpg.configure_item('errMouseAxis', show=True)
            return
        
        mouseAxisX = 0
        if mouseAxisXTag == 'y':
            mouseAxisX = 1
        elif mouseAxisXTag == 'z':
            mouseAxisX = 2
        
        mouseAxisY = 1
        if mouseAxisYTag == 'x':
            mouseAxisY = 0
        elif mouseAxisYTag == 'z':
            mouseAxisY = 2
        
        mouseAxisZ = 3 - mouseAxisX - mouseAxisY
        
        centers = self.ptXYID[np.logical_not(np.isnan(self.ptXYID[:,2])),:] # MouseX,MouseY,MouseXID,MouseYID
        self.centerExport = np.zeros(shape=(centers.shape[0],7)) # WorldX,WorldY,WorldZ,Row,Col,MouseX,MouseY
        
        unit = dpg.get_value('dist')
        self.centerExport[:,mouseAxisX] = centers[:,2] * unit
        self.centerExport[:,mouseAxisY] = centers[:,3] * unit
        self.centerExport[:,mouseAxisZ] = dpg.get_value('Axis3')
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
        
        df = pd.DataFrame(self.centerExport, columns=['WorldX','WorldY','WorldZ','Col(ImgX)','Row(ImgY)','MouseX','MouseY'])
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