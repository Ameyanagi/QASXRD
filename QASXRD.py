from pydoc import doc
import fabio
import pyFAI

import matplotlib.pyplot as plt
import cv2
import os
import glob
import time

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

from IPython.display import clear_output
import ipywidgets as widgets
from ipywidgets import HBox, VBox
from IPython.display import display

class QASXRD(object):
    """Module to integrate XRD data at QAS Beamline.
    It will automatically find the latest calibration file and integrate the latest tiff file.
    
    Usage:
    qa = QASXRD(args) # Initialize QASXRD object
    qa.plotwidget() # Show plot widget and change the brightness and contrast of the image
    qa.watch_update() # Start watching for new files

    Args:
        calibration: Path to the calibration file. If not provided, the latest calibration file will be used.
        data_dir: Path to the data directory. Default is "/nsls2/data/qas-new/legacy/processed/".
        year: Year of the data. Default is "2022".
        cycle: Cycle of the data. Default is "2".
        output_dir: Path to the output directory. Default is "./output/".
        debug_dir: Path to the debug directory. Please use this if you want to debug the code. Default is None.
    """
    def __init__(self, 
                 calibration:str = None, 
                 data_dir = "/nsls2/data/qas-new/legacy/processed/",
                 year = "2022",
                 cycle = "2",
                 proposal = "310712XRD",
                 output_dir = "./output/",
                 debug_dir = None,
                 *args):
        
        self.data_dir = data_dir
        self.year = year
        self.cycle = cycle
        self.proposal = proposal
        self.debug_dir = debug_dir
        self.output_dir = output_dir
        
        self.init_root_dir()
        self.update_watch_regex()
        self.obtain_caliberation_files()
        self.init_current_job_files()
        
        self.plot_min = 0
        self.plot_max = 255
        
        
        self.init_pyFAI(calibration)
    
    def init_pyFAI(self, calibration:str = None):
       
        self.load_calibration(calibration)
    
    def load_calibration(self, calibration:str = None):
        if calibration:
            print("Loading calibration file: " + calibration)
            self.ai = pyFAI.load(calibration)
        else:
            if len(self.calibration_files) > 0:
                print("Loading calibration file: " + self.calibration_files[-1])
                self.ai = pyFAI.load(self.calibration_files[-1])
                
                print("\nList of calibration files found: ")
                for file in self.calibration_files:
                    print(file)
                print("Use load_calibration('calibration file path') to load other calibration file.")
            else:
                print("No calibration file found. Use load_calibration('calibration file path') to load a calibration file.")
                self.ai = pyFAI 
        
    # Initialize root directory
    # If debug_dir is not None, use debug_dir instead of data_dir
    def init_root_dir(self):
        
        if self.debug_dir is None:      
            self.root_dir = self.data_dir + self.year + "/" + self.cycle + "/" + self.proposal + "/"
        else:
            self.root_dir = self.debug_dir
        
        if not os.path.exists(self.root_dir):
            print("Root directory does not exist: " + self.root_dir)
    
    def update_watch_regex(self, regex = [r'.*primary.*\.tiff$']):
        self.watch_regex = regex
        
    def obtain_caliberation_files(self):
        list_of_poni_files = glob.glob(self.root_dir + "*.poni")
        self.calibration_files = sorted( list_of_poni_files,
                        key = os.path.getmtime)
        
    def show_caliberation_files(self):
        list_of_poni_files = glob.glob(self.root_dir + "*.poni")
        
        print("Calibration files:")
        print(list_of_poni_files)
        print("use load_calibration('calibration file path') to load a calibration file")
    
    def init_current_job_files(self):
        self.obtain_tiff_list()
        
        # Obtain current dat files in order of modification time
    def obtain_tiff_list(self):
        list_of_dat_files = glob.glob(self.root_dir + "*primary*.tiff")
        self.tiff_list = sorted( list_of_dat_files,
                        key = os.path.getmtime)
    
    def on_modified(self, event):
        clear_output(wait=True)
        filepath = event.src_path
        print("File modified: " + filepath)
        self.obtain_tiff_list()
        
        if len(self.tiff_list) > 0:
            self.plot_image_2theta()
        else:
            pass
        
    def on_created(self, event):
        self.on_modified(event)
    
    def watch_update(self):
        self.plot_image_2theta()
        
        event_handler = RegexMatchingEventHandler(self.watch_regex)
        event_handler.on_modified = self.on_modified
        event_handler.on_created = self.on_created
    
        observer = Observer()
        observer.schedule(event_handler, self.root_dir, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(10)
                
        except KeyboardInterrupt:
            observer.stop()
            
        observer.join()
    
    def set_plot_min_max(self, min, max):
        self.plot_max = max
        self.plot_min = min
    
    def plot_image_2theta(self):
       
        if self.output_dir is None:
            output = None
        else:
            os.makedirs(os.path.dirname(self.output_dir), exist_ok=True)
            output = self.output_dir + "/" + os.path.basename(self.tiff_list[-1]) + ".txt"
            output_fig = self.output_dir + "/" + os.path.basename(self.tiff_list[-1]) + ".png"
            
        im = fabio.open(self.tiff_list[-1])
        print(self.tiff_list[-1])
        tth, I = self.ai.integrate1d(im.data[::-1], 2048, unit="2th_deg", method="csr", filename=output)
        
        im_cv = cv2.imread(self.tiff_list[-1])

        fig, ax = plt.subplots(1, 2, figsize=(10,5))
        ax[0].imshow(im_cv[:,:,-1], cmap='gray', vmin=self.plot_min, vmax=self.plot_max)
        ax[0].set_xlabel("X")
        ax[0].set_ylabel("Y")
        
        ax[1].plot(tth, I)
        ax[1].set_xlabel("$2{\\theta} (^{\circ}$)")
        ax[1].set_ylabel("Intensity (a.u.)")
        plt.tight_layout()
        plt.show()
        plt.savefig(output_fig)
    
    def plot_widget(self):
        im = fabio.open(self.tiff_list[-1])
        print(self.tiff_list[-1])
        tth, I = self.ai.integrate1d(im.data[::-1], 2048, unit="2th_deg", method="csr")
        
        im_cv = cv2.imread(self.tiff_list[-1])

        @widgets.interact(plot_min=widgets.IntSlider(min=0, max=255, step=1, value=0),
                          plot_max=widgets.IntSlider(min=0, max=255, step=1, value=255))
        def plot_image(plot_min, plot_max):
            self.plot_max = plot_max
            self.plot_min = plot_min
            
            fig, ax = plt.subplots(1, 2, figsize=(10,5))
            ax[0].imshow(im_cv[:,:,-1], cmap='gray', vmin=plot_min, vmax=plot_max)
            ax[0].set_xlabel("X")
            ax[0].set_ylabel("Y")
            
            ax[1].plot(tth, I)
            ax[1].set_xlabel("$2{\\theta} (^{\circ}$)")
            ax[1].set_ylabel("Intensity (a.u.)")
            plt.tight_layout()
            plt.show()

def main():
    ai = QASXRD(debug_dir = "./XRD_data/", output_dir="./output/")
    ai.plot_widget()
        

if __name__ == '__main__':
    main()
    