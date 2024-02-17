import dearpygui.dearpygui as dpg
import cv2
import numpy as np
import pandas as pd
import os.path
import itertools 
from scipy.optimize import minimize
from multiprocessing import Pool

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
        self.rotMatInvList = []
        self.transVecInvList = [] # - inv(R) @ T
        
        self.nCam = None
        self.camFixID = []
        
        self.tracksFilePath = None
        self.tracksFileName = None
        self.tracks = None
        self.goodTracksThreshold = None
        self.particleInfo = None
        
        self.imgFilePath = []
        self.imgFilePath = []
        
        self.nThreads = None
        self.nIter = None
        
        # Outputs 
        self.exportFolderPath = None
        self.exportFilePrefix = None
        self.optParam = []
    
    def runVsc(self, sender=None, app_data=None):
        if self.nCam < 2:
            dpg.configure_item('noVscCam', show=True)
            return
        
        self.goodTracksThreshold = dpg.get_value('inputVscGoodTracksThreshold')
        
        # select good tracks 
        dpg.set_value('vscStatus', 'Status: Selecting good tracks!')
        self.selectGoodTracks()
        
        # select particles 
        dpg.set_value('vscStatus', 'Status: Selecting particles!')
        nParticles = dpg.get_value('inputVscNumParticles')
        goodParticles = self.selectParticles(nParticles)
        
        # get particle info: (WorldX, WorldY, WorldZ, Cam1ImgX, Cam1ImgY, ...)
        dpg.set_value('vscStatus', 'Status: Extracting particle info!')
        self.getParticleInfo(goodParticles)
        # print(self.particleInfo.shape)
        
        # optimize pose parameters 
        dpg.set_value('vscStatus', 'Status: Optimizing!')
        dpg.show_item('vscCurrentIter')
        dpg.show_item('vscCurrentCost')
        self.optCalib()
        
        dpg.set_value('vscStatus', 'Status: Finish!')
        
        
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
        goodParticles = self.tracks.iloc[isSelect.astype(bool), :]
        goodParticles.reset_index(drop=True, inplace=True)
        goodParticles.to_csv(self.camFilePath[0].replace(self.camFileName[0],'goodParticles.csv'), index=False)
        
        print('Finish selecting good particles!')
        
        return np.array(goodParticles, dtype=np.float32)
    
    def getParticleInfo(self, goodParticles):
        
        nParticles = goodParticles.shape[0]
        
        # project 3D points onto each camera
        # pt3D (WorldX, WorldY, WorldZ) => pt2D (ImgX, ImgY)
        searchR = dpg.get_value('inputVscParticleRadius') * 0.75
        pt2DList = np.zeros((nParticles, 2 * self.nCam), dtype=np.float32)
        
        pt3D = np.reshape(goodParticles[:, 2:5], (nParticles, 1, 3))
        for i in range(self.nCam):
            pt2D, _ = cv2.projectPoints(pt3D, self.rotVecList[i], self.transVecList[i], self.camMatList[i], self.distCoeffList[i])
            pt2D = np.reshape(pt2D, (nParticles, 2))
            pt2DList[:, 2*i:2*i+2] = pt2D
            
        # find candidates on each camera for each particle
        # check triangulation error
        # particle info: (WorldX, WorldY, WorldZ, Cam1ImgX, Cam1ImgY, ...)
        particleInfo = []
        for j in range(nParticles):
            delete = False
            imgCandidatesList = []
            imgCandidatesIDList = []
            
            for i in range(self.nCam):
                # load image 
                file = self.imgFilePath[i]
                with open(file, 'r') as f:
                    lines = f.readlines()
                    frameID = int(goodParticles[j,1])
                    # imgPath = self.imgFilePath[i].replace(self.imgFileName[i], lines[frameID].strip('\n'))
                    imgPath = lines[frameID].strip('\n')
                img = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE and cv2.IMREAD_ANYDEPTH)
                height, width = img.shape
                
                # define search range
                pt2D = pt2DList[j, 2*i:2*i+2]
                imgX = pt2D[0] # col 
                imgY = pt2D[1] # row
                rowMin = max(1, int(np.floor(imgY-searchR)))
                rowMax = min(height, int(np.ceil(imgY+searchR+1)))
                colMin = max(1, int(np.floor(imgX-searchR)))
                colMax = min(width, int(np.ceil(imgX+searchR+1)))
                searchImg = img[
                    rowMin : rowMax, 
                    colMin : colMax 
                ]

                # find candidates on img 
                imgCandidates = self.getImgCandidates(searchImg)
                if imgCandidates.shape[0] == 0:
                    delete = True
                    break
                else:
                    imgCandidates[:,0] += colMin # col
                    imgCandidates[:,1] += rowMin # row
                    imgCandidatesList.append(imgCandidates)
                    imgCandidatesIDList.append(list(range(imgCandidates.shape[0])))
              
            if delete:
                continue
            
            # Calculate triangulation error
            pairIDList = list(itertools.product(*imgCandidatesIDList))
            nPairs = len(pairIDList)
            errList = np.zeros(nPairs)
            tri3DList = np.zeros((nPairs, 3))
            errMin = np.inf
            errMinID = None
            errThreshold = dpg.get_value('inputVscTriangulationThreshold')
            bestImgCandidatesPair = []
            
            for idx, pairID in enumerate(pairIDList):
                imgCandidatesPair = []
                for camID in range(self.nCam):
                    imgCandidatesPair.append(imgCandidatesList[camID][pairID[camID],:])
                    
                tri3D, err = self.triangulation(imgCandidatesPair, param=[self.camMatList, self.distCoeffList, self.rotVecList, self.transVecList])
                tri3DList[idx, :] = tri3D
                errList[idx] = err
                
                if err < errMin:
                    errMin = err
                    errMinID = idx
                    bestImgCandidatesPair = imgCandidatesPair
            
            # print(errMin, flush=True)
            if errMin < errThreshold:
                info = [tri3DList[errMinID, :]]
                info += bestImgCandidatesPair[:]
                particleInfo.append(np.hstack(info))
                
        self.particleInfo = np.array(particleInfo)
        colName = ['WorldX', 'WorldY', 'WorldZ']
        for i in range(self.nCam):
            colName += ['Cam'+str(i+1)+'ImgX', 'Cam'+str(i+1)+'ImgY']
        df = pd.DataFrame(self.particleInfo, columns=colName)
        df.to_csv(self.camFilePath[0].replace(self.camFileName[0],'particleInfo.csv'), index=False)
        
        print('Finish extracting particle info!')

    def getImgCandidates(self, searchImg):
        nRow, nCol = searchImg.shape
        threshold = 35
        pt2DList = []
        for i in range(1, nRow-1): 
            for j in range(1, nCol-1):
                if searchImg[i, j] >= threshold and self.isLocalMax(searchImg, i, j):
                    x1,x2,x3,y1,y2,y3 = [j-1,j,j+1,i-1,i,i+1]
                    ln1 = self.nonInfLog(searchImg[i, j-1])
                    ln2 = self.nonInfLog(searchImg[i, j])
                    ln3 = self.nonInfLog(searchImg[i, j+1])
                
                    xc = -0.5 * (ln1*(x2*x2-x3*x3) - ln2*(x1*x1-x3*x3) + ln3*(x1*x1-x2*x2)) / (ln1*(x3-x2) - ln3*(x1-x2) + ln2*(x1-x3))
                    
                    ln1 = self.nonInfLog(searchImg[i-1, j])
                    ln2 = self.nonInfLog(searchImg[i, j])
                    ln3 = self.nonInfLog(searchImg[i+1, j])
                    yc = -0.5 * (ln1*(y2*y2-y3*y3) - ln2*(y1*y1-y3*y3) + ln3*(y1*y1-y2*y2)) / (ln1*(y3-y2) - ln3*(y1-y2) + ln2*(y1-y3))
                    
                    if not np.isinf(xc) and not np.isinf(yc):
                        pt2DList.append([xc, yc])
        return np.array(pt2DList)

    def isLocalMax(self, img, i, j):
        if img[i,j] > img[i-1,j] and img[i,j] > img[i,j-1] and img[i,j] > img[i,j+1] and img[i,j] > img[i+1,j]:
            return True
        else:
            return False
    
    def nonInfLog(self, x):
        if x == 0:
            x = 1e-4
        return np.log(x)
    
    def triangulation(self, imgCandidatesPair, param): 
        A = np.zeros((3, 3), dtype=np.float32)
        B = np.zeros((3, 1), dtype=np.float32)
        
        camMatList, distCoeffList, rotVecList, transVecList = param
        
        # get line of sight for each camera
        lineList = []
        for i in range(self.nCam):
            # undistort
            imgCandidate = np.reshape(imgCandidatesPair[i], (1,1,2))
            # pt = cv2.undistortPoints(imgCandidate, self.camMatList[i], self.distCoeffList[i])
            pt = cv2.undistortPointsIter(imgCandidate, camMatList[i], distCoeffList[i], R=np.eye(3), P=camMatList[i], criteria=(cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 100, 1e-5))
            
            ptUndistort = np.ones((3,1))
            ptUndistort[0] = pt[0,0,0]
            ptUndistort[1] = pt[0,0,1]
            # ptUndistort[0] = imgCandidatesPair[i][0]
            # ptUndistort[1] = imgCandidatesPair[i][1]
            
            # get rotation matrix   
            rotMat = cv2.Rodrigues(rotVecList[i])[0]
            rotMatInv = np.linalg.inv(rotMat)
            transVecInv = -rotMatInv @ transVecList[i]
            
            pt3D = rotMatInv @ np.linalg.inv(camMatList[i]) @ ptUndistort + transVecInv
            unitVec = pt3D - transVecInv
            unitVec = unitVec/np.linalg.norm(unitVec)

            lineList.append([transVecInv, unitVec])
            
            C = np.eye(3) - unitVec @ unitVec.T
            A += C
            B += C @ transVecInv
            
        # get intersection point
        tri3D = np.linalg.inv(A) @ B

        # get triangulation error
        err = 0
        for i in range(self.nCam):
            diff = tri3D - lineList[i][0]
            err += np.sqrt(np.abs(diff.T @ diff - (diff.T @ lineList[i][1])**2))
        err /= self.nCam
        
        return np.reshape(tri3D, (1,3)), err[0,0]
    
    def optCalib(self):
        
        # get fix cam id
        self.camFixID = [] 
        for i in range(self.nCam):
            if dpg.get_value('vscCamFixTable'+str(i)) == True:
                self.camFixID.append(i)
        
        # optimize pose parameters        
        x = np.zeros(6*(self.nCam-len(self.camFixID)), dtype=np.float32)
        idx = 0
        for i in range(self.nCam):
            if i in self.camFixID:
                continue
            else:
                x[6*idx:6*idx+3] = self.rotVecList[i][:,0]
                x[6*idx+3:6*idx+6] = self.transVecList[i][:,0]
                idx += 1
                
        maxIter = dpg.get_value('inputVscMaxIterations') 
        self.nThreads = dpg.get_value('inputVscNumThreads')  
        tolerance = dpg.get_value('inputVscTolerance')
        # res = minimize(self.costfunc, x, method='BFGS', tol=tolerance, options={'disp':True, 'maxiter':maxIter})
        self.nIter = 1
        res = minimize(self.costfunc, x, method='BFGS', options={'disp':True, 'maxiter':maxIter, 'xrtol': tolerance}, callback=self.optCallback)
        
        # get optimized pose parameters
        rotVecList = []
        transVecList = []
        idx = 0
        for i in range(self.nCam):
            if i in self.camFixID:
                rotVecList.append(self.rotVecList[i])
                transVecList.append(self.transVecList[i])
            else:
                rotVec = np.zeros((3,1))
                rotVec[:,0] = res.x[6*idx:6*idx+3]
                rotVecList.append(rotVec)
                transVec = np.zeros((3,1))
                transVec[:,0] = res.x[6*idx+3:6*idx+6]
                transVecList.append(transVec)
                idx += 1
        
        self.optParam = [rotVecList, transVecList]
        
        # print optimized results
        initCost = self.costfunc(x)
        finalCost = self.costfunc(res.x) 
        dpg.set_value('vscInitialCost', 'Initial Cost: ' + str(initCost).format('%.3f'))
        dpg.set_value('vscFinalCost', 'Final Cost: ' + str(finalCost).format('%.3f'))
                
        for tag in dpg.get_item_children('vscCamParamOptTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(self.nCam):
            rotMat = cv2.Rodrigues(rotVecList[i])[0]
            with dpg.table_row(parent='vscCamParamOptTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(str(rotMat))
                dpg.add_text(str(transVecList[i]))
                        
        dpg.configure_item('vscOptParamParent', show=True)
        dpg.configure_item('vscExportParent', show=True)
        
        print('Finish optimization!')
        
    def costfunc(self, x):
        
        # get pose parameters
        rotVecList = []
        transVecList = []
        idx = 0
        for i in range(self.nCam):
            if i in self.camFixID:
                rotVecList.append(self.rotVecList[i])
                transVecList.append(self.transVecList[i])
            else:
                rotVec = np.zeros((3,1))
                rotVec[:,0] = x[6*idx:6*idx+3]
                rotVecList.append(rotVec)
                transVec = np.zeros((3,1))
                transVec[:,0] = x[6*idx+3:6*idx+6]
                transVecList.append(transVec)
                idx += 1
        
        triParam = [self.camMatList, self.distCoeffList, rotVecList, transVecList]
        with Pool(self.nThreads) as pool:
            res = pool.starmap(self.costfuncTask, zip(self.particleInfo[:, 3:], itertools.repeat(triParam)))
        # cost = np.mean(res)
        # cost = np.max(res)
        cost = np.sum(res)
        # print(cost)
        return cost
    
    def costfuncTask(self, pair, param):
        pair = list(np.reshape(pair, (self.nCam, 2)))
        _, err = self.triangulation(pair, param)
        return err
    
    def optCallback(self, xi):
        if self.nIter%1 == 0:
            dpg.set_value('vscCurrentIter', 'Current Iteration: ' + str(self.nIter))
            dpg.set_value('vscCurrentCost', 'Current Cost: ' + str(self.costfunc(xi)).format('%.3f'))
        self.nIter += 1
    
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
        self.rotMatInvList = []
        self.transVecInvList = [] # - inv(R) @ T
        
        selections = app_data['selections']
        self.nCam = len(selections)
        if self.nCam == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('No file selected', parent='noVscPath')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.add_text('Wrong path:', parent='noVscPath')
                dpg.add_text(values, parent='noVscPath')
                return
            self.camFilePath.append(values)
            self.camFileName.append(keys)
        
            # Load camera parameters
            with open(values, 'r') as f:
                lines = f.readlines()[2:]
                
                if 'None' in lines[1] or 'none' in lines[1]:
                    self.camcalibErrList.append(None)
                else:
                    self.camcalibErrList.append(float(lines[1]))
                if 'None' in lines[3] or 'none' in lines[3]:
                    self.posecalibErrList.append(None)
                else:
                    self.posecalibErrList.append(float(lines[3]))
                
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
                rotMatInv = np.zeros((3,3))
                rotMatInv[0,:] = np.array(lines[17].split(',')).astype(np.float32)
                rotMatInv[1,:] = np.array(lines[18].split(',')).astype(np.float32)
                rotMatInv[2,:] = np.array(lines[19].split(',')).astype(np.float32)
                self.rotMatInvList.append(rotMatInv)
                
                transVec = np.zeros((3,1))
                transVec[:,0] = np.array(lines[21].split(',')).astype(np.float32)
                self.transVecList.append(transVec)
                # line 23 is transVecInv
                transVecInv = np.zeros((3,1))
                transVecInv[:,0] = np.array(lines[23].split(',')).astype(np.float32)
                self.transVecInvList.append(transVecInv)
                
        # Update status 
        dpg.set_value('vscCamStatus', 'Status: Finish!')
    
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
    
        # Update camera fix table 
        for tag in dpg.get_item_children('vscCamFixTable')[1]:
            dpg.delete_item(tag)
        for i in range(self.nCam):
            with dpg.table_row(parent='vscCamFixTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_checkbox(tag='vscCamFixTable'+str(i), default_value=False)     
    
    def cancelCamImportFile(self, sender=None, app_data=None):
        dpg.hide_item('file_dialog_vscCam')
    
    def openTracksFile(self, sender=None, app_data=None):
        self.tracksFilePath = app_data['file_path_name']
        self.tracksFileName = app_data['file_name']
        
        if os.path.isfile(self.tracksFilePath) is False:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('Wrong path:', parent='noVscPath')
            dpg.add_text(self.tracksFilePath, parent='noVscPath')
            return
                    
        # Load tracks data
        self.tracks = pd.read_csv(self.tracksFilePath)
        
        # Update status 
        dpg.set_value('vscTracksStatus', 'Status: Finish!')
        
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
        selections = app_data['selections']
        if len(selections) == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('No file selected', parent='noVscPath')
            return
        elif len(selections) != self.nCam:
            dpg.configure_item('noVscPath', show=True)
            dpg.add_text('The number of selected files does not match the number of cameras', parent='noVscPath')
            return
        
        self.imgFilePath = []
        self.imgFileName = []
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.add_text('Wrong path:', parent='noVscPath')
                dpg.add_text(values, parent='noVscPath')
                return
            self.imgFilePath.append(values)
            self.imgFileName.append(keys)
        
        # Update status
        dpg.set_value('vscImgStatus', 'Status: Finish!')
        
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
        self.exportFolderPath = app_data['file_path_name']
        self.exportFilePrefix = dpg.get_value('inputVscFilePrefix')

        dpg.set_value('exportVscFolderName', 'Folder: ' + self.exportFolderPath)
        dpg.set_value('exportVscPrefixName', 'Prefix: ' + self.exportFilePrefix)
    
    def exportVsc(self, sender=None, app_data=None):
        if self.exportFolderPath is None:
            dpg.configure_item('exportVscError', show=True)
            return
        dpg.configure_item('exportVscError', show=False)
        
        rotVecList, transVecList = self.optParam
        # Export optimized camera file
        for i in range(self.nCam):
            if i not in self.camFixID:
                filePath = os.path.join(self.exportFolderPath, self.exportFilePrefix+'cam'+str(i+1)+'.txt')
                with open(filePath, 'w') as f:
                    f.write('# Camera Model: (PINHOLE/POLYNOMIAL)\n' + str('PINHOLE') + '\n')
                    f.write('# Camera Calibration Error: \n' + str(self.camcalibErrList[i]) + '\n')
                    f.write('# Pose Calibration Error: \n' + str(self.posecalibErrList[i]) + '\n')
                    
                    f.write('# Camera Matrix: \n')
                    f.write(str(self.camMatList[i][0,0])+','+str(self.camMatList[i][0,1])+','+str(self.camMatList[i][0,2])+'\n')
                    f.write(str(self.camMatList[i][1,0])+','+str(self.camMatList[i][1,1])+','+str(self.camMatList[i][1,2])+'\n')
                    f.write(str(self.camMatList[i][2,0])+','+str(self.camMatList[i][2,1])+','+str(self.camMatList[i][2,2])+'\n')
                    f.write('# Distortion Coefficients: \n')
                    f.write(str(self.distCoeffList[i][0,0])+','+str(self.distCoeffList[i][0,1])+','+str(self.distCoeffList[i][0,2])+','+str(self.distCoeffList[i][0,3])+','+str(self.distCoeffList[i][0,4])+'\n')
                    
                    f.write('# Rotation Vector: \n')
                    f.write(str(rotVecList[i][0,0])+','+str(rotVecList[i][1,0])+','+str(rotVecList[i][2,0])+'\n')
                    f.write('# Rotation Matrix: \n')
                    rotMat = cv2.Rodrigues(rotVecList[i])[0]
                    f.write(str(rotMat[0,0])+','+str(rotMat[0,1])+','+str(rotMat[0,2])+'\n')
                    f.write(str(rotMat[1,0])+','+str(rotMat[1,1])+','+str(rotMat[1,2])+'\n')
                    f.write(str(rotMat[2,0])+','+str(rotMat[2,1])+','+str(rotMat[2,2])+'\n')
                    f.write('# Inverse of Rotation Matrix: \n')
                    rotMatInv = np.linalg.inv(rotMat)
                    f.write(str(rotMatInv[0,0])+','+str(rotMatInv[0,1])+','+str(rotMatInv[0,2])+'\n')
                    f.write(str(rotMatInv[1,0])+','+str(rotMatInv[1,1])+','+str(rotMatInv[1,2])+'\n')
                    f.write(str(rotMatInv[2,0])+','+str(rotMatInv[2,1])+','+str(rotMatInv[2,2])+'\n')
                    f.write('# Translation Vector: \n')
                    f.write(str(transVecList[i][0,0])+','+str(transVecList[i][1,0])+','+str(transVecList[i][2,0])+'\n')
                    f.write('# Inverse of Translation Vector: \n')
                    transVecInv = -np.matmul(rotMatInv, transVecList[i])
                    f.write(str(transVecInv[0,0])+','+str(transVecInv[1,0])+','+str(transVecInv[2,0])+'\n')
            
        dpg.configure_item("exportVsc", show=False)
        dpg.configure_item('vscExportFolder', show=True)
        dpg.set_value('vscExportFolder', 'Export Folder: ' + self.exportFolderPath)
        
    def cancelExportVsc(self, sender=None, app_data=None):
        dpg.hide_item('dir_dialog_vscOutput')
    