from .Tool import Tool, ToolStateError

import cv2
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import numpy as np
import time
import platform
if platform.system() == 'Linux':
    import picamera # Note that this can only be installed on raspbery pi. 

class Camera(Tool):
    def __init__(self, machine, index, name, details):
        super().__init__(machine, index, name, details)
        self._camera_matrix = None
        self._dist_matrix = None
        
        self.load_coefficients('/home/pi/duckbot/duckbot/tools/calibration_checkerboard.yml')
        
        
    def load_coefficients(self, path):
        '''Loads camera matrix and distortion coefficients.'''
        #N.B. opencv doesn't like opening files in different directories :/
        # ToDo: do this from a json, and update calibration process accordingly
        # FILE_STORAGE_READ
        cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)

        # note we also have to specify the type to retrieve other wise we only get a
        # FileNode object back instead of a matrix
        camera_matrix = cv_file.getNode('K').mat()
        dist_matrix = cv_file.getNode('D').mat()
        self._camera_matrix = camera_matrix
        self._dist_matrix = dist_matrix

        cv_file.release()
        return [camera_matrix, dist_matrix]
    
    def get_camera_indices(self):
        """Returns valid camera indices for use with OpenCV"""
        index = 0
        arr = []
        i = 4
        while i > 0:
            try:
                cap = cv2.VideoCapture(index)
                if cap.read()[0]:
                    arr.append(index)
                    cap.release()
            except:
                print('exception')
            index += 1
            i -= 1
        return arr
    
    def get_frame(self, resolution = [1200, 1200], uvc = False):
        with picamera.PiCamera() as camera:
            camera.resolution = (1200, 1200)
            camera.framerate = 24
            time.sleep(2)
            # print("... camera connection established")
            output = np.empty((resolution[1], resolution[0], 3), dtype=np.uint8)
            camera.capture(output, 'rgb', use_video_port = True)
            tpose = np.transpose(output, axes = (1,0,2))
            undistorted = cv2.undistort(tpose, self._camera_matrix, self._dist_matrix, None, self._camera_matrix)
            return undistorted
        
    def show_frame(self, frame, grid=False, save=False):
        plt.imshow(frame)
        plt.title('frame capture')
        if grid:
            plt.grid() # add a grid
            h, w, z = frame.shape
            plt.plot([w/2], [h/2], marker='o') # put a marker in the center of the image
        if save:
            plt.savefig('fig.png');
        plt.show()
    
    def get_show_frame(self):
        self.show_frame(self.get_frame())
        
    def video_stream(self, camera_index = 0):
        cap = cv2.VideoCapture(camera_index) #Note that the index corresponding to your camera may not be zero but this is the most common default

        # draw a circle in the center of the frame
        center = None
        while center is None:
            # the first frame grab is sometimes empty
            ret, frame = cap.read()
            h, w = frame.shape[0:2]
            center = (int(w/2), int(h/2))
            print(center)

        while True:
            ret, frame = cap.read()
            target = cv2.circle(frame, center, 5, (0,255,0), -1)
            cv2.imshow('Input', frame)
            c = cv2.waitKey(1)
            if c ==27: #27 is the built in code for ESC so press escape to close the window. 
                break 

        cap.release()
        cv2.destroyAllWindows()

    
    
    