import json
import pathlib

import geojson
import numpy as np
import shapely
from pymap3d import ecef
import shapely.geometry

from .absolute_rotaion_poles_from_ITRF2005 import ABSOLUTE_ROTATION_POLES


def lonlatvector2uvw(lat: float, lon: float, large: float) -> tuple[float, float, float]:
    """地球重心からlonlat方向のベクトルを地心直交座標系に変換
    """
    lat_radian = np.radians(lat)
    lon_radian = np.radians(lon)
    u = large * np.cos(lat_radian) * np.cos(lon_radian)
    v = large * np.cos(lat_radian) * np.sin(lon_radian)
    w = large * np.sin(lat_radian)
    return u, v, w


def plate_motion_uvw(lat: float, lon: float, height: float,
                     phi0: float, lambda0: float, omega0: float) -> tuple[float, float, float]:
    """地球上の点が回転極によりどう動くかをUVWで表示。vec(v) = vec(omega) x vec(x)

    Parameters
    ----------
    lat : float
    lon : float
    height: float(楕円体高)
        地球上の点(deg,deg,m)
    phi0 : float
    lambda0 : float
    omaga0 : float
        回転極(deg,deg,deg/m.y.)

    Returns
    -------
    tuple[float, float, float]
        u,v,w(m/year)
    """
    x, y, z = ecef.geodetic2ecef(lat, lon, height)
    large = np.sqrt(x**2+y**2+z**2)
    point_vec = lonlatvector2uvw(lat, lon, large)
    omega_vec = lonlatvector2uvw(phi0, lambda0, np.radians(omega0))
    # vec(v) = vec(omega) x vec(x) axisa=0, axisb=0で(x1,y1,z1)*(x'1,y'1,z'1)での外積にする。
    # axisc=0で[[u1,u2],[v1,v2],[w1,w2]]の形にして出力される。
    velo_vec = np.cross(omega_vec, point_vec, axisa=0, axisb=0, axisc=0)  # type: ignore
    u, v, w = velo_vec/(10**6)
    return u, v, w


def plate_motion_enu(lat: float, lon: float, height: float,
                     phi0: float, lambda0: float, omega0: float) -> tuple[float, float, float]:
    """地球上の点が回転極によりどう動くかをENUで表示。vec(v) = vec(omega) x vec(x)

    Parameters
    ----------
    lat : float
    lon : float
    height: float(楕円体高)
        地球上の点(deg,deg,m)
    phi0 : float
    lambda0 : float
    omaga0 : float
        回転極(deg,deg,deg/m.y.)

    Returns
    -------
    tuple[float, float, float]
        e,n,u(m/year)
    """
    u, v, w = plate_motion_uvw(lat, lon, height, phi0, lambda0, omega0)
    east, north, up = ecef.uvw2enu(u, v, w, lat, lon)
    return east, north, up


def plate_motion(plate_name: str, lat: float, lon: float, height: float) -> tuple[float, float, float]:
    """地球上の点が回転極によりどう動くかをENUで表示

    Parameters
    ----------
    plate_name : str
        プレート名
    lat : float
    lon : float
    height: float(楕円体高)
        地球上の点(deg,deg,m)

    Returns
    -------
    tuple[float, float, float]
        e,n,u(m/year)
    """
    phi0 = ABSOLUTE_ROTATION_POLES[plate_name]['phi0']
    lambda0 = ABSOLUTE_ROTATION_POLES[plate_name]['lambda0']
    omega0 = ABSOLUTE_ROTATION_POLES[plate_name]['omega0']
    east, north, up = plate_motion_enu(lat, lon, height, phi0, lambda0, omega0)
    return east, north, up


MY_DIR_PATH = pathlib.Path(__file__).parent
PLATE_PATH = MY_DIR_PATH / 'plate_boundaries/pb2002_plates.geojson'

with PLATE_PATH.open(mode='r') as fp:
    geojson_dict: geojson.FeatureCollection = json.load(fp)
PLATES: dict[str, shapely.Polygon] = {}
for feature in geojson_dict['features']:
    name = feature['properties']['name']
    polygon = shapely.geometry.shape(feature['geometry'])
    PLATES[name] = polygon


def belong_plate_name(lat: float, lon: float,
                      plates: dict[str, shapely.Polygon] = PLATES) -> str | None:
    """点がどのプレートに属するかをしらべプレート名を返す。

    Parameters
    ----------
    lat : float
    lon : float
        点
    plates: dict[str, shapely.Polygon]
        plateの名前と範囲

    Returns
    -------
    str | None
        プレート名
    """
    point = shapely.Point(lon, lat)  # 順番注意:geojsonはlon->latの順
    for name, plate in plates.items():
        if plate.contains(point):
            return name
    return None
