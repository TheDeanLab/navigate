# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
#  import logging

# Third Party Imports

# Local Imports

# Logger Setup
#  p = __name__.split(".")[1]
#  logger = logging.getLogger(p)


class Objective:
    def __init__(self):
        self.properties = {
            "N40X_NIR": {
                "manufacturer": "Nikon",
                "part_number": "MRD07420",
                "numerical_aperture": 0.8,
                "focal_length": 5,
                "entrance_pupil": 8,
                "parfocal_length": 60,
                "working_distance": 3.5,
            },
            "N16XLWD-PF": {
                "manufacturer": "Nikon",
                "part_number": "MRP07220",
                "numerical_aperture": 0.8,
                "focal_length": 12.5,
                "entrance_pupil": 20,
                "parfocal_length": 75,
                "working_distance": 3,
            },
            "N25X-APO-MP": {
                "manufacturer": "Nikon",
                "part_number": "MRD77220",
                "numerical_aperture": 1.1,
                "focal_length": 8,
                "entrance_pupil": 17.6,
                "parfocal_length": 75,
                "working_distance": 2,
            },
            "54-10-12": {
                "manufacturer": "ASI",
                "part_number": "54-10-12",
                "numerical_aperture": 0.4,
                "focal_length": 12,
                "entrance_pupil": 9.6,
                "parfocal_length": 61.6,
                "working_distance": 12,
            },
            "54-12-8": {
                "manufacturer": "ASI",
                "part_number": "54-12-8",
                "numerical_aperture": 0.7,
                "focal_length": 8.4,
                "entrance_pupil": 11.76,
                "parfocal_length": 83,
                "working_distance": 10,
            },
        }

    def calculate_entrance_pupil(self, objective):
        """Calculates the entrance pupil from other objective properties.

        Variable Incidence Angle Fluorescence Interference Contrast Microscopy for Z-Imaging Single Objects
        Caroline M.Ajo-Franklin, Prasad V.Ganesan, Steven G.Boxer
        Biophys. J. Volume 89, Issue 4, October 2005, Pages 2759-2769

        Parameters
        ----------
        objective : str
            Name of the objective from the properties dict

        Returns
        -------
        entrance_pupil_diameter : float
            Diameter of the objective entrance pupil in millimeters.

        """
        focal_length = self.properties[objective]["focal_length"]
        numerical_aperture = self.properties[objective]["numerical_aperture"]
        if self.properties[objective]["manufacturer"] == "Olympus":
            tube_lens_focal_length = 180
        else:
            tube_lens_focal_length = 200
        magnification = tube_lens_focal_length / focal_length
        entrance_pupil_diameter = 2 * (
            (numerical_aperture * tube_lens_focal_length) / magnification
        )
        return entrance_pupil_diameter


if __name__ == "__main__":
    test = Objective()
    objective_name = "54-10-12"
    print(
        "The entrance pupil diameter for the ",
        objective_name,
        "is ",
        test.calculate_entrance_pupil("54-10-12"),
        "mm.",
    )
