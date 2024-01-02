import dearpygui.dearpygui as dpg

def showProcessing(callbacks):
    with dpg.group(horizontal=True):
        with dpg.child_window(width=400, horizontal_scrollbar=True):
            
            with dpg.file_dialog(directory_selector=False, min_size=[400,300], show=False, tag='file_dialog_id', callback=callbacks.imageProcessing.openFile, cancel_callback=callbacks.imageProcessing.cancelImportImage):
                dpg.add_file_extension("", color=(150, 255, 150, 255))
                dpg.add_file_extension(".png", color=(0, 255, 255, 255))
                dpg.add_file_extension(".tif", color=(0, 255, 255, 255))
                dpg.add_file_extension(".tiff", color=(0, 255, 255, 255))
                dpg.add_file_extension(".jpg", color=(0, 255, 255, 255))
                dpg.add_file_extension(".dcm", color=(0, 255, 255, 255))
                dpg.add_file_extension(".dicom", color=(0, 255, 255, 255))
                dpg.add_file_extension(".jpeg", color=(0, 255, 255, 255))
                dpg.add_file_extension(".bmp", color=(0, 255, 255, 255))
                dpg.add_file_extension(".pgm", color=(0, 255, 255, 255))
                dpg.add_file_extension(".ppm", color=(0, 255, 255, 255))
                dpg.add_file_extension(".sr", color=(0, 255, 255, 255))
                dpg.add_file_extension(".ras", color=(0, 255, 255, 255))
                dpg.add_file_extension(".jpe", color=(0, 255, 255, 255))
                dpg.add_file_extension(".jp2", color=(0, 255, 255, 255))

            dpg.add_text('Select a Image to Use')
            dpg.add_button(tag='import_image', width=-1, label='Import Image', callback=lambda: dpg.show_item("file_dialog_id"))
            dpg.add_text('File Name:', tag='file_name_text')
            dpg.add_text('File Path:', tag='file_path_text')
            dpg.add_separator()
            dpg.add_text('Image Resolution:')
            dpg.add_text('Width:',  tag='imgWidth')
            dpg.add_text('Height:', tag='imgHeight')

            with dpg.group(tag="exportImageAsFileProcessingGroup", show=False):
                dpg.add_separator()
                dpg.add_text("Save Image")
                dpg.add_button(tag='exportImageAsFileProcessing', width=-1, label='Export Image as File', callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, 'Processing'))

            with dpg.window(label="ERROR! There is no image!", modal=True, show=False, tag="noImage", no_title_bar=False):
                dpg.add_text("ERROR: You must import an image.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noImage", show=False))
            dpg.add_separator()

            with dpg.window(label="ERROR! Select an image!", modal=True, show=False, tag="noPath", no_title_bar=False):
                dpg.add_text("ERROR: This is not a valid path.")
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("noPath", show=False))
            dpg.add_separator()


        with dpg.child_window(tag='ProcessingParent'):
            with dpg.plot(tag="ProcessingPlotParent", label="Processing", height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="Processing_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="Processing_y_axis")
            pass
