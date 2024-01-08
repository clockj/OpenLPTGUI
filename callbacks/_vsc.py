import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import pandas as pd
import os.path

class Vsc:
    def __init__(self) -> None:
        self.camFilePath = [] 
        self.camFileName = []

        self.camcalibErrList = []
        self.posecalibErrList = []
        self.camMatList = [] 
        self.distCoeffList = []
        self.rotVecList = []
        self.rotMatList = []
        self.transVecList = []
        
        self.nCam = None
        
        self.tracksFilePath = None
        self.tracksFileName = None
        self.tracks = None
        self.goodTracksThreshold = None
        
        self.imgFilePath = []
        self.imgFilePath = []
    
    def runVsc(self, sender=None, app_data=None):
        if self.nCam < 2:
            dpg.configure_item('noVscCam', show=True)
            return
        
        self.goodTracksThreshold = dpg.get_value('inputVscGoodTracksThreshold')
        
        # select good tracks 
        self.selectGoodTracks()
        
        # select particles 
        nParticles = dpg.get_value('inputVscNumParticles')
        goodParticles = self.selectParticles(nParticles)
        
        # get particle info: (WorldX, WorldY, WorldZ, Cam1ImgX, Cam1ImgY, ...)
        
        
        
    def selectGoodTracks(self):
        
        trackIDList = self.tracks['TrackID'].unique()
        
        for trackID in trackIDList:
            track = self.tracks.loc[self.tracks['TrackID'] == trackID]  
            length = track.shape[0]
            if length < 20:
                continue
            
            errVec = np.zeros(3)
            nFit = 10
            xFit = np.array(range(nFit))
            for j in range(3):
                yFit = track.iloc[-nFit:, j+2]
                _,residue,_,_,_ = np.polyfit(xFit, yFit, 3, full=True)
                errVec[j] = np.sqrt(np.mean(residue))
            error = np.sqrt(np.sum(errVec*errVec))
            
            if error > self.goodTracksThreshold:
                self.tracks.drop(track.index, inplace=True)
                
        self.tracks.reset_index(drop=True, inplace=True)
        self.tracks.to_csv(self.camFilePath[0].replace(self.camFileName[0],'goodTracks.csv'), index=False)
        
        print('Finish selecting good tracks!')
    
    def selectParticles(self, nParticles):
        nSegVec = np.array([10, 10, 10])
        nParticleSeg = int(np.ceil(nParticles / np.prod(nSegVec)))
        
        xMin = self.tracks['WorldX'].min()
        xMax = self.tracks['WorldX'].max()
        yMin = self.tracks['WorldY'].min()
        yMax = self.tracks['WorldY'].max()
        zMin = self.tracks['WorldZ'].min()
        zMax = self.tracks['WorldZ'].max()

        isSelect = np.zeros(self.tracks.shape[0])
        
        for i in range(nSegVec[0]):
            for j in range(nSegVec[1]):
                for k in range(nSegVec[2]):
                    xLow = xMin + i * (xMax - xMin) / nSegVec[0]
                    yLow = yMin + j * (yMax - yMin) / nSegVec[1]
                    zLow = zMin + k * (zMax - zMin) / nSegVec[2]
                    xUp = xMin + (i+1) * (xMax - xMin) / nSegVec[0]
                    yUp = yMin + (j+1) * (yMax - yMin) / nSegVec[1]
                    zUp = zMin + (k+1) * (zMax - zMin) / nSegVec[2]

                    judge = (self.tracks['WorldX'] > xLow) & (self.tracks['WorldX'] < xUp) & (self.tracks['WorldY'] > yLow) & (self.tracks['WorldY'] < yUp) & (self.tracks['WorldZ'] > zLow) & (self.tracks['WorldZ'] < zUp)
                    
                    index = self.tracks.index[judge]
                    nInside = len(index)
                    if nInside > nParticleSeg:
                        # if the number of particles in this cube is more than the number to be selected, then choose them randomly
                        id = np.array(range(nInside))
                        idSelect = np.random.choice(id, nParticleSeg, replace=False)
                        isSelect[index[idSelect]] = 1
                    elif nInside > 0:
                        # if the number of particles in this cube is less than the number to be selected, then select all of them
                        isSelect[index] = 1

        # for the number of selected particle is less than the required number, then select them again from the orginal data randomly
        nLess = int(nParticles - np.sum(isSelect))
        if nLess > 0:
            id = np.array(range(self.tracks.shape[0]))
            notSelectID = id[isSelect==0]
            newSelectID = np.random.choice(notSelectID, nLess, replace=False)
            isSelect[newSelectID] = 1

        # fill in the goodParticles dataframe
        goodParticles = self.tracks.iloc[isSelect, :]
        goodParticles.reset_index(drop=True, inplace=True)
        goodParticles.to_csv(self.camFilePath[0].replace(self.camFileName[0],'goodParticles.csv'), index=False)
        
        print('Finish selecting good particles!')
        
        return np.array(goodParticles)
    
    def getParticleInfo(self, goodParticles):
        particleInfo = []
        
        nParticles = goodParticles.shape[0]
        pt3D = np.reshape(goodParticles[:, 2:5], (nParticles, 1, 3))
        
        # project 3D points onto each camera
        # pt3D (WorldX, WorldY, WorldZ) => pt2D (ImgX, ImgY)
        searchR = dpg.get_value('inputVscParticleRadius') * 0.75
        pt2DList = np.zeros((nParticles, 2 * self.nCam))
        isDelete = np.zeros(nParticles)
        for i in range(self.nCam):
            pt2D, _ = cv2.projectPoints(pt3D, self.rotVecList[i], self.transVecList[i], self.camMatList[i], self.distCoeffList[i])
            pt2D = np.reshape(pt2D, (nParticles, 2))
            pt2DList[:, 2*i:2*i+2] = pt2D
            
            # find candidates on img for each particle
            for j in range(nParticles):
                # load image 
                file = self.imgFilePath[i]
                with open(file, 'r') as f:
                    lines = f.readlines()
                    frameID = int(goodParticles['FrameID'][j])
                    imgPath = lines[frameID].strip('\n')
                img = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE, cv2.IMREAD_ANYDEPTH)
                height, width = img.shape
                
                # define search range
                imgX = pt2D[j,0] # col 
                imgY = pt2D[j,1] # row
                searchRange = img[
                    max(1, int(np.floor(imgY-searchR))) : min(height, int(np.ceil(imgY+searchR+1))), 
                    max(1, int(np.floor(imgX-searchR))) : min(width, int(np.ceil(imgX+searchR+1)))
                ]

                # find candidates on img 
                
        
        return particleInfo
    
    def openCamFile(self, sender=None, app_data=None):
        self.camFilePath = [] 
        self.camFileName = []
        self.camcalibErrList = []
        self.posecalibErrList = []
        self.camMatList = [] 
        self.distCoeffList = []
        self.rotVecList = []
        self.rotMatList = []
        self.transVecList = []
        
        selections = app_data['selections']
        self.nCam = len(selections)
        if self.nCam == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('No file selected', parent='noVscPath')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.add_text('Wrong path:')
                dpg.add_text(values, parent='noVscPath')
                return
            self.camFilePath.append(values)
            self.camFileName.append(keys)
        
            # Load camera parameters
            with open(values, 'r') as f:
                lines = f.readlines()
                
                if 'None' in lines[1] or 'none' in lines[1]:
                    self.camcalibErrList.append(None)
                else:
                    self.camcalibErrList.append(float(lines[1]))
                if 'None' in lines[3] or 'none' in lines[3]:
                    self.posecalibErrList.append(None)
                else:
                    self.posecalibErrList.append(float(lines[3]))
                # self.posecalibErrList.append(float(lines[3]))
                
                camMat = np.zeros((3,3))
                camMat[0,:] = np.array(lines[5].split(',')).astype(np.float32)
                camMat[1,:] = np.array(lines[6].split(',')).astype(np.float32)
                camMat[2,:] = np.array(lines[7].split(',')).astype(np.float32)
                self.camMatList.append(camMat)
                
                distCoeff = np.array([lines[9].split(',')]).astype(np.float32)
                self.distCoeffList.append(distCoeff)
                
                rotVec = np.zeros((3,1))
                rotVec[:,0] = np.array(lines[11].split(',')).astype(np.float32)
                self.rotVecList.append(rotVec)
                
                rotMat = np.zeros((3,3))
                rotMat[0,:] = np.array(lines[13].split(',')).astype(np.float32)
                rotMat[1,:] = np.array(lines[14].split(',')).astype(np.float32)
                rotMat[2,:] = np.array(lines[15].split(',')).astype(np.float32)
                self.rotMatList.append(rotMat)
                # line 17,18,19 are rotMatInv
                
                transVec = np.zeros((3,1))
                transVec[:,0] = np.array(lines[21].split(',')).astype(np.float32)
                self.transVecList.append(transVec)
                # line 23 is transVecInv
                
        # Print outputs onto the output window 
        dpg.configure_item('vscCamOutputParent', show=True)
        
        for tag in dpg.get_item_children('vscCamFileTable')[1]:
            dpg.delete_item(tag)
        for tag in dpg.get_item_children('vscCamParamTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(self.nCam):
            with dpg.table_row(parent='vscCamFileTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(self.camFileName[i])
                dpg.add_text(self.camFilePath[i])

            with dpg.table_row(parent='vscCamParamTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(str(self.camMatList[i]))
                dpg.add_text(str(self.distCoeffList[i]))
                dpg.add_text(str(self.rotMatList[i]))
                dpg.add_text(str(self.transVecList[i]))
                dpg.add_text(str(self.camcalibErrList[i]))
                dpg.add_text(str(self.posecalibErrList[i]))
    
    def cancelCamImportFile(self, sender=None, app_data=None):
        dpg.hide_item('file_dialog_vscCam')
    
    def openTracksFile(self, sender=None, app_data=None):
        self.tracksFilePath = app_data['file_path_name']
        self.tracksFileName = app_data['file_name']
        
        if os.path.isfile(self.tracksFilePath) is False:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('Wrong path:')
            dpg.add_text(self.tracksFilePath, parent='noVscPath')
            return
                    
        # Load tracks data
        self.tracks = pd.read_csv(self.tracksFilePath)
        
        # Print tracks output 
        dpg.configure_item('vscTracksOutputParent', show=True)
        
        for tag in dpg.get_item_children('vscTracksFileTable')[1]:
            dpg.delete_item(tag)
        
        with dpg.table_row(parent='vscTracksFileTable'):
            dpg.add_text(self.tracksFileName)
            dpg.add_text(self.tracksFilePath)
        
        for i in range(len(self.tracks.head())):
            with dpg.table_row(parent='vscTracksDataTable'):
                dpg.add_text(str(self.tracks.iloc[i,0]))
                dpg.add_text(str(self.tracks.iloc[i,1]))
                dpg.add_text(str(self.tracks.iloc[i,2]))
                dpg.add_text(str(self.tracks.iloc[i,3]))
                dpg.add_text(str(self.tracks.iloc[i,4]))
        with dpg.table_row(parent='vscTracksDataTable'):
            dpg.add_text('...')
            dpg.add_text('...')
            dpg.add_text('...')
            dpg.add_text('...')
            dpg.add_text('...')
    
    def cancelTracksImportFile(self, sender=None, app_data=None):
        dpg.hide_item('file_dialog_vscTracks')
    
    def openImgFile(self, sender=None, app_data=None):
        self.imgFilePath = []
        self.imgFileName = []
        
        selections = app_data['selections']
        if len(selections) == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('No file selected', parent='noVscPath')
            return
        elif len(selections) != self.nCam:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('The number of selected files does not match the number of cameras', parent='noVscPath')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.add_text('Wrong path:')
                dpg.add_text(values, parent='noVscPath')
                return
            self.imgFilePath.append(values)
            self.imgFileName.append(keys)
            
        # Print outputs onto the output window
        dpg.configure_item('vscImgOutputParent', show=True)
        
        for tag in dpg.get_item_children('vscImgFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(len(self.imgFileName)):
            with dpg.table_row(parent='vscImgFileTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(self.imgFileName[i])
                dpg.add_text(self.imgFilePath[i])
        
    def cancelImgImportFile(self, sender=None, app_data=None):
        dpg.hide_item('file_dialog_vscImg')
    
    def selectFolder(self, sender=None, app_data=None):
        pass    
    
    def exportVsc(self, sender=None, app_data=None):
        pass
    