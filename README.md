# OpenLPTGUI 1.0

OpenLPTGUI 1.0 is a user-friendly GUI written in **python** for [OpenLPT](https://github.com/clockj/OpenLPT.git). OpenLPT is a code for Lagrangian particle tracking, and OpenLPTGUI is a GUI including **camera calibration, image pre-processing, installing/running OpenLPT, and Volume Self-Calibration**. 

This code is modified from [contExt](https://github.com/RafaelCasamaximo/contExt.git).

Look how easy it is to use:
```bash 
conda activate OpenLPTGUI
python main.py
```
or double-click the installed execusable file **./release/dist/OpenLPTGUI.exe**.


## Installation
Pre-request: [anaconda](https://www.anaconda.com/) (make sure the path to the **/bin/** folder is added to the system environment variable)

```bash
conda create --name OpenLPTGUI python=3.9.18

conda activate OpenLPTGUI

pip install -r requirements.txt

git clone https://github.com/clockj/OpenLPTGUI.git
```

If users want to generate the excusable file, you can run the following code:
- **Windows**: `.\build.cmd`
- **Linux**: `bash ./build.sh`
