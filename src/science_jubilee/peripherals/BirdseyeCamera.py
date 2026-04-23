import json
import os
import time
from typing import Dict, List, Optional, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np

from science_jubilee.labware.Labware import Labware, Well
from science_jubilee.tools.Tool import Tool, ToolConfigurationError


# Supported ArUco dictionary names
ARUCO_DICTS = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
}


class BirdseyeCamera(Tool):
    """A USB webcam mounted overhead (not on the tool carriage).

    Supports two calibration modes:

    **2D homography** (``calibrate()``) — maps pixel coordinates to machine XY
    at a fixed Z height. Simple, requires no lens calibration, but coordinate
    conversion is only accurate at the calibration Z.

    **3D pose** (``calibrate_3d()``) — solves for the camera's full 3D position
    and orientation using ``solvePnP``. Requires lens intrinsic calibration
    (``load_lens_calibration()``). Once calibrated, ``pixel_to_machine(px, py, z)``
    correctly handles any bed Z height via ray-plane intersection — useful when
    the bed moves in Z between captures.

    The 3D calibration is saved alongside the 2D homography; both are usable
    from the same ``.npz`` file. Markers only need to be visible during the
    one-time calibration; after saving, they can be removed or covered.

    Typical 3D workflow::

        cam = BirdseyeCamera.from_config("BirdseyeCamera_config.json")
        cam.attach(machine)

        # Load lens intrinsics first (from a checkerboard calibration)
        cam.load_lens_calibration(camera_matrix, dist_coeffs)

        # Jog tool tip to corner 0 of each marker, record positions
        positions = {}
        positions[0] = cam.collect_calibration_point(0)[1]  # returns (id, (x,y,z))
        positions[1] = cam.collect_calibration_point(1)[1]
        positions[2] = cam.collect_calibration_point(2)[1]
        positions[3] = cam.collect_calibration_point(3)[1]

        # Calibrate and save — markers can be removed after this
        cam.calibrate_3d(positions, corner=0, save_path="calibration.npz")

        # Later sessions
        cam.load_lens_calibration(camera_matrix, dist_coeffs)
        cam.load_calibration("calibration.npz")

        # Convert a detected pixel at a known bed Z to machine coordinates
        mx, my = cam.pixel_to_machine(px, py, z=current_bed_z)
        cam.move_to_pixel(px, py, z_target=current_bed_z, z_move=10)
    """

    def __init__(
        self,
        name: str,
        camera_index: int = 0,
        image_folder: str = ".",
        focus_height: float = 0.0,
        resolution: Tuple[int, int] = (1920, 1080),
        aruco_dict: str = "DICT_4X4_50",
    ):
        """Initialize the BirdseyeCamera tool.

        :param name: Tool name
        :type name: str
        :param camera_index: OpenCV camera device index, defaults to 0
        :type camera_index: int, optional
        :param image_folder: Directory for saving captured images, defaults to "."
        :type image_folder: str, optional
        :param focus_height: Z height (mm) at which to image, defaults to 0.0
        :type focus_height: float, optional
        :param resolution: Capture resolution as (width, height), defaults to (1920, 1080)
        :type resolution: Tuple[int, int], optional
        :param aruco_dict: ArUco dictionary name (see ARUCO_DICTS), defaults to "DICT_4X4_50"
        :type aruco_dict: str, optional
        """
        super().__init__(
            -1,
            name,
            camera_index=camera_index,
            image_folder=image_folder,
            focus_height=focus_height,
            resolution=resolution,
            aruco_dict=aruco_dict,
        )
        self._cap = None

        self._homography = None  # pixel coords → machine XY (2D)
        self._homography_inv = None  # machine XY → pixel coords (2D)
        self._camera_matrix = None  # intrinsic matrix
        self._dist_coeffs = None  # distortion coefficients
        self._rvec = None  # rotation vector (3D extrinsic)
        self._tvec = None  # translation vector (3D extrinsic)
        # Z-stack: list of (z_cal, rvec, tvec) from successive calibrate_3d_charuco calls
        self._z_cal_stack: List = []
        # Board geometry — set by calibrate_3d_charuco, persisted via save/load
        self._board_origin = None
        self._board_x_unit = None
        self._board_y_unit = None
        self._board_square_mm = None
        self._board_n_cx = None
        self._board_n_markers = None
        self._calib_obj_pts = None
        self._calib_img_pts = None
        self._calib_board_idx = None
        self._calib_board_geoms = None

        if aruco_dict not in ARUCO_DICTS:
            raise ToolConfigurationError(
                f"Unknown ArUco dictionary '{aruco_dict}'. "
                f"Choose from: {list(ARUCO_DICTS.keys())}"
            )
        aruco_dict_obj = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[aruco_dict])
        aruco_params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(aruco_dict_obj, aruco_params)

    @classmethod
    def from_config(
        cls,
        config_file: str,
        name: str = "birdseye_cam",
        path: str = os.path.join(os.path.dirname(__file__), "configs", "user"),
    ):
        """Initialize from a JSON config file.

        :param name: Tool name
        :type name: str
        :param config_file: Config filename (relative to ``path``)
        :type config_file: str
        :param path: Directory containing config files, defaults to tools/configs/
        :type path: str, optional
        :return: Initialized BirdseyeCamera
        :rtype: :class:`BirdseyeCamera`
        """
        config_path = os.path.join(path, config_file)
        with open(config_path, "rt") as f:
            kwargs = json.load(f)

        lens_cal_file = kwargs.pop("lens_calibration_path", None)
        cam_cal_file = kwargs.pop("machine_calibration_path", None)

        cam = cls(name=name, **kwargs)

        if lens_cal_file is not None:
            lens_path = os.path.join(path, lens_cal_file)
            lens = np.load(lens_path)
            cam.load_lens_calibration(lens["camera_matrix"], lens["dist_coeffs"])

        if cam_cal_file is not None:
            cam.load_calibration(os.path.join(path, cam_cal_file))

        return cam

    @classmethod
    def create_config(
        cls,
        config_file: str,
        camera_index: int = 0,
        resolution: Tuple[int, int] = (1920, 1080),
        aruco_dict: str = "DICT_4X4_50",
        image_folder: str = "images",
        focus_height: float = 0.0,
        lens_calibration_path: Optional[str] = None,
        machine_calibration_path: Optional[str] = None,
        path: str = os.path.join(os.path.dirname(__file__), "configs", "user"),
    ):
        """Write a new config JSON to the peripherals/configs/user folder.

        Run this once to create a config for your setup, then edit the file
        if needed before calling :meth:`from_config`.

        Example::

            BirdseyeCamera.create_config(
                "MyCamera_config.json",
                camera_index=0,
                resolution=(3264, 2448),
            )

        :param config_file: Output filename (e.g. ``"MyCamera_config.json"``)
        :param camera_index: OpenCV device index of the camera
        :param resolution: Capture resolution as (width, height)
        :param aruco_dict: ArUco dictionary name (see ARUCO_DICTS)
        :param image_folder: Directory for saving captured images
        :param focus_height: Z height (mm) at which to image
        :param lens_calibration_path: Filename of lens calibration .npz in configs folder (optional)
        :param machine_calibration_path: Filename of machine calibration .npz in configs folder (optional)
        :param path: Directory to write into, defaults to peripherals/configs/
        """
        data = {
            "camera_index": camera_index,
            "resolution": list(resolution),
            "aruco_dict": aruco_dict,
            "image_folder": image_folder,
            "focus_height": focus_height,
        }
        if lens_calibration_path is not None:
            data["lens_calibration_path"] = lens_calibration_path
        if machine_calibration_path is not None:
            data["machine_calibration_path"] = machine_calibration_path

        os.makedirs(path, exist_ok=True)
        out_path = os.path.join(path, config_file)
        with open(out_path, "wt") as f:
            json.dump(data, f, indent=4)
        print(f"Config written to {out_path}")
        print(
            "Edit it to add lens_calibration_path and machine_calibration_path once you have those files."
        )

    # ------------------------------------------------------------------
    # Machine attachment
    # ------------------------------------------------------------------

    def attach(self, machine):
        """Attach this camera to a machine without registering it on the tool changer.

        Use this instead of ``machine.load_tool()`` — the BirdseyeCamera is a
        fixed peripheral, not a tool-changer tool, so it has no tool index or
        Z offset on the machine.

        :param machine: The :class:`Machine` instance to attach to
        """
        self._machine = machine
        self.tool_offset = 0

    # ------------------------------------------------------------------
    # Camera connection
    # ------------------------------------------------------------------

    def connect(self):
        """Open the camera device. Called automatically by :meth:`get_frame`."""
        if self._cap is not None and self._cap.isOpened():
            return
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            raise ToolConfigurationError(
                f"Could not open camera at index {self.camera_index}. "
                "Check that the device is connected and the index is correct."
            )
        w, h = self.resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)


    def disconnect(self):
        """Release the camera device."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    # ------------------------------------------------------------------
    # Frame capture
    # ------------------------------------------------------------------

    def get_frame(self) -> np.ndarray:
        """Capture a single frame and return it as an RGB numpy array.

        Opens the camera if not already open, discards a few frames to let
        auto-exposure settle, then returns the captured frame. Applies lens
        undistortion if intrinsic calibration has been loaded.

        :return: Captured frame in RGB format, shape (H, W, 3)
        :rtype: np.ndarray
        :raises RuntimeError: If the frame cannot be read from the camera
        """
        opened_here = False
        if self._cap is None or not self._cap.isOpened():
            self.connect()
            opened_here = True

        # Discard a few frames so auto-exposure can settle
        for _ in range(3):
            self._cap.read()

        ret, frame = self._cap.read()

        if opened_here:
            self.disconnect()

        if not ret:
            raise RuntimeError("Failed to capture frame from camera")

        if self._camera_matrix is not None and self._dist_coeffs is not None:
            frame = cv2.undistort(frame, self._camera_matrix, self._dist_coeffs)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def save_frame(self, frame: np.ndarray, filename: str) -> str:
        """Save a frame to the image folder.

        :param frame: RGB frame to save
        :type frame: np.ndarray
        :param filename: Filename (e.g. ``"well_A1.png"``), without path prefix
        :type filename: str
        :return: Full path to the saved file
        :rtype: str
        """
        os.makedirs(self.image_folder, exist_ok=True)
        path = os.path.join(self.image_folder, filename)
        cv2.imwrite(path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        return path

    def capture(self, filename: str = "capture.jpg") -> str:
        """Capture a frame and save it to the image folder.

        :param filename: Output filename, defaults to "capture.jpg"
        :type filename: str, optional
        :return: Full path to the saved file
        :rtype: str
        """
        frame = self.get_frame()
        os.makedirs(self.image_folder, exist_ok=True)
        filepath = os.path.join(self.image_folder, filename)
        cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"Saved to {filepath}")
        return filepath

    def show_frame(self, frame: np.ndarray, show_pixels: bool = True):
        """Display a captured frame using matplotlib.

        :param frame: RGB frame to display
        :type frame: np.ndarray
        :param show_pixels: Show pixel coordinate axes, defaults to True
        :type show_pixels: bool, optional
        """
        plt.figure(figsize=(10, 8))
        plt.imshow(frame)
        if show_pixels:
            plt.axis("on")
            plt.xlabel("px")
            plt.ylabel("py")
        else:
            plt.axis("off")
        plt.tight_layout()
        plt.show()

    def video_stream(self):
        """Open a live video stream in an OpenCV window. Press ESC or 'q' to exit."""
        self.connect()
        try:
            while True:
                ret, frame = self._cap.read()
                if not ret:
                    break
                cv2.imshow("BirdseyeCamera — press ESC to exit", frame)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
        finally:
            cv2.destroyAllWindows()
            self.disconnect()

    def capture_at_location(
        self,
        location: Union[Well, Tuple],
        save_filename: Optional[str] = None,
    ) -> np.ndarray:
        """Move the machine to a labware location and capture an image.

        :param location: Target :class:`Well` or ``(x, y, z)`` tuple
        :type location: Union[Well, Tuple]
        :param save_filename: If given, save the image with this filename in
            :attr:`image_folder`, defaults to None
        :type save_filename: str, optional
        :return: Captured RGB frame
        :rtype: np.ndarray
        """
        x, y, _ = Labware._getxyz(location)
        self._machine.safe_z_movement()
        self._machine.move_to(x=x, y=y, wait=True)
        picture_height = self.focus_height - abs(self.tool_offset)
        self._machine.move_to(z=picture_height, wait=True)
        time.sleep(0.5)  # let vibrations settle

        frame = self.get_frame()
        if save_filename is not None:
            self.save_frame(frame, save_filename)
        return frame

    # ------------------------------------------------------------------
    # ArUco detection
    # ------------------------------------------------------------------

    def detect_aruco(
        self, frame: Optional[np.ndarray] = None
    ) -> Tuple[List, Optional[np.ndarray], List]:
        """Detect ArUco markers in a frame.

        :param frame: RGB frame to search; captures a new frame if None
        :type frame: np.ndarray, optional
        :return: ``(corners, ids, rejected)`` as returned by
            :class:`cv2.aruco.ArucoDetector`. ``ids`` is ``None`` if no markers found.
        :rtype: Tuple[List, Optional[np.ndarray], List]
        """
        if frame is None:
            frame = self.get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        corners, ids, rejected = self._detector.detectMarkers(gray)
        return corners, ids, rejected

    def draw_detected_markers(
        self,
        frame: np.ndarray,
        corners: List,
        ids: Optional[np.ndarray],
    ) -> np.ndarray:
        """Return a copy of ``frame`` with detected ArUco markers drawn on it.

        :param frame: RGB frame
        :type frame: np.ndarray
        :param corners: Corners list from :meth:`detect_aruco`
        :type corners: List
        :param ids: IDs array from :meth:`detect_aruco`
        :type ids: Optional[np.ndarray]
        :return: Annotated RGB frame
        :rtype: np.ndarray
        """
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(bgr, corners, ids)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def collect_calibration_point(
        self, marker_id: int
    ) -> Tuple[int, Tuple[float, float, float]]:
        """Record a calibration point using the machine's current position.

        Jog the tool tip to corner 0 (top-left, marked with the printed ID
        number) of an ArUco marker, then call this method. Records the current
        machine (x, y, z) — the Z is needed for 3D calibration.

        Example::

            positions = {}
            positions[0] = cam.collect_calibration_point(0)[1]
            positions[1] = cam.collect_calibration_point(1)[1]
            positions[2] = cam.collect_calibration_point(2)[1]
            positions[3] = cam.collect_calibration_point(3)[1]
            cam.calibrate_3d(positions, corner=0, save_path="calibration.npz")

        :param marker_id: The ArUco marker ID you are currently positioned over
        :type marker_id: int
        :return: ``(marker_id, (machine_x, machine_y, machine_z))``
        :rtype: Tuple[int, Tuple[float, float, float]]
        """
        pos = self._machine.get_position()
        x, y = float(pos["X"]), float(pos["Y"])

        # M114 returns carriage Z. If a tool is active, add its offset to get
        # the world Z of the point the tip is touching.
        z_carriage = float(pos["Z"])
        active_idx = self._machine.active_tool_index
        if active_idx != -1 and active_idx in self._machine.tools:
            tool_offset = self._machine.tools[active_idx]["tool"].tool_offset
            z = z_carriage + abs(tool_offset) if tool_offset is not None else z_carriage
        else:
            z = z_carriage

        print(f"Marker {marker_id} → machine position ({x:.3f}, {y:.3f}, {z:.3f})")
        return marker_id, (x, y, z)

    def calibrate(
        self,
        marker_machine_positions: Dict[int, Tuple],
        frame: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        corner: Optional[int] = None,
    ) -> np.ndarray:
        """Compute a 2D homography from pixel space to machine XY coordinates.

        Accurate only at the Z height used during calibration. For Z-aware
        coordinate conversion use :meth:`calibrate_3d` instead.

        ArUco corner ordering: 0=top-left, 1=top-right, 2=bottom-right,
        3=bottom-left. The printed markers have the ID number in the quiet
        zone at corner 0.

        :param marker_machine_positions: Mapping of ArUco marker ID to its
            known machine position. Accepts ``(x, y)`` or ``(x, y, z)`` tuples;
            Z is ignored here but used by :meth:`calibrate_3d`.
        :type marker_machine_positions: Dict[int, Tuple]
        :param frame: Use this frame instead of capturing a new one, defaults to None
        :type frame: np.ndarray, optional
        :param save_path: If given, save the calibration to this ``.npz`` file
        :type save_path: str, optional
        :param corner: Which marker corner (0–3) was used as the reference point;
            if None, uses the marker center.
        :type corner: int, optional
        :return: The 3×3 homography matrix (pixel → machine XY)
        :rtype: np.ndarray
        :raises ValueError: If fewer than 4 markers with known positions are detected
        """
        if corner is not None and corner not in (0, 1, 2, 3):
            raise ValueError(f"corner must be 0, 1, 2, or 3, got {corner}")

        if frame is None:
            frame = self.get_frame()

        corners, ids, _ = self.detect_aruco(frame)

        if ids is None or len(ids) == 0:
            raise ValueError("No ArUco markers detected in frame.")

        pixel_pts = []
        machine_pts = []
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in marker_machine_positions:
                pixel_pt = (
                    corners[i][0].mean(axis=0)
                    if corner is None
                    else corners[i][0][corner]
                )
                pixel_pts.append(pixel_pt)
                machine_pts.append(marker_machine_positions[marker_id][:2])

        if len(pixel_pts) < 4:
            detected = set(ids.flatten().tolist())
            known = set(marker_machine_positions.keys())
            raise ValueError(
                f"Only {len(pixel_pts)} markers with known positions detected "
                f"(need ≥ 4). Detected IDs: {detected}, provided IDs: {known}"
            )

        pixel_pts = np.array(pixel_pts, dtype=np.float64)
        machine_pts = np.array(machine_pts, dtype=np.float64)

        H, mask = cv2.findHomography(pixel_pts, machine_pts, cv2.RANSAC, 5.0)
        H_inv, _ = cv2.findHomography(machine_pts, pixel_pts, cv2.RANSAC, 5.0)

        self._homography = H
        self._homography_inv = H_inv

        inliers = int(mask.sum()) if mask is not None else len(pixel_pts)
        print(f"2D calibration complete: {inliers}/{len(pixel_pts)} inliers")

        if save_path is not None:
            self.save_calibration(save_path)

        return H

    def calibrate_3d(
        self,
        marker_machine_positions: Dict[int, Tuple[float, float, float]],
        frame: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        corner: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the camera's 3D pose using ``solvePnP``.

        Requires lens intrinsic calibration to be loaded first via
        :meth:`load_lens_calibration`. Once solved, :meth:`pixel_to_machine`
        accepts a ``z`` argument and uses ray-plane intersection to give
        correct XY coordinates at any bed Z height.

        Place ArUco markers at known 3D positions on the bed (typically all at
        the same Z = current bed height during calibration). The markers only
        need to be visible during this call; after saving the calibration they
        can be removed or covered.

        :param marker_machine_positions: Mapping of ArUco marker ID to its
            known machine ``(x, y, z)`` position in mm, measured at the
            reference point (corner or center).
        :type marker_machine_positions: Dict[int, Tuple[float, float, float]]
        :param frame: Use this frame instead of capturing a new one, defaults to None
        :type frame: np.ndarray, optional
        :param save_path: If given, save the calibration to this ``.npz`` file
        :type save_path: str, optional
        :param corner: Which marker corner (0–3) was used as the reference point;
            if None, uses the marker center.
        :type corner: int, optional
        :return: ``(rvec, tvec)`` — the rotation and translation vectors
        :rtype: Tuple[np.ndarray, np.ndarray]
        :raises RuntimeError: If lens intrinsic calibration has not been loaded
        :raises ValueError: If fewer than 4 markers with known positions are detected
        """
        if self._camera_matrix is None or self._dist_coeffs is None:
            raise RuntimeError(
                "Lens intrinsic calibration required for 3D calibration. "
                "Call load_lens_calibration(camera_matrix, dist_coeffs) first."
            )
        if corner is not None and corner not in (0, 1, 2, 3):
            raise ValueError(f"corner must be 0, 1, 2, or 3, got {corner}")

        if frame is None:
            frame = self.get_frame()

        corners, ids, _ = self.detect_aruco(frame)

        if ids is None or len(ids) == 0:
            raise ValueError("No ArUco markers detected in frame.")

        image_pts = []
        object_pts = []
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in marker_machine_positions:
                pixel_pt = (
                    corners[i][0].mean(axis=0)
                    if corner is None
                    else corners[i][0][corner]
                )
                image_pts.append(pixel_pt)
                object_pts.append(marker_machine_positions[marker_id])

        if len(image_pts) < 4:
            detected = set(ids.flatten().tolist())
            known = set(marker_machine_positions.keys())
            raise ValueError(
                f"Only {len(image_pts)} markers with known positions detected "
                f"(need ≥ 4). Detected IDs: {detected}, provided IDs: {known}"
            )

        object_pts = np.array(object_pts, dtype=np.float64)
        image_pts = np.array(image_pts, dtype=np.float64)

        # get_frame() returns an already-undistorted image, so we tell solvePnP
        # there is no distortion (zero coefficients). Using the real dist_coeffs
        # here would double-undistort the detected corners.
        zero_dist = np.zeros_like(self._dist_coeffs)
        success, rvec, tvec, inliers = cv2.solvePnPRansac(
            object_pts, image_pts, self._camera_matrix, zero_dist
        )

        if not success:
            raise RuntimeError("solvePnP failed to find a solution.")

        self._rvec = rvec
        self._tvec = tvec

        n_inliers = len(inliers) if inliers is not None else len(image_pts)
        print(f"3D calibration complete: {n_inliers}/{len(image_pts)} inliers")

        if save_path is not None:
            self.save_calibration(save_path)

        return rvec, tvec

    def calibrate_3d_charuco(
        self,
        boards: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
        board_cols: int,
        board_rows: int,
        square_mm: float,
        frame: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        y_sign: Optional[int] = None,
        pixel_axes: Optional[Tuple] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the camera's 3D pose using one or more ChArUco boards.

        Requires lens intrinsic calibration (see :meth:`load_lens_calibration`).
        Each board contributes ~30 sub-pixel corner correspondences; using three
        boards spread across the bed gives ~90 points with full-frame coverage.

        **Setup:** generate boards with ``scripts/generate_charuco_board.py`` and
        tape them flat on the bed. Jog the tool tip to each board's dot A then
        dot B, recording each position with :meth:`collect_calibration_point`.
        Boards can be removed after saving the calibration.

        Dot A = interior corner ``(col=0, row=0)`` — one square in from the A side.
        Dot B = interior corner ``(col=board_cols−2, row=0)`` — one square in from the B side.
        Boards may be taped at any angle.

        Example (3 boards)::

            rvec, tvec = cam.calibrate_3d_charuco(
                boards=[(a1, b1), (a2, b2), (a3, b3)],
                board_cols=9, board_rows=6, square_mm=20,
                save_path="camera_calibration.npz",
            )

        If IPPE gives the wrong camera-Z sign, describe the camera's pixel-to-machine
        axis mapping so the code can construct a reliable initial rotation guess::

            # px increases → machine -Y direction; py increases → machine -X direction
            rvec, tvec = cam.calibrate_3d_charuco(
                ..., y_sign=-1,
                pixel_axes=([0,-1,0], [-1,0,0]),
            )

        ``pixel_axes=(px_machine_dir, py_machine_dir)`` where each is the approximate
        machine-space direction (3-element, need not be unit) that the named pixel axis
        increases toward.  The two vectors must not be parallel.

        :param boards: List of ``(corner_a_pos, corner_b_pos)`` tuples, one per
            board. Each position is a machine ``(x, y, z)`` tuple in mm.
        :type boards: List[Tuple[Tuple[float,float,float], Tuple[float,float,float]]]
        :param board_cols: Number of squares across (must match generated boards)
        :type board_cols: int
        :param board_rows: Number of squares down
        :type board_rows: int
        :param square_mm: Physical square size in mm
        :type square_mm: float
        :param frame: Use this frame instead of capturing a new one
        :type frame: np.ndarray, optional
        :param save_path: If given, save the calibration to this ``.npz`` file
        :type save_path: str, optional
        :param y_sign: Force the Y-axis orientation: ``1`` or ``-1``. If
            ``None`` (default), the orientation is chosen automatically based
            on physical validity (camera above bed) then RMS. Pass ``-1`` if
            the automatic choice gives the wrong Y direction on the machine.
        :type y_sign: int, optional
        :param pixel_axes: ``(px_machine_dir, py_machine_dir)`` — the approximate
            machine-space directions that +px and +py point toward.  Used to
            construct an initial rotation guess that bypasses IPPE's mirror
            ambiguity.  Example: ``([0,-1,0], [-1,0,0])`` means px increases
            toward machine -Y and py increases toward machine -X.
        :type pixel_axes: tuple of two array-like, optional
        :return: ``(rvec, tvec)``
        :rtype: Tuple[np.ndarray, np.ndarray]
        :raises RuntimeError: If lens calibration is not loaded, or solvePnP fails
        :raises ValueError: If fewer than 6 total ChArUco corners are detected
        """
        if self._camera_matrix is None or self._dist_coeffs is None:
            raise RuntimeError(
                "Lens intrinsic calibration required. "
                "Call load_lens_calibration() first."
            )

        if frame is None:
            frame = self.get_frame()

        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        zero_dist = np.zeros_like(self._dist_coeffs)
        n_cx = board_cols - 1  # interior corners per row
        n_markers = (board_cols * board_rows + 1) // 2
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

        all_obj_pts: List = []
        all_img_pts: List = []
        all_board_idx: List = []
        all_board_geoms: List = []  # (a, x_unit, y_unit) per board

        # Build initial rotation from pixel_axes hint when provided.
        # This bypasses IPPE's mirror ambiguity for unusual camera geometries.
        _pixel_axes_rvec: Optional[np.ndarray] = None
        if pixel_axes is not None:
            px_dir = np.array(pixel_axes[0], dtype=np.float64)
            py_dir = np.array(pixel_axes[1], dtype=np.float64)
            px_dir /= np.linalg.norm(px_dir)
            py_dir /= np.linalg.norm(py_dir)
            pz_dir = np.cross(px_dir, py_dir)
            pz_dir /= np.linalg.norm(pz_dir)
            # Rows of R map world coords to camera coords; rows are camera axes
            # expressed in the world (machine) frame.
            R_hint = np.stack([px_dir, py_dir, pz_dir], axis=0)
            # Project to SO(3) via SVD in case the hint vectors weren't exactly
            # orthogonal, and to ensure det=+1.
            U, _, Vt = np.linalg.svd(R_hint)
            R_hint = U @ np.diag([1.0, 1.0, float(np.linalg.det(U @ Vt))]) @ Vt
            _pixel_axes_rvec, _ = cv2.Rodrigues(R_hint)

        _initial_rvec: Optional[np.ndarray] = _pixel_axes_rvec
        _initial_tvec: Optional[np.ndarray] = None
        _best_y_unit_board0: Optional[np.ndarray] = None

        for board_idx, (corner_a_pos, corner_b_pos) in enumerate(boards):
            # Each board has a unique contiguous range of ArUco marker IDs
            first_id = board_idx * n_markers
            marker_ids = np.arange(first_id, first_id + n_markers, dtype=np.int32)
            board_obj = cv2.aruco.CharucoBoard(
                (board_cols, board_rows),
                square_mm,
                square_mm * 0.75,
                aruco_dict,
                marker_ids,
            )
            detector = cv2.aruco.CharucoDetector(board_obj)
            charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)

            if charuco_ids is None or len(charuco_ids) == 0:
                print(f"  Board {board_idx+1}: no corners detected — check visibility")
                continue

            # Derive board axes from the two jogged reference corners
            a = np.array(corner_a_pos[:2], dtype=np.float64)
            b = np.array(corner_b_pos[:2], dtype=np.float64)
            z = float(corner_a_pos[2])

            x_vec = b - a
            expected_dist = (n_cx - 1) * square_mm
            actual_dist = float(np.linalg.norm(x_vec))
            if abs(actual_dist - expected_dist) / expected_dist > 0.05:
                print(
                    f"  Board {board_idx+1} warning: A→B distance {actual_dist:.1f} mm, "
                    f"expected {expected_dist:.1f} mm — check square_mm or jog positions."
                )
            x_unit = x_vec / actual_dist

            # Pick Y axis orientation.  Always run IPPE for both ±90° candidates
            # to find the best physically valid (cam_Z < 0) initial pose guess.
            # When y_sign is forced, the object points from that sign are used but
            # the initial rvec/tvec for LM refinement comes from whichever sign
            # IPPE can reliably place the camera overhead (negative machine Z).
            signs_to_try = [float(y_sign)] if y_sign is not None else [1.0, -1.0]
            best_y: Optional[Tuple] = (
                None  # (cam_pos_z, y_unit, obj_pts, img_pts, rv, tv)
            )
            best_neg_init: Optional[Tuple] = (
                None  # (cam_z, rv, tv) — best cam_Z<0 from any sign
            )

            for sign in [1.0, -1.0]:  # always try both for initial-guess tracking
                y_unit = sign * np.array([-x_unit[1], x_unit[0]])
                obj_pts, img_pts = [], []
                for k, cid in enumerate(charuco_ids.flatten()):
                    local_id = int(cid) - first_id
                    col = local_id % n_cx
                    row = local_id // n_cx
                    obj_pts.append(
                        [
                            a[0]
                            + col * square_mm * x_unit[0]
                            + row * square_mm * y_unit[0],
                            a[1]
                            + col * square_mm * x_unit[1]
                            + row * square_mm * y_unit[1],
                            z,
                        ]
                    )
                    img_pts.append(charuco_corners[k][0])

                obj_arr_s = np.array(obj_pts, dtype=np.float64)
                img_arr_s = np.array(img_pts, dtype=np.float64)
                retval, rvecs_ippe, tvecs_ippe, _ = cv2.solvePnPGeneric(
                    obj_arr_s,
                    img_arr_s,
                    self._camera_matrix,
                    zero_dist,
                    flags=cv2.SOLVEPNP_IPPE,
                )
                if retval == 0:
                    continue

                # From IPPE's two solutions, prefer tvec[2] > 0 (board in front
                # of camera), then pick the one with the most negative camera Z.
                chosen_rv, chosen_tv, chosen_cam_z = None, None, np.inf
                for rv_i, tv_i in zip(rvecs_ippe, tvecs_ippe):
                    if float(tv_i[2]) > 0:
                        R_i, _ = cv2.Rodrigues(rv_i)
                        cz = float((-R_i.T @ tv_i).flatten()[2])
                        if cz < chosen_cam_z:
                            chosen_cam_z, chosen_rv, chosen_tv = cz, rv_i, tv_i
                if chosen_rv is None:
                    # Fallback: no front-facing solution; pick most-negative cam Z
                    for rv_i, tv_i in zip(rvecs_ippe, tvecs_ippe):
                        R_i, _ = cv2.Rodrigues(rv_i)
                        cz = float((-R_i.T @ tv_i).flatten()[2])
                        if cz < chosen_cam_z:
                            chosen_cam_z, chosen_rv, chosen_tv = cz, rv_i, tv_i

                # Track best physically valid (cam_Z < 0) initial guess from any sign
                if chosen_cam_z < 0 and (
                    best_neg_init is None or chosen_cam_z < best_neg_init[0]
                ):
                    best_neg_init = (chosen_cam_z, chosen_rv, chosen_tv)

                if sign in signs_to_try:
                    if y_sign is not None or best_y is None or chosen_cam_z < best_y[0]:
                        best_y = (
                            chosen_cam_z,
                            y_unit,
                            obj_pts,
                            img_pts,
                            chosen_rv,
                            chosen_tv,
                        )

            if best_y is None:
                print(f"  Board {board_idx+1}: solvePnP failed, skipping.")
                continue

            _, selected_y_unit, obj_pts, img_pts, board_rv, board_tv = best_y
            if board_idx == 0:
                _best_y_unit_board0 = selected_y_unit
                if _initial_rvec is None:
                    # No pixel_axes hint: use the best physically valid
                    # (cam_Z < 0) IPPE guess, or fall back to best_y's pose.
                    _initial_rvec = (
                        best_neg_init[1] if best_neg_init is not None else board_rv
                    )
                    _initial_tvec = (
                        best_neg_init[2] if best_neg_init is not None else board_tv
                    )
                else:
                    # pixel_axes supplied the rotation; estimate tvec via linear
                    # least squares so IPPE's tvec sign can't corrupt the seed.
                    # For each (world_pt, img_pt): q = R @ world_pt, then
                    #   tvec[0] - un*tvec[2] = un*q[2] - q[0]
                    #   tvec[1] - vn*tvec[2] = vn*q[2] - q[1]
                    R_h, _ = cv2.Rodrigues(_initial_rvec)
                    K = self._camera_matrix
                    q_pts = (R_h @ np.array(obj_pts, dtype=np.float64).T).T
                    ip_pts = np.array(img_pts, dtype=np.float64)
                    rows, rhs = [], []
                    for q_i, ip_i in zip(q_pts, ip_pts):
                        un = (ip_i[0] - K[0, 2]) / K[0, 0]
                        vn = (ip_i[1] - K[1, 2]) / K[1, 1]
                        rows.append([1.0, 0.0, -un])
                        rhs.append(un * q_i[2] - q_i[0])
                        rows.append([0.0, 1.0, -vn])
                        rhs.append(vn * q_i[2] - q_i[1])
                    t_lin, _, _, _ = np.linalg.lstsq(
                        np.array(rows), np.array(rhs), rcond=None
                    )
                    _initial_tvec = t_lin.reshape(3, 1)
            all_obj_pts.extend(obj_pts)
            all_img_pts.extend(img_pts)
            all_board_idx.extend([board_idx] * len(obj_pts))
            all_board_geoms.append((a, x_unit, selected_y_unit))
            print(f"  Board {board_idx+1}: {len(obj_pts)} corners")

        total = len(all_obj_pts)
        if total < 6:
            raise ValueError(
                f"Only {total} corners detected across all boards (need ≥ 6). "
                "Check that boards are well-lit and fully visible."
            )

        obj_arr = np.array(all_obj_pts, dtype=np.float64)
        img_arr = np.array(all_img_pts, dtype=np.float64)

        # Refine from the initial guess with Levenberg-Marquardt.
        ok, rvec, tvec = cv2.solvePnP(
            obj_arr,
            img_arr,
            self._camera_matrix,
            zero_dist,
            rvec=_initial_rvec.copy(),
            tvec=_initial_tvec.copy(),
            useExtrinsicGuess=True,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            raise RuntimeError("Final solvePnP failed.")

        proj, _ = cv2.projectPoints(obj_arr, rvec, tvec, self._camera_matrix, zero_dist)
        per_pt_err = np.sqrt(np.sum((img_arr - proj.reshape(-1, 2)) ** 2, axis=1))
        rms = float(np.sqrt(np.mean(per_pt_err**2)))
        n_good = int(np.sum(per_pt_err < 2.0))
        R_final, _ = cv2.Rodrigues(rvec)
        cam_pos_final = (-R_final.T @ tvec).flatten()

        self._rvec = rvec
        self._tvec = tvec

        # Add to Z-stack (replace any entry within 2 mm of this Z)
        z_cal = float(boards[0][0][2])
        self._z_cal_stack = [e for e in self._z_cal_stack if abs(e[0] - z_cal) > 2.0]
        self._z_cal_stack.append((z_cal, rvec.copy(), tvec.copy()))

        # Store calibration points and board geometry for refine_calibration_z / flip_y_axis
        self._calib_obj_pts = obj_arr
        self._calib_img_pts = img_arr
        self._calib_board_idx = np.array(all_board_idx, dtype=np.int32)

        # Store board 0 geometry for refine_calibration_z
        _a0, _b0 = boards[0]
        _a_xy = np.array(_a0[:2], dtype=np.float64)
        _b_xy = np.array(_b0[:2], dtype=np.float64)
        _xv = _b_xy - _a_xy
        self._board_origin = _a_xy
        self._board_x_unit = _xv / np.linalg.norm(_xv)
        self._board_y_unit = _best_y_unit_board0
        self._board_square_mm = square_mm
        self._board_n_cx = n_cx
        self._board_n_markers = n_markers
        self._calib_board_geoms = all_board_geoms  # [(a, x_unit, y_unit), ...]

        print(
            f"ChArUco 3D calibration: {n_good}/{total} within 2px, RMS {rms:.2f} px  "
            f"(camera Z={cam_pos_final[2]:.1f} mm)"
        )

        if save_path is not None:
            self.save_calibration(save_path)

        return rvec, tvec

    def refine_calibration_z(
        self,
        frame: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Refine camera pose using the same board at the current (different) bed Z.

        Call this after :meth:`calibrate_3d_charuco` with the board still on the
        bed but the bed moved to a new Z height. The board's XY positions are
        unchanged; only Z differs. Adding non-planar data removes the height
        ambiguity that causes inaccuracy at Z heights other than the calibration Z.

        Typical workflow::

            # Normal calibration at Z1
            cam.calibrate_3d_charuco(boards=[(a, b)], ..., save_path="cal.npz")

            # Move bed to a different Z (e.g. raise/lower 20-40 mm), then:
            cam.refine_calibration_z(save_path="cal.npz")

        :param frame: Frame to use; captures a new one if None
        :type frame: np.ndarray, optional
        :param save_path: If given, overwrite the calibration file
        :type save_path: str, optional
        :return: Refined ``(rvec, tvec)``
        :rtype: Tuple[np.ndarray, np.ndarray]
        :raises RuntimeError: If calibrate_3d_charuco has not been run first
        """
        if self._rvec is None or not hasattr(self, "_calib_obj_pts"):
            raise RuntimeError(
                "Run calibrate_3d_charuco() before refine_calibration_z()."
            )
        if self._board_y_unit is None:
            raise RuntimeError(
                "Board Y axis could not be recovered from calibration data. "
                "Re-run calibrate_3d_charuco() and try again."
            )

        if frame is None:
            frame = self.get_frame()

        z2 = float(self._machine.get_position()["Z"])
        print(f"Refining at Z = {z2:.2f} mm")

        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        marker_ids = np.arange(0, self._board_n_markers, dtype=np.int32)
        board_cols = self._board_n_cx + 1
        board_rows = (self._board_n_markers * 2 + board_cols - 1) // board_cols
        board_obj = cv2.aruco.CharucoBoard(
            (board_cols, board_rows),
            self._board_square_mm,
            self._board_square_mm * 0.75,
            aruco_dict,
            marker_ids,
        )
        detector = cv2.aruco.CharucoDetector(board_obj)
        corners2, ids2, _, _ = detector.detectBoard(gray)

        if ids2 is None or len(ids2) < 4:
            raise ValueError(
                f"Only {len(ids2) if ids2 is not None else 0} corners detected at Z={z2:.1f}. "
                "Ensure the board is visible and well-lit."
            )

        a = self._board_origin
        x_unit = self._board_x_unit
        y_unit = self._board_y_unit
        sq = self._board_square_mm
        n_cx = self._board_n_cx

        new_obj, new_img = [], []
        for k, cid in enumerate(ids2.flatten()):
            col = int(cid) % n_cx
            row = int(cid) // n_cx
            new_obj.append(
                [
                    a[0] + col * sq * x_unit[0] + row * sq * y_unit[0],
                    a[1] + col * sq * x_unit[1] + row * sq * y_unit[1],
                    z2,
                ]
            )
            new_img.append(corners2[k][0])

        print(f"  Detected {len(new_obj)} corners at Z={z2:.2f}")

        combined_obj = np.vstack(
            [self._calib_obj_pts, np.array(new_obj, dtype=np.float64)]
        )
        combined_img = np.vstack(
            [self._calib_img_pts, np.array(new_img, dtype=np.float64)]
        )
        combined_board_idx = np.concatenate(
            [
                self._calib_board_idx,
                np.zeros(len(new_obj), dtype=np.int32),
            ]
        )

        zero_dist = np.zeros_like(self._dist_coeffs)
        # Use iterative LM refinement from the known-good initial pose rather than
        # RANSAC, which can sample degenerate all-same-Z subsets and flip to the
        # mirror solution.
        ok, rvec, tvec = cv2.solvePnP(
            combined_obj,
            combined_img,
            self._camera_matrix,
            zero_dist,
            rvec=self._rvec.copy(),
            tvec=self._tvec.copy(),
            useExtrinsicGuess=True,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            raise RuntimeError("solvePnP failed during Z refinement.")

        proj, _ = cv2.projectPoints(
            combined_obj, rvec, tvec, self._camera_matrix, zero_dist
        )
        rms = float(np.sqrt(np.mean((combined_img - proj.reshape(-1, 2)) ** 2)))
        n_inliers = len(combined_obj)

        self._rvec = rvec
        self._tvec = tvec
        self._calib_obj_pts = combined_obj
        self._calib_img_pts = combined_img
        self._calib_board_idx = combined_board_idx

        R, _ = cv2.Rodrigues(rvec)
        cam_pos = (-R.T @ tvec).flatten()
        print(
            f"Refined calibration: {n_inliers} pts, "
            f"RMS {rms:.2f} px,  camera at Z={cam_pos[2]:.1f} mm"
        )

        if save_path is not None:
            self.save_calibration(save_path)

        return rvec, tvec

    def flip_y_axis(self, save_path=None):
        """Flip the board Y axis and re-run solvePnP.

        Call this after ``calibrate_3d_charuco()`` if the Y axis appears
        mirrored or inverted. Negates ``_board_y_unit``, recomputes all stored
        object points, and refits the camera pose.

        :param save_path: If provided, save the updated calibration to this path.
        :type save_path: str, optional
        """
        if self._rvec is None or self._calib_obj_pts is None:
            raise RuntimeError(
                "No calibration to flip. Run calibrate_3d_charuco() first."
            )
        if not hasattr(self, "_calib_board_geoms") or not self._calib_board_geoms:
            raise RuntimeError(
                "Board geometry not stored. Re-run calibrate_3d_charuco()."
            )

        sq = self._board_square_mm

        # Negate Y unit for all boards
        new_geoms = []
        for a_b, x_b, y_b in self._calib_board_geoms:
            new_geoms.append((a_b, x_b, -np.array(y_b)))
        self._calib_board_geoms = new_geoms
        self._board_y_unit = -np.array(self._board_y_unit)

        # Recompute each object point using its own board's geometry
        new_obj = []
        for i, pt in enumerate(self._calib_obj_pts):
            b_idx = int(self._calib_board_idx[i])
            a_b, x_b, y_b_new = self._calib_board_geoms[b_idx]
            y_b_old = -y_b_new  # y_unit before negation
            diff2 = pt[:2] - a_b
            col = round(np.dot(diff2, x_b) / sq)
            row = round(np.dot(diff2, y_b_old) / sq)
            z = pt[2]
            new_obj.append(
                [
                    a_b[0] + col * sq * x_b[0] + row * sq * y_b_new[0],
                    a_b[1] + col * sq * x_b[1] + row * sq * y_b_new[1],
                    z,
                ]
            )

        self._calib_obj_pts = np.array(new_obj, dtype=np.float64)

        zero_dist = np.zeros_like(self._dist_coeffs)
        z_vals = self._calib_obj_pts[:, 2]
        is_coplanar = bool(np.ptp(z_vals) < 0.5)

        if is_coplanar:
            # IPPE analytically returns both solutions; pick most-negative camera Z.
            retval, rvecs_m, tvecs_m, _ = cv2.solvePnPGeneric(
                self._calib_obj_pts,
                self._calib_img_pts,
                self._camera_matrix,
                zero_dist,
                flags=cv2.SOLVEPNP_IPPE,
            )
            if retval == 0:
                raise RuntimeError("IPPE failed after flipping Y axis.")
            rvec, tvec = rvecs_m[0], tvecs_m[0]
            best_cz = np.inf
            for rv_i, tv_i in zip(rvecs_m, tvecs_m):
                if float(tv_i[2]) > 0:
                    R_i, _ = cv2.Rodrigues(rv_i)
                    cz = float((-R_i.T @ tv_i).flatten()[2])
                    if cz < best_cz:
                        best_cz, rvec, tvec = cz, rv_i, tv_i
            # Refine with LM from the IPPE solution
            ok, rvec, tvec = cv2.solvePnP(
                self._calib_obj_pts,
                self._calib_img_pts,
                self._camera_matrix,
                zero_dist,
                rvec=rvec,
                tvec=tvec,
                useExtrinsicGuess=True,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
        else:
            # Non-coplanar (after refine_calibration_z): use SQPNP global solver
            # then refine with LM.
            retval, rvecs_m, tvecs_m, _ = cv2.solvePnPGeneric(
                self._calib_obj_pts,
                self._calib_img_pts,
                self._camera_matrix,
                zero_dist,
                flags=cv2.SOLVEPNP_SQPNP,
            )
            if retval == 0:
                raise RuntimeError("SQPNP failed after flipping Y axis.")
            ok, rvec, tvec = cv2.solvePnP(
                self._calib_obj_pts,
                self._calib_img_pts,
                self._camera_matrix,
                zero_dist,
                rvec=rvecs_m[0],
                tvec=tvecs_m[0],
                useExtrinsicGuess=True,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
        if not ok:
            raise RuntimeError("solvePnP failed after flipping Y axis.")

        proj, _ = cv2.projectPoints(
            self._calib_obj_pts, rvec, tvec, self._camera_matrix, zero_dist
        )
        per_pt_err = np.sqrt(
            np.sum((self._calib_img_pts - proj.reshape(-1, 2)) ** 2, axis=1)
        )
        rms = float(np.sqrt(np.mean(per_pt_err**2)))
        n_good = int(np.sum(per_pt_err < 2.0))

        self._rvec = rvec
        self._tvec = tvec

        R, _ = cv2.Rodrigues(rvec)
        cam_pos = (-R.T @ tvec).flatten()
        print(
            f"Y axis flipped: {n_good}/{len(self._calib_obj_pts)} within 2px, "
            f"RMS {rms:.2f} px,  camera at Z={cam_pos[2]:.1f} mm"
        )

        if save_path is not None:
            self.save_calibration(save_path)

    def save_calibration(self, path: str):
        """Save all calibration data to a ``.npz`` file.

        Saves whichever of the following are available: 2D homographies,
        lens intrinsics, and 3D pose (rvec/tvec).

        :param path: Destination file path (e.g. ``"calibration.npz"``)
        :type path: str
        """
        data = {}
        if self._homography is not None:
            data["homography"] = self._homography
            data["homography_inv"] = self._homography_inv
        if self._camera_matrix is not None:
            data["camera_matrix"] = self._camera_matrix
            data["dist_coeffs"] = self._dist_coeffs
        if self._rvec is not None:
            data["rvec"] = self._rvec
            data["tvec"] = self._tvec
        if self._board_origin is not None:
            data["board_origin"] = self._board_origin
            data["board_x_unit"] = self._board_x_unit
            data["board_y_unit"] = self._board_y_unit
            data["board_square_mm"] = np.array([self._board_square_mm])
            data["board_n_cx"] = np.array([self._board_n_cx])
            data["board_n_markers"] = np.array([self._board_n_markers])
        if self._calib_obj_pts is not None:
            data["calib_obj_pts"] = self._calib_obj_pts
            data["calib_img_pts"] = self._calib_img_pts
            data["calib_board_idx"] = self._calib_board_idx
        if self._calib_board_geoms:
            data["board_geoms_a"] = np.array([g[0] for g in self._calib_board_geoms])
            data["board_geoms_x"] = np.array([g[1] for g in self._calib_board_geoms])
            data["board_geoms_y"] = np.array([g[2] for g in self._calib_board_geoms])
        if self._z_cal_stack:
            data["z_cal_stack_z"] = np.array([e[0] for e in self._z_cal_stack])
            data["z_cal_stack_rvecs"] = np.array([e[1] for e in self._z_cal_stack])
            data["z_cal_stack_tvecs"] = np.array([e[2] for e in self._z_cal_stack])
        np.savez(path, **data)
        print(f"Calibration saved to {path}")

    def load_calibration(self, path: str):
        """Load calibration data from a ``.npz`` file.

        :param path: Path to the ``.npz`` calibration file
        :type path: str
        """
        data = np.load(path)
        if "homography" in data:
            self._homography = data["homography"]
            self._homography_inv = data["homography_inv"]
        if "camera_matrix" in data:
            self._camera_matrix = data["camera_matrix"]
            self._dist_coeffs = data["dist_coeffs"]
        if "rvec" in data:
            self._rvec = data["rvec"]
            self._tvec = data["tvec"]
        if "board_origin" in data:
            self._board_origin = data["board_origin"]
            self._board_x_unit = data["board_x_unit"]
            self._board_y_unit = data["board_y_unit"]
            self._board_square_mm = float(data["board_square_mm"][0])
            self._board_n_cx = int(data["board_n_cx"][0])
            self._board_n_markers = int(data["board_n_markers"][0])
        if "calib_obj_pts" in data:
            self._calib_obj_pts = data["calib_obj_pts"]
            self._calib_img_pts = data["calib_img_pts"]
            self._calib_board_idx = data["calib_board_idx"]
        if "board_geoms_a" in data:
            n = len(data["board_geoms_a"])
            self._calib_board_geoms = [
                (
                    data["board_geoms_a"][i],
                    data["board_geoms_x"][i],
                    data["board_geoms_y"][i],
                )
                for i in range(n)
            ]
        if "z_cal_stack_z" in data:
            zs = data["z_cal_stack_z"]
            rvecs = data["z_cal_stack_rvecs"]
            tvecs = data["z_cal_stack_tvecs"]
            self._z_cal_stack = [
                (float(zs[i]), rvecs[i], tvecs[i]) for i in range(len(zs))
            ]
        print(f"Calibration loaded from {path}")

    def load_lens_calibration(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        """Provide lens intrinsic calibration.

        Required before calling :meth:`calibrate_3d`. If set, frames are
        automatically undistorted in :meth:`get_frame`.

        Obtain these values from a standard OpenCV checkerboard calibration.

        :param camera_matrix: 3×3 intrinsic camera matrix
        :type camera_matrix: np.ndarray
        :param dist_coeffs: Distortion coefficients (k1, k2, p1, p2[, k3])
        :type dist_coeffs: np.ndarray
        """
        self._camera_matrix = camera_matrix
        self._dist_coeffs = dist_coeffs

    @property
    def is_calibrated(self) -> bool:
        """``True`` if a 2D pixel-to-machine homography is available."""
        return self._homography is not None

    @property
    def is_calibrated_3d(self) -> bool:
        """``True`` if a 3D camera pose (rvec/tvec) is available."""
        return self._rvec is not None

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def pixel_to_machine(
        self, px: float, py: float, z: Optional[float] = None
    ) -> Tuple[float, float]:
        """Convert pixel coordinates to machine (x, y) coordinates in mm.

        If ``z`` is provided and 3D calibration is available, uses ray-plane
        intersection for Z-aware conversion — accurate at any bed height.

        If ``z`` is omitted or only 2D calibration is available, falls back to
        the homography — accurate only at the calibration Z height.

        :param px: Pixel x coordinate
        :type px: float
        :param py: Pixel y coordinate
        :type py: float
        :param z: Z height (mm) of the target plane in machine coordinates.
            Required for Z-aware 3D conversion.
        :type z: float, optional
        :return: Machine ``(x, y)`` in mm
        :rtype: Tuple[float, float]
        :raises RuntimeError: If no calibration is available
        """
        if z is not None and self.is_calibrated_3d:
            return self._pixel_to_machine_3d(px, py, z)

        self._require_calibration()
        pt = np.array([[[px, py]]], dtype=np.float64)
        result = cv2.perspectiveTransform(pt, self._homography)
        mx, my = result[0][0]
        return float(mx), float(my)

    def machine_to_pixel(
        self, mx: float, my: float, mz: float = 0.0
    ) -> Tuple[float, float]:
        """Convert machine coordinates to pixel coordinates.

        If 3D calibration is available, uses ``cv2.projectPoints`` and correctly
        accounts for the Z height of the point. Otherwise falls back to the 2D
        homography (``mz`` is ignored).

        :param mx: Machine x coordinate in mm
        :type mx: float
        :param my: Machine y coordinate in mm
        :type my: float
        :param mz: Machine z coordinate in mm, defaults to 0.0
        :type mz: float, optional
        :return: Pixel ``(x, y)``
        :rtype: Tuple[float, float]
        :raises RuntimeError: If no calibration is available
        """
        if self.is_calibrated_3d:
            pts_3d = np.array([[[mx, my, mz]]], dtype=np.float64)
            # Calibration was done on undistorted frames, so project into
            # undistorted pixel space (zero dist_coeffs).
            zero_dist = np.zeros_like(self._dist_coeffs)
            pts_2d, _ = cv2.projectPoints(
                pts_3d,
                self._rvec,
                self._tvec,
                self._camera_matrix,
                zero_dist,
            )
            px, py = pts_2d[0][0]
            return float(px), float(py)

        self._require_calibration()
        pt = np.array([[[mx, my]]], dtype=np.float64)
        result = cv2.perspectiveTransform(pt, self._homography_inv)
        px, py = result[0][0]
        return float(px), float(py)

    # ------------------------------------------------------------------
    # Machine movement based on camera detections
    # ------------------------------------------------------------------

    def move_to_pixel(
        self,
        px: float,
        py: float,
        z_target: Optional[float] = None,
        z_move: Optional[float] = None,
        wait: bool = True,
    ):
        """Move the machine to the position corresponding to a pixel coordinate.

        ``z_target`` is the Z height of the object being detected — used for
        coordinate conversion when 3D calibration is active. ``z_move`` is the
        Z height the machine actually moves to, which may differ (e.g. detect
        an object sitting on the bed at z=0, but move the tool to z=10 to
        avoid crashing into it).

        If ``z_move`` is omitted, it defaults to ``z_target``; if both are
        omitted, :attr:`focus_height` is used for movement and the 2D
        homography is used for conversion.

        :param px: Target pixel x coordinate
        :type px: float
        :param py: Target pixel y coordinate
        :type py: float
        :param z_target: Z height of the detected object in machine coordinates,
            used for 3D coordinate conversion. Defaults to ``z_move``.
        :type z_target: float, optional
        :param z_move: Z height to move the machine to. Defaults to ``z_target``
            or :attr:`focus_height`.
        :type z_move: float, optional
        :param wait: Wait for machine movement to complete, defaults to True
        :type wait: bool, optional
        """
        # Resolve z_target for coordinate conversion.
        # If not provided and 3D calibration is available, read current machine Z.
        coord_z = z_target if z_target is not None else z_move
        if coord_z is None and self._rvec is not None and hasattr(self, "_machine"):
            pos = self._machine.get_position()
            z_carriage = float(pos["Z"])
            active_idx = self._machine.active_tool_index
            if active_idx != -1 and active_idx in self._machine.tools:
                tool_offset = self._machine.tools[active_idx]["tool"].tool_offset
                coord_z = (
                    z_carriage + abs(tool_offset)
                    if tool_offset is not None
                    else z_carriage
                )
            else:
                coord_z = z_carriage
        mx, my = self.pixel_to_machine(px, py, z=coord_z)
        self._move_machine_xy(mx, my, z=z_move, wait=wait)

    def move_to_detection(
        self,
        marker_id: int,
        frame: Optional[np.ndarray] = None,
        z_target: Optional[float] = None,
        z_move: Optional[float] = None,
        wait: bool = True,
    ):
        """Detect a specific ArUco marker and move the machine to its center.

        :param marker_id: The ArUco marker ID to locate and move to
        :type marker_id: int
        :param frame: Use this frame instead of capturing a new one, defaults to None
        :type frame: np.ndarray, optional
        :param z_target: Z height of the marker in machine coordinates, for 3D
            coordinate conversion. Defaults to ``z_move``.
        :type z_target: float, optional
        :param z_move: Z height to move the machine to. Defaults to
            :attr:`focus_height`.
        :type z_move: float, optional
        :param wait: Wait for machine movement to complete, defaults to True
        :type wait: bool, optional
        :raises ValueError: If the requested marker is not found in the frame
        """
        if not self.is_calibrated and not self.is_calibrated_3d:
            raise RuntimeError(
                "Camera not calibrated. Call calibrate(), calibrate_3d(), "
                "or load_calibration() first."
            )
        corners, ids, _ = self.detect_aruco(frame)

        if ids is None or marker_id not in ids.flatten():
            raise ValueError(
                f"Marker ID {marker_id} not detected. "
                f"Detected IDs: {ids.flatten().tolist() if ids is not None else []}"
            )

        idx = list(ids.flatten()).index(marker_id)
        center = corners[idx][0].mean(axis=0)
        self.move_to_pixel(
            float(center[0]),
            float(center[1]),
            z_target=z_target,
            z_move=z_move,
            wait=wait,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_calibration(self):
        if not self.is_calibrated:
            raise RuntimeError(
                "Camera not calibrated. Call calibrate(), calibrate_3d(), "
                "or load_calibration() first."
            )

    def _pixel_to_machine_3d(
        self, px: float, py: float, z_target: float
    ) -> Tuple[float, float]:
        """Ray-plane intersection: pixel + known Z → machine (x, y).

        Casts a ray from the camera through pixel ``(px, py)`` and finds where
        it intersects the horizontal plane ``Z = z_target`` in machine space.

        :param px: Pixel x coordinate
        :param py: Pixel y coordinate
        :param z_target: Z height of the target plane in machine coordinates (mm)
        :raises RuntimeError: If the ray is parallel to the target plane
        """
        # The pixel is already in undistorted space (get_frame undistorts).
        # Apply K^-1 to get a normalized camera-space ray direction.
        K = self._camera_matrix
        ray_cam = np.array(
            [
                (px - K[0, 2]) / K[0, 0],
                (py - K[1, 2]) / K[1, 1],
                1.0,
            ]
        )

        # Select calibration: use nearest-Z entry from z_cal_stack if available
        if self._z_cal_stack:
            best = min(self._z_cal_stack, key=lambda e: abs(e[0] - z_target))
            rvec_use, tvec_use = best[1], best[2]
        else:
            rvec_use, tvec_use = self._rvec, self._tvec

        # Camera pose: R rotates from camera space to world space
        R, _ = cv2.Rodrigues(rvec_use)

        # Ray direction in world (machine) space
        ray_world = R.T @ ray_cam

        # Camera position in world space: C = -R^T * t
        cam_pos = (-R.T @ tvec_use).flatten()

        # Intersect ray with plane Z = z_target
        # cam_pos[2] + t * ray_world[2] = z_target  →  solve for t
        if abs(ray_world[2]) < 1e-10:
            raise RuntimeError(
                f"Ray through pixel ({px}, {py}) is parallel to the target "
                f"plane Z={z_target} and does not intersect it."
            )
        t = (z_target - cam_pos[2]) / ray_world[2]
        world_pt = cam_pos + t * ray_world

        return float(world_pt[0]), float(world_pt[1])

    def _move_machine_xy(
        self,
        mx: float,
        my: float,
        z: Optional[float] = None,
        wait: bool = True,
    ):
        target_z = z if z is not None else self.focus_height
        # self._machine.safe_z_movement()
        self._machine.move_to(x=mx, y=my, wait=wait)
