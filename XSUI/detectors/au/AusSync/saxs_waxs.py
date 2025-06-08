from pyFAI import detectors
import os


class SAXS_WAXS(detectors._dectris.Pilatus2M):
    """
    A representation of the SAXS/WAXS detector used at the SAXS/WAXS beamline.

    Specification for the beamline can be found at
    https://asuserwiki.atlassian.net/wiki/spaces/UO/pages/328957957/Technical+Information+SAXS+WAXS

    Specification for the detector can be found at
    https://media.dectris.com/filer_public/41/8e/418eecb3-8253-4da3-8e35-30c0bf757c03/technicalspecification_pilatus3_x_2m.pdf
    """

    intermodule_gap_size = (17, 7)
    """The gap size between the modules in pixels."""


if __name__ == "__main__":

    det = SAXS_WAXS()
    print(det)
    print(det.MAX_SHAPE)
    print(det.module_size)

    example_dir = r"D:\Datasets\2024-12 GIWAXS\McNeill_22484\exp2\images"
