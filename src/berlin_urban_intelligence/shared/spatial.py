"""Geospatial helpers.

API interchange uses WGS84 (EPSG:4326). Metric calculations in Berlin use ETRS89 / UTM
zone 33N (EPSG:25833), avoiding degree-based distance calculations.
"""

from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

_WGS84_TO_BERLIN_METRIC = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)


def metric_distance_m(a_lon_lat: tuple[float, float], b_lon_lat: tuple[float, float]) -> float:
    a = transform(_WGS84_TO_BERLIN_METRIC.transform, Point(a_lon_lat))
    b = transform(_WGS84_TO_BERLIN_METRIC.transform, Point(b_lon_lat))
    return float(a.distance(b))
