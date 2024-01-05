import dearpygui.dearpygui as dpg

def showVSC(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300,horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_vscCam', callback=callbacks.Vsc.openCamFile, cancel_callback=callbacks.Vsc.cancelCamImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
                
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, file_count=20, tag='file_dialog_vscTrack', callback=callbacks.Vsc.openTrackFile, cancel_callback=callbacks.Vsc.cancelTrackImportFile):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".csv", color=(0, 255, 255, 255))
                dpg.add_file_extension(".txt", color=(0, 255, 255, 255))
            
            dpg.add_text('1. Import Camera Parameters')
            dpg.add_button(tag='import_VscCam', label='Import Camera Parameters', callback=lambda: dpg.show_item("file_dialog_vscCam"))
            dpg.add_separator()
            
            dpg.add_text('2. Import Tracking Data')
            dpg.add_button(tag='import_VscTrack', label='Import Tracking Data', callback=lambda: dpg.show_item("file_dialog_vscTrack"))
            dpg.add_separator()
                        
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
            dpg.add_separator()
        
        with dpg.child_window(tag='vscOutputParent'):
            
            dpg.add_text('VSC Outputs')
            
            