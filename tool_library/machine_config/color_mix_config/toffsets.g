; Tool Offsets
; These are XYZ offsets from the tip of the tool to the
; trigger location of the Z Probe.
; See the wiki on how to calculate these:
; https://jubilee3d.com/index.php?title=Setting_Tool_Offsets

;G10		P0 	Z-0.35	X6.9 Y41.7  ; tool 0
;G10		P1 	Z-0.35	X6.9 Y41.7  ; tool 1, etc.

; Camera Setup
; ----------------------------------
G10 P0 X-2.10 Y44.70 Z-8.80 ; setting tool offset- This is to change the Z-reference point to the tip of the tool
	; X-1.4 Y49.88									 ; instead of the Z-switch position 

; Pipette Tool (OT2-P300) Setup
; ----------------------------------
G10 P1 X-0.17 Y39.93 Z-100.01				 ; setting tool offset- This is to change the Z-reference point to the tip of the tool
										 ; instead of the Z-switch position 

; Sonicator Horn
; ----------------------------------
G10 P2 X2.56 Y38.462 Z-148					 ; setting tool offset- This is to change the Z-reference point to the tip of the tool
										 ; instead of the Z-switch position
  
; Spectroscopy Tool Setup
; ----------------------------------
G10 P3 X-0.60 Y32.70 Z-51.80		 ; setting tool offset- This is to change the Z-reference point to the tip of the tool
										 ; instead of the Z-switch position 
										 
; Electromagnet Tool Setup
; ----------------------------------

;G10 P4 X-0.18 Y27.86