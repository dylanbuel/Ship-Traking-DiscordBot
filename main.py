import asyncio
import websockets
import json
from datetime import datetime, timezone
from discord_webhook import DiscordWebhook

AIS_NAV_STATUS =[
    "underway using engine",
    "at anchor",
    "not under command",
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

async def connect_ais_stream(config):

    print("Setting up Discord webhooks")
    pos_discord_webhook = DiscordWebhook(url=config["WEB_HOOK"], content="Waiting for PositionReport")
    pos_discord_webhook.execute()
    static_discord_webhook = DiscordWebhook(url=config["WEB_HOOK"], content="Waiting for ShipStaticData")
    static_discord_webhook.execute()

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": config["API_KEY"],  # Required !
                             "BoundingBoxes": [[[-90, -180], [90, 180]]], # Required!
                             "FiltersShipMMSI": config["SHIP_MMSI"], # Optional!
                            }

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message["MessageType"]
            
            if message_type == "PositionReport":
                # the message parameter contains a key of the message type which contains the message itself
                ais_message = message['Message']['PositionReport']
                pos_printtext = f"[{datetime.now(timezone.utc)}] ShipId: {ais_message['UserID']} Status: {AIS_NAV_STATUS[ais_message['NavigationalStatus']]} Latitude: {ais_message['Latitude']} Latitude: {ais_message['Longitude']}"                 
                pos_discord_webhook.content = pos_printtext
                pos_discord_webhook.edit()
                print(pos_printtext)
            elif message_type == "ShipStaticData":
                ais_message = message['Message']['ShipStaticData']
                static_printtext = f"[{datetime.now(timezone.utc)}] Destination: {ais_message['Destination']} ETA: Day:{ais_message['Eta']['Day']} Hour:{ais_message['Eta']['Hour']} Minute:{ais_message['Eta']['Minute']}"
                static_discord_webhook.content = static_printtext
                static_discord_webhook.edit()
                print(static_printtext)
            else:
                other_printtext = message
                print(other_printtext)



if __name__ == "__main__":
    config = getconfig()
    asyncio.run(asyncio.run(connect_ais_stream(config)))
