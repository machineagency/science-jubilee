"""Intrinsic lens calibration for BirdseyeCamera.

Two-step script:
    1. Collect calibration images from your USB webcam
    2. Run calibration and verify the result

Usage:
    # Step 1 — collect images (press SPACE to capture, ESC to finish)
    python calibrate_birdseye_camera.py collect

    # Step 2 — calibrate and verify
    python calibrate_birdseye_camera.py calibrate

    # Step 2 with non-default options
    python calibrate_birdseye_camera.py calibrate --corners 8 5 --square-mm 25

Output:
    lens_calibration.npz  — camera_matrix and dist_coeffs, ready to pass to
                            cam.load_lens_calibration()

Checkerboard:
    Print a standard OpenCV checkerboard. The default here assumes a 9x6 board
    (8x5 interior corners, 25mm squares = 200x125mm total). This is a good size
    for a Jubilee overhead camera. Glue or tape the printout flat to a rigid
    backing — any warping in the board degrades calibration quality.

    Cover the full frame during collection:
      - Move the board to all four corners of the frame
      - Tilt it at ~30-45 degrees in both X and Y
      - Vary the distance (closer and farther)
      - 20-30 images is sufficient
"""

import argparse
import glob
import os
import sys

import cv2
import numpy as np


# -----------------------------------------------------------------------
# Defaults — adjust to match your printed checkerboard
# -----------------------------------------------------------------------
DEFAULT_CORNERS = (8, 5)  # interior corners (cols-1, rows-1)
DEFAULT_SQUARE_MM = 27.0  # physical size of one square in mm
DEFAULT_CAMERA_INDEX = 0
DEFAULT_IMAGE_DIR = "calibration_images"
DEFAULT_OUTPUT = "lens_calibration.npz"
DEFAULT_WIDTH = 3264
DEFAULT_HEIGHT = 2448


# -----------------------------------------------------------------------
# Step 1: collect images
# -----------------------------------------------------------------------


def collect(camera_index: int, image_dir: str, width: int, height: int):
    """Capture calibration images interactively.

    Press SPACE to save a frame, ESC to finish.
    """
    os.makedirs(image_dir, exist_ok=True)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: could not open camera {camera_index}")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolution: requested {width}x{height}, got {actual_w}x{actual_h}")

    count = len(glob.glob(os.path.join(image_dir, "*.png")))
    print(f"Saving to '{image_dir}/'  ({count} images already present)")
    print("SPACE = capture frame    ESC = done")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        display = frame.copy()
        cv2.putText(
            display,
            f"Captured: {count}  |  SPACE=capture  ESC=done",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 200, 0),
            2,
        )
        cv2.imshow("Calibration capture", display)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        if key == 32:  # SPACE
            path = os.path.join(image_dir, f"frame_{count:03d}.png")
            cv2.imwrite(path, frame)
            print(f"  Saved {path}")
            count += 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. {count} images in '{image_dir}/'")


# -----------------------------------------------------------------------
# Step 2: calibrate and verify
# -----------------------------------------------------------------------


def calibrate(
    corners: tuple,
    square_mm: float,
    image_dir: str,
    output: str,
):
    """Run calibration from saved images and show verification."""
    images = sorted(glob.glob(os.path.join(image_dir, "*.png")))
    if not images:
        print(f"No images found in '{image_dir}/'  — run 'collect' first.")
        sys.exit(1)

    print(f"Found {len(images)} images in '{image_dir}/'")
    print(
        f"Checkerboard: {corners[0]}x{corners[1]} interior corners, "
        f"{square_mm}mm squares\n"
    )

    # Build the 3D object points for one checkerboard view
    objp = np.zeros((corners[0] * corners[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : corners[0], 0 : corners[1]].T.reshape(-1, 2)
    objp *= square_mm

    obj_points = []
    img_points = []
    image_size = None
    failed = []

    for path in images:
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_size = gray.shape[::-1]

        ret, found_corners = cv2.findChessboardCorners(gray, corners, None)
        if ret:
            refined = cv2.cornerSubPix(
                gray,
                found_corners,
                (11, 11),
                (-1, -1),
                criteria=(
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001,
                ),
            )
            obj_points.append(objp)
            img_points.append(refined)
        else:
            failed.append(os.path.basename(path))

    print(f"Corners detected:  {len(obj_points)}/{len(images)} images")
    if failed:
        print(f"Corners not found: {', '.join(failed)}")
    print()

    if len(obj_points) < 10:
        print("Need at least 10 successful detections for reliable calibration.")
        print("Collect more images and try again.")
        sys.exit(1)

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, image_size, None, None
    )

    # ---- Print results ----
    print("=" * 50)
    print(f"RMS reprojection error: {rms:.4f} px")
    if rms < 0.5:
        print("  Excellent (< 0.5 px)")
    elif rms < 1.0:
        print("  Good (0.5 – 1.0 px)")
    elif rms < 2.0:
        print("  Marginal (1.0 – 2.0 px) — consider recollecting images")
    else:
        print("  Poor (> 2.0 px) — recollect images with better coverage")

    print(f"\nCamera matrix:\n{camera_matrix}")
    print(f"\nDistortion coefficients:\n{dist_coeffs.ravel()}")
    print("=" * 50)

    # ---- Per-image reprojection errors ----
    print("\nPer-image reprojection error (px):")
    per_image_errors = []
    for i, (op, ip, rv, tv) in enumerate(zip(obj_points, img_points, rvecs, tvecs)):
        projected, _ = cv2.projectPoints(op, rv, tv, camera_matrix, dist_coeffs)
        err = np.sqrt(np.mean((ip - projected) ** 2))
        per_image_errors.append(err)
    for i, (path, err) in enumerate(
        zip(
            [p for p in images if os.path.basename(p) not in failed],
            per_image_errors,
        )
    ):
        flag = "  <-- outlier, consider removing" if err > 2 * rms else ""
        print(f"  {os.path.basename(path)}: {err:.4f} px{flag}")

    # ---- Save ----
    np.savez(output, camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
    print(f"\nCalibration saved to '{output}'")
    print("\nLoad in BirdseyeCamera:")
    print(f"    data = np.load('{output}')")
    print("    cam.load_lens_calibration(data['camera_matrix'], data['dist_coeffs'])")

    # ---- Visual verification ----
    print("\nShowing undistortion comparison.")
    print("Look for: straight lines that were curved, square checkerboard squares.")
    print("Press any key to advance, ESC to exit.\n")

    for path in images[:5]:  # show first 5
        img = cv2.imread(path)
        h, w = img.shape[:2]
        new_K, roi = cv2.getOptimalNewCameraMatrix(
            camera_matrix, dist_coeffs, (w, h), alpha=1
        )
        undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_K)

        # Draw detected corners on original
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners_found = cv2.findChessboardCorners(gray, corners, None)
        if ret:
            cv2.drawChessboardCorners(img, corners, corners_found, ret)

        combined = np.hstack([img, undistorted])
        label = f"{os.path.basename(path)} — original (left) vs undistorted (right)"
        cv2.putText(
            combined,
            label,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Verification", combined)
        key = cv2.waitKey(0) & 0xFF
        if key == 27:
            break

    cv2.destroyAllWindows()


# -----------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Intrinsic lens calibration for BirdseyeCamera"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # collect subcommand
    collect_parser = subparsers.add_parser("collect", help="Capture calibration images")
    collect_parser.add_argument(
        "--camera",
        type=int,
        default=DEFAULT_CAMERA_INDEX,
        help=f"OpenCV camera index (default: {DEFAULT_CAMERA_INDEX})",
    )
    collect_parser.add_argument(
        "--image-dir",
        default=DEFAULT_IMAGE_DIR,
        help=f"Directory to save images (default: {DEFAULT_IMAGE_DIR})",
    )
    collect_parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Capture width in pixels (default: {DEFAULT_WIDTH})",
    )
    collect_parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Capture height in pixels (default: {DEFAULT_HEIGHT})",
    )

    # calibrate subcommand
    cal_parser = subparsers.add_parser("calibrate", help="Run calibration from images")
    cal_parser.add_argument(
        "--corners",
        type=int,
        nargs=2,
        default=list(DEFAULT_CORNERS),
        metavar=("COLS", "ROWS"),
        help=f"Interior corner count cols rows (default: {DEFAULT_CORNERS[0]} {DEFAULT_CORNERS[1]})",
    )
    cal_parser.add_argument(
        "--square-mm",
        type=float,
        default=DEFAULT_SQUARE_MM,
        help=f"Physical square size in mm (default: {DEFAULT_SQUARE_MM})",
    )
    cal_parser.add_argument(
        "--image-dir",
        default=DEFAULT_IMAGE_DIR,
        help=f"Directory of calibration images (default: {DEFAULT_IMAGE_DIR})",
    )
    cal_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output .npz file (default: {DEFAULT_OUTPUT})",
    )

    args = parser.parse_args()

    if args.command == "collect":
        collect(args.camera, args.image_dir, args.width, args.height)
    elif args.command == "calibrate":
        calibrate(
            corners=tuple(args.corners),
            square_mm=args.square_mm,
            image_dir=args.image_dir,
            output=args.output,
        )


if __name__ == "__main__":
    main()
