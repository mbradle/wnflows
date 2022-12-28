import wnutils.xml as wx
import numpy as np
import wnnet.consts as wc
from scipy.interpolate import interp1d


class Nuc:
    """A class for handling nuclei and their data."""

    def __init__(self, file):
        self.xml = wx.Xml(file)
        self.nuclides = self.xml.get_nuclide_data()

    def get_nuclides(self, nuc_xpath=""):
        if not nuc_xpath:
            return self.nuclides
        else:
            return self.xml.get_nuclide_data(nuc_xpath=nuc_xpath)

    def compute_nuclear_partition_function(self, name, t9):
        """Method to compute the nuclear partition function for a species.

        Args:
            ``name`` (:obj:`str`): A string giving the name of the nuclide
            whose partition function should be computed.

            ``t9`` (:obj:`float`): The temperature in 10\ :sup:`9` K at which
            to compute the partition function.

        Returns:
            A :obj:`float` giving the nuclear partition function for the species
            at the input temperature.

        """

        nuclide = self.get_nuclides()[name]
        t = nuclide["t9"]
        lg = np.log10(nuclide["partf"])

        if t9 < t[0]:
            return np.power(10.0, lg[0])
        elif t9 > t[len(t) - 1]:
            return np.power(10.0, lg[len(t) - 1])

        if len(t) <= 2:
            f = interp1d(t, lg, kind="linear")
            return np.power(10.0, f(t9))
        else:
            f = interp1d(t, lg, kind="cubic")
            return np.power(10.0, f(t9))

    def compute_quantum_abundance(self, name, t9, rho):
        assert t9 > 0 and rho > 0

        nuclide = self.get_nuclides()[name]

        m = wc.m_u_in_MeV * nuclide["a"] + nuclide["mass excess"]

        result = self.compute_nuclear_partition_function(name, t9) / (rho * wc.N_A)

        p1 = (m * wc.MeV_to_ergs) * wc.k_B * t9 * 1.0e9
        p2 = 2.0 * np.pi * np.power(wc.hbar * wc.c, 2)

        result *= np.power((p1 / p2), 1.5)

        return result

    def compute_binding_energy(self, name):
        nuclides = self.get_nuclides()
        nuclide = nuclides[name]
        delta_p = nuclides["h1"]["mass excess"]
        delta_n = nuclides["n"]["mass excess"]

        return (
            nuclide["z"] * delta_p
            + (nuclide["a"] - nuclide["z"]) * delta_n
            - nuclide["mass excess"]
        )

    def _compute_NSE_factor(self, name, t9, rho):
        return np.log(self.compute_quantum_abundance(name, t9, rho)) + (
            (self.compute_binding_energy(name) * wc.MeV_to_ergs)
        ) / (wc.k_B * (t9 * 1.0e9))
