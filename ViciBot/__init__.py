import re
import urllib
import requests
import configparser


# Vici
from .vici import Vici


# Bot
from . import botserver as server

from .botserver import telegrambot
from .botserver import kikbot
from .botserver import facebookbot
from .botserver import htmlbot



# Read config file
config = configparser.ConfigParser()
config.read('config.ini')

NAME = config["general"]["name"]
VICIDB = config["general"]["vicidb"]
GOOGLEAPI = config["general"]["googleapi"]

serv = server.ServerHelper()

Regex = serv.vagueReply.regex

class MyViciBot(server.Bot):
    
    vici = Vici(VICIDB)
    
    hearts = [":red_heart:", ":green_heart:", ":black_heart:", ":blue_heart:", ":purple_heart:", ":yellow_heart:"]

    yes = serv.vagueReply.new("positive", hearts+["yes", "ya", "yea", "yeah", "sure", "of course", "ok", "okay", ":thumbs_up:", ":OK_hand:", ":OK_button:", ":COOL_button:", ":heavy_check_mark:", ":white_heavy_check_mark:", ":ballot_box_with_check:"])
    no = serv.vagueReply.new("negative", [Regex("no+"), ":thumbs_down:", ":cross_mark:", ":cross_mark_button:", ":heavy_multiplication_x:", ":no_entry:", ":prohibited:", ":broken_heart:"])

    
    startMessageText = """Welcome to the """+NAME
    startMessageText_full = startMessageText+"""
This bot helps you to access data from vici.org. The data is available to this bot and to you by the following license:

All content on Vici.org is published under the Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0) license.
It may be shared, adapted or commercially used under the condition that a reference with link to http://vici.org/, or to the relevant page on Vici.org, as the source is provided.
If you alter, transform, or build upon this work, you may distribute the resulting work only under the same or similar license to this one. """

    
    geocodeCache = {}
    
    
    @serv.textStartsWith("/test")
    def testMessage(self, msg):
    
        m = re.search(r"\/test\s*(\d+)", msg["text_nice_lower"])
        if m is not None:
            N = int(m.group(1))
        else:
            N = 3000
    
    
        emojis = [':fish:', ':squid:', ':shark:', ':octopus:', ':fried_shrimp:', ':cow:', ':pig:', ':horse:', ':boar:', ':goat:', ':deer:', ':rabbit:', ':sheep:', ':rooster:', ':turkey:', ':duck:', ':panda_face:', ':mushroom:', ':tangerine:', ':lemon:', ':peach:', ':baguette_bread:', ':grapes:', 
        ':tomato:', ':strawberry:', ':banana:', ':cherries:', ':wine_glass:', ':eggplant:', ':ear_of_corn:', ':carrot:', ':cucumber:', ':peanuts:', ':potato:', ':roasted_sweet_potato:', ':honey_pot:', ':poultry_leg:', ':cheese_wedge:', ':pizza:', ':hamburger:', ':burrito:', ':french_fries:', ':stuffed_flatbread:', 
        ':green_salad:', ':bacon:', ':spaghetti:', ':cooked_rice:', ':bento_box:', ':shortcake:', ':cookie:', ':pancakes:', ':chocolate_bar:', ':ice_cream:', ':doughnut:', ':hot_beverage:', ':beer_mug:', ':wrapped_gift:']
    
        text = ""
        
        #for i in range(N):
            #text += "%d %s %s\n" % (i, 5*emojis[i % 50],emojis[i % 50].replace(":","_") )
            #text += "%s\n" % i
            
        text = "a" * N
            
        print(len(text))
        
        SN = "%d" % N
        
        self.sendText(msg, text[:-len(SN)] + SN)
        
        print(len(text))
    

    # Builtin event: called if no other function matches
    @serv.textStartsWith("/search")
    @serv.textStartsWith("search")
    def onOtherResponse(self, msg):
        # Search for features by text
        
        query = msg["text_nice_lower"].strip()
        if query.startswith("/search"):
            query = query[7:]
        if query.startswith("search"):
            query = query[6:]
        query = query.strip()
        
        if len(query) < 3:
            self.sendText(msg, "Search text is to short. Please, be more specific :left-pointing_magnifying_glass:")
            return
        
        features = self.vici.searchFeatures(query)
        if len(features) == 0:
            self.sendText(msg, ":moai: Sorry, no results.")
            return
        
        text = []
        buttons = []
        for row in features:
            text.append("%s /f%d" % (row[1], row[-1]))
            buttons.append(( "%s" % row[1], "/f%d" % row[-1] ))
        
        self.sendTextWithButtons(msg, "\n\n".join(text), buttons=buttons)
        
        
    # Builtin event: called if a location was sent (only Telegram and Facebook support this)
    def onLocation(self, msg):
        # List features in the area
        radius_steps = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 300.0, 1000.0]
        
        self.sendText(msg, str(msg["_location"]))
        lat, lng = msg["_location"]["latitude"], msg["_location"]["longitude"]
        for radius in radius_steps:
            features = self.vici.getFeaturesInCircle(lat, lng , radius)
            if len(features) > 0:
                break

        if len(features) > 0:
            text = []
            buttons = []
            i = 0
            features.sort(key=lambda row: row[-1])  
            for row in features:
                if i == 10:
                    break
                i += 1
                dist = ("%.2fkm" if row[-1] < 5.6 else "%.0fkm") % row[-1]
                
                text.append("%s: %s /f%d" % (dist, row[1], row[-2]))
                buttons.append(( "%s" % row[1], "/f%d" % row[-2] ))
                
            self.sendTextWithButtons(msg, "\n\n".join(text), buttons=buttons)
        

            
        else:
            self.sendText(msg, ":pushpin: Nothing found in your area (radius: %d km)" % radius)

            
            
    @serv.textStartsWith("/map")
    @serv.textStartsWith("map")
    def showMap(self, msg):
        # Send an image of a map with the nearest features
        radius_steps = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 300.0, 1000.0]
        
        # /map 123.23324 -56.5494
        # /map123.23324,-56.5494
        m = re.search(r"map\s*(-?\d+\.\d+)(,|\s+)(-?\d+\.\d+)", msg["text_nice_lower"])
        if m is not None:
            lat, lng = float(m.group(1)), float(m.group(3))
        else:
            # /map Address
            
            m = re.search(r"map\s*(.+)", msg["text_nice_lower"])
            
            if m is None:
                return self.sendText(msg, ":right_arrow: This command shows a map. Either by address or by coordinates. \nCommand format: /map address\nExample: /mapMilano")
            
            query = m.group(1).strip()
            
            # Geocode the query string
            if query in self.geocodeCache: 
                ret = self.geocodeCache[query]
            else:
                url = r"https://maps.googleapis.com/maps/api/geocode/json?address=%s&region=eu&key=%s" % (urllib.parse.quote_plus(query), urllib.parse.quote_plus(GOOGLEAPI))
                r = requests.get(url)
                ret = r.json()
                self.geocodeCache[query] = ret
            
                
            if len(ret["results"]) > 0:
                
                title = ret["results"][0]["formatted_address"]
                lat, lng = ret["results"][0]["geometry"]["location"]["lat"], ret["results"][0]["geometry"]["location"]["lng"]
                
                # Fit bounding area
                ne = ret["results"][0]["geometry"]["viewport"]["northeast"]
                sw = ret["results"][0]["geometry"]["viewport"]["southwest"]
                
                d = self.vici.distance(ne["lat"], ne["lng"], sw["lat"], sw["lng"]) / 2.0
                
                radius_steps = [x for x in radius_steps if x > d]
                
                self.sendText(msg, title)
            else:
                return self.sendText(msg, ":moai: I could not find that address")
        
        
        for radius in radius_steps:
            features = self.vici.getFeaturesInCircle(lat, lng , radius)
            if len(features) > 0:
                break

        if len(features) == 0:
            return self.sendText(msg, ":moai: Sorry, nothing interesting was found in that area :world_map:")
            
            
        # Generate map and text for the labels
        googlemaps = 'https://maps.googleapis.com/maps/api/staticmap?size=700x1200&maptype=roadmap&markers='+urllib.parse.quote_plus('color:0x00DDBB|%f,%f' % (lat,lng))
        i = -1
        labels = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 30
        text = []
        buttons = []
        features.sort(key=lambda row: row[-1])
        for row in features:
            if i == 10:
                break
            i += 1
            dist = ("%.2fkm" if row[-1] < 5.6 else "%.0fkm") % row[-1]
            
            text.append("%s: %s %s /f%d" % (labels[i], dist, row[1], row[-2]))
            buttons.append(( "%s" % labels[i], "/f%d" % row[-2]  ))
            
            googlemaps += "&markers="+ urllib.parse.quote_plus("color:0x%02x0000|label:%s|%f,%f" % (255 - i, labels[i], row[6], row[7]))
            
        googlemaps += "&key="+GOOGLEAPI
        self.sendPhoto(msg, googlemaps)
        self.sendTextWithButtons(msg, "\n\n".join(text), buttons=buttons)
            
            
    @serv.textStartsWith("/f")
    @serv.textRegexMatch("/?f\s*(\d+)", re.IGNORECASE)
    def showFeature(self, msg):
        # Show details of a single record/feature
        
        m = re.match(r"/?f\s*(\d+)", msg["text_nice_lower"])
        if m is None:
            return self.sendText(msg, ":right_arrow: This command shows the details of a single record. Command format for feature with id 123:\n/f123")
        fid = int(m.group(1))
        
        f = self.vici.getFeature(fid)

        text = "%s\n%s" % (f.title, f.summary)

        if f.img:
            self.sendPhoto(msg, "https://static.vici.org/cache/800x0-3%s" % f.img)
            
        self.sendText(msg, text)
        
        self.sendLink(msg, "https://vici.org/vici/%d/" % f.id);
        



    def what(self, msg):
        self.sendText(msg, "Whaaaaat?")

    @serv.textLike("/start")
    def commandStart(self, msg):
        # Show the welcome message
        self.sendText(msg, self.startMessageText_full)
        
        self.sendQuestion(msg, "Do you agree to this license?", responses=[("Yes",self.showHelp, self.yes), ("No", self.pleaseLeave, self.no)], onOtherResponse=self.what)

    def pleaseLeave(self, msg):
        self.sendText(msg, "Please stop using this bot :exclamation_mark:")
        
        
    @serv.textLike("hi")
    @serv.textLike("hey")
    @serv.textLike("hello")
    def showHello(self, msg):
        self.sendText(msg, "Salve :raised_back_of_hand:")
        self.showHelp(msg);

    @serv.textLike("/help")
    @serv.textLike("help")
    def showHelp(self, msg):
        self.sendText(msg, "Just send me the name of an object and I will show you all the records.\n\nOther commands:\n" + 
        "\"/map address\"\ne.g. map Pompeii\n" + 
        "\"/search something\"\ne.g. search Colosseum\n" + 
        "\"/f id\"\ne.g. /f11600\n\n" + 
        "(The slashes at the beginning are optional)")



def getMyBot(HOSTNAME):
    # Run all bots
    
    
    myBot = MyViciBot(serv, NAME)
    
    if "telegrambot" in config:
        myBot.addFlaskBot(bottype=telegrambot.TelegramBot, route=config["telegrambot"]["route"], token=config["telegrambot"]["token"], webhook_host=HOSTNAME)
    
    if "kikbot" in config:
        myBot.addFlaskBot(bottype=kikbot.KikBot, route=config["kikbot"]["route"], name=config["kikbot"]["name"], apikey=config["kikbot"]["apikey"], webhook_host=HOSTNAME)
        
    if "facebookbot" in config:
        myBot.addFlaskBot(bottype=facebookbot.FacebookBot,
                          route=config["facebookbot"]["route"],
                          app_secret=config["facebookbot"]["app_secret"],
                          verify_token=config["facebookbot"]["verify_token"],
                          access_token=config["facebookbot"]["access_token"],
                          start_message=MyViciBot.startMessageText)
                          
    if "htmlbot" in config:
        myBot.addFlaskBot(bottype=htmlbot.HtmlBot, route=config["htmlbot"]["route"])
    
    
    
    return myBot

    
def getMyBot_html():
    # Only run the HMTL bot for easier local testing
    myBot = MyViciBot(serv, NAME)
        
    if "htmlbot" in config:
        myBot.addFlaskBot(bottype=htmlbot.HtmlBot, route=config["htmlbot"]["route"])
    
    return myBot
    
def getMyBot_html_and_telegram():
    # Only run the HMTL bot for easier local testing
    myBot = MyViciBot(serv, NAME)
        
    if "htmlbot" in config:
        myBot.addFlaskBot(bottype=htmlbot.HtmlBot, route=config["htmlbot"]["route"])
        
    if "telegrambot" in config:
        myBot.addBot(bottype=telegrambot.TelegramBotWithoutFlask, token=config["telegrambot"]["token"])
    
    
    return myBot
    
    

if __name__ == '__main__':
    getMyBot_html().run(port=80) # http://127.0.0.1:80/chat

