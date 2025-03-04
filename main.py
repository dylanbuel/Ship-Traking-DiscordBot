import asyncio
import websockets
import json
import time
from discord_webhook import DiscordWebhook

AIS_NAV_STATUS =[
    "underway using engine",
    "at anchor",
    "not under command",
    "constrained by her draught",
    "restricted maneuverability",
    "moored",
    "aground",
    "engaged in fishing",
    "underway sailing",
    "reserved",
    "reserved",
    "power-driven vessel towing astern",
    "power-driven vessel pushing ahead or towing alongside",
    "reserved",
    "Search and Rescue / Man Overboard",
    "undefined"]

def getconfig():
    with open("config.json", 'r') as file:
        return json.load(file)

def getdiscordtimestamp():
    return f"<t:{round(time.time())}:f>"

async def connect_ais_stream(config):

    print("Setting up Discord webhooks")
    startup_message = "# Where is Capy \n"
    pos_printtext = "Waiting for PositionReport"
    static_printtext = "Waiting for ShipStaticData"
    text_print = startup_message + pos_printtext + "\n" + static_printtext
    discord_webhook = DiscordWebhook(url=config["WEB_HOOK"], content=text_print)
    discord_webhook.execute()

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": config["API_KEY"],  # Required !
                             "BoundingBoxes": [[[-90, -180], [90, 180]]], # Required!
                             "FiltersShipMMSI": config["SHIP_MMSI"], # Optional!
                            }

        subscribe_message_json = json.dumps(subscribe_message)
        print("Waiting for message")
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message["MessageType"]
            
            if message_type == "PositionReport":
                # the message parameter contains a key of the message type which contains the message itself
                ais_message = message['Message']['PositionReport']
                pos_printtext = f"{getdiscordtimestamp()} **ShipId:** {ais_message['UserID']} **Status:** {AIS_NAV_STATUS[ais_message['NavigationalStatus']]} **Latitude:** {ais_message['Latitude']} **Latitude:** {ais_message['Longitude']}"
                print(pos_printtext)
                pos_printtext = pos_printtext + "\n" + f"https://www.google.com/maps/place/@{ais_message['Latitude']},{ais_message['Longitude']},12.96z"
            elif message_type == "ShipStaticData":
                ais_message = message['Message']['ShipStaticData']
                static_printtext = f"{getdiscordtimestamp()} **Name:** {ais_message['Name']} **Destination:** {ais_message['Destination']} **ETA:** Day:{ais_message['Eta']['Day']} Hour:{ais_message['Eta']['Hour']} Minute:{ais_message['Eta']['Minute']}"
                print(static_printtext)
            else:
                other_printtext = message
                print(other_printtext)
            
            text_print = startup_message + pos_printtext + "\n" + static_printtext
            discord_webhook.content = text_print
            discord_webhook.edit()



if __name__ == "__main__":
    config = getconfig()
    asyncio.run(asyncio.run(connect_ais_stream(config)))
