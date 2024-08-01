import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import pandas as pd
import os.path
from ._texture import Texture

class PolyCalib:
    def __init__(self) -> None:
        self.exportFilePath = None
        self.exportFileName = None
        
        # Input: polynomial calibration parameters
        self.calibFilePath = []
        self.calibFileName = []
        self.calibData = None # pandas dataframes
        self.calibPt2D = None 
        self.calibPt3D = None
        self.imgSize = None # (width, height)
        self.order = None # order of polynomial
        self.refPlane = None # reference plane
        
        # Output: polynomial coefficients
        self.exportFilePath = None
        self.exportFileName = None
        self.order_mat = None
        self.coeff_imgX = None
        self.coeff_imgY = None
        self.err = None
        
        
    def openFile(self, sender = None, app_data = None):
        self.calibFilePath = []
        self.calibFileName = []
        self.calibData = None 
        self.calibPt2D = None 
        self.calibPt3D = None 
        
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
            self.calibFilePath.append(values)
            self.calibFileName.append(keys)
        
        df = pd.DataFrame()
        for i in range(nFiles):
            df = pd.concat([df, pd.read_csv(self.calibFilePath[i])], ignore_index=True)
        self.calibData = df
        
        pt2d = np.array(df.loc[:,['Col(ImgX)','Row(ImgY)']], np.float32)
        self.calibPt2D = np.reshape(pt2d, (pt2d.shape[0],2))
        
        pt3d = np.array(df.loc[:,['WorldX','WorldY','WorldZ']], np.float32)
        self.calibPt3D = np.reshape(pt3d, (pt3d.shape[0],3))
        
        # Print outputs onto the output window 
        for tag in dpg.get_item_children('polyCalibFileTable')[1]:
            dpg.delete_item(tag)
            
        for i in range(nFiles):
            with dpg.table_row(parent='polyCalibFileTable'):
                dpg.add_text(self.calibFileName[i])
                dpg.add_text(self.calibFilePath[i])
        
    def cancelImportFile(self, sender = None, app_data = None):
        dpg.hide_item('file_dialog_polyCalib')
    
    def draw_plus(self, image, center, color=(0, 0, 255), size=5, thickness=1):
        cx, cy = center
        cv2.line(image, (cx - size, cy), (cx + size, cy), color, thickness)
        cv2.line(image, (cx, cy - size), (cx, cy + size), color, thickness)

    def calibrateCamera(self, sender = None, app_data = None):
        if len(self.calibFilePath) == 0:
            dpg.configure_item('noPolyPath', show=True)
            return
        
        self.imgSize = (dpg.get_value('inputPolyCamWidth'), dpg.get_value('inputPolyCamHeight'))
        self.order = dpg.get_value('inputPolyOrder')
        
        # create xyz matrix
        order_mat = []
        for i in range(0,self.order+1):
            for j in range(0,self.order+1-i):
                for k in range(0,self.order+1-i-j):
                    order_mat.append([i,j,k])
        order_mat = np.array(order_mat)
        self.order_mat = order_mat
        
        self.xyz_mat = np.zeros((self.calibPt3D.shape[0], len(order_mat)))
        for i in range(len(order_mat)):
            self.xyz_mat[:,i] = np.prod(self.calibPt3D**order_mat[i,:], axis=1)
            
        # create coeff for imgX, imgY
        self.coeff_imgX = np.linalg.lstsq(self.xyz_mat, self.calibPt2D[:,0].reshape((-1,1)), rcond=None)[0]
        self.coeff_imgY = np.linalg.lstsq(self.xyz_mat, self.calibPt2D[:,1].reshape((-1,1)), rcond=None)[0]
        
        # calculate error 
        imgX = self.xyz_mat @ self.coeff_imgX
        imgY = self.xyz_mat @ self.coeff_imgY
        self.err = np.mean(np.linalg.norm(self.calibPt2D - np.hstack([imgX,imgY]), axis=1))
        print('max err:', np.max(np.linalg.norm(self.calibPt2D - np.hstack([imgX,imgY]), axis=1)))
        print('std err:', np.std(np.linalg.norm(self.calibPt2D - np.hstack([imgX,imgY]), axis=1)))
        
        # print outpus
        dpg.configure_item('polyCalibGroup', show=True)
        dpg.set_value('polyCalibErr', 'Calibration Error: ' + str(self.err))
        output_x = np.hstack([self.coeff_imgX, self.order_mat])
        output_y = np.hstack([self.coeff_imgY, self.order_mat])
        dpg.set_value('polyCalibResults', 'imgX:\n' + str(output_x) + '\nimgY:\n' + str(output_y))
        
        # show reference plane
        dpg.configure_item('polyRefPlane', show=True)
        dpg.configure_item('buttonExportPolyCalib', show=True)
        
        # plot points
        img = np.zeros((self.imgSize[1], self.imgSize[0], 3), np.uint8)
        for i in range(self.calibPt2D.shape[0]):
            self.draw_plus(img, (int(round(self.calibPt2D[i,0])), int(round(self.calibPt2D[i,1]))), (255,0,0))
            cv2.circle(img, (int(imgX[i]), int(imgY[i])), 1, (0,0,255))
        Texture.createTexture('polyPlot', img)
    
    def selectFolder(self, sender = None, app_data = None):
        self.exportFilePath = app_data['file_path_name']
        self.exportFileName = dpg.get_value('inputPolyCalibFileText') + '.txt'
        filePath = os.path.join(self.exportFilePath, self.exportFileName)

        dpg.set_value('exportPolyFileName', 'File Name: ' + self.exportFileName)
        dpg.set_value('exportPolyPathName', 'Complete Path Name: ' + filePath)
    
    def exportCalib(self, sender = None, app_data = None):
        if self.exportFilePath is None:
            dpg.configure_item('exportPolyCalibError', show=True)
            return
        
        dpg.configure_item('exportPolyCalibError', show=False)
        filePath = os.path.join(self.exportFilePath, self.exportFileName)
        
        self.refPlane = [dpg.get_value('selectXYZ'), dpg.get_value('inputPolyRefPlane_1'), dpg.get_value('inputPolyRefPlane_2')]
        
        with open(filePath, 'w') as f:
            f.write('# Camera Model: (PINHOLE/POLYNOMIAL)\n' + str('POLYNOMIAL') + '\n')
            f.write('# Calibration Error: \n' + str(self.err) + '\n')
            
            f.write('# Image Size: (n_row,n_col)\n')
            f.write(str(self.imgSize[1])+','+str(self.imgSize[0])+'\n') # OpenCV: imgSize=(width, height)
            
            f.write('# Reference Plane: (REF_X/REF_Y/REF_Z,coordinate,coordinate)\n')
            f.write(self.refPlane[0]+','+str(self.refPlane[1])+','+str(self.refPlane[2])+'\n')
            
            n_coeff = len(self.order_mat)
            f.write('# Number of Coefficients: \n')
            f.write(str(n_coeff)+'\n')
            
            f.write('# U_Coeff,X_Power,Y_Power,Z_Power \n')
            for i in range(n_coeff):
                f.write(str(self.coeff_imgX[i,0])+','+str(self.order_mat[i,0])+','+str(self.order_mat[i,1])+','+str(self.order_mat[i,2])+'\n')
            
            f.write('# V_Coeff,X_Power,Y_Power,Z_Power \n')
            for i in range(n_coeff):
                f.write(str(self.coeff_imgY[i,0])+','+str(self.order_mat[i,0])+','+str(self.order_mat[i,1])+','+str(self.order_mat[i,2])+'\n')
            
        dpg.configure_item("exportPolyCalib", show=False)
        
        
        
        

        