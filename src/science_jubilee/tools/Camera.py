"""Unified Camera tool with pluggable backends.

The ``"backend"`` key in the config JSON selects the hardware driver:

- ``"opencv"``   — USB webcam via OpenCV ``VideoCapture``
- ``"http"``     — remote Raspberry Pi camera server (HTTP)
- ``"picamera"`` — local Raspberry Pi camera via ``picamera`` library

Users interact only with the public :class:`Camera` class.
"""

import json
import os
import threading
import time
import webbrowser

import cv2
import numpy as np

from science_jubilee.tools.Tool import Tool, requires_active_tool

_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


def _find_config(filename: str, path: str = None) -> str:
    """Return the full path to a config file.

    If *path* is given explicitly, look there.  Otherwise check ``configs/user/``
    first (user-specific calibration), then fall back to ``configs/examples/``
    (shipped example files).
    """
    if path is not None:
        return os.path.join(path, filename)
    user = os.path.join(_CONFIGS_DIR, "user", filename)
    if os.path.isfile(user):
        return user
    return os.path.join(_CONFIGS_DIR, "examples", filename)


# ---------------------------------------------------------------------------
# Backends (private implementation details)
# ---------------------------------------------------------------------------


class _CameraBackend:
    """Abstract base for camera hardware backends."""

    def capture_frame(self) -> np.ndarray:
        """Capture a single frame and return it as an RGB ndarray."""
        raise NotImplementedError

    def record_video(self, filepath: str, duration: int):
        """Record video to *filepath* for *duration* seconds."""
        raise NotImplementedError("Video recording is not supported by this backend")

    def record_video_async(self, filepath: str, duration: int):
        """Record video asynchronously in a background thread."""
        raise NotImplementedError(
            "Async video recording is not supported by this backend"
        )

    def stop_video_recording(self):
        """Stop an in-progress async recording."""
        raise NotImplementedError

    def video_feed(self):
        """Open a browser-based video feed (HTTP backend only)."""
        raise NotImplementedError("Video feed is not supported by this backend")

    def release(self):
        """Release hardware resources."""
        pass


class _OpenCVBackend(_CameraBackend):
    """USB / local webcam via OpenCV ``VideoCapture``."""

    def __init__(self, camera_index: int = 0, **kwargs):
        self.camera_index = camera_index
        self.camera = cv2.VideoCapture(camera_index)
        self._stop_recording_flag = False
        self._video_thread = None

        if not self.camera.isOpened():
            raise RuntimeError(
                f"Could not open camera at index {camera_index}. "
                f"Check that your webcam is connected and try a different camera_index."
            )

        # Warm-up: some cameras need a few frames before they produce valid output
        for _ in range(5):
            self.camera.read()

        # Probe autofocus support
        self._has_autofocus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS) >= 0

    def capture_frame(self) -> np.ndarray:
        ret, frame = self.camera.read()
        if not ret:
            # Try reopening the camera once before giving up
            self.camera.release()
            self.camera = cv2.VideoCapture(self.camera_index)
            for _ in range(5):
                self.camera.read()
            ret, frame = self.camera.read()
            if not ret:
                raise RuntimeError(
                    f"Failed to capture frame from camera at index {self.camera_index}."
                )
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def record_video(self, filepath: str, duration: int = 10):
        """Record video to file."""
        # Use mp4v codec (.mp4) which is widely supported on macOS/Linux/Windows
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 20.0
        frame_size = (
            int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )

        # Ensure filepath uses .mp4 extension to match codec
        if filepath.endswith(".avi"):
            filepath = filepath[:-4] + ".mp4"

        out = cv2.VideoWriter(filepath, fourcc, fps, frame_size)
        if not out.isOpened():
            raise RuntimeError(
                f"Could not open video writer for {filepath}. "
                f"Check that the output directory exists."
            )

        # Verify camera is still readable
        ret, test_frame = self.camera.read()
        if not ret:
            out.release()
            raise RuntimeError("Camera is not producing frames. Try re-initializing.")

        out.write(test_frame)
        print(f"Recording video for {duration} seconds...")
        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = self.camera.read()
            if ret:
                out.write(frame)

        out.release()
        print(f"Video saved to {filepath}")

    def record_video_async(self, filepath: str, duration: float = None):
        self._stop_recording_flag = False
        self._video_thread = threading.Thread(
            target=self._record_video_worker, args=(filepath, duration)
        )
        self._video_thread.start()

    def _record_video_worker(self, filepath: str, duration: float = None):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 20.0
        frame_size = (
            int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        out = cv2.VideoWriter(filepath, fourcc, fps, frame_size)

        print("Recording...")
        start_time = time.time()
        while True:
            if self._stop_recording_flag:
                break
            if duration is not None and time.time() - start_time >= duration:
                break
            ret, frame = self.camera.read()
            if not ret:
                continue
            out.write(frame)

        out.release()
        elapsed = time.time() - start_time
        print(f"Video saved to {filepath} ({elapsed:.1f}s)")

    def stop_video_recording(self):
        self._stop_recording_flag = True
        if self._video_thread is not None:
            self._video_thread.join()
            self._video_thread = None
            print("Video recording thread stopped.")

    def release(self):
        self.camera.release()
        cv2.destroyAllWindows()

    # -- Focus control --

    def set_manual_focus(self, focus_value: int) -> bool:
        if not self._has_autofocus:
            print("This camera doesn't support focus control.")
            return False
        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        success = self.camera.set(cv2.CAP_PROP_FOCUS, focus_value)
        if success:
            print(f"Manual focus set to {focus_value}")
        else:
            print("Failed to set manual focus value")
        return bool(success)

    def enable_auto_focus(self) -> bool:
        if not self._has_autofocus:
            print("Auto-focus is not supported on this camera.")
            return False
        success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        if success:
            print("Auto-focus enabled.")
        else:
            print("Failed to enable auto-focus.")
        return bool(success)

    def disable_auto_focus(self) -> bool:
        if not self._has_autofocus:
            print("Auto-focus is not supported on this camera.")
            return False
        success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        if success:
            print("Auto-focus disabled.")
        else:
            print("Failed to disable auto-focus.")
        return bool(success)


class _HTTPBackend(_CameraBackend):
    """Remote Raspberry Pi camera server accessed over HTTP."""

    def __init__(
        self,
        ip_address: str,
        port: int,
        video_endpoint: str = "video_feed",
        still_endpoint: str = "picture",
        light: bool = False,
        light_pin: int = None,
        **kwargs,
    ):
        import requests as _requests

        self._requests = _requests
        self.ip_address = ip_address
        self.port = port
        self.still_url = f"http://{ip_address}:{port}/{still_endpoint}"
        self.video_url = f"http://{ip_address}:{port}/{video_endpoint}"
        self.light = light
        self.light_pin = light_pin

    def capture_frame(self, timeout: int = 30) -> np.ndarray:
        time.sleep(1)
        response = self._requests.get(self.still_url, timeout=timeout)
        time.sleep(2)
        if response.status_code != 200:
            raise RuntimeError(
                f"Camera server returned status {response.status_code}"
            )
        # Decode bytes to RGB ndarray
        image_arr = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def capture_raw(self, timeout: int = 30) -> bytes:
        """Return raw image bytes (useful when you need the original encoding)."""
        time.sleep(1)
        response = self._requests.get(self.still_url, timeout=timeout)
        time.sleep(2)
        if response.status_code != 200:
            raise RuntimeError(
                f"Camera server returned status {response.status_code}"
            )
        return response.content

    def video_feed(self):
        webbrowser.open(self.video_url)


class _PiCameraBackend(_CameraBackend):
    """Local Raspberry Pi camera via the ``picamera`` library."""

    def __init__(self, resolution: list = None, **kwargs):
        try:
            import picamera  # noqa: F401
        except ImportError:
            raise ImportError(
                "The picamera library is required for the 'picamera' backend. "
                "It is only available on Raspberry Pi (Linux)."
            )
        self._picamera = picamera
        self.resolution = tuple(resolution) if resolution else (1200, 1200)

    def capture_frame(self) -> np.ndarray:
        with self._picamera.PiCamera() as camera:
            camera.resolution = self.resolution
            camera.framerate = 24
            time.sleep(5)  # warm-up
            output = np.empty(
                (self.resolution[1], self.resolution[0], 3), dtype=np.uint8
            )
            camera.capture(output, "rgb", use_video_port=True)
            return np.transpose(output, axes=(1, 0, 2))


_BACKENDS = {
    "opencv": _OpenCVBackend,
    "http": _HTTPBackend,
    "picamera": _PiCameraBackend,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class Camera(Tool):
    """A unified camera tool supporting multiple hardware backends.

    The backend is selected via the ``"backend"`` key in the config JSON or
    the *backend* constructor argument.  All backends expose the same core
    API: ``capture()``, ``record()``, ``start_recording()``, ``stop_recording()``.

    :param Tool: The base tool class
    :type Tool: :class:`Tool`
    """

    def __init__(
        self,
        index: int,
        name: str,
        backend: str,
        focus_height: float = 100,
        output_dir: str = "./camera_output",
        **backend_kwargs,
    ):
        """Initialize the Camera.

        :param index: Tool index on the machine
        :type index: int
        :param name: Tool name
        :type name: str
        :param backend: Backend identifier — one of ``"opencv"``, ``"http"``, ``"picamera"``
        :type backend: str
        :param focus_height: Z-height for focusing, defaults to 100
        :type focus_height: float, optional
        :param output_dir: Directory for saved images/videos, defaults to "./camera_output"
        :type output_dir: str, optional
        :param backend_kwargs: Additional keyword arguments forwarded to the backend constructor
        """
        super().__init__(index, name, focus_height=focus_height)

        if backend not in _BACKENDS:
            raise ValueError(
                f"Unknown backend {backend!r}. Choose from: {list(_BACKENDS)}"
            )

        self._backend = _BACKENDS[backend](**backend_kwargs)
        self._backend_name = backend
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    @classmethod
    def from_config(cls, index: int, name: str, config_file: str, path: str = None):
        """Initialize from a JSON config file.

        :param index: Tool index on the machine
        :type index: int
        :param name: Tool name
        :type name: str
        :param config_file: Config filename (with or without ``.json`` extension)
        :type config_file: str
        :param path: Directory containing the config file.  If omitted,
            ``configs/user/`` is checked first, then ``configs/examples/``.
        :type path: str, optional
        :return: Initialized :class:`Camera`
        :rtype: :class:`Camera`
        """
        if not config_file.endswith(".json"):
            config_file += ".json"
        config_path = _find_config(config_file, path)
        with open(config_path, "rt") as f:
            kwargs = json.load(f)
        return cls(index=index, name=name, **kwargs)

    # -- Capture ---------------------------------------------------------------

    @requires_active_tool
    def capture(self, filename: str = "capture.jpg") -> str:
        """Capture a frame and save it to the output directory.

        :param filename: Output filename, defaults to "capture.jpg"
        :type filename: str, optional
        :return: Full path to the saved file
        :rtype: str
        """
        frame = self._backend.capture_frame()
        filepath = os.path.join(self.output_dir, filename)
        cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"Saved to {filepath}")
        return filepath

    @requires_active_tool
    def show_image(self):
        """Capture a frame and display it inline (Jupyter notebook).

        :return: Captured image as RGB ndarray
        :rtype: np.ndarray
        """
        from PIL import Image
        from IPython.display import display

        frame = self._backend.capture_frame()
        display(Image.fromarray(frame))
        return frame

    # -- Video -----------------------------------------------------------------

    @requires_active_tool
    def record(self, filename: str = "video.avi", duration: int = 10) -> str:
        """Record video and save to the output directory (blocking).

        Waits until recording is complete before returning.

        :param filename: Output filename, defaults to "video.avi"
        :type filename: str, optional
        :param duration: Recording duration in seconds, defaults to 10
        :type duration: int, optional
        :return: Full path to the saved file
        :rtype: str
        """
        filepath = os.path.join(self.output_dir, filename)
        self._backend.record_video(filepath, duration)
        return filepath

    @requires_active_tool
    def start_recording(self, filename: str = "video.mp4", duration: float = None):
        """Start recording video in the background (non-blocking).

        Returns immediately so you can move the machine or do other work
        while recording.  Call :meth:`stop_recording` to end.

        :param filename: Output filename, defaults to "video.mp4"
        :type filename: str, optional
        :param duration: Maximum recording duration in seconds. If None, records until stop_recording() is called.
        :type duration: float, optional
        """
        filepath = os.path.join(self.output_dir, filename)
        self._backend.record_video_async(filepath, duration)

    def stop_recording(self):
        """Stop an in-progress background recording."""
        self._backend.stop_video_recording()

    # -- Focus (OpenCV backend only) -------------------------------------------

    def set_manual_focus(self, focus_value: int) -> bool:
        """Set manual focus value (OpenCV backend only).

        :param focus_value: Focus value (typically 0–255)
        :type focus_value: int
        :return: Whether the operation succeeded
        :rtype: bool
        """
        if not hasattr(self._backend, "set_manual_focus"):
            print("Focus control is not supported by this backend.")
            return False
        return self._backend.set_manual_focus(focus_value)

    def enable_auto_focus(self) -> bool:
        """Enable auto-focus (OpenCV backend only)."""
        if not hasattr(self._backend, "enable_auto_focus"):
            print("Focus control is not supported by this backend.")
            return False
        return self._backend.enable_auto_focus()

    def disable_auto_focus(self) -> bool:
        """Disable auto-focus (OpenCV backend only)."""
        if not hasattr(self._backend, "disable_auto_focus"):
            print("Focus control is not supported by this backend.")
            return False
        return self._backend.disable_auto_focus()

    # -- Resource management ---------------------------------------------------

    def release(self):
        """Release hardware resources held by the backend."""
        self._backend.release()
