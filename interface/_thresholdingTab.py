import dearpygui.dearpygui as dpg

def showThresholding(callbacks):
    subwindow_width = dpg.get_item_width('calibPlate')
    
    with dpg.group(horizontal=True):
        with dpg.child_window(width=0.3*subwindow_width, horizontal_scrollbar=True):
            dpg.add_text('Convert image into a binary format')
            dpg.add_text('Note: Make sure the calibration dots are white!', color=(255, 255, 0, 255))
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='globalThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('globalThresholding', sender, app_data))
                dpg.add_text('Global Thresholding')
            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='invertGlobalThresholding', callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
                dpg.add_text('Invert Tresholding')
            dpg.add_text('Threshold')
            dpg.add_slider_int(tag='globalThresholdSlider', default_value=127, min_value=0, max_value=255, width=-1, callback=lambda: callbacks.imageProcessing.executeQuery('globalThresholding'))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptativeThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptativeMeanThresholding', sender, app_data))
                dpg.add_text('Adaptative Mean Thresholding')
                dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='adaptativeGaussianThresholdingCheckbox', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('adaptativeGaussianThresholding', sender, app_data))
                dpg.add_text('Adaptative Gaussian Thresholding')
                dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_checkbox(tag='otsuBinarization', callback=lambda sender, app_data: callbacks.imageProcessing.toggleAndExecuteQuery('otsuBinarization', sender, app_data))
                dpg.add_text('Otsu\'s Binarization')
                dpg.add_text('(Works better after Gaussian Blur)')
                dpg.add_separator()

            with dpg.group(tag="exportImageAsFileThresholdingGroup", show=False):
                dpg.add_text("Save Image")
                dpg.add_button(tag='exportImageAsFileThresholding', label='Export Image as File', width=-1, callback=lambda sender, app_data: callbacks.imageProcessing.exportImage(sender, app_data, 'Thresholding'))
                dpg.add_separator()

            
        with dpg.child_window(tag='ThresholdingParent'):
            with dpg.plot(tag="ThresholdingPlotParent", label="Thresholding", height=-1, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="Thresholding_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="Thresholding_y_axis", invert=True)