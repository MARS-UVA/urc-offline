import matplotlib.patheffects as pe
import matplotlib.pyplot as plt

from elevation_map import plot_elevation_map
from pathfinding import elevationPathfinding

DEM = 'output_USGS1m_small.tif'
OUT = './path_map_small.png'


def plot_path(dem, path, outfile):
    # Draws a path of (lat, lon) over the satellite + elevation map and saves it
    fig, ax, to_plot = plot_elevation_map(dem)
    xs, ys = zip(*(to_plot(lat, lon) for lat, lon in path))
    outline = [pe.withStroke(linewidth=5, foreground='black')]
    ax.plot(xs, ys, color='red', linewidth=2.5, path_effects=outline, label='path')
    ax.scatter(xs[0], ys[0], s=120, color='lime', edgecolor='black', zorder=5, label='start')
    ax.scatter(xs[-1], ys[-1], s=200, marker='*', color='yellow', edgecolor='black', zorder=5, label='goal')
    ax.legend(loc='upper right')
    ax.set_title(f'A* path over elevation ({len(path)} nodes)', fontsize=14)
    plt.savefig(outfile, dpi=110, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    pf = elevationPathfinding(DEM)
    w, h = len(pf.map2d), len(pf.map2d[0])
    start = pf.xyToLatLon((w // 10, h // 10))
    goal = pf.xyToLatLon((w * 9 // 10, h * 9 // 10))
    path = pf.getPath(start, goal)
    plot_path(DEM, path, OUT)
    print('saved', OUT)
