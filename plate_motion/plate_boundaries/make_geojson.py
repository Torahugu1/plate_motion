import pathlib

import antimeridian
import geojson
import pandas as pd

MY_DIR_PATH = pathlib.Path(__file__).parent
TABLE = MY_DIR_PATH / 'ggge192-sup-0001-t01.txt'

names = ['Identifier',
         'Plate NameArea',
         'Steradian',
         'Pole Latitude',
         'Pole Longitude',
         'Rotation Rate',
         'Reference'
         ]
# NAという文字列がありそれがNAN判定されないようにするため。
plate_name_df = pd.read_csv(TABLE, header=None, sep=r'\t+',
                            names=names, skiprows=6, skipfooter=3,
                            engine="python", keep_default_na=False)
plate_name_df = plate_name_df.set_index('Identifier')

print(plate_name_df)


# geojsonは経度180度で分割すべきという仕様があるため、またぐポリゴンを分割するため以下のようにする。
# antimeridianを使用する

PLATE_PATH = MY_DIR_PATH / 'pb2002_plates.dig'
with PLATE_PATH.open(mode='r') as fp:
    Features = []
    lonlats = []
    name = None
    for string in fp:
        string = string.strip()
        if len(string) == 2:
            name = plate_name_df['Plate NameArea'][string]
        elif string == '*** end of line segment ***':
            geometry = geojson.Polygon([lonlats])
            properties = {'name': name}
            Feature = geojson.Feature(geometry=geometry, properties=properties)
            Feature = antimeridian.fix_geojson(Feature)
            Features.append(Feature)
            lonlats = []
            name = None
        else:
            lon_str, lat_str = string.split(sep=',')
            lonlats.append([float(lon_str), float(lat_str)])
    FC = geojson.FeatureCollection(Features)

OUTPUT_PATH = MY_DIR_PATH / 'pb2002_plates.geojson'
with OUTPUT_PATH.open(mode='w') as fp:
    geojson.dump(FC, fp, indent=2)

print(f'output: {OUTPUT_PATH}')
