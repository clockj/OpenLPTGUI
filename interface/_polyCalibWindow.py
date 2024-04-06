import dearpygui.dearpygui as dpg

def showPolyCalib(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300,horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_polyCalib', callback=callbacks.polyCalib.openFile, cancel_callback=callbacks.polyCalib.cancelImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            dpg.add_text('Polynomial Camera Calibration')
            dpg.add_separator()
            
            dpg.add_button(tag='import_polyCalib', label='Import Files', callback=lambda: dpg.show_item("file_dialog_polyCalib"))
            
            with dpg.group(horizontal=True):
                dpg.add_text('Image Width')
                dpg.add_input_int(tag='inputPolyCamWidth', default_value=1280)
            with dpg.group(horizontal=True):
                dpg.add_text('Image Height')
                dpg.add_input_int(tag='inputPolyCamHeight', default_value=800)
            
            with dpg.group(horizontal=True):
                dpg.add_text('Order of polynomial')
                dpg.add_input_int(tag='inputPolyOrder', default_value=3)
            
            dpg.add_button(tag='calibrate_polyCalib', label='Run Calibration', callback=callbacks.polyCalib.calibrateCamera)
           
            dpg.add_separator()
            
            with dpg.group(tag='polyRefPlane', show=False):
                dpg.add_text('Select Reference Plane:')
                dpg.add_text('(for line of sight calculation)')
                dpg.add_listbox(items=['REF_X','REF_Y','REF_Z'], width=-1, default_value='REF_Z', tag='selectXYZ')
                
                with dpg.group(horizontal=True):
                    dpg.add_text('Loaction 1: ')
                    dpg.add_input_float(tag='inputPolyRefPlane_1', default_value=0.0)
                with dpg.group(horizontal=True):
                    dpg.add_text('Loaction 2: ')
                    dpg.add_input_float(tag='inputPolyRefPlane_2', default_value=5)
            
            dpg.add_separator()
            dpg.add_button(tag="buttonExportPolyCalib",label='Export Coefficients', callback=lambda: dpg.show_item("exportPolyCalib"), show=False)
            
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportPolyCalib", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputPolyCalibFileText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                
                dpg.add_button(label='Select the directory', width=-1, callback=lambda: dpg.show_item("folderExportPolyCalib"))

                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='folderExportPolyCalib', id="folderExportPolyCalib", callback=callbacks.polyCalib.selectFolder)
                
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportPolyFileName')
                dpg.add_text('Complete Path Name: ', tag='exportPolyPathName')

                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.polyCalib.exportCalib)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportPolyCalib', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportPolyCalibError", show=False)
            
            with dpg.window(label="ERROR! Select a data file!", modal=True, show=False, tag="noPolyPath", no_title_bar=False):
                dpg.add_text("ERROR: This is not a valid path.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noPolyPath", show=False))
            dpg.add_separator()
        
        with dpg.child_window(tag='polyOutputParent'):
            
            dpg.add_text('Polynomial Calibration Outputs')
            
            dpg.add_text('Input Files:')
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True, scrollY=True, height=200,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, tag='polyCalibFileTable'):
                dpg.add_table_column(label='File Name', width_fixed=True)
                dpg.add_table_column(label='File Path', width_fixed=True)
            
            with dpg.group(show=False, tag='polyCalibGroup'):
                dpg.add_text('Calibration Error:', tag='polyCalibErr') 
                
                dpg.add_text('Calibration Results: (coeff,x_order,y_order,z_order)')
                dpg.add_text('', tag='polyCalibResults')
                
                

            
