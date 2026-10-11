"""Where a shared location falls: the nearest of Lebanon's 26 cazas.

The Facility Locator gives a caza for each facility but no coordinates, so a location can only be
narrowed to its caza. Centres are approximate, leaning towards each caza's main towns; caza names
are spelled as the Facility Locator spells them (caza_en).
"""

from math import cos, radians, sqrt
from typing import NamedTuple


class Caza(NamedTuple):
    name: str  # caza_en in the Facility Locator
    governorate: str
    lat: float
    lon: float


CAZAS = [
    Caza("Beirut", "Beirut", 33.893, 35.495),
    Caza("Baabda", "Mount Lebanon", 33.845, 35.540),
    Caza("El Meten", "Mount Lebanon", 33.900, 35.580),
    Caza("Aley", "Mount Lebanon", 33.790, 35.560),
    Caza("Chouf", "Mount Lebanon", 33.680, 35.560),
    Caza("Kesrouane", "Keserwan-Jbeil", 34.010, 35.680),
    Caza("Jbeil", "Keserwan-Jbeil", 34.120, 35.700),
    Caza("Tripoli", "North", 34.430, 35.840),
    Caza("Zgharta", "North", 34.360, 35.920),
    Caza("El Koura", "North", 34.300, 35.810),
    Caza("El Batroun", "North", 34.250, 35.710),
    Caza("Bcharre", "North", 34.250, 36.010),
    Caza("El Minieh-Dennie", "North", 34.440, 35.990),
    Caza("Akkar", "Akkar", 34.540, 36.120),
    Caza("Baalbek", "Baalbek-Hermel", 34.050, 36.270),
    Caza("Hermel", "Baalbek-Hermel", 34.390, 36.380),
    Caza("Zahle", "Bekaa", 33.850, 35.900),
    Caza("West Bekaa", "Bekaa", 33.600, 35.760),
    Caza("Rachaya", "Bekaa", 33.500, 35.860),
    Caza("Saida", "South", 33.550, 35.390),
    Caza("Sour", "South", 33.250, 35.250),
    Caza("Jezzine", "South", 33.540, 35.600),
    Caza("El Nabatieh", "Nabatieh", 33.380, 35.490),
    Caza("Bint Jbeil", "Nabatieh", 33.130, 35.430),
    Caza("Marjaayoun", "Nabatieh", 33.320, 35.590),
    Caza("Hasbaya", "Nabatieh", 33.400, 35.690),
]

MAX_KM = 35  # farther than this from every centre is outside Lebanon (or lat and lon swapped)


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance on a flat map: close enough within Lebanon."""
    x = radians(lon2 - lon1) * cos(radians((lat1 + lat2) / 2))
    return 6371 * sqrt(x * x + radians(lat2 - lat1) ** 2)


def caza_at(lat: float, lon: float) -> Caza | None:
    """The caza whose centre is nearest, or None when the point is not in Lebanon."""
    caza = min(CAZAS, key=lambda c: _km(lat, lon, c.lat, c.lon))
    return caza if _km(lat, lon, caza.lat, caza.lon) <= MAX_KM else None
