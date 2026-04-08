"""Generate a calibration checkerboard sized for the Jubilee overhead camera.

Defaults match calibrate_birdseye_camera.py (9x6 board, 20mm squares).
Outputs a PNG at 300 DPI — print at 100% scale, do not scale to fit.

Usage:
    python generate_checkerboard.py
    python generate_checkerboard.py --cols 9 --rows 6 --square-mm 30
"""

import argparse
import os
import numpy as np
import cv2


DPI = 300
MM_PER_INCH = 25.4


def generate_checkerboard(cols: int, rows: int, square_mm: float, output: str):
    px_per_mm = DPI / MM_PER_INCH
    square_px = round(square_mm * px_per_mm)

    board_w = cols * square_px
    board_h = rows * square_px

    # White canvas with a margin for cutting/mounting
    margin_px = round(10 * px_per_mm)   # 10mm margin all around
    canvas_w = board_w + 2 * margin_px
    canvas_h = board_h + 2 * margin_px

    canvas = np.full((canvas_h, canvas_w), 255, dtype=np.uint8)

    # Draw squares
    for row in range(rows):
        for col in range(cols):
            if (row + col) % 2 == 0:
                x0 = margin_px + col * square_px
                y0 = margin_px + row * square_px
                canvas[y0:y0 + square_px, x0:x0 + square_px] = 0

    # Label: print instructions at the bottom margin
    label = (
        f"{cols}x{rows} board  |  {square_mm:.0f}mm squares  |  "
        f"Print at 100% scale (no fit-to-page)  |  {DPI} DPI"
    )
    font_scale = margin_px / 60
    thickness = max(1, round(font_scale))
    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    text_x = max(2, (canvas_w - text_size[0]) // 2)
    text_y = canvas_h - round(3 * px_per_mm)
    cv2.putText(canvas, label, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, 0, thickness, cv2.LINE_AA)

    cv2.imwrite(output, canvas)

    w_mm = cols * square_mm
    h_mm = rows * square_mm
    interior_cols = cols - 1
    interior_rows = rows - 1
    print(f"Saved '{output}'")
    print(f"  Board:           {cols}x{rows} squares  ({interior_cols}x{interior_rows} interior corners)")
    print(f"  Printed size:    {w_mm:.0f} x {h_mm:.0f} mm  ({w_mm/MM_PER_INCH:.2f} x {h_mm/MM_PER_INCH:.2f} in)")
    print(f"  Image size:      {canvas_w} x {canvas_h} px at {DPI} DPI")
    print()
    print("In calibrate_birdseye_camera.py use:")
    print(f"    --corners {interior_cols} {interior_rows} --square-mm {square_mm:.0f}")


def main():
    parser = argparse.ArgumentParser(description="Generate calibration checkerboard")
    parser.add_argument("--cols", type=int, default=9,
                        help="Number of squares across (default: 9)")
    parser.add_argument("--rows", type=int, default=6,
                        help="Number of squares down (default: 6)")
    parser.add_argument("--square-mm", type=float, default=20.0,
                        help="Square size in mm (default: 20)")
    parser.add_argument("--output", default="checkerboard.png",
                        help="Output filename (default: checkerboard.png)")
    args = parser.parse_args()

    generate_checkerboard(args.cols, args.rows, args.square_mm, args.output)


if __name__ == "__main__":
    main()
