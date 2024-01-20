import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import pandas as pd
import os.path

class OpencvCalib:
    def __init__(self) -> None:
        self.exportFilePath = None
        self.exportFileName = None
        
        # Input: camera calibration parameters
        self.camcalibFilePath = []
        self.camcalibFileName = []
        self.camcalibData = [] # list of pandas dataframes
        self.camcalibPt2D = [] # 
        self.camcalibPt3D = [] #
        self.imgSize = None
        
        # Input: pose calibration parameters
        self.posecalibFilePath = []
        self.posecalibFileName = []
        self.posecalibData = None # list of pandas dataframes
        self.posecalibPt2D = None #
        self.posecalibPt3D = None #
        
        # Output: camera parameter
        self.camcalibErr = None
        self.camMat = None 
        self.distCoeff = None
        
        self.posecalibErr = None
        self.rotVec = None
        self.rotMat = None
        self.transVec = None
        

    def calibrateCamera(self, sender=None, app_data=None):
        if len(self.camcalibFilePath) == 0:
            dpg.configure_item('noOpencvPath', show=True)
            dpg.add_text('No file imported', parent='noOpencvPath')
            return
        
        width = dpg.get_value('inputOpencvCamWidth')  
        height = dpg.get_value('inputOpencvCamHeight')
        self.imgSize = (width, height)

        # Perform camera calibration
        self.camcalibErr, self.camMat, self.distCoeff, _, _ = cv2.calibrateCamera(
            self.camcalibPt3D, self.camcalibPt2D, self.imgSize, None, None
        )
        
        # Print outputs onto the output window 
        dpg.configure_item('opencvCalibGroup', show=True)
        dpg.set_value('opencvCamcalibErr', f'Camera Calibration Error: {self.camcalibErr}')
        dpg.set_value('opencvCamMat', f'{self.camMat}')
        dpg.set_value('opencvDistCoeff', f'{self.distCoeff}')
        
        dpg.configure_item('OpenCV Calibrate Pose Parameters', show=True)

    def calibratePose(self, sender=None, app_data=None):
        if len(self.posecalibFilePath) == 0:
            dpg.configure_item('noOpencvPath', show=True)
            dpg.add_text('No file imported', parent='noOpencvPath')
            return
        
        # Get optimization method
        optMethod = dpg.get_value('opencvPoseOptMethod')
        optFlag = cv2.SOLVEPNP_ITERATIVE
        if optMethod == 'SOLVEPNP_EPNP':
            optFlag = cv2.SOLVEPNP_EPNP
        elif optMethod == 'SOLVEPNP_IPPE':
            optFlag = cv2.SOLVEPNP_IPPE
        elif optMethod == 'SOLVEPNP_SQPNP':
            optFlag = cv2.SOLVEPNP_SQPNP
        
        # Perform pose calibration
        _, self.rotVec, self.transVec = cv2.solvePnP(
            self.posecalibPt3D, self.posecalibPt2D, self.camMat, self.distCoeff, flags=optFlag)
        self.rotMat = cv2.Rodrigues(self.rotVec)[0]
        
        pt2D, _ = cv2.projectPoints(
            self.posecalibPt3D, self.rotVec, self.transVec, self.camMat, self.distCoeff)
        self.posecalibErr = cv2.norm(pt2D, self.posecalibPt2D, cv2.NORM_L2)/self.posecalibPt2D.shape[0]
        
        # Print outputs onto the output window 
        dpg.set_value('opencvPosecalibErr', f'Pose Calibration Error: {self.posecalibErr}')
        dpg.set_value('opencvRotMat', f'{self.rotMat}')
        dpg.set_value('opencvRotVec', f'{self.rotVec}')
        dpg.set_value('opencvTransVec', f'{self.transVec}')
        
        dpg.configure_item('buttonExportOpencvCalib', show=True)
       
    def openCamcalibFile(self, sender = None, app_data = None): 
        self.camcalibFilePath = []
        self.camcalibFileName = []
        self.camcalibData = []
        
        selections = app_data['selections']
        nFiles = len(selections)
        if nFiles == 0:
            dpg.configure_item('noOpencvPath', show=True)
            dpg.add_text('No file selected', parent='noOpencvPath')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noOpencvPath', show=True)
                dpg.add_text('Wrong path:')
                dpg.add_text(values, parent='noOpencvPath')
                return
            self.camcalibFilePath.append(values)
            self.camcalibFileName.append(keys)
        
        for i in range(nFiles):
            df = pd.read_csv(self.camcalibFilePath[i])
            self.camcalibData.append(df)
            
            pt2d = np.array(df.loc[:,['Col(ImgX)','Row(ImgY)']], np.float32)
            self.camcalibPt2D.append(np.reshape(pt2d, (pt2d.shape[0],1,2)))
            
            pt3d = np.array(df.loc[:,['WorldX','WorldY','WorldZ']], np.float32)
            pt3d[:,2] = 0 # OpenCV require: z=0 for camera calibtraion
            self.camcalibPt3D.append(np.reshape(pt3d, (pt3d.shape[0],1,3)))
        
        # Print outputs onto the output window 
        dpg.configure_item('opencvOutputParent', show=True)
        for tag in dpg.get_item_children('opencvCamcalibFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(nFiles):
            with dpg.table_row(parent='opencvCamcalibFileTable'):
                dpg.add_text(self.camcalibFileName[i])
                dpg.add_text(self.camcalibFilePath[i])
        
    def cancelCamcalibImportFile(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_opencvCamCalib")

    def openPoseCalibFile(self, sender = None, app_data = None):
        self.posecalibFilePath = []
        self.posecalibFileName = []
        self.posecalibData = None 
        self.posecalibPt2D = None 
        self.posecalibPt3D = None 
        
        selections = app_data['selections']
        nFiles = len(selections)
        if nFiles == 0:
            dpg.configure_item('noOpencvPath', show=True)
            dpg.add_text('No file selected', parent='noOpencvPath')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noOpencvPath', show=True)
                dpg.add_text('Wrong path:')
                dpg.add_text(values, parent='noOpencvPath')
                return
            self.posecalibFilePath.append(values)
            self.posecalibFileName.append(keys)
        
        df = pd.DataFrame()
        for i in range(nFiles):
            df = pd.concat([df, pd.read_csv(self.posecalibFilePath[i])], ignore_index=True)
        self.posecalibData = df
        
        pt2d = np.array(df.loc[:,['Col(ImgX)','Row(ImgY)']], np.float32)
        self.posecalibPt2D = np.reshape(pt2d, (pt2d.shape[0],1,2))
        
        pt3d = np.array(df.loc[:,['WorldX','WorldY','WorldZ']], np.float32)
        pt3d[:,2] = 0 # OpenCV require: z=0 for camera calibtraion
        self.posecalibPt3D = np.reshape(pt3d, (pt3d.shape[0],1,3))
        
        # Print outputs onto the output window 
        with dpg.table_row(parent='opencvPosecalibFileTable'):
            dpg.add_text(self.posecalibFileName[i])
            dpg.add_text(self.posecalibFilePath[i])
        pass
    
    def cancelPoseCalibImportFile(self, sender = None, app_data = None):
        dpg.hide_item("file_dialog_opencvPoseCalib")
    
    def selectFolder(self, sender = None, app_data = None):
        self.exportFilePath = app_data['file_path_name']
        self.exportFileName = dpg.get_value('inputOpencvCalibFileText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportOpencvFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportOpencvPathName', 'Complete Path Name: ' + filePath)
    
    def exportOpencvCalib(self, sender = None, app_data = None):
        if self.exportFilePath is None:
            dpg.configure_item('exportOpencvCalibError', show=True)
            return
        
        dpg.configure_item('exportOpencvCalibError', show=False)
        filePath = os.path.join(self.exportFilePath, self.exportFileName)
        
        with open(filePath, 'w') as f:
            f.write('# Camera Calibration Error: \n' + str(self.camcalibErr) + '\n')
            f.write('# Pose Calibration Error: \n' + str(self.posecalibErr) + '\n')
            
            f.write('# Camera Matrix: \n')
            f.write(str(self.camMat[0,0])+','+str(self.camMat[0,1])+','+str(self.camMat[0,2])+'\n')
            f.write(str(self.camMat[1,0])+','+str(self.camMat[1,1])+','+str(self.camMat[1,2])+'\n')
            f.write(str(self.camMat[2,0])+','+str(self.camMat[2,1])+','+str(self.camMat[2,2])+'\n')
            f.write('# Distortion Coefficients: \n')
            f.write(str(self.distCoeff[0,0])+','+str(self.distCoeff[0,1])+','+str(self.distCoeff[0,2])+','+str(self.distCoeff[0,3])+','+str(self.distCoeff[0,4])+'\n')
            f.write('# Rotation Vector: \n')
            f.write(str(self.rotVec[0,0])+','+str(self.rotVec[1,0])+','+str(self.rotVec[2,0])+'\n')
            f.write('# Rotation Matrix: \n')
            f.write(str(self.rotMat[0,0])+','+str(self.rotMat[0,1])+','+str(self.rotMat[0,2])+'\n')
            f.write(str(self.rotMat[1,0])+','+str(self.rotMat[1,1])+','+str(self.rotMat[1,2])+'\n')
            f.write(str(self.rotMat[2,0])+','+str(self.rotMat[2,1])+','+str(self.rotMat[2,2])+'\n')
            f.write('# Inverse of Rotation Matrix: \n')
            rotMatInv = np.linalg.inv(self.rotMat)
            f.write(str(rotMatInv[0,0])+','+str(rotMatInv[0,1])+','+str(rotMatInv[0,2])+'\n')
            f.write(str(rotMatInv[1,0])+','+str(rotMatInv[1,1])+','+str(rotMatInv[1,2])+'\n')
            f.write(str(rotMatInv[2,0])+','+str(rotMatInv[2,1])+','+str(rotMatInv[2,2])+'\n')
            f.write('# Translation Vector: \n')
            f.write(str(self.transVec[0,0])+','+str(self.transVec[1,0])+','+str(self.transVec[2,0])+'\n')
            f.write('# Inverse of Translation Vector: \n')
            transVecInv = -np.matmul(rotMatInv, self.transVec)
            f.write(str(transVecInv[0,0])+','+str(transVecInv[1,0])+','+str(transVecInv[2,0])+'\n')
            
        dpg.configure_item("exportOpencvCalib", show=False)

    
    