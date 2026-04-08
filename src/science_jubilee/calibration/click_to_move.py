"""Click-to-move demo for BirdseyeCamera.

Run from the repo root:
    python src/science_jubilee/calibration/click_to_move.py

Calibration is loaded automatically from the config file in peripherals/configs/user/.
Click anywhere in the video window to move the machine there.
Press Q or ESC to quit cleanly.
"""

import threading

import cv2

# ── Edit these to match your setup ──────────────────────────────────────────
MACHINE_ADDRESS = "192.168.1.2"
CONFIG_FILE = "BirdseyeCamera_config.json"  # must be in peripherals/configs/user/
WIN = "Click to move  —  Q / ESC to quit"
# ────────────────────────────────────────────────────────────────────────────

from science_jubilee.Machine import Machine
from science_jubilee.peripherals.BirdseyeCamera import BirdseyeCamera

machine = Machine(address=MACHINE_ADDRESS)
cam = BirdseyeCamera.from_config(CONFIG_FILE)
cam.attach(machine)

K = cam._camera_matrix
D = cam._dist_coeffs

h, w = cam.resolution[1], cam.resolution[0]
new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, (w, h), alpha=1)
map1, map2 = cv2.initUndistortRectifyMap(K, D, None, new_K, (w, h), cv2.CV_16SC2)

_pending = [None]
_moving = [False]
_last_click = [None]


def _mouse_cb(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and not _moving[0]:
        _pending[0] = (x, y)


def _move_worker(px, py):
    # Re-read Z_BED from current machine position in case bed has moved
    pos = machine.get_position()
    z_carriage = float(pos["Z"])
    active_idx = machine.active_tool_index
    if active_idx != -1 and active_idx in machine.tools:
        tool_offset = machine.tools[active_idx]["tool"].tool_offset
        z_bed = z_carriage + abs(tool_offset) if tool_offset is not None else z_carriage
    else:
        z_bed = z_carriage

    # Convert from new_K pixel space (full-frame display) back to K pixel space
    # (which matches the calibration, done on plain-undistort frames)
    px_k = (px - new_K[0, 2]) / new_K[0, 0] * K[0, 0] + K[0, 2]
    py_k = (py - new_K[1, 2]) / new_K[1, 1] * K[1, 1] + K[1, 2]
    mx, my = cam.pixel_to_machine(px_k, py_k, z=z_bed)
    print(f"  Click ({px}, {py})  →  machine ({mx:.2f}, {my:.2f})  [Z_BED={z_bed:.2f}]")
    machine.move_to(x=mx, y=my, wait=True)
    _moving[0] = False


cam.connect()
cv2.namedWindow(WIN)
cv2.setMouseCallback(WIN, _mouse_cb)

while True:
    ret, raw = cam._cap.read()
    if not ret:
        break

    frame = cv2.remap(raw, map1, map2, cv2.INTER_LINEAR)

    if _pending[0] is not None and not _moving[0]:
        px, py = _pending[0]
        _pending[0] = None
        _last_click[0] = (px, py)
        _moving[0] = True
        threading.Thread(target=_move_worker, args=(px, py), daemon=True).start()

    if _last_click[0]:
        cv2.drawMarker(frame, _last_click[0], (0, 0, 255), cv2.MARKER_CROSS, 40, 3)
    if _moving[0]:
        cv2.putText(
            frame, "Moving...", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 0), 2
        )

    cv2.imshow(WIN, frame)
    if cv2.waitKey(1) & 0xFF in (27, ord("q")):
        break

cam.disconnect()
cv2.destroyAllWindows()
