import platform
import time

import cv2
import matplotlib
import numpy as np

matplotlib.use("TkAgg")
from typing import Tuple

import yaml
from matplotlib import pyplot as plt

from science_jubilee.labware.Labware import Well
from science_jubilee.tools.Tool import Tool, requires_active_tool

if platform.system() == "Linux":
    import picamera  # Note that this can only be installed on raspbery pi.


class Camera(Tool):
    """A class representation of a Raspberry Pi camera.

    :param Tool: The base tool class
    :type Tool: class:`Tool`
    """

    def __init__(self, index, name):
        """Constructor method"""
        super().__init__(index, name)
        self._camera_matrix = None
        self._dist_matrix = None
        # self.load_coefficients(
        #     "/home/pi/POSE/science-jubilee/science-jubilee/tools/configs/calibration_checkerboard.yml"
        # )

    def load_coefficients(self, path):
        """Loads camera matrix and distortion coefficients.

        :param path: Path to your camera calibration file
        :type path: str
        :return: A list containing your camera matrix (index 0) and distortion matrix (index 1)
        :rtype: list
        """ """"""
        with open(path, "r") as file:
            config = yaml.safe_load(file)

        k_data = config["K"]["data"]
        camera_matrix = np.array(
            [k_data[i : i + 3] for i in range(0, len(k_data), 3)], dtype=object
        )

        d_data = config["D"]["data"]
        dist_matrix = np.array(
            [d_data[i : i + 3] for i in range(0, len(d_data), 3)], dtype=object
        )
        self._camera_matrix = camera_matrix
        self._dist_matrix = dist_matrix

        return [camera_matrix, dist_matrix]

    def get_camera_indices(self):
        """Returns valid camera indices for use with OpenCV

        :return: A list of valid camera indices
        :rtype: list
        """
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
        """Take a picture and return the image. Compensates for lens distortion using camera calibration file.

        :param resolution: Camera resolution, defaults to [1200, 1200]
        :type resolution: list, optional
        :param uvc: True if the camera is a USB video class (UVC) camera for programmatically setting focus, defaults to False
        :type uvc: bool, optional
        :return: The captured frame
        :rtype: ndarray
        """
        with picamera.PiCamera() as camera:
            camera.resolution = (1200, 1200)
            camera.framerate = 24
            time.sleep(5)
            output = np.empty((resolution[1], resolution[0], 3), dtype=np.uint8)
            camera.capture(output, "rgb", use_video_port=True)
            tpose = np.transpose(output, axes=(1, 0, 2))
            # undistorted = cv2.undistort(
            #     tpose, self._camera_matrix, self._dist_matrix, None, self._camera_matrix
            # )
            return tpose

    def show_frame(self, frame, grid=False, save=False, save_path="fig.png"):
        """Show a captured frame using matplotlib.

        :param frame: The captured frame to show
        :type frame: ndarray
        :param grid: Show grid lines, defaults to False
        :type grid: bool, optional
        :param save: Save to file, defaults to False
        :type save: bool, optional
        :param save_path: File path to save image, defaults to "fig.png"
        :type save_path: str, optional
        """
        plt.imshow(frame)
        plt.title("frame capture")
        if grid:
            plt.grid()  # add a grid
            h, w, z = frame.shape
            plt.plot(
                [w / 2], [h / 2], marker="o"
            )  # put a marker in the center of the image
        if save:
            plt.axis("off")
            plt.savefig(f"{save_path}")
        plt.show()

    def get_show_frame(self):
        """Get and show a frame."""
        self.show_frame(self.get_frame())

    @requires_active_tool
    def video_stream(self, camera_index=0):
        """Start a video stream from the camera.

        :param camera_index: The camera index, defaults to 0
        :type camera_index: int, optional
        """
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
        """Move to a number of wells to take and show images.

        :param resolution: Camera resolution, defaults to [1200, 1200]
        :type resolution: list, optional
        :param uvc: True if the camera is a USB video class (UVC) camera for programmatically setting focus, defaults to False
        :type uvc: bool, optional
        :param wells: A list of wells to image, defaults to None
        :type wells: :class:`Well`, optional
        """
        # TODO: different functions for saving many images, showing images, or getting frames for analysis?
        if type(wells) != list:
            wells = [wells]

        for well in wells:
            x, y, z_bottom = self._get_xyz(well=well)
            self._machine.safe_z_movement()
            self._machine.move_to(x=x, y=y)
            self._machine.move_to(z=30)  # focus height; read in from config
            time.sleep(1)  # ToDo: Better way to sync gcode movements & images
            f = self.get_frame()
            self.show_frame(f)

    @requires_active_tool
    def get_well_image(self, resolution=[1200, 1200], uvc=False, well: Well = None):
        """Move to a single well to take a picture and return the frame.

        :param resolution: Camera resolution, defaults to [1200, 1200]
        :type resolution: list, optional
        :param uvc: True if the camera is a USB video class (UVC) camera for programmatically setting focus, defaults to False
        :type uvc: bool, optional
        :param well: The well to image, defaults to None
        :type well: :class:`Well`, optional
        :return: The captured frame
        :rtype: ndarray
        """
        x, y, z_bottom = self._get_xyz(well=well)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y)
        self._machine.move_to(z=30)  # focus height; read in from config
        time.sleep(1)  # ToDo: Better way to sync gcode movements & images
        f = self.get_frame()
        return f

    @staticmethod
    def _get_xyz(well: Well = None, location: Tuple[float] = None):
        """Get the (x,y,z) position of a well.

        :param well: The well to fetch position of, defaults to None
        :type well: :class:`Well`, optional
        :param location: Directly specify an (x,y,z) location, defaults to None
        :type location: Tuple[float], optional
        :raises ValueError: Must specify either a well or a location
        :return: The well location
        :rtype: Tuple[float, float, float]
        """
        if well is not None and location is not None:
            raise ValueError("Specify only one of Well or x,y,z location")
        elif well is not None:
            x, y, z = well.x, well.y, well.z
        else:
            x, y, z = location
        return x, y, z

    @staticmethod
    def _get_top_bottom(well: Well = None):
        """Get the top and bottom heights of a well.

        :param well: The well to fetch position of, defaults to None
        :type well: Well, optional
        :return: The z-height of the top and bottom of the well
        :rtype: Tuple[float, float]
        """
        top = well.top
        bottom = well.bottom
        return top, bottom
