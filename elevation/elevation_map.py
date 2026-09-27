import io
import math
from concurrent.futures import ThreadPoolExecutor

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from matplotlib.patches import Rectangle
from PIL import Image
from pyproj import Transformer
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject, transform_bounds

DEM = 'output_USGS1m_small.tif'
OUT = './elevation_map_small.png'
ZOOM = 16    # satellite tile zoom (~1.9 m/px at this latitude)
PX = 2       # plot grid resolution in meters
ALPHA = 0.5  # elevation overlay opacity

TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
R = 6378137.0  # Web Mercator sphere radius


def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_to_mercator(tx, ty, z):
    n = 2 ** z
    return tx / n * 2 * math.pi * R - math.pi * R, math.pi * R - ty / n * 2 * math.pi * R


def fetch_tile(xy):
    x, y = xy
    r = requests.get(TILE_URL.format(z=ZOOM, x=x, y=y), timeout=30)
    r.raise_for_status()
    return xy, Image.open(io.BytesIO(r.content)).convert('RGB')


with rasterio.open(DEM) as dataset:
    elevations = dataset.read(1)[::PX, ::PX]
    bounds = dataset.bounds
    crs = dataset.crs

H, W = elevations.shape
dst_transform = rasterio.Affine(PX, 0, bounds.left, 0, -PX, bounds.top)

# Download satellite tiles covering the DEM and stitch them together
west, south, east, north = transform_bounds(crs, 'EPSG:4326', *bounds, densify_pts=21)
tx0, ty0 = lonlat_to_tile(west, north, ZOOM)
tx1, ty1 = lonlat_to_tile(east, south, ZOOM)
txs = range(int(tx0), int(tx1) + 1)
tys = range(int(ty0), int(ty1) + 1)
with ThreadPoolExecutor(8) as pool:
    tiles = dict(pool.map(fetch_tile, [(x, y) for x in txs for y in tys]))

mosaic = Image.new('RGB', (256 * len(txs), 256 * len(tys)))
for (x, y), tile in tiles.items():
    mosaic.paste(tile, ((x - txs[0]) * 256, (y - tys[0]) * 256))

mx0, my0 = tile_to_mercator(txs[0], tys[0], ZOOM)
mx1, my1 = tile_to_mercator(txs[-1] + 1, tys[-1] + 1, ZOOM)
src_transform = from_bounds(mx0, my1, mx1, my0, mosaic.width, mosaic.height)

# Reproject the imagery (Web Mercator) onto the DEM's UTM grid so they line up
imagery = np.zeros((3, H, W), dtype=np.uint8)
reproject(np.moveaxis(np.asarray(mosaic), 2, 0), imagery,
          src_transform=src_transform, src_crs='EPSG:3857',
          dst_transform=dst_transform, dst_crs=crs, resampling=Resampling.bilinear)
imagery = np.moveaxis(imagery, 0, 2)

# Plot in meters from the SW corner so the scale bar is exact
width_m, height_m = W * PX, H * PX
extent = [0, width_m, 0, height_m]
fig, ax = plt.subplots(figsize=(16, 12.5))
ax.imshow(imagery, extent=extent)
im = ax.imshow(np.ma.masked_equal(elevations, -999999.0), extent=extent, cmap='terrain', alpha=ALPHA)

cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
cbar.set_label('elevation (m)')
cbar.solids.set_alpha(1)

# Lat/lon tick labels along the edges
to_utm = Transformer.from_crs('EPSG:4326', crs, always_xy=True)
lon_ticks = np.arange(math.ceil(west / 0.01) * 0.01, east, 0.01)
lat_ticks = np.arange(math.ceil(south / 0.01) * 0.01, north, 0.01)
ax.set_xticks([to_utm.transform(lon, south)[0] - bounds.left for lon in lon_ticks])
ax.set_xticklabels([f'{lon:.2f}°' for lon in lon_ticks])
ax.set_yticks([to_utm.transform(west, lat)[1] - bounds.bottom for lat in lat_ticks])
ax.set_yticklabels([f'{lat:.2f}°' for lat in lat_ticks])
ax.set_xlabel('longitude')
ax.set_ylabel('latitude')

# 1 km scale bar in the bottom-left corner
outline = [pe.withStroke(linewidth=3, foreground='black')]
sx, sy, seg = 250, 250, 250
for i in range(4):
    ax.add_patch(Rectangle((sx + i * seg, sy), seg, 45,
                           facecolor='white' if i % 2 == 0 else 'black', edgecolor='black'))
for i, label in enumerate(['0', '250', '500', '750', '1 km']):
    ax.text(sx + i * seg, sy + 80, label, color='white', ha='center', fontsize=11,
            weight='bold', path_effects=outline)

ax.set_title('Elevation over satellite imagery (USGS 1 m DEM)', fontsize=14)
ax.text(width_m - 10, 10, 'Imagery: Esri World Imagery', color='white', ha='right', va='bottom', fontsize=9)
plt.savefig(OUT, dpi=110, bbox_inches='tight')
print('saved', OUT)
