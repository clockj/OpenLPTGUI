# OpenLPTGUI 1.0

OpenLPTGUI 1.0 is a user-friendly GUI written in **python** for [OpenLPT](https://github.com/clockj/OpenLPT.git). OpenLPT is a code for Lagrangian particle tracking, and OpenLPTGUI is a GUI including **camera calibration, image pre-processing, installing/running OpenLPT, and Volume Self-Calibration**. 

This code is modified from [contExt](https://github.com/RafaelCasamaximo/contExt.git).

Look how easy it is to use:
```bash 
conda activate OpenLPT
python main.py
```
or double-click the installed execusable file **./release/dist/OpenLPTGUI.exe**.


## Installation
### Pre-request: 
1. [Anaconda](https://www.anaconda.com/): add the **/bin/** folder to the system environment variable.
2. [pyOpenLPT](https://github.com/clockj/OpenLPT.git): make sure this package is installed in the same python environment.

```bash
git clone https://github.com/clockj/OpenLPTGUI.git

conda create --name OpenLPT python=3.9.18

conda activate OpenLPT

pip install -r requirements.txt

conda deactivate
```

If users want to generate the excusable file, you can run the following code:
- **Windows**: `.\build.cmd`
- **Linux**: `bash ./build.sh`
