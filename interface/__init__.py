import dearpygui.dearpygui as dpg
import tkinter as tk
import os
from ._extractionTab import showContourExtraction
from ._filteringTab import showFiltering
from ._processingTab import showProcessing
from ._thresholdingTab import showThresholding
from ._theme import applyTheme

from ._camCalibWindow import showOpenCVCalib
from ._polyCalibWindow import showPolyCalib
from ._vscWindow import showVSC
from ._imgProcessWindow import showImgProcess
from ._openLPTWindow import showOpenLPT

class Interface:

    def __init__(self, callbacks) -> None:
        self.callbacks = callbacks
        root = tk.Tk()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()
        
        self.width_factor = 0.9
        self.height_factor = 0.9
        self.font_factor = 0.02
        
        self.window_width = int(self.screen_width * self.width_factor)
        self.window_height = int(self.screen_height * self.height_factor)
        self.font_size = int(self.window_height * self.font_factor)
        
        self.subwindow_width = int(0.98 * self.window_width)
        self.subwindow_height = int(0.9 * self.window_height)
        
        print(f"Screen Width: {self.screen_width}")
        print(f"Screen Height: {self.screen_height}")
        print(f"Window Width: {self.window_width}")
        print(f"Window Height: {self.window_height}")
        print(f"Font Size: {self.font_size}")
        
        self.show()

    def show(self):
        dpg.create_context()        
        dpg.create_viewport(title='OpenLPT - An Open Source Software for Lagragian Particle Tracking', width=self.window_width, height=self.window_height, x_pos=self.screen_width//2 - self.window_width//2, y_pos=self.screen_height//2 - self.window_height//2)

        applyTheme(self.font_size, int(1e-3*self.window_width))
        
        with dpg.window(tag="Main"):
            dpg.add_text('1. Select a calibration method')
            dpg.add_listbox(tag='calibMethod', items=['Calibration Plate', 'Easy Wand'])
            dpg.add_button(label='Apply Method', callback=self.selectCalibMethod)
            dpg.add_text('')
            
            dpg.add_text('2. Select a camera model')
            dpg.add_listbox(tag='camModel', items=['Pinhole', 'Polynomial'])
            dpg.add_button(label='Apply Model', callback=self.selectCamModel)
            dpg.add_text('')
            
            dpg.add_text('3. Image Preprocessing (Optional)')
            dpg.add_button(label='Run Preprocessing', callback=lambda: dpg.configure_item('imgProcess', show=True))
            dpg.add_text('')
            
            dpg.add_text('4. Run OpenLPT')
            dpg.add_button(label='Run OpenLPT', callback=lambda: dpg.configure_item('openLPT', show=True))
            dpg.add_text('')
            
            dpg.add_text('5. Run Volume Self Calibration (Optional, suggested for few calibration points)')
            dpg.add_button(label='Run VSC', callback=lambda: dpg.configure_item('vsc', show=True))
            dpg.add_text('')
            
               
        with dpg.window(tag="calibPlate", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Calibration Plate'):
            self.showCalibPlateTabBar()
            self.createSaveImageDialog()

        with dpg.window(tag="easyWand", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Easy Wand'):
            dpg.add_text('Easy Wand')
            
        with dpg.window(tag="opcvCalib", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Pinhole Calibration'):
            showOpenCVCalib(self.callbacks)
        
        with dpg.window(tag="polyCalib", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Polynomial Calibration'):
            showPolyCalib(self.callbacks)
        
        with dpg.window(tag="vsc", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Volume Self Calibration'):
            showVSC(self.callbacks)
            
        with dpg.window(tag="imgProcess", show=False, width=self.subwindow_width, height=self.subwindow_height, label='Image Processing'):
            showImgProcess(self.callbacks)
            self.callbacks.lptImgProcess.disableAllTags()
        
        with dpg.window(tag="openLPT", show=False, width=self.subwindow_width, height=self.subwindow_height, label='OpenLPT'):
            showOpenLPT(self.callbacks)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Main", True)
        dpg.start_dearpygui()
        dpg.destroy_context()
    
    def selectCalibMethod(self, sender=None, app_data=None):
        method = dpg.get_value('calibMethod')
        if method == 'Calibration Plate':
            dpg.configure_item('calibPlate', show=True)
        elif method == 'Easy Wand':
            dpg.configure_item('easyWand', show=True)
    
    def selectCamModel(self, sender=None, app_data=None):
        model = dpg.get_value('camModel')
        if model == 'Pinhole':
            dpg.configure_item('opcvCalib', show=True)
        elif model == 'Polynomial':
            dpg.configure_item('polyCalib', show=True)
    
    """
        Responsible for invoking individual tabs.
    """
    def showCalibPlateTabBar(self):
        with dpg.tab_bar():
            self.showCalibPlateTabs()

    def showCalibPlateTabs(self):
        dpg.add_texture_registry(show=False, tag='textureRegistry')
        with dpg.tab(label='1. Importing'):
            showProcessing(self.callbacks)
        with dpg.tab(label='2. Filtering (Optional)'):
            showFiltering(self.callbacks)
        with dpg.tab(label='3. Thresholding'):
            showThresholding(self.callbacks)
        with dpg.tab(label='4. Extracting'):
            showContourExtraction(self.callbacks)
        self.callbacks.imageProcessing.disableAllTags()

    def createSaveImageDialog(self):
        with dpg.window(label="Export Image as File", modal=False, show=False, tag="exportImageAsFile", no_title_bar=False, min_size=[600,255]):
            dpg.add_text("Name your file")
            dpg.add_input_text(tag='imageNameExportAsFile')
            dpg.add_separator()
            dpg.add_text("You MUST enter a File Name to select a directory")
            dpg.add_button(width=-1, label='Select the directory', callback=self.callbacks.imageProcessing.exportImageDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, width=0.7*self.subwindow_width, height=0.7*self.subwindow_height,  min_size=[400,300], show=False, tag='exportImageDirectorySelector', id="exportImageDirectorySelector", callback=lambda sender, app_data: self.callbacks.imageProcessing.exportImageSelectDirectory(sender, app_data))
            dpg.add_separator()
            dpg.add_text('File Name: ', tag='exportImageFileName')
            dpg.add_text('Complete Path Name: ', tag='exportImageFilePath')
            with dpg.group(horizontal=True):
                dpg.add_button(label='Save', width=-1, callback=self.callbacks.imageProcessing.exportImageAsFile)
                dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportImageAsFile', show=False))
            dpg.add_text("Missing file name or directory.", tag="exportImageError", show=False)