"""Convert Natural Earth 10m ocean polygons (EPSG:4326) into a
Web-Mercator (EPSG:3857) water_polygons shapefile for Planetiler/tilemaker."""
import math, os, zipfile
import shapefile
from shapely.geometry import shape
from shapely.geometry.polygon import orient

SRC = r"G:\sketcyshitx2\data\sources\ne_ocean_extract\ne_10m_ocean.shp"
OUT = r"G:\sketcyshitx2\data\sources\water_polygons"
os.makedirs(OUT, exist_ok=True)
base = os.path.join(OUT, "water_polygons")


def merc(lon, lat):
    lat = max(-85.05112878, min(85.05112878, lat))
    x = lon * 20037508.342789244 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) * 20037508.342789244 / math.pi
    return x, y


def write_poly(w, poly):
    poly = orient(poly, sign=-1.0)  # shapefile: exterior clockwise
    rings = [list(poly.exterior.coords)] + [list(h.coords) for h in poly.interiors]
    rings = [[merc(lon, lat) for lon, lat in ring] for ring in rings]
    w.poly(rings)
    w.record("ocean")


r = shapefile.Reader(SRC)
w = shapefile.Writer(base, shapeType=shapefile.POLYGON)
w.field("class", "C", size=20)
n = 0
for shprec in r.iterShapes():
    g = shape(shprec.__geo_interface__)
    if g.is_empty:
        continue
    if g.geom_type == "Polygon":
        write_poly(w, g); n += 1
    elif g.geom_type == "MultiPolygon":
        for p in g.geoms:
            write_poly(w, p); n += 1
w.close()

with open(base + ".prj", "w") as f:
    f.write('PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",'
            'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,0.0]],'
            'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
            'PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],'
            'PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],'
            'PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],'
            'UNIT["Meter",1.0]]')

zp = base + ".zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for ext in (".shp", ".shx", ".dbf", ".prj"):
        p = base + ext
        if os.path.exists(p):
            z.write(p, os.path.basename(p))

print(f"polygons={n}  zip={zp}  size={os.path.getsize(zp)/1024/1024:.1f} MB")
