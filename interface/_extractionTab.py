import dearpygui.dearpygui as dpg

def showContourExtraction(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300):
            dpg.add_text('OpenCV2 Find Contour')
            dpg.add_text('Approximation Mode')
            dpg.add_listbox(tag='approximationModeListbox', items=['None', 'Simple', 'TC89_L1', 'TC89_KCOS'], width=-1)
            dpg.add_text('Region Size Range (Diameter)')
            dpg.add_input_float(tag='regionSizeMin', label="Min", default_value=3)
            dpg.add_input_float(tag='regionSizeMax', label="Max", default_value=50)
            with dpg.window(label="ERROR! Max size cannot be smaller than min size!", modal=True, show=False, tag="errRange", no_title_bar=False):
                dpg.add_text("ERROR: You must reset the size values.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errRange", show=False))
            
            dpg.add_text('Contour Thickness (For drawing)')
            dpg.add_slider_int(tag='contourThicknessSlider', default_value=3, min_value=1, max_value=100,  width=-1)
            dpg.add_button(tag='extractContourButton', width=-1, label='Apply Method', callback=lambda sender, app_data: callbacks.contourExtraction.extractContour(sender, app_data))
            with dpg.window(label="ERROR! The image must be in a binary color scheme!", modal=True, show=False, tag="nonBinary", no_title_bar=False):
                dpg.add_text("ERROR: You must select a binarization filter on the Thresholding Tab.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("nonBinary", show=False))
            
            dpg.add_separator()
            dpg.add_separator()
            
            with dpg.group(tag='Extract Plane Coordinate',show=False):
                dpg.add_text('Extract Plane Coordinates')

                dpg.add_text('Enter min and max index for left axis')
                dpg.add_input_int(tag='Axis1',label='Fix x', default_value=-9)
                dpg.add_input_int(tag='Axis1_Min',label='Min y', default_value=-7)
                dpg.add_input_int(tag='Axis1_Max',label='Max y', default_value=7)
                dpg.add_button(tag='selectAxis1',label='Select min and max points',callback=callbacks.contourExtraction.selectAxis)
                dpg.add_text('Point 1: --',tag='selectAxis1Pt1')
                dpg.add_text('Point 2: --',tag='selectAxis1Pt2')
                
                dpg.add_text('Enter min and max index for bottom axis')
                dpg.add_input_int(tag='Axis2',label='Fix y', default_value=-7)
                dpg.add_input_int(tag='Axis2_Min',label='Min x', default_value=-9)
                dpg.add_input_int(tag='Axis2_Max',label='Max x', default_value=9)
                dpg.add_button(tag='selectAxis2',label='Select min and max points',callback=callbacks.contourExtraction.selectAxis)
                dpg.add_text('Point 1: --',tag='selectAxis2Pt1')
                dpg.add_text('Point 2: --',tag='selectAxis2Pt2')

                dpg.add_button(tag='extractPtOnPlane', label='Extract points on the plane', callback=callbacks.contourExtraction.extractPoints)
                
            dpg.add_separator()
            dpg.add_separator()
            with dpg.group(tag='Extract World Coordinate',show=False):  
                dpg.add_text('Extract World Coordinates')
                dpg.add_text('Enter depth coordinate for the plane:')
                dpg.add_input_float(tag='Axis3',label='In physical unit',default_value=0.5)
                dpg.add_text('Enter distance between calibration dots:')
                dpg.add_input_float(tag='dist',label='Distance')
                dpg.add_text('The world axis for plane axis x is:')
                dpg.add_listbox(tag='imgAxisX', items=['x', 'y', 'z'], width=-1, default_value='x')
                dpg.add_text('The world axis for plane axis y is:')
                dpg.add_listbox(tag='imgAxisY', items=['x', 'y', 'z'], width=-1, default_value='y')
                
                dpg.add_button(tag='extractWorldCoordinate', label='Extract world coordinate', callback=callbacks.contourExtraction.extractWorldCoordinate)
                
            
            with dpg.window(label="ERROR! The previous axis selection is not finished!", modal=True, show=False, tag="errAxis", no_title_bar=False):
                dpg.add_text("ERROR: You must finish selecting the previous axis.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errAxis", show=False))
                
            with dpg.window(label="ERROR! The previous xmin is different from the current value!", modal=True, show=False, tag="errXMin", no_title_bar=False):
                dpg.add_text("ERROR: You must finish reset xmin index.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errXMin", show=False))
                
            with dpg.window(label="ERROR! The previous ymin is different from the current value!", modal=True, show=False, tag="errYMin", no_title_bar=False):
                dpg.add_text("ERROR: You must finish reset ymin index.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errYMin", show=False))
                
            with dpg.window(label="ERROR! The world axis for x and y must be different!", modal=True, show=False, tag="errImgAxis", no_title_bar=False):
                dpg.add_text("ERROR: You must finish reselect world axis.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errImgAxis", show=False))
            
            
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportCenters", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputCenterNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback= callbacks.contourExtraction.openCentersDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directoryFolderexportCenters', id="directoryFolderexportCenters", callback=callbacks.contourExtraction.selectCentersFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='centerFileName')
                dpg.add_text('Complete Path Name: ', tag='centerPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.contourExtraction.exportCentersToFile)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportCenters', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportCentersError", show=False)
                    
                pass
            
            with dpg.window(label="Save File", modal=False, show=False, tag="exportContourWindow", no_title_bar=False, min_size=[600,280]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputContourNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback= callbacks.contourExtraction.openDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directorySelectorFileDialog', id="directorySelectorFileDialog", callback=callbacks.contourExtraction.selectFolder)
                dpg.add_separator()
                dpg.add_text('Contour ID: ', tag='contourIdExportText')
                dpg.add_text('File Name: ', tag='exportFileName')
                dpg.add_text('Complete Path Name: ', tag='exportPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=lambda: callbacks.contourExtraction.exportIndividualContourToFile())
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportContourWindow', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportContourError", show=False)

            with dpg.window(label="Save Files", modal=False, show=False, tag="exportSelectedContourWindow", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name the prefix of your file")
                dpg.add_input_text(tag='inputSelectedContourNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a prefix to the File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback= callbacks.contourExtraction.openExportSelectedDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='directoryFolderExportSelected', id="directoryFolderExportSelected", callback=callbacks.contourExtraction.selectExportAllFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportSelectedFileName')
                dpg.add_text('Complete Path Name: ', tag='exportSelectedPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.contourExtraction.exportSelectedContourToFile)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportSelectedContourWindow', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportSelectedContourError", show=False)
                    
                pass
        
        with dpg.child_window(tag='ContourExtractionParent'):
            with dpg.plot(tag="ContourExtractionPlotParent", label="ContourExtraction", height=-1 - 50, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="ContourExtraction_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="ContourExtraction_y_axis")
                
                with dpg.handler_registry(tag="selectAxis handler"):
                    dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left,
                                                callback=callbacks.contourExtraction.createAxis)
                