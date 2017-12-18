import sqlite3
import math
import collections

from . import geolocation

GeoLocation = geolocation.GeoLocation

class Vici:

    def __init__(self, databasefile):

        # same_thread, because we never write to the database
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
        self.conn = sqlite3.connect(databasefile, check_same_thread=False)
        
    def distance(self, lat0, lng0, lat1, lng1, zoom=1000.0):
        
        loc0 = GeoLocation.from_degrees(lat0, lng0)
        loc1 = GeoLocation.from_degrees(lat1, lng1)
        
        return loc0.distance_to(loc1)
        
        

    def getFeaturesInCircle(self, lat0, lng0, distance, zoom=1000.0):
        """
        :param distance: in kilometers
        """

        
        ret = []

        loc = GeoLocation.from_degrees(lat0, lng0)
        lat0_r, lng0_r = loc.rad_lat, loc.rad_lon
        bounding = loc.bounding_locations(distance)
        distance_div_radius = distance / GeoLocation.EARTH_RADIUS

        meridian180WithinDistance = bounding[0].rad_lon > bounding[1].rad_lon
        
        c = self.conn.cursor()


        # Line ids in bounding rect

        query = """SELECT DISTINCT points.lineid, points.lat, points.lng
                    FROM points
                    WHERE
                    (points.lat >= %f AND points.lat <= %f)
                    AND
                    (points.lng >= %f %s points.lng <= %f)""" % (
                    bounding[0].deg_lat,
                    bounding[1].deg_lat,
                    bounding[0].deg_lon,
                    "OR" if meridian180WithinDistance else "AND",
                    bounding[1].deg_lon
                        )

        c.execute(query)


        # Line ids in circle
        
        point_distance = {}
        
        batch_size = 1000
        while True:
            rows = c.fetchmany(batch_size)
            if not rows: break
            for pid, lat, lng in rows:
                lat_r = math.radians(lat)
                lng_r = math.radians(lng)
                d = math.acos(math.sin(lat0_r) * math.sin(lat_r) + math.cos(lat0_r) * math.cos(lat_r) * math.cos(lng_r - lng0_r))
                if d <= distance_div_radius:
                    d *= GeoLocation.EARTH_RADIUS
                    if pid not in point_distance or point_distance[pid] > d:
                        point_distance[pid] = d
                        
                    
        point_ids = [str(id) for id in point_distance]
        
        if len(point_ids) > 0:

            # Join feature data to relevant line ids
            
            query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                    points.lineid, points.id, points.lat, points.lng, 
                    lines.kind, lines.note, 
                    features.zoomnormal, features.zoomsmall, features.id
                    FROM points, lines, features 
                    WHERE points.lineid IN (
                        %s
                    )
                    AND features.zoomsmall <= %f
                    AND features.id = lines.marker
                    AND points.lineid = lines.id
                    ORDER BY points.lineid, points.id""" % (
                        ", ".join(point_ids),
                        zoom
                        )
            query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                    points.lineid, points.id, points.lat, points.lng, 
                    lines.kind, lines.note, 
                    features.zoomnormal, features.zoomsmall, features.id
                    FROM points, lines, features 
                    WHERE points.lineid IN (
                        %s
                    )
                    AND features.zoomsmall <= %f
                    AND features.id = lines.marker
                    AND points.lineid = lines.id
                    GROUP BY features.id
                    ORDER BY features.id""" % (
                        ", ".join(point_ids),
                        zoom
                        )
                        
                        
            c.execute(query)
            
            while True:
                rows = c.fetchmany(batch_size)
                if not rows: break
                for row in rows:
                    lat_r, lng_r = math.radians(row[6]), math.radians(row[7])
                    d = math.acos(math.sin(lat0_r) * math.sin(lat_r) + math.cos(lat0_r) * math.cos(lat_r) * math.cos(lng_r - lng0_r))
                    row = list(row)
                    row.append(d*GeoLocation.EARTH_RADIUS)
                    ret.append(row)

        # Others in bounding rectangle
        
        query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                features.zoomnormal, features.zoomsmall, features.lat, features.lng, features.id
                FROM features 
                WHERE
                features.zoomsmall <= %f
                AND
                (features.lat >= %f AND features.lat <= %f)
                AND
                (features.lng >= %f %s features.lng <= %f)
                ORDER BY features.id""" % (
                    zoom,
                    bounding[0].deg_lat,
                    bounding[1].deg_lat,
                    bounding[0].deg_lon,
                    "OR" if meridian180WithinDistance else "AND",
                    bounding[1].deg_lon 
                    )
        c.execute(query)

        # Others in circle

        while True:
            rows = c.fetchmany(batch_size)
            if not rows: break
            for row in rows:
                lat_r, lng_r = math.radians(row[6]), math.radians(row[7])
                d = math.acos(math.sin(lat0_r) * math.sin(lat_r) + math.cos(lat0_r) * math.cos(lat_r) * math.cos(lng_r - lng0_r))
                if d <= distance_div_radius:
                    row = list(row)
                    row.append(d*GeoLocation.EARTH_RADIUS)
                    ret.append(row)

        
        c.close()
  

        return ret


    def getFeaturesInRect(self, lat0, lng0, lat1, lng1, zoom=1000.0):


        minLat, maxLat = sorted([lat0, lat1])
        minLng, maxLng = sorted([lng0, lng1])

        # Lines
        c = self.conn.cursor()
        query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                points.lineid, points.id, points.lat, points.lng, 
                lines.kind, lines.marker, lines.note, 
                features.zoomnormal, features.zoomsmall, features.id
                FROM points, lines, features 
                WHERE features.id = lines.marker
                AND points.lineid = lines.id 
                AND features.zoomsmall <= %f
                AND points.lineid IN (
                SELECT DISTINCT points.lineid 
                FROM points
                WHERE points.lat >= %f
                AND points.lat <= %f
                AND points.lng >= %f
                AND points.lng <= %f) 
                ORDER BY points.lineid, points.id""" % (zoom, minLat, maxLat, minLng, maxLng)
        c.execute(query)

        ret = c.fetchall()

        # Others
        query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                features.zoomnormal, features.zoomsmall, features.lat, features.lng, features.id
                FROM features 
                WHERE 
                AND features.zoomsmall <= %f
                AND features.lat >= %f
                AND features.lat <= %f
                AND features.lng >= %f
                AND features.lng <= %f
                ORDER BY features.id""" % (zoom, minLat, maxLat, minLng, maxLng)
        c.execute(query)

        ret += c.fetchall()
        
        
        c.close()

        return ret
    
    def searchFeatures(self, str):
        str = "%" + str + "%"

        # Others
        query = """SELECT features.isvisible,features.title,features.summary,features.url, 
                features.zoomnormal, features.zoomsmall, features.lat, features.lng, features.id
                FROM features 
                WHERE features.title LIKE ?
                UNION
                SELECT features.isvisible,features.title,features.summary,features.url, 
                features.zoomnormal, features.zoomsmall, features.lat, features.lng, features.id
                FROM features 
                WHERE features.summary LIKE ?
                """
                
        c = self.conn.cursor()
        c.execute(query, (str, str))

        ret = c.fetchall()
        
        c.close()

        return ret

        
    def getFeature(self, fid):
    
        fid = int(fid)
        
        fields = "id,identified,img,isvisible,kind,summary,title,url,zindex,zoomnormal,zoomsmall,lat,lng"
    
        c = self.conn.cursor()
        query = """SELECT %s
                FROM features 
                WHERE features.id = %d""" % (fields, fid)
        c.execute(query)

        ret = c.fetchone()
        c.close()
        
        if ret is None:
            return None
        Feature = collections.namedtuple('Feature', fields)
        r = Feature(*ret)

        return r
