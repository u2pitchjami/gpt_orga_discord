from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import os
import pytz
from dotenv import load_dotenv
import discord
import asyncio

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)
# 🔹 Remplace par le chemin de ton fichier credentials.json
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
CALENDAR = os.getenv('CALENDAR')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

# Définis ton fuseau horaire (ex: France = "Europe/Paris")
LOCAL_TZ = pytz.timezone("Europe/Paris")


# 🔹 Authentification Google API
SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
service = build("calendar", "v3", credentials=creds)
calendar_list = service.calendarList().list().execute()


def add_event_to_google_calendar(summary, start_time, duration_minutes=60):
    """
    Ajoute un événement à Google Agenda.
    - summary : Titre de l'événement
    - start_time : Datetime en format ISO (ex: "2025-03-01T14:00:00")
    - duration_minutes : Durée en minutes (par défaut 1h)
    """
    calendar_list = service.calendarList().list().execute()
    
    for cal in calendar_list["items"]:
        print(f"📅 Agenda détecté : {cal['summary']} (ID : {cal['id']})")

    end_time = datetime.datetime.fromisoformat(start_time) + datetime.timedelta(minutes=duration_minutes)
    event = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "Europe/Paris"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Paris"},
    }

    event = service.events().insert(calendarId=CALENDAR, body=event).execute()
    print("📌 DEBUG : Événement ajouté avec ID :", event.get("id"))
    print("📌 DEBUG : Google API Response :", event)

    return f"📅 Événement ajouté : {event['summary']} le {event['start']['dateTime']}"


# 🔹 Fonction pour envoyer un rappel Discord
async def send_reminder():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ Connecté pour les rappels en tant que {client.user}")
        channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
        print(f"📌 Vérification du channel : {channel}")  # DEBUG
        # if channel:
        #     await channel.send("🚀 Test de rappel, ça fonctionne ?")
        # else:
        #     print("❌ Erreur : Channel non trouvé, vérifie DISCORD_CHANNEL_ID !")
        while True:
            print("⏳ Vérification des événements Google Agenda...")
            events = get_todays_events()
            print("📌 Événements détectés :", events)
            now = datetime.datetime.now(LOCAL_TZ)  # Mettre l'heure actuelle dans le bon fuseau

            for event in events:
                start_time = event["start"].get("dateTime", event["start"].get("date"))
                if start_time:
                    event_time = datetime.datetime.fromisoformat(start_time).replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
                    diff = (event_time - now).total_seconds()

                    if 0 < diff <= 1800:  # Moins de 30 minutes avant
                        print(f"🔔 Envoi d'un rappel Discord pour {event['summary']}")
                        await channel.send(f"⏳ **Rappel** : {event['summary']} commence dans 30 minutes !")

            await asyncio.sleep(600)  # Vérifie toutes les 10 minutes


    await client.start(DISCORD_BOT_TOKEN)  # ✅ Compatible avec async

# 🔹 Fonction pour récupérer les événements du jour
def get_todays_events():
    print ("entrée get_todays")
    now = datetime.datetime.now(datetime.UTC).isoformat()

    events_result = service.events().list(
        calendarId=CALENDAR,
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    if not events:
        return "📅 Aucun événement prévu aujourd’hui."
    
    event_list = "**📅 Événements du jour :**\n"
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        event_list += f"- {event['summary']} ({start})\n"
    
    return event_list

# 🔹 Test : affiche les événements du jour
if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())  # ✅ Force un nouvel event loop
    asyncio.run(send_reminder())
