import dearpygui.dearpygui as dpg

def showVSC(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300,horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_vscCam', callback=callbacks.Vsc.openCamFile, cancel_callback=callbacks.Vsc.cancelCamImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, tag='file_dialog_vscTracks', callback=callbacks.Vsc.openTracksFile, cancel_callback=callbacks.Vsc.cancelTracksImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            with dpg.file_dialog(directory_selector=False, file_count=20, min_size=[400,300], show=False, tag='file_dialog_vscImg', callback=callbacks.Vsc.openImgFile, cancel_callback=callbacks.Vsc.cancelImgImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            dpg.add_text('1. Import Camera Files')
            dpg.add_button(tag='import_VscCam', label='Import Camera Files', callback=lambda: dpg.show_item("file_dialog_vscCam"))
            dpg.add_separator()
            
            dpg.add_text('2. Import Image Files')
            dpg.add_button(tag='import_VscImg', label='Import Image Files', callback=lambda: dpg.show_item("file_dialog_vscImg"))
            dpg.add_separator()
            
            dpg.add_text('3. Import Tracks File')
            dpg.add_button(tag='import_VscTracks', label='Import Tracks File', callback=lambda: dpg.show_item("file_dialog_vscTracks"))
            dpg.add_separator()
            
            
            dpg.add_text('4. Volume Self Calibration')
            dpg.add_text('Tracks fitting threshold: (view volume size / 1000)')
            dpg.add_input_float(tag='inputVscGoodTracksThreshold', default_value=0.04)
            dpg.add_text('Number of particles:')
            dpg.add_input_int(tag='inputVscNumParticles', default_value=4000)
            dpg.add_text('Particle Radius: [pix]')
            dpg.add_input_int(tag='inputVscParticleRadius', default_value=4)
            
            dpg.add_button(label='Run VSC', callback=callbacks.Vsc.runVsc)
            dpg.add_separator()
                   
                   
                   
            ############################     
            dpg.add_button(tag="buttonExportVsc",label='Export VSC Outputs', callback=lambda: dpg.show_item("exportVsc"), show=False)     
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportVsc", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your file")
                dpg.add_input_text(tag='inputVscFileText')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback=lambda: dpg.show_item("folderExportVsc"))
                dpg.add_file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='folderExportVsc', id="folderExportVsc", callback=callbacks.Vsc.selectFolder)
                dpg.add_separator()
                dpg.add_text('File Default Name: ', tag='exportVscFileName')
                dpg.add_text('Complete Path Name: ', tag='exportVscPathName')

                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.Vsc.exportVsc)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportVsc', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportVscError", show=False)
            
            with dpg.window(label="ERROR! Select a data file!", modal=True, show=False, tag="noVscPath", no_title_bar=False):
                dpg.add_text("ERROR: This is not a valid path.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noVscPath", show=False))
            
            with dpg.window(label="ERROR! Import more camera files!", modal=True, show=False, tag="noVscCam", no_title_bar=False):
                dpg.add_text("ERROR: You must import at least 2 cameras.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noVscCam", show=False))
        
        with dpg.child_window(tag='vscOutputParent'):
            
            dpg.add_text('VSC Outputs')
            dpg.add_separator()
            
            with dpg.group(show=False, tag='vscCamOutputParent'):
                dpg.add_text('Camera File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscCamFileTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='File Path', width_fixed=True)
                
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscCamParamTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='CamMat', width_fixed=True)
                    dpg.add_table_column(label='DistCoeff', width_fixed=True)
                    dpg.add_table_column(label='RotMat', width_fixed=True)
                    dpg.add_table_column(label='TransVec', width_fixed=True)
                    dpg.add_table_column(label='CamCalib Error', width_fixed=True) 
                    dpg.add_table_column(label='PoseCalib Error', width_fixed=True)
            
            dpg.add_separator()
            with dpg.group(show=False, tag='vscImgOutputParent'):
                dpg.add_text('Image File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscImgFileTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='File Path', width_fixed=True)
            
            dpg.add_separator()
            with dpg.group(show=False, tag='vscTracksOutputParent'):
                dpg.add_text('Tracks File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscTracksFileTable'):
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='File Path', width_fixed=True)
                    
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscTracksDataTable'):
                    dpg.add_table_column(label='TrackID', width_fixed=True)
                    dpg.add_table_column(label='FrameID', width_fixed=True)
                    dpg.add_table_column(label='WorldX', width_fixed=True)
                    dpg.add_table_column(label='WorldY', width_fixed=True)
                    dpg.add_table_column(label='WorldZ', width_fixed=True)
                
            
                    

            
            
            