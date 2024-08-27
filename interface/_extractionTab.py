import dearpygui.dearpygui as dpg

def showContourExtraction(callbacks):
    subwindow_width = dpg.get_item_width('calibPlate')
    subwindow_height = dpg.get_item_height('calibPlate')    
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width,horizontal_scrollbar=True):
            dpg.add_text('Find Contour')
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_text('Diameter range of calibration dots')
                dpg.add_button(label='?', callback=callbacks.contourExtraction.helpDiaRange)
            dpg.add_input_float(tag='regionSizeMin', label="Min", default_value=3, step=-1)
            dpg.add_input_float(tag='regionSizeMax', label="Max", default_value=50, step=-1)
            
            dpg.add_button(tag='extractContourButton', width=-1, label='Apply Method', callback=lambda sender, app_data: callbacks.contourExtraction.extractContour(sender, app_data))
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label='Remove Wrong Points', tag='removeWrongPts', default_value=False)
                dpg.add_button(label='?', callback=callbacks.contourExtraction.helpRemovePts)
            dpg.add_button(label='Remove', callback=callbacks.contourExtraction.removePts)
            dpg.add_separator()
            
            with dpg.group(tag='Extract Plane Coordinate',show=False):
                dpg.add_text('Extract Plane Coordinates')
                
                with dpg.group(horizontal=True):
                    dpg.add_text('Enter index for each axis')
                    dpg.add_button(label='?', callback=callbacks.contourExtraction.helpAxisIndex)
                dpg.add_input_int(tag='AxisID_Bottom',label='Bottom ID', default_value=-7, step=-1)
                dpg.add_input_int(tag='AxisID_Top',label='Top ID', default_value=7, step=-1)
                dpg.add_input_int(tag='AxisID_Left',label='Left ID', default_value=-9, step=-1)
                dpg.add_input_int(tag='AxisID_Right',label='Right ID', default_value=9, step=-1)
                # dpg.add_input_int(tag='AxisID_Bottom',label='Bottom ID', default_value=-6, step=-1)
                # dpg.add_input_int(tag='AxisID_Top',label='Top ID', default_value=7, step=-1)
                # dpg.add_input_int(tag='AxisID_Left',label='Left ID', default_value=-13, step=-1)
                # dpg.add_input_int(tag='AxisID_Right',label='Right ID', default_value=10, step=-1)
                
                with dpg.group(horizontal=True):
                    dpg.add_text('Select the four corners')
                    dpg.add_button(label='?', callback=callbacks.contourExtraction.helpSelectCorners)
                dpg.add_text('Bottom Left -> Top Left -> Top Right -> Bottom Right')
                dpg.add_button(tag='selectCorners',label='Select corners',callback=callbacks.contourExtraction.selectCorners)
                dpg.add_text('BL: --',tag='selectCorners1')
                dpg.add_text('TL: --',tag='selectCorners2')
                dpg.add_text('TR: --',tag='selectCorners3')
                dpg.add_text('BR: --',tag='selectCorners4') 
                dpg.add_separator()
                
                with dpg.group(horizontal=True):
                    dpg.add_text('Input threshold to find axis points')
                    dpg.add_button(label='?', callback=callbacks.contourExtraction.helpAxisThreshold)
                dpg.add_input_float(tag='axisThreshold', default_value=10, step=-1)   

                dpg.add_button(tag='extractPtOnPlane', label='Extract points on the plane', callback=callbacks.contourExtraction.extractPoints)
                dpg.add_separator()
                
            with dpg.group(tag='Extract World Coordinate',show=False):  
                dpg.add_text('Extract World Coordinates')
                dpg.add_text('Enter depth coordinate for the plane:')
                dpg.add_input_float(tag='Axis3',label='In physical unit', step=-1)
                dpg.add_text('Enter distance between calibration dots:')
                dpg.add_input_float(tag='dist',label='in physical unit',default_value=0.5, step=-1)
                dpg.add_text('The world axis for plane axis x is:')
                dpg.add_listbox(tag='mouseAxisX', items=['x', 'y', 'z'], width=-1, default_value='x')
                dpg.add_text('The world axis for plane axis y is:')
                dpg.add_listbox(tag='mouseAxisY', items=['x', 'y', 'z'], width=-1, default_value='y')
                
                dpg.add_button(tag='extractWorldCoordinate', label='Extract world coordinate', callback=callbacks.contourExtraction.extractWorldCoordinate)
              
            
            # error window
            with dpg.window(label="ERROR! The image must be binirized!", modal=True, show=False, tag="nonBinary", no_title_bar=False):
                dpg.add_text("ERROR: You must select a binarization method in the Thresholding Tab.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("nonBinary", show=False))
            
            with dpg.window(label="ERROR! Max size cannot be smaller than min size!", modal=True, show=False, tag="errRange", no_title_bar=False):
                dpg.add_text("ERROR: You must reset the size values.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errRange", show=False))
            
            with dpg.window(label="ERROR! The previous corner selection is not finished!", modal=True, show=False, tag="errCorners", no_title_bar=False):
                dpg.add_text("ERROR: You must finish selecting the corners.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errCorners", show=False))
            
            with dpg.window(label="ERROR! The axis point extraction is not as expected!", modal=True, show=False, tag="errAxisPoints", no_title_bar=False):
                dpg.add_text("ERROR: You must check the points near the axis.", tag="errAxisPointsText")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errAxisPoints", show=False))
            
            with dpg.window(label="ERROR! The world axis for x and y must be different!", modal=True, show=False, tag="errMouseAxis", no_title_bar=False):
                dpg.add_text("ERROR: You must reselect world axis.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("errMouseAxis", show=False))
            
            
            # help window shown in the middle
            with dpg.window(label="Help!", modal=True, show=False, tag="extraTab_help", no_title_bar=False, width=0.3*subwindow_width, height=0.3*subwindow_height, pos=[0.35*subwindow_width,0.35*subwindow_height]):
                dpg.add_text("", tag="extraTab_helpText", wrap=0.295*subwindow_width)
                dpg.add_text("")
                dpg.add_separator()
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("extraTab_help", show=False))
            
            
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportCenters", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputCenterNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback= callbacks.contourExtraction.openCentersDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='directoryFolderexportCenters', id="directoryFolderexportCenters", callback=callbacks.contourExtraction.selectCentersFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='centerFileName')
                dpg.add_text('Complete Path Name: ', tag='centerPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.contourExtraction.exportCentersToFile)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportCenters', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportCentersError", show=False)
                    
            with dpg.window(label="Save File", modal=False, show=False, tag="exportContourWindow", no_title_bar=False, min_size=[600,280]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputContourNameText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback= callbacks.contourExtraction.openDirectorySelector)
                dpg.add_file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='directorySelectorFileDialog', id="directorySelectorFileDialog", callback=callbacks.contourExtraction.selectFolder)
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
                dpg.add_file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='directoryFolderExportSelected', id="directoryFolderExportSelected", callback=callbacks.contourExtraction.selectExportAllFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportSelectedFileName')
                dpg.add_text('Complete Path Name: ', tag='exportSelectedPathName')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.contourExtraction.exportSelectedContourToFile)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportSelectedContourWindow', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportSelectedContourError", show=False)
        
        with dpg.child_window(tag='ContourExtractionParent'):
            with dpg.plot(tag="ContourExtractionPlotParent", label="ContourExtraction", height=-1, width=-1, query=True, query_button=dpg.mvMouseButton_Left, pan_button=dpg.mvMouseButton_Middle):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="ContourExtraction_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="ContourExtraction_y_axis", invert=True)
                
                with dpg.handler_registry(tag="selectAxis handler"):
                    dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=callbacks.contourExtraction.createAxis)
                