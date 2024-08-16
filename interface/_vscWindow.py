import dearpygui.dearpygui as dpg

def showVSC(callbacks):
    subwindow_width = dpg.get_item_width('vsc')
    subwindow_height = dpg.get_item_height('vsc')
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width,horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, file_count=100, tag='file_dialog_vscCam', callback=callbacks.vsc.openCamFile, cancel_callback=callbacks.vsc.cancelCamImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, file_count=100, tag='file_dialog_vscTracks', callback=callbacks.vsc.openTracksFile, cancel_callback=callbacks.vsc.cancelTracksImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, file_count=100, min_size=[400,300], show=False, tag='file_dialog_vscImg', callback=callbacks.vsc.openImgFile, cancel_callback=callbacks.vsc.cancelImgImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            
            dpg.add_text('1. Import Camera Files')
            dpg.add_button(tag='import_VscCam', label='Import Camera Files', callback=lambda: dpg.show_item("file_dialog_vscCam"))
            dpg.add_text('Status: --', tag='vscCamStatus')
            dpg.add_separator()
            
            dpg.add_text('2. Import Image Files')
            dpg.add_button(tag='import_VscImg', label='Import Image Files', callback=lambda: dpg.show_item("file_dialog_vscImg"))
            dpg.add_text('Status: --', tag='vscImgStatus')
            dpg.add_separator()
            
            dpg.add_text('3. Import Tracks File')
            dpg.add_button(tag='import_VscTracks', label='Import Tracks File', callback=lambda: dpg.show_item("file_dialog_vscTracks"))
            dpg.add_text('Status: --', tag='vscTracksStatus')
            dpg.add_separator()
            

            dpg.add_text('4. Volume Self Calibration')
            dpg.add_text('Tracks fitting threshold: (view volume size / 1000)')
            dpg.add_input_float(tag='inputVscGoodTracksThreshold', default_value=0.04)
            dpg.add_text('Number of particles:')
            dpg.add_input_int(tag='inputVscNumParticles', default_value=4000)
            dpg.add_text('Particle Radius: [pix]')
            dpg.add_input_int(tag='inputVscParticleRadius', default_value=4)
            dpg.add_text('Triangulation Threshold: [physical unit]')
            dpg.add_input_float(tag='inputVscTriangulationThreshold', default_value=2.5)
            dpg.add_text('Select fix cameras')
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscCamFixTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='Fix', width_fixed=True)
            dpg.add_text('Input max iterations:')
            dpg.add_input_int(tag='inputVscMaxIterations', default_value=20)
            # dpg.add_text('Input number of parallel threads:')
            # dpg.add_input_int(tag='inputVscNumThreads', default_value=10)
            dpg.add_text('Input convergence tolerance:')
            dpg.add_input_float(tag='inputVscTolerance', default_value=1e-6, format='%.3e')
            dpg.add_button(label='Run VSC', callback=callbacks.vsc.runVsc)
            dpg.add_text('Status: --', tag='vscStatus')
            dpg.add_text('Selecting good tracks: --', tag='vscStatus_goodTracks')
            dpg.add_text('Selecting particles: --', tag='vscStatus_particles')
            dpg.add_text('Extracting particle info: --', tag='vscStatus_particleInfo')
            dpg.add_text('Optimizing: --', tag='vscStatus_optimize')
            dpg.add_separator()
                   
            with dpg.group(tag='vscExportParent', show=False):  
                dpg.add_text('5. Export VSC Outputs')  
                dpg.add_button(tag="buttonExportVsc",label='Export VSC Outputs', callback=lambda: dpg.show_item("exportVsc"), show=True)   
                  
            with dpg.window(label="Save Files", modal=False, show=False, tag="exportVsc", no_title_bar=False, min_size=[600,255]):
                dpg.add_text("Name your camera file prefix")
                dpg.add_input_text(tag='inputVscFilePrefix', default_value='VSC_')
                dpg.add_separator()
                dpg.add_text("You MUST enter a File Name to select a directory")
                dpg.add_button(label='Select the directory', width=-1, callback=lambda: dpg.show_item("folderExportVsc"))
                dpg.add_file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='folderExportVsc', id="folderExportVsc", callback=callbacks.vsc.selectFolder)
                dpg.add_separator()
                dpg.add_text('Folder: ', tag='exportVscFolderName')
                dpg.add_text('Prefix: ', tag='exportVscPrefixName')

                with dpg.group(horizontal=True):
                    dpg.add_button(label='Save', width=-1, callback=callbacks.vsc.exportVsc)
                    dpg.add_button(label='Cancel', width=-1, callback=lambda: dpg.configure_item('exportVsc', show=False))
                dpg.add_text("Missing file name or directory.", tag="exportVscError", show=False)
            
            with dpg.window(label="ERROR! Import correct files!", modal=True, show=False, tag="noVscPath", no_title_bar=False):
                dpg.add_text("", tag="noVscPathText")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noVscPath", show=False))
            
            with dpg.window(label="ERROR! Import more camera files!", modal=True, show=False, tag="noVscCam", no_title_bar=False):
                dpg.add_text("ERROR: You must import at least 2 cameras.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noVscCam", show=False))
        
        with dpg.child_window(tag='vscOutputParent', horizontal_scrollbar=True):

            dpg.add_text('VSC Outputs')
            dpg.add_separator()
            
            
            # add plots 
            dpg.add_text('Plot Buttons')
            with dpg.group(tag='vscPlotButtonParent', horizontal=True):
                dpg.add_button(tag='vscPlotButton_importedTracks', label='Imported Tracks', callback=callbacks.vsc.plotImportedTracks, show=False)
                dpg.add_button(tag='vscPlotButton_loss', label='Loss', callback=callbacks.vsc.plotLoss, show=False)
                dpg.add_button(tag='vscPlotButton_selectedParticles', label='Selected Particles', callback=callbacks.vsc.plotSelectedParticles, show=False)
                dpg.add_button(tag='vscPlotButton_errhist', label='Error Histogram', callback=callbacks.vsc.plotErrorHistogram, show=False)
            dpg.add_separator()
                
                
            with dpg.plot(tag="vscPlotParent", label='VSC Plot', height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="vscPlot_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="vscPlot_y_axis")
            
            with dpg.group(show=False, tag='vscCamOutputParent'):
                dpg.add_text('Camera File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='vscCamFileTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='File Path', width_fixed=True)
                        
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
                dpg.add_separator()
                   
            dpg.add_text('Export path: --', tag='vscExportFolder', show=False)
                
            
                    

            
            
            