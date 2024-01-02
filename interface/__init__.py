import dearpygui.dearpygui as dpg
from ._extractionTab import showContourExtraction
from ._filteringTab import showFiltering
from ._processingTab import showProcessing
from ._thresholdingTab import showThresholding
from ._theme import applyTheme

class Interface:

    def __init__(self, callbacks) -> None:
        self.callbacks = callbacks
        self.show()
        pass

    def show(self):
        dpg.create_context()
        dpg.create_viewport(title='OpenLPT - An Open Source Software for Lagragian Particle Tracking', width=900, height=600, min_height=600, min_width=900)
        
        with dpg.window(tag="Main"):
            applyTheme()
            dpg.add_text('1. Select a calibration method')
            dpg.add_listbox(tag='CalibMethod', items=['Calibration Plate', 'Easy Wand'])
            dpg.add_button(label='Apply Method', callback=self.selectCalibMethod)
            
            dpg.add_text('2. Calibrate each camera')
            dpg.add_button(label='Start calibration', callback=self.calibration)
            
            dpg.add_text('3. Set OpenLPT parameters')
            
            
            dpg.add_text('4. Run OpenLPT')
            
            
            
        with dpg.window(tag="CalibPlate", show=False):
            applyTheme()
            self.showCalibPlateTabBar()
            self.createSaveImageDialog()

        with dpg.window(tag="EasyWand", show=False):
            applyTheme()
            dpg.add_text('Easy Wand')
            
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Main", True)
        dpg.start_dearpygui()
        dpg.destroy_context()
        pass
    
    def selectCalibMethod(self, sender=None, app_data=None):
        method = dpg.get_value('CalibMethod')
        if method == 'Calibration Plate':
            dpg.configure_item('CalibPlate', show=True)
        else:
            dpg.configure_item('EasyWand', show=True)
        pass
    
    def calibration(self, sender=None, app_data=None):
        
        pass
    
    """
        Responsible for invoking individual tabs.
    """
    def showCalibPlateTabBar(self):
        with dpg.tab_bar():
            self.showCalibPlateTabs()
        pass

    def showCalibPlateTabs(self):
        dpg.add_texture_registry(show=False, tag='textureRegistry')
        with dpg.tab(label='Processing'):
            showProcessing(self.callbacks)
            pass
        with dpg.tab(label='Filtering'):
            showFiltering(self.callbacks)
            pass
        with dpg.tab(label='Thresholding'):
            showThresholding(self.callbacks)
            pass
        with dpg.tab(label='Contour Extraction'):
            showContourExtraction(self.callbacks)
            pass
        self.callbacks.imageProcessing.disableAllTags()
        pass

    def createSaveImageDialog(self):
        with dpg.window(label="Export Image as File", modal=False, show=False, tag="exportImageAsFile", no_title_bar=False, min_size=[600,255]):
            dpg.add_text("Name your file")
            dpg.add_input_text(tag='imageNameExportAsFile')
            dpg.add_separator()
            dpg.add_text("You MUST enter a File Name to select a directory")
            dpg.add_button(width=-1, label='Select the directory', callback=self.callbacks.imageProcessing.exportImageDirectorySelector)
            dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='exportImageDirectorySelector', id="exportImageDirectorySelector", callback=lambda sender, app_data: self.callbacks.imageProcessing.exportImageSelectDirectory(sender, app_data))
            dpg.add_separator()
            dpg.add_text('File Name: ', tag='exportImageFileName')
            dpg.add_text('Complete Path Name: ', tag='exportImageFilePath')
            with dpg.group(horizontal=True):
                dpg.add_button(label='Save', width=-1, callback=self.callbacks.imageProcessing.exportImageAsFile)
                dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportImageAsFile', show=False))
            dpg.add_text("Missing file name or directory.", tag="exportImageError", show=False)