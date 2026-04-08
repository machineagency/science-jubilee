"""Generate ChArUco calibration boards for BirdseyeCamera machine calibration.

Generates one board per output file, each using a non-overlapping range of
ArUco marker IDs so all boards can be detected simultaneously in a single frame.
Uses DICT_4X4_100 (100 markers) to accommodate up to ~3 boards.

Usage:
    python generate_charuco_board.py              # generates 3 boards
    python generate_charuco_board.py --count 1    # single board
    python generate_charuco_board.py --cols 9 --rows 6 --square-mm 20

Output:
    charuco_board_1.png, charuco_board_2.png, ... — print each at 100% scale
    (no fit-to-page), 300 DPI. Glue or tape flat to rigid backing.

Calibration workflow (notebook):
    1. Tape boards flat on the bed, spread across the full bed area.
    2. Jog tool tip to dot A on board 1, call cam.collect_calibration_point().
    3. Jog to dot B on board 1, call cam.collect_calibration_point().
    4. Repeat for each board.
    5. cam.calibrate_3d_charuco(
           boards=[(a1,b1), (a2,b2), (a3,b3)],
           board_cols=9, board_rows=6, square_mm=20,
       )

Dot A = interior corner (col=0, row=0): one square in from the A side.
Dot B = interior corner (col=board_cols-2, row=0): one square in from the B side.
"""

import argparse
import math

import cv2
import numpy as np

DPI = 300
MM_PER_INCH = 25.4
MARKER_FRACTION = 0.75
ARUCO_DICT = cv2.aruco.DICT_4X4_100  # must match calibrate_3d_charuco


def _n_markers(cols: int, rows: int) -> int:
    """Number of ArUco markers on a cols×rows ChArUco board."""
    return math.ceil(cols * rows / 2)


def generate_board(
    cols: int,
    rows: int,
    square_mm: float,
    board_index: int,      # 1-based, used for ID offset and filename label
    output: str,
):
    px_per_mm = DPI / MM_PER_INCH
    square_px = round(square_mm * px_per_mm)
    margin_px = round(10 * px_per_mm)
    label_height_px = round(12 * px_per_mm)

    board_w_px = cols * square_px
    board_h_px = rows * square_px
    canvas_w = board_w_px + 2 * margin_px
    canvas_h = board_h_px + 2 * margin_px + label_height_px

    # Assign non-overlapping marker IDs for this board
    n_m = _n_markers(cols, rows)
    first_id = (board_index - 1) * n_m
    marker_ids = np.arange(first_id, first_id + n_m, dtype=np.int32)

    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    board = cv2.aruco.CharucoBoard(
        (cols, rows), square_mm, square_mm * MARKER_FRACTION, aruco_dict, marker_ids
    )
    board_img = board.generateImage((board_w_px, board_h_px), marginSize=0, borderBits=1)

    canvas = np.full((canvas_h, canvas_w), 255, dtype=np.uint8)
    canvas[margin_px : margin_px + board_h_px, margin_px : margin_px + board_w_px] = board_img

    # Reference corner dots
    #   interior corner (col, row) is at pixel (margin + (col+1)*sq, margin + (row+1)*sq)
    n_cx = cols - 1
    a_px = (margin_px + square_px,              margin_px + square_px)   # col=0, row=0
    b_px = (margin_px + n_cx * square_px,       margin_px + square_px)   # col=n_cx-1, row=0

    dot_r = round(3.5 * px_per_mm)
    outline_r = dot_r + round(1.5 * px_per_mm)
    for pt in (a_px, b_px):
        cv2.circle(canvas, pt, outline_r, 255, -1)  # white outline
        cv2.circle(canvas, pt, dot_r, 0, -1)        # black dot

    # Side labels "A" and "B" in the bottom margin
    font = cv2.FONT_HERSHEY_SIMPLEX
    side_fs = margin_px / 35
    side_th = max(1, round(side_fs * 1.2))
    label_y = canvas_h - round(3 * px_per_mm)

    for text, x_anchor in [("A", margin_px), ("B", canvas_w - margin_px)]:
        (tw, _), _ = cv2.getTextSize(text, font, side_fs, side_th)
        tx = x_anchor - tw // 2
        cv2.putText(canvas, text, (tx, label_y), font, side_fs, 0, side_th, cv2.LINE_AA)

    # Centre info label
    info = (
        f"Board {board_index}  |  {cols}x{rows} ChArUco  |  {square_mm:.0f}mm squares  |  "
        f"100% scale  |  {DPI} DPI  |  IDs {first_id}–{first_id+n_m-1}"
    )
    info_fs = margin_px / 75
    info_th = max(1, round(info_fs))
    (iw, _), _ = cv2.getTextSize(info, font, info_fs, info_th)
    cv2.putText(canvas, info, ((canvas_w - iw) // 2, label_y),
                font, info_fs, 0, info_th, cv2.LINE_AA)

    cv2.imwrite(output, canvas)

    w_mm = cols * square_mm
    h_mm = rows * square_mm
    print(f"Saved '{output}'  (board {board_index}, ArUco IDs {first_id}–{first_id+n_m-1})")
    print(f"  Printed size: {w_mm:.0f} × {h_mm:.0f} mm")
    print(f"  Dot A (•): interior corner col=0, row=0  — jog here first")
    print(f"  Dot B (•): interior corner col={n_cx-1}, row=0  — jog here second")


def main():
    parser = argparse.ArgumentParser(description="Generate ChArUco calibration boards")
    parser.add_argument("--cols", type=int, default=9, help="Squares across (default: 9)")
    parser.add_argument("--rows", type=int, default=6, help="Squares down (default: 6)")
    parser.add_argument("--square-mm", type=float, default=20.0, help="Square size in mm (default: 20)")
    parser.add_argument("--count", type=int, default=3, help="Number of boards to generate (default: 3)")
    args = parser.parse_args()

    n_m = _n_markers(args.cols, args.rows)
    max_boards = 100 // n_m
    if args.count > max_boards:
        raise SystemExit(
            f"DICT_4X4_100 only has 100 marker IDs; "
            f"a {args.cols}×{args.rows} board uses {n_m} IDs, "
            f"so max {max_boards} boards are supported."
        )

    for i in range(1, args.count + 1):
        output = f"charuco_board_{i}.png"
        generate_board(args.cols, args.rows, args.square_mm, i, output)
        print()

    print(f"In BirdseyeCamera use:")
    print(f"  cam.calibrate_3d_charuco(")
    print(f"      boards=[(a1, b1), (a2, b2), ...],")
    print(f"      board_cols={args.cols}, board_rows={args.rows}, square_mm={args.square_mm:.0f},")
    print(f"  )")


if __name__ == "__main__":
    main()
