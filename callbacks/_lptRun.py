import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import pandas as pd
import os
import itertools
from scipy.optimize import minimize
import time
import pyOpenLPT as lpt

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ._texture import Texture


class LptRun:
    def __init__(self) -> None:
        self.camFilePath = [] 
        self.camFileName = []
        self.nCam = None
        
        self.imgFilePath = []
        self.imgFileName = []
        self.nFrame = None
         
        self.resultFolder = None
        self.laTrackPath_temp = None
        self.saTrackPath_temp = None
        self.objects = []
        
        self.exportFolder = None
        
        # run openlpt
        self.mainConfigFile = None
        self.mainParams = {} 
        self.cam_list = None
        self.imgio_list = []
        self.stb_list = []
        
        # post-processing 
        self.tracksFilePath = []
        self.tracksFileName = []
        self.plotFolder = None
        self.tracks = None
        self.nTracks = None
        
        
    def openCamFile(self, sender=None, app_data=None):
        selections = app_data['selections']
        self.nCam = len(selections)
        if self.nCam == 0:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'No file selected!')
            return
        
        if self.nCam < 2:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Require at least 2 cameras!')
            return
        
        # init
        self.camFilePath = []
        self.camFileName = []
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('lptRun_noPath', show=True)
                dpg.set_value('lptRun_noPathText', 'Wrong path:\n'+values)
                return
            self.camFilePath.append(values)
            self.camFileName.append(keys)
                
        # Update status 
        dpg.set_value('lptRun_camStatus', 'Status: Finish!')
    
        # Print outputs onto the output window
        dpg.configure_item('lptRun_camOutputParent', show=True)
        
        for tag in dpg.get_item_children('lptRun_camFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(self.nCam):
            with dpg.table_row(parent='lptRun_camFileTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(self.camFileName[i])
                dpg.add_text(self.camFilePath[i])
                
    def openImgFile(self, sender=None, app_data=None):
        selections = app_data['selections']
        if len(selections) == 0:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'No file selected!')
            return
        
        # init
        self.imgFilePath = []
        self.imgFileName = []
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('lptRun_noPath', show=True)
                dpg.set_value('lptRun_noPathText', 'Wrong path:\n'+values)
                return
            self.imgFilePath.append(values)
            self.imgFileName.append(keys)
        
        if len(self.imgFilePath) != self.nCam:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Number of images must be equal to number of cameras!')
            return
        
        # check number of frames 
        nFrame = []
        for file in self.imgFilePath:
            lines = open(file).readlines()
            contents = []
            for line in lines:
                if line.startswith('#' or '\n'):
                    continue
                contents.append(line)
            nFrame.append(len(contents))
        if np.sum(np.diff(nFrame) != 0) != 0:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Number of frames for each image file must be equal!')
            return
        self.nFrame = nFrame[0]
        
        dpg.configure_item('lptRun_frameRange_input', default_value=[0,self.nFrame-1], max_value=self.nFrame-1, max_clamped=True)
        dpg.set_value('lptRun_imgStatus', 'Status: Finish!')
         
        # Print outputs onto the output window
        dpg.configure_item('lptRun_imgOutputParent', show=True)
        
        for tag in dpg.get_item_children('lptRun_imgFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(len(self.imgFilePath)):
            with dpg.table_row(parent='lptRun_imgFileTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(self.imgFileName[i])
                dpg.add_text(str(self.nFrame) + f', ID: 0~{self.nFrame-1}')
                dpg.add_text(self.imgFilePath[i])
    
    def selectResultFolder(self, sender=None, app_data=None):
        self.resultFolder = app_data['file_path_name']

    def setMainParams(self, sender=None, app_data=None):
        self.mainParams = {}
        
        self.mainParams['frameRange'] = dpg.get_value('lptRun_frameRange_input')[:2]
        if self.mainParams['frameRange'][0] > self.mainParams['frameRange'][1]:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Wrong frame range!')
            return
        
        self.mainParams['nThread'] = dpg.get_value('lptRun_nThread_input')
        self.mainParams['nDigit'] = dpg.get_value('lptRun_nDigit_input')
        
        x_limit = dpg.get_value('lptRun_viewVolume_x_input')[:2]
        y_limit = dpg.get_value('lptRun_viewVolume_y_input')[:2]
        z_limit = dpg.get_value('lptRun_viewVolume_z_input')[:2]
        self.mainParams['viewVolume'] = x_limit + y_limit + z_limit
        
        self.mainParams['voxelToMM'] = dpg.get_value('lptRun_voxelToMM_input')
        
        self.mainParams['isLoadTracks'] = dpg.get_value('lptRun_isLoadTracks_input')
        self.mainParams['prevFrameID'] = self.mainParams['frameRange'][0]-1
        if self.mainParams['isLoadTracks']:
            self.mainParams['prevFrameID'] = dpg.get_value('lptRun_prevFrameID_input')
            
            if self.mainParams['prevFrameID'] < self.mainParams['frameRange'][0]-1 or self.mainParams['prevFrameID'] > self.mainParams['frameRange'][1]-1:
                dpg.configure_item('lptRun_noPath', show=True)
                dpg.set_value('lptRun_noPathText', 'Wrong previous frame ID!')
                return
        
        if self.resultFolder is None:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Please select result folder path!')
            return
        self.mainParams['resultFolder'] = self.resultFolder
            
        # Print outputs onto the output window
        dpg.set_value('lptRun_frameRange', 'Frame ID Range: ' + str(self.mainParams['frameRange']))
        dpg.set_value('lptRun_nThread', 'Number of Threads: ' + str(self.mainParams['nThread']))
        dpg.set_value('lptRun_nDigit', 'Digits of Images: ' + str(self.mainParams['nDigit']))
        dpg.set_value('lptRun_viewVolume', 'View Volume: ' + str(self.mainParams['viewVolume']))
        dpg.set_value('lptRun_voxelToMM', 'Voxel to mm ratio: ' + "{:.3f}".format(self.mainParams['voxelToMM']))
        if self.mainParams['isLoadTracks']:
            dpg.set_value('lptRun_isLoadTracks', 'Start from previous frame ID: ' + str(self.mainParams['prevFrameID']))
        # print(self.mainParams['prevFrameID'])
        dpg.set_value('lptRun_resultFolder', 'Result Folder: ' + self.resultFolder)
        
        if self.mainParams['isLoadTracks']:
            dpg.configure_item('lptRun_trackPathTable', show=True)
        else:
            for tag in dpg.get_item_children('lptRun_trackPathTable')[1]:
                dpg.delete_item(tag)
            dpg.configure_item('lptRun_trackPathTable', show=False)
        
        dpg.configure_item('lptRun_setMainParams', show=False)
    
    def selectObjectTypes(self, sender=None, app_data=None):
        objectType = dpg.get_value('lptRun_objectType_input')
        
        if objectType == 'Tracer':
            dpg.configure_item('lptRun_addTracerParams', show=True)
            if self.mainParams['isLoadTracks']:
                dpg.configure_item('lptRun_Tracer_loadPrevTrack_parent', show=True)
            else:
                dpg.configure_item('lptRun_Tracer_loadPrevTrack_parent', show=False)
    
    def selectLongActiveTrack(self, sender=None, app_data=None):
        self.laTrackPath_temp = app_data['file_path_name']
    
    def selectShortActiveTrack(self, sender=None, app_data=None):
        self.saTrackPath_temp = app_data['file_path_name']
    
    def addTracerParams(self, sender=None, app_data=None):
        objectType = dpg.get_value('lptRun_objectType_input')
        
        object = {'type': objectType}
        
        object['searchRadius'] = dpg.get_value('lptRun_Tracer_searchRadius_input')
        object['nFrameInitPhase'] = dpg.get_value('lptRun_Tracer_nFrameInitPhase_input')
        object['avgInterParticleDist'] = dpg.get_value('lptRun_Tracer_avgInterParticleDist_input')
        
        object['shakeWidth'] = dpg.get_value('lptRun_Tracer_shakeWidth_input')
        
        object['pfGrids'] = dpg.get_value('lptRun_Tracer_pfGrids_input')
        object['pfSearchRadius'] = dpg.get_value('lptRun_Tracer_pfSearchRadius_input')
        
        object['nIPRLoop'] = dpg.get_value('lptRun_Tracer_nIPRLoop_input')
        object['nShakeLoop'] = dpg.get_value('lptRun_Tracer_nShakeLoop_input')
        object['ghostThreshold'] = dpg.get_value('lptRun_Tracer_ghostThreshold_input')
        object['tol_2d'] = dpg.get_value('lptRun_Tracer_tol_2d_input')
        object['tol_3d'] = dpg.get_value('lptRun_Tracer_tol_3d_input')
        
        object['nReducedCam'] = dpg.get_value('lptRun_Tracer_nReducedCam_input')
        object['nIPRLoopReduced'] = dpg.get_value('lptRun_Tracer_nIPRLoopReduced_input')
        
        object['intensityThreshold'] = dpg.get_value('lptRun_Tracer_2DThreshold_input')
        object['r_2d'] = dpg.get_value('lptRun_Tracer_2DRadius_input')
        
        if self.mainParams['isLoadTracks']:
            if self.laTrackPath_temp is None:
                dpg.configure_item('lptRun_noPath', show=True)
                dpg.set_value('lptRun_noPathText', 'Please select long active track path!')
                return
            if self.saTrackPath_temp is None:
                dpg.configure_item('lptRun_noPath', show=True)
                dpg.set_value('lptRun_noPathText', 'Please select short active track path!')
                return
            object['laTrackPath'] = self.laTrackPath_temp
            object['saTrackPath'] = self.saTrackPath_temp
        
        self.objects.append(object)
        
        # Print outputs onto the output window
        type_list = [obj['type'] for obj in self.objects]
        dpg.set_value('lptRun_objectTypes', 'Object Types: ' + ", ".join(type_list))
        
        if self.mainParams['isLoadTracks']:
            with dpg.table_row(parent='lptRun_trackPathTable'):
                dpg.add_text(len(self.objects)-1)
                dpg.add_text('Tracer')
                dpg.add_text(self.laTrackPath_temp)
                dpg.add_text(self.saTrackPath_temp)
        
        dpg.configure_item('lptRun_addTracerParams', show=False)     
        
    def clearObjects(self, sender=None, app_data=None):
        self.objects = []
        for tag in dpg.get_item_children('lptRun_trackPathTable')[1]:
            dpg.delete_item(tag)
        dpg.set_value('lptRun_objectTypes', 'Object Types: --')
    
    def selectExportFolder(self, sender=None, app_data=None):
        self.exportFolder = app_data['file_path_name']
        
        if os.path.isdir(self.exportFolder) is False:
            dpg.configure_item('lptRun_noPath', show=True)
            dpg.set_value('lptRun_noPathText', 'Wrong path:\n'+self.exportFolder)
            return
        
        dpg.set_value('lptRun_exportFolder', 'Export Folder: ' + self.exportFolder)
        dpg.configure_item('lptRun_generateConfig_button', show=True)
        dpg.set_value('lptRun_generateConfigStatus', 'Status: Ready!')
    
    def saveMainConfig(self, config_file):
        with open(config_file, 'w') as f:
            f.write('# Frame Range: [startID,endID]\n')
            f.write(",".join(map(str, self.mainParams['frameRange']))+'\n')
            f.write('# Frame Rate: [Hz]\n1\n')
            f.write('# Number of Threads: (0: use as many as possible)\n')
            f.write(str(self.mainParams['nThread'])+'\n')
            f.write('# Number of Cameras:\n')
            f.write(str(self.nCam)+'\n')
            f.write('# Camera File Path, Max Intensity\n')
            f.write('\n'.join([self.camFilePath[i]+','+str(2**self.mainParams['nDigit']-1) for i in range(self.nCam)])+'\n')
            f.write('# Image File Path\n')
            f.write('\n'.join(self.imgFilePath)+'\n')
            f.write('# View Volume: (xmin,xmax,ymin,ymax,zmin,zmax)\n')
            f.write(",".join(map(str, self.mainParams['viewVolume']))+'\n')
            f.write('# Voxel to MM:\n')
            f.write(str(self.mainParams['voxelToMM'])+'\n')
            f.write('# Output Folder Path:\n')
            f.write(self.mainParams['resultFolder']+os.path.sep+'\n')
            
            # object info 
            f.write('# Object Types:\n')
            f.write(','.join([obj['type'] for obj in self.objects])+'\n')
            
            f.write('# STB Config Files:\n')
            for i in range(len(self.objects)):
                if self.objects[i]['type'] == 'Tracer':
                    f.write(os.path.join(self.exportFolder, 'tracerConfig_'+str(i)+'.txt')+'\n')
            
            if self.mainParams['isLoadTracks']:
                f.write('# Flag to load previous track files, previous frameID\n')
                f.write('1,'+str(self.mainParams['prevFrameID'])+'\n')

                f.write('# Path to long active track files\n')
                for obj in self.objects:
                    f.write(obj['laTrackPath']+'\n')
                
                f.write('# Path to short active track files\n')
                for obj in self.objects:
                    f.write(obj['saTrackPath']+'\n')
    
    def saveTracerConfig(self, config_file, obj):
        with open(config_file, 'w') as f:
            f.write('#'*28+'\n')
            f.write('#'*9+' Tracking '+'#'*9+'\n')
            f.write('#'*28+'\n')
             
            f.write('#'*6 + ' Initial Phase ' + '#'*6 + '\n')
            f.write('1 # Flag for using ipr in initialphase (or use .csv files)\n')
            f.write(str(obj['searchRadius']) + ' # Search radius for connecting tracks to objects\n')
            f.write(str(obj['nFrameInitPhase']) + ' # Number of frames for initial phase\n')
             
            f.write('#'*5 + ' Convergence Phase ' + '#'*5 + '\n')
            f.write(str(obj['avgInterParticleDist']) + ' # Avg Interparticle spacing. (vox) to identify neighbour tracks\n')
            f.write('4 # Radius to find predicted particle (pixel)\n') # TODO: delete this param in the future
            
            f.write('#'*25+'\n')
            f.write('#'*9+' Shake '+'#'*9+'\n') 
            f.write('#'*25+'\n')
            f.write(str(obj['shakeWidth']) + ' # Shake width\n')
            
            f.write('#'*33+'\n')
            f.write('#'*9+' Predict Field '+'#'*9+'\n')
            f.write('#'*33+'\n')
            f.write(str(obj['pfGrids'][0]) + ' # xgrid\n')
            f.write(str(obj['pfGrids'][1]) + ' # ygrid\n')
            f.write(str(obj['pfGrids'][2]) + ' # zgrid\n')
            f.write(str(obj['pfSearchRadius']) + ' # Search radius for predict field [voxel]\n')
            
            f.write('#'*23+'\n')
            f.write('#'*9+' IPR '+'#'*9+'\n')
            f.write('#'*23+'\n')
            f.write('0 # Triangulation/IPR Only (No IPR/tracking)? 1 for only tri (no ipr or tracking), 2 for only tri+ipr (no tracking), otherwise with tri and ipr\n')
            f.write(str(obj['nIPRLoop']) + ' # No. of IPR loop\n')
            f.write(str(obj['nShakeLoop']) + ' # No. of Shake loop\n')
            f.write(str(obj['ghostThreshold']) + ' # Ghost threshold\n')
            f.write('100000 # maximum number of tracers in each camera\n')
            f.write(str(obj['tol_2d']) + ' # 2D tolerance [px]\n')
            f.write(str(obj['tol_3d']) + ' # 3D tolerance [vox]\n')
            f.write(str(obj['nReducedCam']) + ' # No. of reduced cameras\n')
            f.write(str(obj['nIPRLoopReduced']) + ' # No. of IPR loop for each reduced camera combination\n')
            
            f.write('#'*31+'\n')
            f.write('#'*9+' Object Info '+'#'*9+'\n')
            f.write('#'*31+'\n')
            f.write('255 # Max intensity for each pixel\n') # TODO: delete this param in the future
            f.write(str(obj['intensityThreshold']) + ' # 2D particle finder threshold\n')
            f.write(str(obj['r_2d']) + ' # Particle radius [px], for calculating residue image and shaking\n')
            
    def generateConfig(self, sender=None, app_data=None):
        # generate main config file 
        config_file = os.path.join(self.exportFolder, 'config.txt')
        self.saveMainConfig(config_file)
        
        # generate object config files
        for i in range(len(self.objects)):
            if self.objects[i]['type'] == 'Tracer':
                config_file = os.path.join(self.exportFolder, 'tracerConfig_'+str(i)+'.txt')
                self.saveTracerConfig(config_file, self.objects[i])
        
        dpg.set_value('lptRun_generateConfigStatus', 'Status: Finish!')
        
        # print outputs onto the output window
        dpg.set_value('lptRun_mainConfigFile', 'Main Config File: ' + os.path.join(self.exportFolder, 'config.txt'))

    def loadMainConfig(self, config_file):
        lines = open(config_file).readlines()
        content = []
        for line in lines:
            if line.startswith('#' or '\n'):
                continue
            content.append(line.strip())
        
        mainParams = {}
        
        line_id = 0
        mainParams['frameRange'] = list(map(int, content[line_id].split(',')))
        
        line_id += 2
        mainParams['nThread'] = int(content[line_id])
        
        line_id += 1
        self.nCam = int(content[line_id])
        
        line_id += 1
        mainParams['nDigit'] = len(bin(int(content[line_id].split(',')[1])))-2
        
        camFilePath = []
        cam = []
        intensity_max = []
        useid_list = list(range(self.nCam))
        for _ in range(self.nCam):
            camFilePath.append(content[line_id].split(',')[0])
            cam.append(lpt.math.Camera(camFilePath[-1]))
            intensity_max.append(int(content[line_id].split(',')[1]))
            line_id += 1 
        line_id -= 1
        self.cam_list = lpt.math.CamList()
        self.cam_list.cam_list = cam
        self.cam_list.intensity_max = intensity_max
        self.cam_list.useid_list = useid_list
        
        line_id += 1
        imgFilePath = []
        self.imgio_list = []
        for _ in range(self.nCam):
            imgFilePath.append(content[line_id])
            self.imgio_list.append(lpt.math.ImageIO('', content[line_id]))
            line_id += 1
        line_id -= 1
        
        line_id += 1
        mainParams['viewVolume'] = list(map(float, content[line_id].split(',')))
        axis_limit = lpt.AxisLimit(mainParams['viewVolume'][0], mainParams['viewVolume'][1], mainParams['viewVolume'][2], mainParams['viewVolume'][3], mainParams['viewVolume'][4], mainParams['viewVolume'][5])
        
        line_id += 1
        mainParams['voxelToMM'] = float(content[line_id])
        
        line_id += 1
        mainParams['resultFolder'] = content[line_id]
        
        line_id += 1
        mainParams['objectTypes'] = content[line_id].split(',')
        n_obj = len(mainParams['objectTypes'])
        
        mainParams['stbPaths'] = [content[i] for i in range(line_id+1, line_id+1+n_obj)]
        print(mainParams['stbPaths'])
        
        self.stb_list = []
        for i in range(n_obj):
            if mainParams['objectTypes'][i] == 'Tracer':
                self.stb_list.append(lpt.stb.STBTracer(
                        mainParams['frameRange'][0], 
                        mainParams['frameRange'][1], 
                        1, 
                        mainParams['voxelToMM'], 
                        mainParams['nThread'], 
                        mainParams['resultFolder']+'Tracer_'+str(i)+os.path.sep, 
                        self.cam_list, 
                        axis_limit, 
                        mainParams['stbPaths'][i]
                    )
                )
        
        line_id += 1 + n_obj
        mainParams['isLoadTracks'] = 0
        if line_id < len(content):
            mainParams['isLoadTracks'], mainParams['prevFrameID'] = map(int, content[line_id].split(','))
            
            line_id += 1
            mainParams['laTrackPath'] = []
            for _ in range(n_obj):
                mainParams['laTrackPath'].append(content[line_id])
                line_id += 1
                
            mainParams['saTrackPath'] = []
            for _ in range(n_obj):
                mainParams['saTrackPath'].append(content[line_id])
                line_id += 1
        
        self.mainParams = mainParams.copy()
        self.camFilePath = camFilePath.copy()
        self.imgFilePath = imgFilePath.copy()
      
    def openMainConfig(self, sender=None, app_data=None):
        self.mainConfigFile = app_data['file_path_name']
        if self.mainConfigFile is None:
            dpg.configure_item('lptRun_Run_noPath', show=True)
            dpg.set_value('lptRun_Run_noPathText', 'No file selected!')
            return
        
        self.loadMainConfig(self.mainConfigFile)
        
        dpg.configure_item('lptRun_Run_runButton', show=True)
        dpg.set_value('lptRun_Run_mainConfigStatus', 'Status: Finish!')
        dpg.set_value('lptRun_Run_processStatus', 'Status: Ready!')
        
        # config items for step 2. 
        n_obj = len(self.mainParams['objectTypes'])
        dpg.configure_item('lptRun_Run_objFinder_objType_input', items=[self.mainParams['objectTypes'][i]+'_'+str(i) for i in range(n_obj)])
        dpg.configure_item('lptRun_Run_objFinder_cam_input', items=[f'cam{i+1}' for i in range(self.nCam)])
        dpg.set_value('lptRun_Run_objFinder_frameID_text', 'Enter frame ID ('+str(self.mainParams['frameRange'][0])+'~'+str(self.mainParams['frameRange'][1])+')')
        dpg.configure_item('lptRun_Run_objFinder_frameID_input', default_value=self.mainParams['frameRange'][0], max_value=self.mainParams['frameRange'][1], max_clamped=True, min_clamped=True)
        
        # print outputs onto the output window
        dpg.set_value('lptRun_Run_mainConfigFile', 'Main Config File: ' + self.mainConfigFile)
        dpg.set_value('lptRun_Run_resultFolder', 'Result Folder: ' + self.mainParams['resultFolder'])
        self.updateImage()
    
    def updateImage(self, sender=None, app_data=None):
        cam_id = int(dpg.get_value('lptRun_Run_objFinder_cam_input').replace('cam',''))-1
        frame_id = dpg.get_value('lptRun_Run_objFinder_frameID_input')
        img = lpt.math.matrix_to_numpy(self.imgio_list[cam_id].loadImg(frame_id)).astype('uint'+str(self.mainParams['nDigit']))
        Texture.createTexture('lptRun_Run_Plot', np.flipud(img))
    
    def draw_plus(self, image, center, color=(0, 0, 255), size=5, thickness=1):
        cx, cy = center
        cv2.line(image, (cx - size, cy), (cx + size, cy), color, thickness)
        cv2.line(image, (cx, cy - size), (cx, cy + size), color, thickness)
    
    def checkObjFinder(self, sender=None, app_data=None):
        objectTypeInput = dpg.get_value('lptRun_Run_objFinder_objType_input')
        cam_id = int(dpg.get_value('lptRun_Run_objFinder_cam_input').replace('cam',''))-1
        frame_id = dpg.get_value('lptRun_Run_objFinder_frameID_input')
        
        img = self.imgio_list[cam_id].loadImg(frame_id)
        obj2d_list = []
        
        objectType, obj_id = objectTypeInput.split('_')
        obj_id = int(obj_id)
        if objectType == 'Tracer':
            # run tracer identification 
            obj_params = self.stb_list[obj_id].getObjParam()
            obj2d_list = lpt.object.ObjectFinder2D().findTracer2D(img, obj_params)
        else:
            dpg.configure_item('lptRun_Run_noPath', show=True)
            dpg.set_value('lptRun_Run_noPathText', 'Object type: '+objectType+' is not found!')
            return
        
        # update image 
        img = lpt.math.matrix_to_numpy(img).astype('uint'+str(self.mainParams['nDigit']))
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for obj2d in obj2d_list:
            cv2.circle(img, (int(round(obj2d._pt_center[0])), int(round(obj2d._pt_center[1]))), 1, (0,0,255), 1)
            # self.draw_plus(img, (int(round(obj2d._pt_center[0])), int(round(obj2d._pt_center[1]))))
        Texture.createTexture('lptRun_Run_Plot', np.flipud(img))
       
    def runOpenLPT(self, sender=None, app_data=None):      
        # run openlpt
        lpt.run(self.mainConfigFile)
        dpg.set_value('lptRun_Run_processStatus', 'Status: Finish!')

    def openTracksFile(self, sender=None, app_data=None):
        # open tracks file
        self.tracksFilePath = []
        self.tracksFileName = []
        self.tracks = pd.DataFrame()
        
        selections = app_data['selections']
        nFiles = len(selections)
        if nFiles == 0:
            dpg.configure_item('lptRun_Post_noPath', show=True)
            dpg.set_value('lptRun_Post_noPathText', 'No file selected!')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('lptRun_Post_noPath', show=True)
                dpg.set_value('lptRun_Post_noPathText', 'Wrong path:\n'+values)
                return
            self.tracksFilePath.append(values)
            self.tracksFileName.append(keys)
        
        nTracks_list = []
        for i in range(nFiles):
            df = pd.read_csv(self.tracksFilePath[i])
            nTracks_list.append(df['TrackID'].unique().shape[0])
            if not self.tracks.empty:
                df['TrackID'] += self.tracks['TrackID'].unique().shape[0]
            self.tracks = pd.concat([self.tracks, df], axis=0, ignore_index=True)
        self.tracks.reset_index(drop=True, inplace=True)
        
        dpg.set_value('lptRun_Post_loadTrackStatus', 'Status: Finish!')
        
        # Print outputs onto the output window
        dpg.configure_item('lptRun_Post_tracksFileTable', show=True)
        for tag in dpg.get_item_children('lptRun_Post_tracksFileTable')[1]:
            dpg.delete_item(tag)
        for i in range(nFiles):
            with dpg.table_row(parent='lptRun_Post_tracksFileTable'):
                dpg.add_text(self.tracksFileName[i])
                dpg.add_text(str(nTracks_list[i]))
                dpg.add_text(self.tracksFilePath[i])
        
        self.nTracks = self.tracks['TrackID'].unique().shape[0]
        dpg.set_value('lptRun_Post_nTracks', 'Number of tracks: ' + str(self.nTracks))
    
    def selectPlotFolder(self, sender=None, app_data=None):
        self.plotFolder = app_data['file_path_name']
    
    def checkPlotRequirement(self):
        if self.tracks.empty:
            dpg.configure_item('lptRun_Post_noPath', show=True)
            dpg.set_value('lptRun_Post_noPathText', 'No tracks loaded!')
            return
        if self.plotFolder is None:
            dpg.configure_item('lptRun_Post_noPath', show=True)
            dpg.set_value('lptRun_Post_noPathText', 'Please select a plot folder!')
            return
    
    def plotTracks(self, sender=None, app_data=None):
        self.checkPlotRequirement()
        
        percent = dpg.get_value('lptRun_Post_plotPercent_input')
        nTracks_plot = int(self.nTracks*percent/100)
        trackID_plot = np.random.choice(self.tracks['TrackID'].unique(), nTracks_plot, replace=False)
        
        # plot tracks
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for trackID in trackID_plot:
            track = self.tracks[self.tracks['TrackID'] == trackID]
            ax.plot(track['WorldX'], track['WorldY'], track['WorldZ'], '-')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.title(str(percent)+'% Tracks')
        plt.tight_layout()
        
        # save figure
        fig.savefig(os.path.join(self.plotFolder, 'tracks.png'), dpi=600)
        plt.close(fig)
        
        Texture.createTexture('lptRun_Post_Plot', cv2.imread(os.path.join(self.plotFolder, 'tracks.png')))

    def plotNParticles(self, sender=None, app_data=None):
        self.checkPlotRequirement()
        
        particles_per_frame = self.tracks.groupby('FrameID').size()
        frame = self.tracks['FrameID'].unique()
        
        plt.figure()
        plt.plot(frame, particles_per_frame, '.-')
        plt.xlabel('Frame ID')
        plt.ylabel('Number of Particles')
        plt.title('Number of Particles per Frame')
        plt.tight_layout()
        plt.savefig(os.path.join(self.plotFolder, 'nptsPerFrame.png'), dpi=600)
        plt.close()
        
        Texture.createTexture('lptRun_Post_Plot', cv2.imread(os.path.join(self.plotFolder, 'nptsPerFrame.png')))
        
    def plotTrackLength(self, sender=None, app_data=None):
        self.checkPlotRequirement()
        
        track_length = self.tracks.groupby('TrackID').size()
        nFrame = self.tracks['FrameID'].unique().shape[0]
        
        plt.figure()
        plt.hist(track_length, bins = nFrame)
        plt.xlabel('Track Length')
        plt.ylabel('Number of Tracks')
        plt.title('Track Length Distribution')
        plt.tight_layout()
        plt.savefig(os.path.join(self.plotFolder, 'trackLength.png'), dpi=600)
        plt.close()
        
        Texture.createTexture('lptRun_Post_Plot', cv2.imread(os.path.join(self.plotFolder, 'trackLength.png')))
        
    
    def helpVoxToMM(self, sender=None, app_data=None):
        dpg.set_value('lptRun_helpText', 'Voxel is a 3D definition of pixel, which is used to quantified the uncertainty of 3D distance. \n\n1. Voxel to physical unit ratio is the ratio between the voxel size and the real world size. \n\n2. The number of voxels can be chosen as a similar number to camera resolution. For example, we can use 1000x1000x1000 voxels for camera resolution as 1024x1024. \n\n3. The voxel to physical unit ratio (voxel size) is determined by the camera resolution and the view volume. If the camera resolution is 1024x1024 and the view volume is [-20,20]x[-20,20]x[-20,20], this value could be set as 40/1000=0.04.')
        dpg.configure_item('lptRun_help', show=True)
    
    def helpObjFinder(self, sender=None, app_data=None):
        dpg.set_value('lptRun_Run_helpText', 'Check the quality of object identification. \n\n1. If lots of noisy points exist, try to increase the object finder threshold or improve image quality in the pre-processing step. \n\n2. If objects cannot be correctly identified, please try to adjust the object parameters.')
        dpg.configure_item('lptRun_Run_help', show=True) 
        
    
    