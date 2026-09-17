import csv
import rasterio
from pyproj import Transformer

RESOLUTION_M = 5

with rasterio.open('output_USGS1m.tif') as dataset, open('elevation.csv', 'w', newline='') as f:

    print(dataset.crs)
    print(dataset.width, dataset.height)
    print(dataset.bounds)
    print({i: dtype for i, dtype in zip(dataset.indexes, dataset.dtypes)})

    xl = int(dataset.bounds.left)+1
    yl = int(dataset.bounds.bottom)+1
    elevations = dataset.read(1)
    transformer = Transformer.from_crs(dataset.crs, "epsg:4326", always_xy=True)
    writer = csv.writer(f)
    writer.writerow(['lat', 'lon', 'elevation (m)'])
    for x in range(xl, xl+dataset.width, RESOLUTION_M):
        for y in range(yl, yl+dataset.height, RESOLUTION_M):
            row, col = dataset.index(x, y)
            e = elevations[row, col]
            lon, lat = transformer.transform(x, y)
            writer.writerow([lat, lon, e])