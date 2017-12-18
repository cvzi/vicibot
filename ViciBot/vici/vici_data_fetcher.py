#! python3
import urllib.request
import json
import pickle
import re

print("Download and pickle?")
x = input("yes/no: ")
if x != "yes":
    print("Cancelled")
    exit()


url = r'http://vici.org/data.php'
outfile = r"vici.pickle"


print("Downloading:\n%s" % url)

with urllib.request.urlopen(url) as r:
    s = r.read().decode(r.info().get_param('charset') or 'utf-8')

    

print("Correcting errors...")

    
botches = ["\,\[-?\d+\.\d+\,-?\d+\}\,", "\,\[-?\d+\.\d+\}\,", "\,\[-?\d+\.\d+\,-?\d+\.\}\,"]
    
for botch in botches:
    s = re.sub(botch, "]},", s)


print("Decoding JSON...")

data = json.loads(s)

print("Saving pickle file...")

with open(outfile, "wb") as fout:
    pickle.dump(data, fout)
    
print("Done:\n%s" % outfile)