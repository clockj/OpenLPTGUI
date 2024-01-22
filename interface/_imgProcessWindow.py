import dearpygui.dearpygui as dpg

def showImgProcess(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300, horizontal_scrollbar=True):
            with dpg.file_dialog(directory_selector=True, min_size=[400,300], show=False, tag='dir_dialog_imgprocess', callback=callbacks.lptImgProcess.openFile, cancel_callback=callbacks.imageProcessing.cancelImportImage):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
            pass 
        
        
        with dpg.child_window(horizontal_scrollbar=True):
            dpg.add_text('Image Sample')
            
            pass
    
    pass