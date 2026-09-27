from astar import AStar
import rasterio
from pyproj import Transformer
import math

class elevationAstar(AStar):
    def __init__(self, res, map2d):
        self.res = res
        self.map2d = map2d

    def neighbors(self, n):
        x, y = n
        dirs = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        nbrs = []
        for dir in dirs:
            nx = x+dir[0]
            ny = y+dir[1]
            if nx >= 0 and nx < len(self.map2d) and ny >= 0 and ny < len(self.map2d[0]):
                nbrs.append((nx, ny))
        return nbrs

    def distance_between(self, n1, n2):
        x1, y1 = n1
        x2, y2 = n2

        elevationDiff = abs(float(self.map2d[x1][y1]) - float(self.map2d[x2][y2]))
        return self.res+elevationDiff*elevationDiff

    def heuristic_cost_estimate(self, current, goal):
        xd = goal[0]-current[0]
        yd = goal[1]-current[1]
        return self.res*math.sqrt(xd*xd+yd*yd)

    def is_goal_reached(self, current, goal):
        return current == goal

class elevationPathfinding:
    RESOLUTION_M = 5
    def __init__(self, GEOTIFF):
        # map2d[xi][yi]: xi steps east, yi steps north, RESOLUTION_M meters per step
        self.map2d = []
        self.latlon2xy = {}
        with rasterio.open(GEOTIFF) as dataset:
            self.xl = int(dataset.bounds.left)+1
            self.yl = int(dataset.bounds.bottom)+1
            elevations = dataset.read(1)
            self.toLatLon = Transformer.from_crs(dataset.crs, "epsg:4326", always_xy=True)
            self.fromLatLon = Transformer.from_crs("epsg:4326", dataset.crs, always_xy=True)

            for xi, x in enumerate(range(self.xl, self.xl+dataset.width, self.RESOLUTION_M)):
                self.map2d.append([])
                for yi, y in enumerate(range(self.yl, self.yl+dataset.height, self.RESOLUTION_M)):
                    row, col = dataset.index(x, y)
                    e = elevations[row, col]
                    lon, lat = self.toLatLon.transform(x, y)
                    self.latlon2xy[(lat, lon)] = (xi, yi)
                    self.map2d[xi].append(e)

        self.AST = elevationAstar(self.RESOLUTION_M, self.map2d)

    def getPath(self, start, goal):
        # start, goal: (lat, lon). Returns list of (lat, lon), or None if no path.
        startNode = self.getClosestXY(start)
        goalNode = self.getClosestXY(goal)
        path = self.AST.astar(startNode, goalNode)
        if path is None:
            return None
        return [self.xyToLatLon(n) for n in path]

    def getClosestXY(self, point):
        # point: (lat, lon). Returns the nearest grid node (xi, yi), clamped to the map.
        lat, lon = point
        x, y = self.fromLatLon.transform(lon, lat)
        xi = round((x - self.xl) / self.RESOLUTION_M)
        yi = round((y - self.yl) / self.RESOLUTION_M)
        xi = min(max(xi, 0), len(self.map2d)-1)
        yi = min(max(yi, 0), len(self.map2d[0])-1)
        return (xi, yi)

    def xyToLatLon(self, node):
        xi, yi = node
        x = self.xl + xi*self.RESOLUTION_M
        y = self.yl + yi*self.RESOLUTION_M
        lon, lat = self.toLatLon.transform(x, y)
        return (lat, lon)
