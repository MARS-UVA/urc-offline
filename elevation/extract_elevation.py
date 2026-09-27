import csv
import rasterio
from pyproj import Transformer

RESOLUTION_M = 5
TIFF = 'output_USGS1m_small.tif'
OUT = 'elevation.csv'

def elevationCSV(GEOTIFF, outfile):
    elevations = extractElevation(GEOTIFF)
    with open(outfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon', 'elevation (m)'])
        for (lat, lon, e) in elevations:
            writer.writerow([lat, lon, e])


def elevationMap(GEOTIFF):
    elevations = extractElevation(GEOTIFF)
    elevationMap = {}
    for (lat, lon, e) in elevations:
        elevationMap[(lat, lon)] = e
    return elevationMap

def extractElevation(GEOTIFF):
    # return list of (lat, lon, elevation)
    elevations = []
    with rasterio.open(GEOTIFF) as dataset:
        print("Extracting data from", GEOTIFF)
        print(dataset.crs)
        print(dataset.width, dataset.height)
        print(dataset.bounds)
        print({i: dtype for i, dtype in zip(dataset.indexes, dataset.dtypes)})
    
        xl = int(dataset.bounds.left)+1
        yl = int(dataset.bounds.bottom)+1
        elevations = dataset.read(1)
        transformer = Transformer.from_crs(dataset.crs, "epsg:4326", always_xy=True)
        
        for y in range(yl, yl+dataset.height, RESOLUTION_M):
            for x in range(xl, xl+dataset.width, RESOLUTION_M):
                row, col = dataset.index(x, y)
                e = elevations[row, col]
                lon, lat = transformer.transform(x, y)
                elevations.append((lat, lon, e))



if __name__ == "__main__":
    elevationCSV(TIFF, 'elevation.csv')