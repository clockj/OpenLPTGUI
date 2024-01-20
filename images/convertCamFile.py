#%%
import numpy as np 
import cv2
#%%
origFileList = ['cam1Params.txt', 'cam2Params.txt', 'cam3Params.txt', 'cam4Params.txt']
newFileList = ['cam1.txt', 'cam2.txt', 'cam3.txt', 'cam4.txt']
nCam = len(origFileList)

for i in range(nCam):
    # load camera parameters
    camParam = np.loadtxt(origFileList[i])

    # camera matrix
    camMat = np.zeros((3,3))
    camMat[0,0] = camParam[6] / camParam[4]
    camMat[0,2] = (camParam[2]) / 2 - 1
    camMat[1,1] = -camParam[6] / camParam[5]
    camMat[1,2] = (camParam[3]) / 2 - 1
    camMat[2,2] = 1

    # distortion coefficients
    distCoeff = np.zeros((1,5))
    distCoeff[0,0] = camParam[7]

    # rotation matrix
    rotMat = np.reshape(camParam[9:18], (3,3))
    # rotMat[1,:] = -rotMat[1,:]

    # inverse of rotation matrix
    rotMatInv = np.linalg.inv(rotMat)

    # rotation vector
    rotVec = cv2.Rodrigues(rotMat)[0]

    # translation vector 
    transVec = np.reshape(camParam[18:21], (3,1))
    # transVec[1,0] = -transVec[1,0]

    # inverse of translation vector
    transVecInv = - rotMatInv @ transVec
    
    # save camera parameters
    with open(newFileList[i], 'w') as f:
        f.write('# Camera Calibration Error: \n' + str(None) + '\n')
        f.write('# Pose Calibration Error: \n' + str(None) + '\n')
        
        f.write('# Camera Matrix: \n')
        f.write(str(camMat[0,0])+','+str(camMat[0,1])+','+str(camMat[0,2])+'\n')
        f.write(str(camMat[1,0])+','+str(camMat[1,1])+','+str(camMat[1,2])+'\n')
        f.write(str(camMat[2,0])+','+str(camMat[2,1])+','+str(camMat[2,2])+'\n')
        f.write('# Distortion Coefficients: \n')
        f.write(str(distCoeff[0,0])+','+str(distCoeff[0,1])+','+str(distCoeff[0,2])+','+str(distCoeff[0,3])+','+str(distCoeff[0,4])+'\n')
        f.write('# Rotation Vector: \n')
        f.write(str(rotVec[0,0])+','+str(rotVec[1,0])+','+str(rotVec[2,0])+'\n')
        f.write('# Rotation Matrix: \n')
        f.write(str(rotMat[0,0])+','+str(rotMat[0,1])+','+str(rotMat[0,2])+'\n')
        f.write(str(rotMat[1,0])+','+str(rotMat[1,1])+','+str(rotMat[1,2])+'\n')
        f.write(str(rotMat[2,0])+','+str(rotMat[2,1])+','+str(rotMat[2,2])+'\n')
        f.write('# Inverse of Rotation Matrix: \n')
        f.write(str(rotMatInv[0,0])+','+str(rotMatInv[0,1])+','+str(rotMatInv[0,2])+'\n')
        f.write(str(rotMatInv[1,0])+','+str(rotMatInv[1,1])+','+str(rotMatInv[1,2])+'\n')
        f.write(str(rotMatInv[2,0])+','+str(rotMatInv[2,1])+','+str(rotMatInv[2,2])+'\n')
        f.write('# Translation Vector: \n')
        f.write(str(transVec[0,0])+','+str(transVec[1,0])+','+str(transVec[2,0])+'\n')
        f.write('# Inverse of Translation Vector: \n')
        f.write(str(transVecInv[0,0])+','+str(transVecInv[1,0])+','+str(transVecInv[2,0])+'\n')

# %%
