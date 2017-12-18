#! python3
import pickle
from pprint import pprint
import sqlite3

FILE_IN = "vici.pickle"
FILENAME = "vici.db"

data = pickle.load(open(FILE_IN, "rb"))
 
conn = sqlite3.connect(FILENAME)
 
cursor = conn.cursor()


try:
    cursor.execute("DROP TABLE features")
except:
    pass
try:
    cursor.execute("DROP TABLE points")
except:
    pass
try:
    cursor.execute("DROP TABLE lines")
except:
    pass
try:
    cursor.execute("VACUUM")
except:
    pass

    
# create tables
cursor.execute("""CREATE TABLE features
    (id INTEGER PRIMARY KEY,
    identified INTEGER,
    img TEXT,
    isvisible INTEGER,
    kind TEXT,
    summary TEXT,
    title TEXT,
    url TEXT,
    zindex INTEGER,
    zoomnormal INTEGER,
    zoomsmall INTEGER,
    lat REAL,
    lng REAL)
""")

cursor.execute("""CREATE TABLE lines
    (id INTEGER PRIMARY KEY,
    kind TEXT,
    marker INTEGER,
    note TEXT)
""")

cursor.execute("""CREATE TABLE points
    (lineid INTEGER,
    id INTEGER,
    lat REAL,
    lng REAL)
""")


conn.commit()

features = []
ids = set()
for feature in data["features"]:
    if not "id" in feature["properties"]:
        continue

    p = feature["properties"]
    g = feature["geometry"]["coordinates"]

    if p["id"] in ids:
        # Skip duplicates
        print("Skipped duplicate: id =",p["id"])
        continue
    else:
        ids.add(p["id"])

    features.append((p["id"],p["identified"],p["img"],p["isvisible"],p["kind"],p["summary"],p["title"],p["url"],p["zindex"],p["zoomnormal"],p["zoomsmall"],g[1],g[0]))


cursor.executemany('INSERT INTO features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', features)
conn.commit()
features = []


points = []
lines = []
for l in data["lines"]:
    if not "id" in l:
        continue
    lines.append((l["id"],l["kind"],l["marker"],l["note"]))
    j = 1
    for p in l["points"]:
        points.append((l["id"], j, p[0], p[1]))
        j += 1

cursor.executemany('INSERT INTO lines VALUES (?,?,?,?)', lines)
cursor.executemany('INSERT INTO points VALUES (?,?,?,?)', points)
conn.commit()
lines = []
points = []

print("Total number of entries:")
cursor.execute("SELECT COUNT(id) from features")
print(cursor.fetchone())
cursor.execute("SELECT COUNT(id) from lines")
print(cursor.fetchone())
cursor.execute("SELECT COUNT(id) from points")
print(cursor.fetchone())

# Limes
cursor.execute('UPDATE features SET zoomsmall = 3 where title in ("Raetischer Limes", "Obergermanischer Limes", "Vallum Antonini")')

print("create indexes?")
x = int(input("(1/0) = "))
if x == 1:
    cursor.execute('CREATE INDEX f_kind_idx ON features (kind)')
    cursor.execute('CREATE INDEX f_lat_idx ON features (lat ASC)')
    cursor.execute('CREATE INDEX f_lng_idx ON features (lng ASC)')
    cursor.execute('CREATE INDEX p_lat_idx ON points (lat ASC)')
    cursor.execute('CREATE INDEX p_lng_idx ON points (lng ASC)')
    cursor.execute('CREATE INDEX p_lineid_idx ON points (lineid)')
    cursor.execute('CREATE INDEX p_sort_idx ON points (lineid,id ASC)')
    print("Index created!")

conn.commit()
cursor.close()
conn.close()
print("Created file: "+FILENAME)
print("")
print("create gzipped file?")
x = int(input("(1/0) = "))
if x == 1:
    import gzip
    f_in = open(FILENAME, 'rb')
    f_out = gzip.open(FILENAME+".gz", 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    print("Created file: "+FILENAME+".gz")


