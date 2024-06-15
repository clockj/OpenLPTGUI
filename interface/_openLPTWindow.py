import dearpygui.dearpygui as dpg
import platform
import subprocess 

def showOpenLPT(callbacks):
    with dpg.tab_bar():
        with dpg.tab(label='Installation'):
            showInstall()
        with dpg.tab(label='Configuration'):
            showConfig()
        with dpg.tab(label='Run'):
            showRun()

            
def showInstall():
    with dpg.child_window(width=800):
        dpg.add_text('OpenLPT Installation')
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            dpg.add_text('1. Download the OpenLPT package:')
            dpg.add_text('https://github.com/clockj/OpenLPT.git')
        dpg.add_button(label='Copy URL', callback=lambda: dpg.set_clipboard_text('https://github.com/clockj/OpenLPT.git'))
        dpg.add_text('')
        
        dpg.add_text('2. Extract the OpenLPT package to a directory of your choice.')
        dpg.add_text('')
        
        dpg.add_text('3. Compile and install the OpenLPT package by following the Readme file of the code.', wrap=800)
        dpg.add_text('')
        
        dpg.add_text('4. Add the /bin/ folder to the system environment variables.')
        dpg.add_text('')


def showConfig():
    with dpg.child_window(width=800):
        dpg.add_text('OpenLPT Configuration')
        dpg.add_separator()
        
        dpg.add_text('1. Generate image file for each camera.') 
        dpg.add_text('')
        
        dpg.add_text('2. Save the path of images into corresponding file.')
        dpg.add_text('')
        
        dpg.add_text('2. Modify the configuration file by following the sample.')

def showRun():
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300, horizontal_scrollbar=True):
            dpg.add_text('OpenLPT Run')
            dpg.add_separator()

            dpg.add_text('Enter the path of config:')
            dpg.add_input_text(tag='inputOpenLPTConfig', default_value="config.txt")
            
            dpg.add_text('Enter the path of log:')
            dpg.add_input_text(tag='inputOpenLPTLog',default_value="log.txt")
            
            dpg.add_button(label='Run', callback=runOpenLPT)
            
        with dpg.child_window(show=True):
            dpg.add_text('OpenLPT Output')
            dpg.add_separator()
            
            dpg.add_text('Output will be displayed here.')
            
            dpg.add_text('', tag='openLPTOutput')


def runOpenLPT():
    configPath = dpg.get_value('inputOpenLPTConfig')
    logPath = dpg.get_value('inputOpenLPTLog')
    

    # powershell = None
    # if platform.system() == 'Windows':
    #     # for windows
    #     powershell = "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
    # else:
    #     # for Linux
    #     powershell = "/bin/bash"
    
    
    # out = subprocess.run(['OpenLPT.exe', ' ', configPath], shell=True, check=False, text=True, capture_output=True, executable=powershell)
    out = subprocess.run(["OpenLPT.exe", configPath], shell=True, check=False, text=True, capture_output=True)
    
    with open(logPath, 'w') as f:
        f.write(out.stdout)
    
    if out.returncode == 0:
        dpg.set_value('openLPTOutput', 'OpenLPT finished successfully!')
    else:
        dpg.set_value('openLPTOutput', 'OpenLPT failed. '+out.stderr)
        print(out.stderr)
        print(out.stdout)
        
        
