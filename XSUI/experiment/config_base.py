from abc import ABCMeta
from dataclasses import dataclass
import pyFAI, pyFAI.calibrant, pyFAI.detectors, pyFAI.io.ponifile


@dataclass
class ConfigBase(metaclass=ABCMeta):
    """
    Base abstract class for scattering configuration management.

    Defines the interface / methods that require implementation in derived classes.
    """

    calibrant: pyFAI.calibrant.Calibrant | None = None
    detector: pyFAI.detectors.Detector | None = None
    poni: pyFAI.io.ponifile.PoniFile | None = None
