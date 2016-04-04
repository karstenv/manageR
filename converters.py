# -*- coding: utf-8 -*-

# regular imports
import time

# rpy2 imports
import rpy2.robjects as robjects
import rpy2.rlike as rlike

#PyQt and PyQGIS imports
from PyQt4.QtCore import (QString, QVariant, QFileInfo)
try:
    from qgis.core import    (QgsVectorLayer, QgsVectorDataProvider, QgsMapLayer,
                              QgsApplication, QgsRectangle, QgsGeometry,
                              QgsCoordinateReferenceSystem, QgsField, QgsPoint,
                              QgsFeature,)
except Exception, e:
    pass

#import traceback

# ---------------------------   VECTOR LAYERS   -------------------------------#
def qQGISVectorDataFrame(layer, keep=False):
    provider = layer.dataProvider()
    selection = layer.selectedFeatureCount()>0
    if keep:
        crs = provider.crs()
        if not crs.isValid():
            proj = 'NA'
        else:
            if not crs.geographicFlag():
                proj = unicode(crs.toProj4())
            else:
                # TODO: Find better way to handle geographic coordinate systems
                # As far as I can tell, R does not like geographic coodinate systems input
                # into it's proj4string argument...
                proj = 'NA'
    attrs = provider.attributeIndexes()
    layer.select(attrs, QgsRectangle())
    fields = qFields(provider)
    if len(fields) < 1:
        raise Exception("Error: attribute table must have at least one field")
    if selection:
        feats = layer.selectedFeatures()
    else:
        feats = qFeatures(layer)
    source = unicode(layer.publicSource())
    name = unicode(QFileInfo(layer.name()).baseName())
    make_names = robjects.r.get('make.names', mode='function')
    newname = make_names(name)[0]
    try:
        df = qData(feats, fields)
        if not keep:
            try:
                robjects.r.assign(unicode(newname), df)
            except:
                raise Exception("Error: unable to assign data.frame object to environment")
            return True
        geoms = qGeometries(feats)
        type = layer.geometryType()
        sp = qSpatial(geoms, type, str(crs.toProj4()))
        result = qSpatialDataFrame(sp, df, type)
        try:
            robjects.r.assign(unicode(newname), result)
        except:
            raise Exception("Error: unable to assign spatial object to environment")
        length, width = list(robjects.r.dim(result))
        print "Name: %s\nSource: %s\n" % (unicode(newname), unicode(source))
        print "with %s rows and %s columns\n" % (unicode(length), unicode(width))
        if not newname == name:
            print "**Note: layer name syntax changed"
    except Exception, e:
        raise Exception("Error: %s" % unicode(e))
    return True

def qFields(provider):
    try:
        return [(field.name(), field.type()) for field in provider.fields().values()]
    except Exception, e:
        raise Exception("error encountered when extracting field names: %s" % unicode(e))

def qFeatures(layer):
    try:
        return [feature for feature in layer]
    except Exception, e:
        raise Exception("error encountered when extracting features: %s" % unicode(e))

def qData(feats, fields):
    try:
        # fields:   fields = [(field.name(), field.type()) for field in provider.fields().values()]
        # features: layer.select(provider.attributeIndexes(), QgsRectangle())
        #           features = [feature for feature in layer]
        attrs = [feat.attributeMap().values() for feat in feats]
        attrst = map(lambda *row: list(row), *attrs)
        df = [
          (
            (str(fields[i][0]), robjects.FloatVector(map(lambda x: x.toDouble()[0], row)))
            if fields[i][1] == 2 else
            (
              (str(fields[i][0]), robjects.IntVector(map(lambda x: x.toInt()[0], row)))
              if fields[i][1] == 6 else
              (
                (str(fields[i][0]), robjects.StrVector(map(lambda x: x.toString(), row)))
              )
            )
          )
          for i, row in enumerate(attrst)
        ]
        df = rlike.container.OrdDict(df)
        return robjects.DataFrame(df)
    except Exception, e:
        raise Exception("error encountered when extracting data.frame: %s" % unicode(e))

def qGeometries(feats):
    # features: layer.select(provider.attributeIndexes(), QgsRectangle())
    #           features = [feature for feature in layer]
    try:
        return [qGeometry(feat) for feat in feats]
    except Exception, e:
        raise Exception("error encountered when extracting geometries: %s" % unicode(e))

def qPolygons(polys, fid):
    try:
        Polygon = robjects.r.get('Polygon', mode='function')
        Polygons = robjects.r.get('Polygons', mode='function')
        result = Polygons(sum([[Polygon(qPoints(line)) for line in poly] for poly in polys], []), str(fid))
        return result
    except Exception, e:
        raise Exception("unable to extract polygon geomety (%s)" % unicode(e))

def qPoints(line):
    try:
        numeric = robjects.FloatVector(sum([[point.x(), point.y()] for point in line], []))
        result = robjects.r.matrix(numeric, ncol=2, byrow=True)
        return result
    except Exception, e:
        raise Exception("unable to extract point geomety (%s)" % unicode(e))

def qLines(lines, fid):
    try:
        Line = robjects.r.get('Line', mode='function')
        Lines = robjects.r.get('Lines', mode='function')
        result = Lines([Line(qPoints(line)) for line in lines], str(fid))
        return result
    except Exception, e:
        raise Exception("unable to extract polyline geomety (%s)" % unicode(e))

def qGeometry(feature):
    try:
        geom = QgsGeometry(feature.geometry())
        fid = feature.id()
        if not geom.isMultipart():
            if not geom.convertToMultiType():
                raise Exception("unable to extract feature geometry (invalid geometry type)")
        if geom.type() == 0:
            return qPoints(geom.asMultiPoint())
        elif geom.type() == 1:
            return qLines(geom.asMultiPolyline(), fid)
        elif geom.type() == 2:
            return qPolygons(geom.asMultiPolygon(), fid)
        else:
            raise Exception("unable to extract feature geometry (unknown geometry type)")
    except Exception, e:
        raise Exception("unable to extract feature geometry: %s" % unicode(e))

def qSpatial(geometries, type, proj="NULL"):
    try:
        SpatialPolygons = robjects.r.get('SpatialPolygons', mode='function')
        SpatialLines = robjects.r.get('SpatialLines', mode='function')
        SpatialPoints = robjects.r.get('SpatialPoints', mode='function')
        CRS = robjects.r.get('CRS', mode='function')
        if type == 0:
            return SpatialPoints(reduce(robjects.r.rbind, geometries), proj4string = CRS(proj))
        elif type == 1:
            return SpatialLines(geometries, proj4string = CRS(proj))
        elif type == 2:
            return SpatialPolygons(geometries, proj4string = CRS(proj))
        else:
            return None
    except Exception, e:
        raise Exception("unable to create spatial object: %s" % unicode(e))

def qSpatialDataFrame(spatial, data, type):
    try:
        SpatialPolygonsDataFrame = robjects.r.get('SpatialPolygonsDataFrame', mode='function')
        SpatialLinesDataFrame = robjects.r.get('SpatialLinesDataFrame', mode='function')
        SpatialPointsDataFrame = robjects.r.get('SpatialPointsDataFrame', mode='function')
        kwargs = {'match.ID':False}
        if type == 0:
            return SpatialPointsDataFrame(spatial, data, **kwargs)
        elif type == 1:
            return SpatialLinesDataFrame(spatial, data, **kwargs)
        elif type == 2:
            return SpatialPolygonsDataFrame(spatial, data, **kwargs)
        else:
            return None
    except Exception, e:
        raise Exception("unable to create spatial dataset: %s" % unicode(e))

def qOGRVectorDataFrame(source, name, encode="", keep=True):
    source = unicode(source)
    name = unicode(name)
    make_names = robjects.r.get('make.names', mode='function')
    newname = make_names(name)[0]
    try:
        rcode = "%s <- readOGR(dsn='%s', layer='%s')" % (unicode(newname), unicode(source), unicode(name))
        if not keep:
            rcode += "@data"
        robjects.r(rcode)
    except Exception, e:
        raise Exception("Error: unable to read vector dataset (%s)" % unicode(e))
    #length, width = list(robjects.r.dim(result))
    #print "Name: %s\nSource: %s\n" % (unicode(newname), unicode(source))
    #print "with %s rows and %s columns\n" % (unicode(length), unicode(width))
    if not newname == name:
        print "**Note: layer name syntax changed"
    return True

# ---------------------------   RASTER LAYERS   -------------------------------#

def qGDALRasterDataFrame(dsn, name, package='raster'):
    dsn = unicode(dsn)
    name = unicode(name)
    make_names = robjects.r.get('make.names', mode='function')
    newname = make_names(name)[0]
    try:
        if package == "raster":
            rcode = "raster('%s')" % dsn
        else:
            rcode = "readGDAL(fname = '%s')" % dsn
        result = robjects.r(rcode)
    except Exception, e:
        raise Exception("Error: unable to read raster dataset (%s)" % unicode(e))
    try:
        robjects.r.assign(unicode(newname), result)
    except:
        raise Exception("Error: unable to assign raster object to environment")
    summary = robjects.r.get('summary', mode='function')
    slot = robjects.r.get('@', mode='function')
    print "Name: %s" % unicode(newname)
    print "Source: %s" % unicode(dsn)
    if package == 'raster':
        print "Used package 'raster'"
    else:
        print unicode(summary(slot(result, 'grid')))
        print "Used package 'rgdal'"
    if not newname == name:
        print "**Note: layer name syntax changed"
    return True

# ---------------------------   RVECTOR LAYERS   -------------------------------#

def spQgsVectorLayer(name):
    spatial = robjects.r.get(name)
    type = spType(spatial)
    layer = QgsVectorLayer(type, unicode(name), "memory")
    crs = QgsCoordinateReferenceSystem()
    proj = spatial.do_slot('proj4string').do_slot('projargs')[0]
    if crs.createFromProj4(proj):
        layer.setCrs(crs)
    else:
        print "Error: unable to parse proj4string: using QGIS default"
    provider = layer.dataProvider()
    fields = spFields(spatial)
    provider.addAttributes(fields)
    feats = spData(spatial)
    features = [spFeature(*feat) for feat in feats]
    provider.addFeatures(features)
    layer.updateExtents()
    return layer

def spFields(spatial):
    typeof = robjects.r.get('class', mode='function')
    sapply = robjects.r.get('sapply', mode='function')
    try:
        types = sapply(spatial.do_slot('data'), typeof)
    except:
        raise Exception("R vector layer contains unsupported field type(s)")
    names = list(spatial.do_slot('data').names)
    fields = [QgsField(name, QVariant.Double) if types[i] == "numeric"
              else QgsField(name, QVariant.String) for i, name in enumerate(names)]
    return fields

def spType(spatial):
    check = spatial.rclass[0]
    if check == "SpatialPointsDataFrame": return "Point"
    elif check == "SpatialPolygonsDataFrame": return "Polygon"
    elif check == "SpatialLinesDataFrame": return "LineString"
    else:
        raise Exception("R vector layer is not of type Spatial*DataFrame")

def spGeometry(geom, type):
    def split(L):
        n = len(L)/2
        return [L[:n], L[n:]]
    if type == "Polygon":
        coords = [map(lambda p: QgsPoint(*p), zip(*split(list(po.do_slot('coords')))))
                 for po in geom.do_slot('Polygons')]
        coords = QgsGeometry.fromMultiPolygon([coords])
    elif type == "LineString":
        coords = [map(lambda p: QgsPoint(*p), zip(*split(list(line.do_slot('coords')))))
                 for line in geom.do_slot('Lines')]
        coords = QgsGeometry.fromMultiPolyline(coords)
    elif type == "Point":
        coords = [QgsPoint(*geom)]
        coords = QgsGeometry.fromMultiPoint(coords)
    else:
        raise Exception("unable to convert geometries")
    return coords

def spAttributes(feat):
    class_ = robjects.r['class']
    keys = range(len(feat))
    values = [at.levels[0] if class_(at)[0]=='factor' else at[0] for at in feat]
    return dict(zip(keys, values))

def spData(spatial):
    data = spatial.do_slot('data')
    type, geoms = spGeometries(spatial)
    return [(spAttributes(list(data.rx(i,True))), spGeometry(geoms[i-1], type)) for i in range(1, data.nrow)]

def spGeometries(spatial):
    type = spType(spatial)
    if type == "Polygon":
        geoms = spatial.do_slot('polygons')
    elif type == "LineString":
        geoms = spatial.do_slot('lines')
    elif type == "Point":
        geoms = zip(*split(list(spatial.do_slot('coords'))))
    else:
        raise Exception("unable to obtain geometries")
    return (type, geoms)

def spFeature(attrs, geom):
    feat = QgsFeature()
    feat.setAttributeMap(attrs)
    feat.setGeometry(geom)
    return feat

def main():
    QgsApplication.setPrefixPath('/usr/local', True)
    QgsApplication.initQgis()
    layer = QgsVectorLayer("/home/cfarmer/Downloads/qgis_sample_data/vmap0_shapefiles/majrivers.shp", "majrivers", "ogr")
    provider = layer.dataProvider()
    if not robjects.r.require('sp')[0]:
        raise Exception("Error: missing 'sp' package: classes and methods for spatial data")
    if not robjects.r.require('rgdal')[0]:
        raise Exception("Error: missing 'rgdal' package: classes and methods for spatial data")
    output = qOGRVectorDataFrame(layer, True)
    robjects.r.plot(robjects.r.get("majrivers"))
    s = raw_input('Waiting for input... (Return)')
    

if __name__ == '__main__':
    main()
