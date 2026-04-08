"""Hardware-agnostic image processing utilities.

All functions are pure — they take numpy arrays or bytes as input and return
processed results.  No camera or robot dependency.
"""

import cv2
import matplotlib.pyplot as plt
import numpy as np


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode binary image data (e.g. from an HTTP response) into an RGB ndarray.

    :param image_bytes: Raw image bytes (JPEG, PNG, etc.)
    :type image_bytes: bytes
    :return: Decoded image in RGB channel order
    :rtype: np.ndarray
    """
    image_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
    # OpenCV loads as BGR — convert to RGB
    image_rgb = image[:, :, [2, 1, 0]]
    return image_rgb


def show_image(image: np.ndarray, save: bool = False, save_path: str = "fig.png"):
    """Display an image inline in a Jupyter notebook.

    :param image: Image array (RGB)
    :type image: np.ndarray
    :param save: Save to file, defaults to False
    :type save: bool, optional
    :param save_path: File path to save image, defaults to "fig.png"
    :type save_path: str, optional
    """
    from PIL import Image
    from IPython.display import display

    pil_image = Image.fromarray(image)
    if save:
        pil_image.save(save_path)
    display(pil_image)


def view_image_file(filepath: str):
    """Load and display an image file using matplotlib.

    :param filepath: Path to the image file
    :type filepath: str
    """
    image = cv2.imread(filepath)
    if image is not None:
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.show()
    else:
        raise FileNotFoundError(f"Failed to load image from {filepath}")


def mask_circle(image: np.ndarray, radius: int = 50) -> np.ndarray:
    """Apply a circular mask centered on the image.

    :param image: Input image array
    :type image: np.ndarray
    :param radius: Radius of the circular mask in pixels, defaults to 50
    :type radius: int, optional
    :return: Masked image (pixels outside the circle are zeroed)
    :rtype: np.ndarray
    """
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    mask = np.zeros((h, w), dtype="uint8")
    cv2.circle(mask, center, radius, 255, -1)
    masked = cv2.bitwise_and(image, image, mask=mask)
    return masked


def get_rgb_average(image: np.ndarray) -> list:
    """Compute mean RGB values of non-zero pixels in an image.

    Useful after applying a mask — only the unmasked region contributes to
    the average.

    :param image: Input image array (RGB)
    :type image: np.ndarray
    :return: Average [R, G, B] values
    :rtype: list
    """
    rgb = []
    for channel in range(3):
        flat = image[:, :, channel].flatten()
        nonzero = flat[flat.nonzero()]
        rgb.append(float(nonzero.mean()) if len(nonzero) > 0 else 0.0)
    return rgb


def load_calibration(path: str) -> tuple:
    """Load camera matrix and distortion coefficients from a YAML file.

    Expects a YAML file with ``K`` (camera matrix) and ``D`` (distortion
    coefficients) entries, each containing a ``data`` list.

    :param path: Path to the calibration YAML file
    :type path: str
    :return: (camera_matrix, dist_coefficients) as numpy arrays
    :rtype: tuple[np.ndarray, np.ndarray]
    """
    import yaml

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    k_data = config["K"]["data"]
    camera_matrix = np.array(
        [k_data[i : i + 3] for i in range(0, len(k_data), 3)], dtype=np.float64
    )

    d_data = config["D"]["data"]
    dist_coefficients = np.array(d_data, dtype=np.float64)

    return camera_matrix, dist_coefficients


def undistort(
    image: np.ndarray,
    camera_matrix: np.ndarray,
    dist_coefficients: np.ndarray,
) -> np.ndarray:
    """Remove lens distortion from an image.

    :param image: Input image array
    :type image: np.ndarray
    :param camera_matrix: 3x3 camera intrinsic matrix
    :type camera_matrix: np.ndarray
    :param dist_coefficients: Distortion coefficients
    :type dist_coefficients: np.ndarray
    :return: Undistorted image
    :rtype: np.ndarray
    """
    return cv2.undistort(image, camera_matrix, dist_coefficients, None, camera_matrix)
