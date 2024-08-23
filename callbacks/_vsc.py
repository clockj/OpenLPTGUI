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

class Vsc:
    def __init__(self) -> None:
        self.camFilePath = [] 
        self.camFileName = []
        self.cam = []

        self.nCam = None
        self.isCamFix = None
        
        self.tracksFilePath = None
        self.tracksFileName = None
        self.tracks = None
        self.goodTracksThreshold = None
        self.particleInfo = None
        
        self.imgFilePath = []
        self.imgFilePath = []
        
        self.nThreads = None
        self.loss = []
        self.cam_update = []
        self.pt2d_list_lpt = []
        
        # Outputs 
        self.exportFolderPath = None
        self.exportFilePrefix = None
    
    def runVsc(self, sender=None, app_data=None):
        if self.nCam < 2:
            dpg.configure_item('noVscCam', show=True)
            return
        
        self.goodTracksThreshold = dpg.get_value('inputVscGoodTracksThreshold')
        
        # init
        dpg.set_value('vscStatus', 'Status: Start!')
        dpg.set_value('vscStatus_goodTracks', 'Selecting good tracks: --')
        dpg.set_value('vscStatus_particles', 'Selecting particles: --')
        dpg.set_value('vscStatus_particleInfo', 'Extracting particle info: --')
        dpg.set_value('vscStatus_optimize', 'Optimizing: --')
        
        # select good tracks
        self.selectGoodTracks()
        dpg.set_value('vscStatus_goodTracks', 'Selecting good tracks: Finish!')
        # only for debug 
        # self.tracks = pd.read_csv(self.camFilePath[0].replace(self.camFileName[0],'goodTracks.csv'))
        
        # select particles 
        nParticles = dpg.get_value('inputVscNumParticles')
        goodParticles = self.selectParticles(nParticles)
        dpg.set_value('vscStatus_particles', 'Selecting particles: Finish!')
        
        # get particle info: (WorldX, WorldY, WorldZ, Cam1ImgX, Cam1ImgY, ...)
        self.getParticleInfo(goodParticles)
        dpg.set_value('vscStatus_particleInfo', 'Extracting particle info: Finish!')
        # only for debug, generate debug dataset
        # npts = 4000
        # np.random.seed(0)
        # pt3d = np.random.rand(npts,3)*40 - 20
        # pt3d_lpt = [lpt.math.Pt3D(pt3d[i,0], pt3d[i,1], pt3d[i,2]) for i in range(npts)]
        # pt2d_list = [cam.project(pt3d_lpt) for cam in self.cam]
        # self.particleInfo = np.zeros((npts, 3+2*self.nCam))
        # self.particleInfo[:,0:3] = pt3d
        # for i in range(self.nCam):
        #     self.particleInfo[:,3+2*i:3+2*(i+1)] = np.array([[pt2d_list[i][j][0], pt2d_list[i][j][1]] for j in range(npts)])
        
        
        # optimize pose parameters 
        self.optCalib()
        dpg.set_value('vscStatus_optimize', 'Optimizing: Finish!')
        dpg.set_value('vscStatus', 'Status: Finish!')
        
    def selectGoodTracks(self):
        trackIDList = self.tracks['TrackID'].unique()
        
        for trackID in trackIDList:
            track = self.tracks.loc[self.tracks['TrackID'] == trackID]  
            length = track.shape[0]
            if length < 20:
                self.tracks.drop(track.index, inplace=True)
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
        nUniform = np.sum(isSelect)
        nLess = int(nParticles - nUniform)
        if nLess > 0:
            id = np.array(range(self.tracks.shape[0]))
            notSelectID = id[isSelect==0]
            if nLess > len(notSelectID):
                newSelectID = notSelectID   
            else:
                newSelectID = np.random.choice(notSelectID, nLess, replace=False)
            isSelect[newSelectID] = 1
            
        print('Number of selected particles:', np.sum(isSelect))
        print('Number of uniformly distributed particles:', nUniform)

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
        pt3d_list = [lpt.math.Pt3D(goodParticles[j, 2], goodParticles[j, 3], goodParticles[j, 4]) for j in range(nParticles)]
        pt2d_list_all = [self.cam[i].project(pt3d_list) for i in range(self.nCam)]
        
        # load imgio 
        imgio_list = [lpt.math.ImageIO('', self.imgFilePath[i]) for i in range(self.nCam)]
            
        # find candidates on each camera for each particle
        # check triangulation error
        # particle info: (WorldX, WorldY, WorldZ, Cam1ImgX, Cam1ImgY, ...)
        searchR = dpg.get_value('inputVscParticleRadius') * 0.75
        errThreshold = dpg.get_value('inputVscTriangulationThreshold')
        
        properties = [2.0**32-1, 35.0, 2.0]
        is_delete = np.array([False]*nParticles)
        particleInfo = []
        for j in range(nParticles):
            pt2d_candidates_list = []
            pt2d_candidates_IDList = []
            sight_list = []
            
            for i in range(self.nCam):
                # load image 
                frameID = int(goodParticles[j,1])
                img = imgio_list[i].loadImg(frameID)
                width = self.cam[i].getNCol()
                height = self.cam[i].getNRow()
                
                # define search range
                region = lpt.PixelRange()
                x = pt2d_list_all[i][j][0]
                y = pt2d_list_all[i][j][1]
                region.row_min = max(1, int(np.floor(y-searchR)))
                region.row_max = min(height, int(np.ceil(y+searchR+1)))
                region.col_min = max(1, int(np.floor(x-searchR)))
                region.col_max = min(width, int(np.ceil(x+searchR+1)))

                # find candidates on img 
                obj2d_list = lpt.object.ObjectFinder2D().findTracer2D(img, properties, region)
                n_obj2d = len(obj2d_list)
                if n_obj2d == 0:
                    is_delete[j] = True
                    break
                else:
                    pt2d_candidates = [lpt.math.Pt2D(obj2d._pt_center) for obj2d in obj2d_list]
                    sight_list.append(self.cam[i].lineOfSight(pt2d_candidates))
                    pt2d_candidates_list.append(pt2d_candidates)
                    pt2d_candidates_IDList.append(list(range(n_obj2d)))
              
            if is_delete[j]:
                continue
            
            # Calculate triangulation error
            pairID_list = list(itertools.product(*pt2d_candidates_IDList))
            sight_list_all = [[sight_list[cam_id][pairID[cam_id]] for cam_id in range(self.nCam)] for pairID in pairID_list]
            
            tri3d_list, err_list = lpt.math.triangulation(sight_list_all)
            
            minid = np.argmin(err_list)
            errMin = err_list[minid]
            if errMin < errThreshold:
                info = [tri3d_list[minid][0], tri3d_list[minid][1], tri3d_list[minid][2]]
                info += [pt2d_candidates_list[cam_id][pairID_list[minid][cam_id]][axis_id] for cam_id in range(self.nCam) for axis_id in range(2)]
                particleInfo.append(np.hstack(info))
                
        self.particleInfo = np.array(particleInfo)
        colName = ['WorldX', 'WorldY', 'WorldZ']
        for i in range(self.nCam):
            colName += ['Cam'+str(i+1)+'ImgX', 'Cam'+str(i+1)+'ImgY']
        df = pd.DataFrame(self.particleInfo, columns=colName)
        df.to_csv(self.camFilePath[0].replace(self.camFileName[0],'particleInfo.csv'), index=False)
        
        print('Finish extracting particle info!')

    def optCalib(self):
        # get fix cam id
        self.isCamFix = np.zeros(self.nCam).astype(bool)
        for i in range(self.nCam):
            if dpg.get_value('vscCamFixTable'+str(i)) == True:
                self.isCamFix[i] = True
        
        # convert to Pt2D list
        self.pt2d_list_lpt = [[lpt.math.Pt2D(self.particleInfo[j, 3+2*i], self.particleInfo[j, 3+2*i+1]) for j in range(self.particleInfo.shape[0])] for i in range(self.nCam)]
        
        # optimize parameters        
        x = []
        id = 0
        for i in range(self.nCam):
            if self.isCamFix[i]:
                continue
            if self.cam[i]._type == lpt.math.CameraType.PINHOLE:
                x += list(lpt.math.matrix_to_numpy(self.cam[i].rmtxTorvec(self.cam[i]._pinhole_param.r_mtx)).reshape(-1,))
                # x += list(cv2.Rodrigues(lpt.math.matrix_to_numpy(cam[i]._pinhole_param.r_mtx))[0].reshape(-1,))
                x += list(lpt.math.matrix_to_numpy(self.cam[i]._pinhole_param.t_vec).reshape(-1,))
                id += 6
            elif self.cam[i]._type == lpt.math.CameraType.POLYNOMIAL:
                x += list(lpt.math.matrix_to_numpy(self.cam[i]._poly_param.u_coeffs)[:,0])
                x += list(lpt.math.matrix_to_numpy(self.cam[i]._poly_param.v_coeffs)[:,0])
                id += self.cam[i]._poly_param.n_coeff * 2
        x = np.array(x) 
        self.cam_update = [lpt.math.Camera(self.cam[i]) for i in range(self.nCam)]
        
        cost = self.costfunc(x)
        print('Initial cost: ', cost)
                
        maxIter = dpg.get_value('inputVscMaxIterations') 
        # self.nThreads = dpg.get_value('inputVscNumThreads')  
        tolerance = dpg.get_value('inputVscTolerance')
        self.loss = [cost]
        
        t_start = time.time()
        res = minimize(self.costfunc, x, method='L-BFGS-B', tol=tolerance, options={'maxiter':maxIter}, callback=self.optCallback)
        t_end = time.time()
        print('Time: ', t_end-t_start)
        
        dpg.configure_item('vscPlotButton_loss', show=True)
        dpg.configure_item('vscPlotButton_selectedParticles', show=True)     
        dpg.configure_item('vscPlotButton_errhist', show=True)       
        dpg.configure_item('vscExportParent', show=True)
        
        print('Finish optimization!')
        
    def costfunc(self, x):
        npts = len(self.pt2d_list_lpt[0])
        
        # update cam 
        id = 0
        line_list_all = []
        for i in range(self.nCam):
            if not self.isCamFix[i]:
                if self.cam_update[i]._type == lpt.math.CameraType.PINHOLE:
                    rotVec = np.array(x[id:id+3])
                    transVec = np.array(x[id+3:id+6]).reshape(3,1)
                    rotMat = cv2.Rodrigues(rotVec)[0]
                    rotMatInv = np.linalg.inv(rotMat)
                    transVecInv = - rotMatInv @ transVec
                    
                    self.cam_update[i]._pinhole_param.r_mtx = lpt.math.numpy_to_matrix(cv2.Rodrigues(rotVec)[0])
                    self.cam_update[i]._pinhole_param.t_vec = lpt.math.Pt3D(transVec[0,0], transVec[1,0], transVec[2,0])
                    self.cam_update[i]._pinhole_param.r_mtx_inv = lpt.math.numpy_to_matrix(rotMatInv)
                    self.cam_update[i]._pinhole_param.t_vec_inv = lpt.math.Pt3D(transVecInv[0,0], transVecInv[1,0], transVecInv[2,0])
                    
                    id += 6
                    
                elif self.cam_update[i]._type == lpt.math.CameraType.POLYNOMIAL:
                    u_coeffs = lpt.math.matrix_to_numpy(self.cam_update[i]._poly_param.u_coeffs)
                    v_coeffs = lpt.math.matrix_to_numpy(self.cam_update[i]._poly_param.v_coeffs)
                    n_coeff = self.cam_update[i]._poly_param.n_coeff
                    
                    u_coeffs[:,0] = x[id:id+n_coeff]
                    v_coeffs[:,0] = x[id+n_coeff:id+n_coeff*2]
                    
                    self.cam_update[i]._poly_param.u_coeffs = lpt.math.numpy_to_matrix(u_coeffs)
                    self.cam_update[i]._poly_param.v_coeffs = lpt.math.numpy_to_matrix(v_coeffs)
                    self.cam_update[i].updatePolyDuDv()
                    
                    id += n_coeff * 2

            line_list = self.cam_update[i].lineOfSight(self.pt2d_list_lpt[i])
            line_list_all.append(line_list)

        # triangulation
        sight_list_all = [[line_list_all[j][i] for j in range(self.nCam)] for i in range(npts)]
        _, err_list = lpt.math.triangulation(sight_list_all)
        return np.mean(err_list)
    
    def optCallback(self, xi):
        self.loss.append(self.costfunc(xi))
    
    def openCamFile(self, sender=None, app_data=None):
        self.cam = [] 
        
        selections = app_data['selections']
        self.nCam = len(selections)
        if self.nCam == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.set_value('noVscPathText', 'No file selected!')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.set_value('noVscPathText', 'Wrong path:\n'+values)
                return
            self.camFilePath.append(values)
            self.camFileName.append(keys)
        
            # Load camera parameters
            self.cam.append(lpt.math.Camera(values))
                
        # Update status 
        dpg.set_value('vscCamStatus', 'Status: Finish!')
    
        # Print outputs onto the output window
        dpg.configure_item('vscCamOutputParent', show=True)
        
        for tag in dpg.get_item_children('vscCamFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(self.nCam):
            with dpg.table_row(parent='vscCamFileTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_text(self.camFileName[i])
                dpg.add_text(self.camFilePath[i])
    
        # Update camera fix table 
        for tag in dpg.get_item_children('vscCamFixTable')[1]:
            dpg.delete_item(tag)
        for i in range(self.nCam):
            with dpg.table_row(parent='vscCamFixTable'):
                dpg.add_text('Cam'+str(i+1))
                dpg.add_checkbox(tag='vscCamFixTable'+str(i), default_value=False)     
    
    
    # plot options 
    def plotImportedTracks(self, sender=None, app_data=None):
        # plot 3d tracks
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(self.tracks['WorldX'], self.tracks['WorldY'], self.tracks['WorldZ'], 'b.', markersize=0.5)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Imported Tracks')
        plt.savefig(self.camFilePath[0].replace(self.camFileName[0],'tracks.png'), dpi=600)
        plt.close()
        Texture.createTexture('vscPlot', cv2.imread(self.camFilePath[0].replace(self.camFileName[0],'tracks.png')))
        
    def plotLoss(self, sender=None, app_data=None):
        # plot loss
        plt.figure()
        plt.plot(np.arange(len(self.loss)), self.loss,'.-')
        plt.xlabel('Iteration')
        plt.ylabel('Loss')
        plt.title('Optimization History')
        plt.savefig(self.camFilePath[0].replace(self.camFileName[0],'loss.png'), dpi=600)
        plt.close()
        Texture.createTexture('vscPlot', cv2.imread(self.camFilePath[0].replace(self.camFileName[0],'loss.png')))
    
    def plotSelectedParticles(self, sender=None, app_data=None):
        # get updated particle info
        npts = len(self.pt2d_list_lpt[0]) 
        line_list_all = []
        for i in range(self.nCam):
            line_list = self.cam_update[i].lineOfSight(self.pt2d_list_lpt[i])
            line_list_all.append(line_list)
        # triangulation
        sight_list_all = [[line_list_all[j][i] for j in range(self.nCam)] for i in range(npts)]
        pt3d_list, _ = lpt.math.triangulation(sight_list_all)
        pt3d_np = np.array([[pt3d_list[i][0], pt3d_list[i][1], pt3d_list[i][2]] for i in range(npts)])
        
        # plot 3d particles
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(self.particleInfo[:,0], self.particleInfo[:,1], self.particleInfo[:,2], 'b.', markersize=0.5, label='Before Optimization')
        ax.plot(pt3d_np[:,0], pt3d_np[:,1], pt3d_np[:,2], 'r+', markersize=0.5, label='After Optimization')
        plt.legend()
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Selected Particles')
        plt.savefig(self.camFilePath[0].replace(self.camFileName[0],'particles.png'), dpi=600)
        plt.close()
        Texture.createTexture('vscPlot', cv2.imread(self.camFilePath[0].replace(self.camFileName[0],'particles.png')))
        
    def plotErrorHistogram(self, sender=None, app_data=None):
        npts = len(self.pt2d_list_lpt[0])
        
        # calculate original error distribution 
        line_list_all = []
        for i in range(self.nCam):
            line_list = self.cam[i].lineOfSight(self.pt2d_list_lpt[i])
            line_list_all.append(line_list)
        # triangulation
        sight_list_all = [[line_list_all[j][i] for j in range(self.nCam)] for i in range(npts)]
        _, err_orig = lpt.math.triangulation(sight_list_all)
        
        # calculate optimized error distribution
        line_list_all = []
        for i in range(self.nCam):
            line_list = self.cam_update[i].lineOfSight(self.pt2d_list_lpt[i])
            line_list_all.append(line_list)
        # triangulation
        sight_list_all = [[line_list_all[j][i] for j in range(self.nCam)] for i in range(npts)]
        _, err_opt = lpt.math.triangulation(sight_list_all)
        
        # plot histogram
        plt.figure()
        plt.hist(err_orig, bins=50, alpha=0.5, label='Before Optimization')
        plt.hist(err_opt, bins=50, alpha=0.5, label='After Optimization')
        plt.xlabel('Error')
        plt.ylabel('Number')
        plt.legend()
        plt.title('Error Distribution')
        plt.tight_layout()
        plt.savefig(self.camFilePath[0].replace(self.camFileName[0],'errorPDF.png'), dpi=600)
        plt.close()
        
        Texture.createTexture('vscPlot', cv2.imread(self.camFilePath[0].replace(self.camFileName[0],'errorPDF.png')))
    
    # File IO
    def cancelCamImportFile(self, sender=None, app_data=None):
        dpg.hide_item('file_dialog_vscCam')
    
    def openTracksFile(self, sender=None, app_data=None):
        self.tracksFilePath = []
        self.tracksFileName = []
        self.tracks = pd.DataFrame()
        
        selections = app_data['selections']
        nFiles = len(selections)
        if nFiles == 0:
            dpg.configure_item('noVscPath', show=True)
            dpg.set_value('noVscPathText', 'No file selected!')
            return
        
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.set_value('noVscPathText', 'Wrong path:\n'+values)
                return
            self.tracksFilePath.append(values)
            self.tracksFileName.append(keys)
        
        for i in range(nFiles):
            df = pd.read_csv(self.tracksFilePath[i])
            if not self.tracks.empty:
                df['TrackID'] += self.tracks['TrackID'].unique().shape[0]
            self.tracks = pd.concat([self.tracks, df], axis=0, ignore_index=True)
        self.tracks.reset_index(drop=True, inplace=True)
        
        # Update status 
        dpg.set_value('vscTracksStatus', 'Status: Finish!')
        
        dpg.configure_item('vscPlotButton_importedTracks', show=True)
        
        # Print tracks output 
        dpg.configure_item('vscTracksOutputParent', show=True)
        
        for tag in dpg.get_item_children('vscTracksFileTable')[1]:
            dpg.delete_item(tag)
        
        for i in range(len(self.tracksFileName)):
            with dpg.table_row(parent='vscTracksFileTable'):
                dpg.add_text(self.tracksFileName[i])
                dpg.add_text(self.tracksFilePath[i])
        
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
            dpg.set_value("noVscPathText", 'No file selected')
            return
        elif len(selections) != self.nCam:
            dpg.configure_item('noVscPath', show=True)
            dpg.set_value("noVscPathText", 'The number of selected files does not match the number of cameras')
            return
        
        self.imgFilePath = []
        self.imgFileName = []
        for keys, values in selections.items():
            if os.path.isfile(values) is False:
                dpg.configure_item('noVscPath', show=True)
                dpg.set_value("noVscPathText", 'Wrong path:\n'+values)
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
        
        # Export optimized camera file
        for i in range(self.nCam):
            if not self.isCamFix[i]:
                filePath = os.path.join(self.exportFolderPath, self.exportFilePrefix+'cam'+str(i+1)+'.txt')
                self.cam_update[i].saveParameters(filePath)
            
        dpg.configure_item("exportVsc", show=False)
        dpg.configure_item('vscExportFolder', show=True)
        dpg.set_value('vscExportFolder', 'Export Folder: ' + self.exportFolderPath)
        
    def cancelExportVsc(self, sender=None, app_data=None):
        dpg.hide_item('dir_dialog_vscOutput')
    