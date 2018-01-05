import os
from ViciBot import getMyBot

def homepage():
    return '''Bot is running.<br>
    <a href="/chat">Start chat</a><br>
    <a href="https://telegram.me/ImperiumRomanumBot">https://telegram.me/ImperiumRomanumBot</a><br>
    <a href="https://kik.me/vicibot">https://kik.me/vicibot</a>''', 200

port = int(os.environ.get('PORT', 33507))

myBot = getMyBot(HOSTNAME=r"https://vicirobot.herokuapp.com")

myBot.getFlask().route("/", methods=['GET'], endpoint="routeHomepage")(homepage)

myBot.run(host='0.0.0.0', port=port)
