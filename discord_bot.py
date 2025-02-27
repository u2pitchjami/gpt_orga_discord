import discord
import os
from discord.ext import commands
import asyncio
from google_agenda import add_event_to_google_calendar
from dotenv import load_dotenv

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
client = commands.Bot(command_prefix="/", intents=intents)

async def sync_commands():
    await client.wait_until_ready()  
    try:
        synced = await client.tree.sync()
        print(f"📌 {len(synced)} commandes synchronisées avec succès !")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")

@client.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {client.user}")
    client.loop.create_task(sync_commands())

@client.tree.command(name="ajouter_evenement", description="Ajoute un événement à Google Agenda")
async def ajouter_evenement(interaction: discord.Interaction, titre: str, date: str, duree: int):
    response = add_event_to_google_calendar(titre, date, duree)
    await interaction.response.send_message(response)

client.run(TOKEN)
