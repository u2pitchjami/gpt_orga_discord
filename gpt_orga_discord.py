import openai
import discord
import os
import asyncio
import re
import datetime
from dotenv import load_dotenv
from google_agenda import get_todays_events, add_event_to_google_calendar




# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)

# 🔹 Clés API OpenAI et Discord
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
OBSIDIAN_TODO_FILE = os.getenv('OBSIDIAN_TODO_FILE')


async def main():
    async with client:
        await client.start(DISCORD_BOT_TOKEN)

def read_tasks_from_obsidian():
    
    if not os.path.exists(OBSIDIAN_TODO_FILE):
        return "Aucune tâche enregistrée."

    with open(OBSIDIAN_TODO_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    categories = {
        "🔥 Priorité haute": [],
        "✅ Routine quotidienne": [],
        "🛠️ Projets en cours": []
    }
    
    
    today = datetime.date.today()
    
    
    for line in lines:
        
        match = re.match(r"- \[ \] \*\*(.+?)\*\* \(📅 (.+?)\)", line)  # Ex: "- [ ] **Payer une facture** (📅 Avant le 03/03)"
        
        if match:
            task, deadline = match.groups()
            deadline_date = parse_deadline(deadline)

            if deadline_date and deadline_date < today:
                task = f"🚨 **URGENT** → {task} (⚠️ {deadline})"
            
            categories["🔥 Priorité haute"].append(task)
            continue
        
        match = re.match(r"- \[ \] \*\*(.+?)\*\* \(⏳ (.+?)\)", line)  # Ex: "- [ ] **Chercher du travail** (⏳ 1x par jour)"
        if match:
            task, frequency = match.groups()
            categories["✅ Routine quotidienne"].append(f"{task} ({frequency})")
            continue
        
        match = re.match(r"- \[ \] \*\*(.+?)\*\*", line)  # Ex: "- [ ] **Optimiser mes scripts Docker**"
        if match:
            task = match.group(1)
            categories["🛠️ Projets en cours"].append(task)
    
    briefing = "**📝 Briefing du jour**\n\n"
    for category, tasks in categories.items():
        if tasks:
            briefing += f"**{category}**\n" + "\n".join(f"- {t}" for t in tasks) + "\n\n"
    
        print("DEBUG - Catégories détectées :")
    for category, tasks in categories.items():
        print(f"\n{category}:")
        for task in tasks:
            print(f"- {task}")

    print("\nDEBUG - Briefing généré :\n", briefing)

    
    return briefing if briefing.strip() else "Aucune tâche enregistrée."

# 🔹 Fonction pour convertir une deadline (ex: "Avant le 03/03") en date
def parse_deadline(text):
    match = re.search(r"(\d{2})/(\d{2})", text)
    if match:
        day, month = map(int, match.groups())
        year = datetime.date.today().year
        return datetime.date(year, month, day)
    return None

# 🔹 Fonction pour demander un briefing au GPT Orga
def get_gpt_briefing(tasks):
    print ("entrée brief")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Tu es un assistant d'organisation. Aide-moi à structurer ma journée."},
            {"role": "user", "content": f"Voici mes tâches:\n{tasks}\nPeux-tu me proposer un plan d'action pour aujourd'hui ?"}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content

# 🔹 Gestion propre d'asyncio avec discord.py
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")
    channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
    print(f"Channel: {channel}")  # Vérifie si c'est None ou un objet valide
    print(f"Type de channel: {type(channel)}")  # Vérifie le type exact
    print(dir(channel))  # Liste toutes les méthodes et attributs disponibles

    permissions = channel.permissions_for(channel.guild.me)
    print(f"Le bot peut envoyer des messages ? {permissions.send_messages}")

    print ("2")
    if channel:
        print ("3")
        tasks = read_tasks_from_obsidian()  # Récupère tes tâches depuis Obsidian
        print ("4")
        agenda = get_todays_events()  # Récupère tes événements Google Agenda
        print ("5")
        briefing = get_gpt_briefing(tasks)  # Demande un briefing à GPT
        print ("6")
        full_message = f"{agenda}\n\n{briefing}"  # Combine tout
        print (full_message)
        print(f"Type de full_message: {type(full_message)}")
        print(f"Longueur de full_message: {len(full_message) if isinstance(full_message, str) else 'N/A'}")
        if len(full_message) > 2000:
            print("Message trop long, découpage en plusieurs morceaux...")
            chunks = [full_message[i:i+2000] for i in range(0, len(full_message), 2000)]
            for i, chunk in enumerate(chunks, start=1):
                await channel.send(f"({i}/{len(chunks)})\n{chunk}")
        else:
            await channel.send(full_message)
                
    await client.close()

# 🔹 Démarrer le bot proprement
if __name__ == "__main__":
    try:
        #asyncio.run(main())
        asyncio.run(client.start(DISCORD_BOT_TOKEN))
        print ("1")
    except RuntimeError:  # Si un event loop est déjà en cours
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.start(DISCORD_BOT_TOKEN))