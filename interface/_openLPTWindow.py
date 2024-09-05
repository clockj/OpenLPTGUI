import dearpygui.dearpygui as dpg

def showOpenLPT(callbacks):
    with dpg.tab_bar():
        with dpg.tab(label='1. Generate Configuration File (Optional)'):
            showConfig(callbacks)
        with dpg.tab(label='2. Run OpenLPT'):
            showRun(callbacks)
        with dpg.tab(label='3. Post-Processing (Optional)'):
            showPostProcessing(callbacks)

def showConfig(callbacks):
    subwindow_width = dpg.get_item_width('imgProcess')
    subwindow_height = dpg.get_item_height('imgProcess')
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width, horizontal_scrollbar=True):        
            dpg.add_text('1. Import camera files') 
            dpg.add_button(label='Import Camera Files', callback=lambda: dpg.show_item("lptRun_importCam"))
            dpg.add_text('Status: --', tag='lptRun_camStatus')
            dpg.add_separator()
            
            dpg.add_text('2. Import image path files')
            dpg.add_button(label='Import Image Files', callback=lambda: dpg.show_item("lptRun_importImg"))
            dpg.add_text('Status: --', tag='lptRun_imgStatus')
            dpg.add_separator()
                    
            dpg.add_text('3. Set main parameters')
            dpg.add_button(label='Set Main Parameters', callback=lambda: dpg.show_item("lptRun_setMainParams"))
            dpg.add_separator()
            
            dpg.add_text('4. Set object parameters')
            dpg.add_listbox(label='Object Types', items=['Tracer'], num_items=2, width=0.3*subwindow_width, tag='lptRun_objectType_input')
            dpg.add_button(label='Add Object Parameters', callback=callbacks.lptRun.selectObjectTypes)
            dpg.add_button(label='Clear Objects', callback=callbacks.lptRun.clearObjects)
            dpg.add_separator()
            
            dpg.add_text('5. Select export folder (for saving configuration files)')
            dpg.add_button(label='Select', callback=lambda: dpg.show_item("lptRun_exportFolderDialog"))
            dpg.add_button(tag='lptRun_generateConfig_button', label='Generate Configuration File', callback=callbacks.lptRun.generateConfig, show=False)
            dpg.add_text('Generating status: --', tag='lptRun_generateConfigStatus')
            
            #--------------------#
            # affiliate sections #
            #--------------------#
            # cam file selection
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, file_count=20, tag='lptRun_importCam', callback=callbacks.lptRun.openCamFile, cancel_callback=lambda: dpg.configure_item('lptRun_importCam', show=False)):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            # img file selection    
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, file_count=60, min_size=[400,300], show=False, tag='lptRun_importImg', callback=callbacks.lptRun.openImgFile, cancel_callback=lambda: dpg.configure_item('lptRun_importImg', show=False)):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            # main parameter setting
            with dpg.window(label="Set Main Parameters",width=0.7*subwindow_width, height=0.9*subwindow_height, modal=False, show=False, tag="lptRun_setMainParams", no_title_bar=False):
                dpg.add_text('1. Enter frame ID range: (start, end)')
                dpg.add_text('Note: frame ID starting from 0!')
                dpg.add_input_intx(tag='lptRun_frameRange_input', width=0.3*subwindow_width, default_value=[0, 100], min_clamped=True, min_value=0, size=2)
                
                dpg.add_text('2. Enter number of threads for parallel processing')
                dpg.add_input_int(tag='lptRun_nThread_input', default_value=6, min_clamped=True, min_value=0, width=0.3*subwindow_width)
                
                dpg.add_text('3. Enter number of bits of image')
                dpg.add_input_int(tag='lptRun_nDigit_input', default_value=8, min_clamped=True, min_value=8, width=0.3*subwindow_width)
                
                dpg.add_text('4. Enter view volume range [physical unit]:')
                dpg.add_input_floatx(tag='lptRun_viewVolume_x_input', label='(x_min,x_max)', width=0.3*subwindow_width, default_value=[-20, 20], size=2)
                dpg.add_input_floatx(tag='lptRun_viewVolume_y_input', label='(y_min,y_max)', width=0.3*subwindow_width, default_value=[-20, 20], size=2)
                dpg.add_input_floatx(tag='lptRun_viewVolume_z_input', label='(z_min,z_max)', width=0.3*subwindow_width, default_value=[-20, 20], size=2)

                with dpg.group(horizontal=True):
                    dpg.add_text('5. Enter voxel size [in physical unit]:')
                    dpg.add_button(label='?', callback=callbacks.lptRun.helpVoxToMM)
                dpg.add_text('e.g. if use 1000^3 voxel, ratio = (xmax-xmin)/1000')
                dpg.add_input_float(tag='lptRun_voxelToMM_input', default_value=0.04)
                
                dpg.add_text('6. Choose whether to track from the previous result')
                dpg.add_checkbox(label='Start from previous result', tag='lptRun_isLoadTracks_input', default_value=False)
                dpg.add_input_int(label='Enter the frame ID of previous result', tag='lptRun_prevFrameID_input', default_value=-1, width=0.3*subwindow_width, step=-1)
                                
                dpg.add_text('7. Select output folder for tracking results')
                dpg.add_button(label='Select', callback=lambda: dpg.configure_item("lptRun_resultFolderDialog", show=True))
                
                dpg.add_separator()
                dpg.add_button(label='Ok', callback=callbacks.lptRun.setMainParams)
                
                # result folder selection
                dpg.add_file_dialog(tag='lptRun_resultFolderDialog', directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, callback=callbacks.lptRun.selectResultFolder, cancel_callback=lambda: dpg.configure_item('lptRun_resultFolderDialog', show=False))
            
            # tracer parameter setting
            with dpg.window(label="Add Tracer Parameters",width=0.7*subwindow_width, height=0.9*subwindow_height, modal=False, show=False, tag="lptRun_addTracerParams", no_title_bar=False): 
                dpg.add_text('Add Tracer Parameters')
                dpg.add_separator()
                
                dpg.add_text('1. Tracking Parameters (unit: voxel)')
                dpg.add_input_float(label='search radius for connect tracks to objects', tag='lptRun_Tracer_searchRadius_input', default_value=10, width=0.3*subwindow_width, step=-1)
                dpg.add_input_int(label='number of frames for initial phase', tag='lptRun_Tracer_nFrameInitPhase_input', default_value=4, width=0.3*subwindow_width, step=-1)
                dpg.add_input_float(label='average interparticle spacing to identify nerghbour tracks', tag='lptRun_Tracer_avgInterParticleDist_input', default_value=30, width=0.3*subwindow_width, step=-1)
                
                dpg.add_text('2. Shake Parameters (unit: voxel)')
                dpg.add_input_float(label='shake width', tag='lptRun_Tracer_shakeWidth_input', default_value=0.25, width=0.3*subwindow_width, step=-1)
                
                dpg.add_text('3. Predictive Field Parameters')
                dpg.add_input_intx(label='number of grids (ngrid_x, ngrid_y, ngrid_z)', tag='lptRun_Tracer_pfGrids_input', default_value=[51, 51, 51], width=0.3*subwindow_width, size=3)
                dpg.add_input_float(label='search radius (unit: voxel)', tag='lptRun_Tracer_pfSearchRadius_input', default_value=25, width=0.3*subwindow_width, step=-1)
                
                dpg.add_text('4. IPR Parameters')
                dpg.add_input_int(label='number of IPR loops', tag='lptRun_Tracer_nIPRLoop_input', default_value=2, width=0.3*subwindow_width, step=-1)
                dpg.add_input_int(label='number of shake loops', tag='lptRun_Tracer_nShakeLoop_input', default_value=4, width=0.3*subwindow_width, step=-1)
                dpg.add_input_float(label='ghost intensity threshold ratio', tag='lptRun_Tracer_ghostThreshold_input', default_value=0.1, width=0.3*subwindow_width, step=-1)
                dpg.add_input_float(label='2D tolerance (unit: pixel)', tag='lptRun_Tracer_tol_2d_input', default_value=0.8, width=0.3*subwindow_width, step=-1)
                dpg.add_input_float(label='3D tolerance (unit: voxel)', tag='lptRun_Tracer_tol_3d_input', default_value=0.6, width=0.3*subwindow_width, step=-1)
                
                dpg.add_input_int(label='number of reduced camera', tag='lptRun_Tracer_nReducedCam_input', default_value=1, width=0.3*subwindow_width, step=-1)
                dpg.add_input_int(label='number of IPR loops for each reduced camera combinition', tag='lptRun_Tracer_nIPRLoopReduced_input', default_value=2, width=0.3*subwindow_width, step=-1)
                
                dpg.add_text('5. Tracer Identification Parameters')
                dpg.add_input_float(label='2D tracer intensity threshold', tag='lptRun_Tracer_2DThreshold_input', default_value=30, width=0.3*subwindow_width, step=-1)
                dpg.add_input_float(label='2D tracer radius (unit: pixel)', tag='lptRun_Tracer_2DRadius_input', default_value=2, width=0.3*subwindow_width, step=-1)
                
                # load previous track path 
                with dpg.group(tag='lptRun_Tracer_loadPrevTrack_parent', show=False):
                    dpg.add_text('6. Load previous track path')
                    dpg.add_button(label='Select previous long active tracks', callback=lambda: dpg.configure_item('lptRun_Tracer_loadLATrack_dialog', show=True))
                    dpg.add_button(label='Select previous short active tracks', callback=lambda: dpg.configure_item('lptRun_Tracer_loadSATrack_dialog', show=True))

                    with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='lptRun_Tracer_loadLATrack_dialog', callback=callbacks.lptRun.selectLongActiveTrack):
                        dpg.add_file_extension("", color=(150, 255, 150, 255))
                        dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                        dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                        
                    with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='lptRun_Tracer_loadSATrack_dialog', callback=callbacks.lptRun.selectShortActiveTrack):
                        dpg.add_file_extension("", color=(150, 255, 150, 255))
                        dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                        dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
                dpg.add_separator()
                dpg.add_button(label='Add', callback=callbacks.lptRun.addTracerParams)
                  
            # export folder selection
            dpg.add_file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='lptRun_exportFolderDialog', callback=callbacks.lptRun.selectExportFolder, cancel_callback=lambda: dpg.configure_item('lptRun_exportFolderDialog', show=False))
            
            # error message
            with dpg.window(label="ERROR!", modal=True, show=False, tag="lptRun_noPath", no_title_bar=False):
                dpg.add_text("", tag="lptRun_noPathText")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("lptRun_noPath", show=False))
                
            # help window 
            with dpg.window(label="Help!", modal=True, show=False, tag="lptRun_help", no_title_bar=False, width=0.3*subwindow_width, height=0.3*subwindow_height, pos=[0.35*subwindow_width,0.35*subwindow_height], horizontal_scrollbar=True):
                dpg.add_text("", tag="lptRun_helpText", wrap=0.295*subwindow_width)
                dpg.add_text("")
                dpg.add_separator()
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("lptRun_help", show=False))
            
        
        with dpg.child_window(tag='lptRun_outputParent', horizontal_scrollbar=True):
            dpg.add_text('Configuration Outputs')
            dpg.add_separator()

            # cam file table
            with dpg.group(show=False, tag='lptRun_camOutputParent'):
                dpg.add_text('Camera File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='lptRun_camFileTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='File Path', width_fixed=True)
            
            # img file table
            with dpg.group(show=False, tag='lptRun_imgOutputParent'):
                dpg.add_text('Image File:')
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='lptRun_imgFileTable'):
                    dpg.add_table_column(label='Cam Name', width_fixed=True)
                    dpg.add_table_column(label='Image File Name', width_fixed=True)
                    dpg.add_table_column(label='Number of Frames', width_fixed=True)
                    dpg.add_table_column(label='Image File Path', width_fixed=True)
                dpg.add_separator()

            # main parameter output
            dpg.add_text('Frame ID Range: --', tag='lptRun_frameRange')
            dpg.add_text('Number of Threads: --', tag='lptRun_nThread')
            dpg.add_text('Digits of Images: --', tag='lptRun_nDigit')
            dpg.add_text('View Volume: --', tag='lptRun_viewVolume')
            dpg.add_text('Voxel to mm ratio: --', tag='lptRun_voxelToMM') 
            dpg.add_text('Start from previous frame ID: --', tag='lptRun_isLoadTracks')
            dpg.add_text('Result Folder: --', tag='lptRun_resultFolder')
            dpg.add_separator()
            
            # object outputs 
            dpg.add_text('Object Types: --', tag='lptRun_objectTypes') 
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, tag='lptRun_trackPathTable', show=False):
                    dpg.add_table_column(label='ID', width_fixed=True)
                    dpg.add_table_column(label='Object Type', width_fixed=True) 
                    dpg.add_table_column(label='Long Active Track Path', width_fixed=True)    
                    dpg.add_table_column(label='Short Active Track Path', width_fixed=True) 
    
            dpg.add_separator()
            
            # export folder output
            dpg.add_text('Export Folder: --', tag='lptRun_exportFolder')
            
            dpg.add_text('Main Config File: --', tag='lptRun_mainConfigFile', color=(255, 255, 0, 255))
            
            
def showRun(callbacks):
    subwindow_width = dpg.get_item_width('imgProcess')
    subwindow_height = dpg.get_item_height('imgProcess')
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width, horizontal_scrollbar=True):
            dpg.add_text('1. Import main config file')
            dpg.add_button(label='Import', callback=lambda: dpg.show_item("lptRun_Run_loadMainConfig_dialog"))
            dpg.add_text('Status: --', tag='lptRun_Run_mainConfigStatus')
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_text('2. Check Object Identification (Optional)')
                dpg.add_button(label='?', callback=callbacks.lptRun.helpObjFinder)
            dpg.add_text('Select one object type for identification')
            dpg.add_listbox( tag='lptRun_Run_objFinder_objType_input')
            dpg.add_text('Select one camera for visualization')
            dpg.add_listbox( tag='lptRun_Run_objFinder_cam_input', callback=callbacks.lptRun.updateImage)
            dpg.add_text('Enter frame ID', tag='lptRun_Run_objFinder_frameID_text')
            dpg.add_input_int(tag='lptRun_Run_objFinder_frameID_input', callback=callbacks.lptRun.updateImage)
            dpg.add_button(label='Check', callback=callbacks.lptRun.checkObjFinder, tag='lptRun_Run_objFinder_checkButton')
            dpg.add_separator()
            
            dpg.add_text('3. Run OpenLPT')
            dpg.add_button(label='Run', callback=callbacks.lptRun.runOpenLPT, tag='lptRun_Run_runButton', show=False)
            dpg.add_text('Status: --', tag='lptRun_Run_processStatus')
            
            
            # Affliate sections
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='lptRun_Run_loadMainConfig_dialog', callback=callbacks.lptRun.openMainConfig):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            # error message
            with dpg.window(label="ERROR!", modal=True, show=False, tag="lptRun_Run_noPath", no_title_bar=False):
                dpg.add_text("", tag="lptRun_Run_noPathText")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("lptRun_Run_noPath", show=False))
                
            # help window 
            with dpg.window(label="Help!", modal=True, show=False, tag="lptRun_Run_help", no_title_bar=False, width=0.3*subwindow_width, height=0.3*subwindow_height, pos=[0.35*subwindow_width,0.35*subwindow_height]):
                dpg.add_text("", tag="lptRun_Run_helpText", wrap=0.295*subwindow_width)
                dpg.add_text("")
                dpg.add_separator()
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("lptRun_Run_help", show=False))
                
                   
        with dpg.child_window(show=True):
            dpg.add_text('OpenLPT Output')
            dpg.add_separator()
            
            dpg.add_text('Main Config File: --', tag='lptRun_Run_mainConfigFile')
            dpg.add_text('Result Folder: --', tag='lptRun_Run_resultFolder')
            dpg.add_separator()
            
            with dpg.plot(tag="lptRun_Run_PlotParent", label='OpenLPT Plot', height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="lptRun_Run_Plot_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="lptRun_Run_Plot_y_axis", invert=True)
            
            

def showPostProcessing(callbacks):
    subwindow_width = dpg.get_item_width('imgProcess')
    subwindow_height = dpg.get_item_height('imgProcess')
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width, horizontal_scrollbar=True):            
            dpg.add_text('1. Import tracks file:')
            dpg.add_button(label='Import', callback=lambda: dpg.show_item("lptRun_Post_loadTrack_dialog"))
            dpg.add_text('Status: --', tag='lptRun_Post_loadTrackStatus')
            dpg.add_separator()
            
            dpg.add_text('2. Select a folder for saving post-processing plots')
            dpg.add_button(label='Select', callback=lambda: dpg.show_item("lptRun_Post_plotFolderDialog"))
            
            dpg.add_text('2. Plot tracks')
            dpg.add_text('Enter percent of tracks for plotting')
            dpg.add_input_int(label='%', step=-1, tag='lptRun_Post_plotPercent_input', default_value=10)
            dpg.add_button(label='Plot', callback=callbacks.lptRun.plotTracks, tag='lptRun_Post_plotTracksButton')
            dpg.add_separator()
            
            dpg.add_text('3. Plot number of found particles per frame')
            dpg.add_button(label='Plot', callback=callbacks.lptRun.plotNParticles, tag='lptRun_Post_plotNParticlesButton')
            dpg.add_separator()
            
            dpg.add_text('4. Plot track length distribution')
            dpg.add_button(label='Plot', callback=callbacks.lptRun.plotTrackLength, tag='lptRun_Post_plotTrackLengthButton')
            dpg.add_separator()
            
        
            # affiliate sections
            with dpg.file_dialog(directory_selector=False, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, file_count=100, tag='lptRun_Post_loadTrack_dialog', callback=callbacks.lptRun.openTracksFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            with dpg.file_dialog(directory_selector=True, width=0.7*subwindow_width, height=0.9*subwindow_height, min_size=[400,300], show=False, tag='lptRun_Post_plotFolderDialog', callback=callbacks.lptRun.selectPlotFolder, cancel_callback=lambda: dpg.configure_item('lptRun_Post_plotFolderDialog', show=False)):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                
            # error message
            with dpg.window(label="ERROR!", modal=True, show=False, tag="lptRun_Post_noPath", no_title_bar=False):
                dpg.add_text("", tag="lptRun_Post_noPathText")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("lptRun_Post_noPath", show=False))
        
        
        with dpg.child_window(show=True):
            dpg.add_text('Post-processing Output')
            dpg.add_separator()
            
            # plot 
            with dpg.plot(tag="lptRun_Post_PlotParent", label='OpenLPT Plot', height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="lptRun_Post_Plot_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="lptRun_Post_Plot_y_axis")
            
            # tracks file table 
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit, row_background=True,
                resizable=True, no_host_extendX=False, hideable=True, scrollY=True, scrollX=True,
                borders_innerV=True, delay_search=True, borders_outerV=True, borders_innerH=True,
                borders_outerH=True, height=0.15*subwindow_height,tag='lptRun_Post_tracksFileTable', show=False):
                    dpg.add_table_column(label='File Name', width_fixed=True)
                    dpg.add_table_column(label='Number of Tracks', width_fixed=True) 
                    dpg.add_table_column(label='File Path', width_fixed=True)
                    
            dpg.add_text('Total Number of tracks: --', tag='lptRun_Post_nTracks', color=(255, 255, 0, 255))
            dpg.add_separator()
            
            
        
