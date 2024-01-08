import dearpygui.dearpygui as dpg

def showOpenCVCalib(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300,horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_opencvCamCalib', callback=callbacks.OpencvCalib.openCamcalibFile, cancel_callback=callbacks.OpencvCalib.cancelCamcalibImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            dpg.add_text('OpenCV Camera Calibration')
            dpg.add_separator()
            
            dpg.add_text('1. Calibrate Camera Parameters')
            dpg.add_text('(Distortion Coeffictions & Camera Matrix)')
            dpg.add_button(tag='import_OpencvCalibCam', label='Import Files', callback=lambda: dpg.show_item("file_dialog_opencvCamCalib"))
            
            with dpg.group(horizontal=True):
                dpg.add_text('Image Width')
                dpg.add_input_int(tag='inputOpencvCamWidth', default_value=1280)
            with dpg.group(horizontal=True):
                dpg.add_text('Image Height')
                dpg.add_input_int(tag='inputOpencvCamHeight', default_value=800)
                
            dpg.add_button(tag='calibrate_OpencvCalibCam', label='Run Calibration', callback=callbacks.OpencvCalib.calibrateCamera)
            
            dpg.add_separator()
            
            with dpg.group(tag='OpenCV Calibrate Pose Parameters',show=False):
                dpg.add_text('2. Calibrate Pose Parameters')
                
                with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_opencvPoseCalib', callback=callbacks.OpencvCalib.openPoseCalibFile, cancel_callback=callbacks.OpencvCalib.cancelPoseCalibImportFile):
                    dpg.add_file_extension("", color=(150, 255, 150, 255))
                    dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                    dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
                dpg.add_button(tag='import_OpencvCalibPose', label='Import Files', callback=lambda: dpg.show_item("file_dialog_opencvPoseCalib"))
                dpg.add_text('Select an optimization method')
                dpg.add_listbox(tag='opencvPoseOptMethod', items=['SOLVEPNP_ITERATIVE', 'SOLVEPNP_EPNP', 'SOLVEPNP_IPPE','SOLVEPNP_SQPNP'])
                dpg.add_button(tag='calibrate_OpencvCalibPose', label='Run Calibration', callback=callbacks.OpencvCalib.calibratePose)
            
            dpg.add_separator()
            
            dpg.add_button(tag="buttonExportOpencvCalib",label='Export Camera Parameters', callback=lambda: dpg.show_item("exportOpencvCalib"), show=False)
                    
                        
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportOpencvCalib", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputOpencvCalibFileText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback=lambda: dpg.show_item("folderExportOpencvCalib"))
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='folderExportOpencvCalib', id="folderExportOpencvCalib", callback=callbacks.OpencvCalib.selectFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportOpencvFileName')
                dpg.add_text('Complete Path Name: ', tag='exportOpencvPathName')

                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.OpencvCalib.exportOpencvCalib)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportOpencvCalib', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportOpencvCalibError", show=False)
            
            with dpg.window(label="ERROR! Select a data file!", modal=True, show=False, tag="noOpencvPath", no_title_bar=False):
                dpg.add_text("ERROR: This is not a valid path.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noOpencvPath", show=False))
            dpg.add_separator()
        
        with dpg.child_window(tag='opencvOutputParent'):
            
            dpg.add_text('OpenCV Outputs')
            
            dpg.add_text('Camera Calibraion Files:')
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
            resizable=True, no_host_extendX=False, hideable=True,
            borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
            borders_outerH=True, tag='opencvCamcalibFileTable'):
                dpg.add_table_column(label='File Name', width_fixed=True)
                dpg.add_table_column(label='File Path', width_fixed=True)
            
            with dpg.group(show=False, tag='opencvCalibGroup'):
                dpg.add_text('Camera Calibration Error:', tag='opencvCamcalibErr') 
                dpg.add_text('Camera Matrix:')
                dpg.add_text('', tag='opencvCamMat')
                dpg.add_text('Distortion Coefficients: (k1,k2,p1,p2,k3)')
                dpg.add_text('', tag='opencvDistCoeff')
                
                dpg.add_separator()
                dpg.add_text('Pose Calibration Files:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                    resizable=True, no_host_extendX=False, hideable=True,
                    borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                    borders_outerH=True, tag='opencvPosecalibFileTable'):
                        dpg.add_table_column(label='File Name', width_fixed=True)
                        dpg.add_table_column(label='File Path', width_fixed=True)
                
                dpg.add_text('Pose Calibraion Error:', tag='opencvPosecalibErr')
                dpg.add_text('Rotation Matrix:')
                dpg.add_text('', tag='opencvRotMat')
                dpg.add_text('Rotation Vector:')
                dpg.add_text('', tag='opencvRotVec')
                dpg.add_text('Translation Vector:')
                dpg.add_text('', tag='opencvTransVec')
                

            
