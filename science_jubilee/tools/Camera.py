from .Tool import Tool, ToolStateError, requires_active_tool
from science_jubilee.labware.Labware import Labware, Well
from typing import Tuple, Union
import cv2
import matplotlib

matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import time
import platform

if platform.system() == "Linux":
    import picamera  # Note that this can only be installed on raspbery pi.


class Camera(Tool):
    def __init__(self, index, name):
        super().__init__(index, name)
        self._camera_matrix = None
        self._dist_matrix = None

        self.load_coefficients(
            "/home/pi/plos-revision-submission/duckbot/science_jubilee/science_jubilee/tools/configs/calibration_checkerboard.yml"
        )

    def load_coefficients(self, path):
        """Loads camera matrix and distortion coefficients."""
        # N.B. opencv doesn't like opening files in different directories :/
        # ToDo: do this from a json, and update calibration process accordingly
        # FILE_STORAGE_READ
        cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)

        # note we also have to specify the type to retrieve other wise we only get a
        # FileNode object back instead of a matrix
        camera_matrix = cv_file.getNode("K").mat()
        dist_matrix = cv_file.getNode("D").mat()
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
                print("exception")
            index += 1
            i -= 1
        return arr
    
    @requires_active_tool
    def get_frame(self, resolution=[1200, 1200], uvc=False):
        with picamera.PiCamera() as camera:
            camera.resolution = (1200, 1200)
            camera.framerate = 24
            time.sleep(2)
            # print("... camera connection established")
            output = np.empty((resolution[1], resolution[0], 3), dtype=np.uint8) 
            camera.capture(output, "rgb", use_video_port=True)
            tpose = np.transpose(output, axes=(1, 0, 2))
            undistorted = cv2.undistort(
                tpose, self._camera_matrix, self._dist_matrix, None, self._camera_matrix
            )
            return undistorted

    def show_frame(self, frame, grid=False, save=False):
        plt.imshow(frame)
        plt.title("frame capture")
        if grid:
            plt.grid()  # add a grid
            h, w, z = frame.shape
            plt.plot(
                [w / 2], [h / 2], marker="o"
            )  # put a marker in the center of the image
        if save:
            plt.savefig("fig.png")
        plt.show()

    def get_show_frame(self):
        self.show_frame(self.get_frame())

    @requires_active_tool
    def video_stream(self, camera_index=0):
        cap = cv2.VideoCapture(
            camera_index
        )  # Note that the index corresponding to your camera may not be zero but this is the most common default

        # draw a circle in the center of the frame
        center = None
        while center is None:
            # the first frame grab is sometimes empty
            ret, frame = cap.read()
            h, w = frame.shape[0:2]
            center = (int(w / 2), int(h / 2))

        while True:
            ret, frame = cap.read()
            target = cv2.circle(frame, center, 5, (0, 255, 0), -1)
            cv2.imshow("Input", frame)
            c = cv2.waitKey(1)
            if (
                c == 27
            ):  # 27 is the built in code for ESC so press escape to close the window.
                break

        cap.release()
        cv2.destroyAllWindows()

    @requires_active_tool
    def image_wells(self, resolution=[1200, 1200], uvc=False, wells: Well = None): 
        # TODO: different functions for saving many images, showing images, or getting frames for analysis?
        if type(wells) != list:
            wells = [wells]
        
        for well in wells:
            x, y, z_bottom = self._get_xyz(well=well)
            self._machine.safe_z_movement()
            self._machine.move_to(x=x, y=y)
            self._machine.move_to(z=30) # focus height; read in from config
            time.sleep(1) # ToDo: Better way to sync gcode movements & images
            f = self.get_frame()
            self.show_frame(f)
            
    @requires_active_tool
    def get_well_image(self, resolution=[1200, 1200], uvc=False, well: Well = None): 
        x, y, z_bottom = self._get_xyz(well=well)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=30) # focus height; read in from config
        time.sleep(1) # ToDo: Better way to sync gcode movements & images
        f = self.get_frame()
        return f
    
    @staticmethod
    def _get_xyz(well: Well = None, location: Tuple[float] = None):
        if well is not None and location is not None:
            raise ValueError("Specify only one of Well or x,y,z location")
        elif well is not None:
            x, y, z = well.x, well.y, well.z
        else:
            x, y, z = location
        return x, y, z
        
    @staticmethod
    def _get_top_bottom(well: Well = None):
        top = well.top
        bottom = well.bottom
        return top, bottom