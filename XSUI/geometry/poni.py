"""
Creates pyFAI PONI (point of normal incidence) filetypes that are compatible
with the XSUI geometry.

This is the orthongonal projection of the origin on the detector surface.

The PONI filetypes are specified using 6 parameters:
- poni1 = d1: The vertical y-distance along the detector, normal to the sample. Together with poni2, this
    defines the position of the orthogonal point on the detector to the sample position.
- poni2 = d2: The horizontal x-distance along the detector, normal to the sample. See poni1.
- poni3 = d3 = 0: The surface of the detector is at z=0. The z-coordinate of the sample position is
    defined by the z-coordinate of the PONI point.
- rot1: Rotation in radians along axis 1 (y-axis).
- rot2: Rotation in radians along axis 2 (x-axis).
- rot3: Rotation in radians along axis 3 (z-axis).

Note that axis are defined by
- 1 = y-axis: vertical axis of the detector
- 2 = x-axis: horizontal axis of the detector towards the centre of the storage ring.
- 3 = z-axis: normal to the detector surface

If all rotations are zero, the detector is in transmission mode, and incident beam is orthogonal to detector surface.

L is the sample/origin centre of rotation.
"""
