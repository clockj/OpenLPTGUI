#%%
import os

#%%
frameIDStart = 1
frameIDEnd = 51
nCam = 4
digit = 5

imgFolder = 'D:\My Code\Tracking Code\LPTGUI\PYTHON\V1\Fig\camImg'
imgFileFolder = 'imgFile'
#%%
frameID = list(range(frameIDStart, frameIDEnd+1))

for i in range(nCam):
    imgFilePath = os.path.join(imgFileFolder, 'cam'+str(i+1)+'ImageNames.txt')
    with open(imgFilePath, 'w') as f:
        for j in frameID:
            imgPath = os.path.join(imgFolder, 'cam'+str(i+1), 'cam'+str(i+1)+'frame'+str(j).zfill(digit) + '.tif\n')
            f.write(imgPath)

# %%
