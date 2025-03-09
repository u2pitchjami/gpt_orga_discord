import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)

# Configurer le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_db():
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        return conn, cursor
    except mysql.connector.Error as err:
        logger.error(f"❌ Erreur connexion DB: {err}")
        raise

# 🔹 1. Vérifier et ajouter les tâches récurrentes si besoin
def check_recurring_tasks():
    conn, cursor = connect_db()
    today = datetime.today().date()

    try:
        cursor.execute("SELECT id, title, last_done, interval_days FROM tasks WHERE interval_days IS NOT NULL")
        tasks = cursor.fetchall()

        for task_id, title, last_done, interval_days in tasks:
            if last_done is None or (last_done + timedelta(days=interval_days)) <= today:
                logger.info(f"📌 Tâche récurrente à faire : {title}")
                cursor.execute("UPDATE tasks SET status='pending' WHERE id=%s", (task_id,))
                conn.commit()
    finally:
        cursor.close()
        conn.close()

# 🔹 2. Récupérer les tâches du jour
def get_todays_tasks():
    conn, cursor = connect_db()
    today = datetime.today().date()

    try:
        cursor.execute("SELECT title FROM tasks WHERE status='todo' AND (due_date=%s OR due_date IS NULL)", (today,))
        tasks = cursor.fetchall()
        return [task[0] for task in tasks]
    finally:
        cursor.close()
        conn.close()

# 🔹 3. Marquer une tâche comme terminée
def mark_task_done(task_title):
    conn, cursor = connect_db()
    today = datetime.today().date()

    try:
        cursor.execute("UPDATE tasks SET status='done', last_done=%s WHERE title=%s", (today, task_title))
        conn.commit()
        logger.info(f"✅ {task_title} marqué comme fait !")
    finally:
        cursor.close()
        conn.close()

# 🔹 4. Ajouter une nouvelle tâche
def add_task(title, category, due_date=None, interval_days=None):
    conn, cursor = connect_db()

    try:
        cursor.execute(
            "INSERT INTO tasks (title, category, due_date, interval_days, status) VALUES (%s, %s, %s, %s, 'todo')",
            (title, category, due_date, interval_days)
        )
        conn.commit()
        logger.info(f"➕ Tâche ajoutée : {title}")
    finally:
        cursor.close()
        conn.close()

# 🔹 5. Interface CLI pour lancer le script
if __name__ == "__main__":
    print("📅 Gestionnaire de tâches")
    
    while True:
        print("\n1️⃣ Voir les tâches du jour")
        print("2️⃣ Ajouter une tâche")
        print("3️⃣ Marquer une tâche comme faite")
        print("4️⃣ Vérifier les tâches récurrentes")
        print("5️⃣ Quitter")
        
        choix = input("👉 Choix : ")

        if choix == "1":
            tasks_today = get_todays_tasks()
            print("📌 Tâches du jour :", tasks_today if tasks_today else "Aucune tâche aujourd’hui.")
        elif choix == "2":
            title = input("📝 Nom de la tâche : ")
            category = input("📂 Catégorie (projet, technique, quotidien, recurrente) : ")
            due_date = input("📅 Date d’échéance (YYYY-MM-DD ou enter pour aucune) : ") or None
            interval_days = input("🔁 Intervalle (si récurrente, nombre de jours) : ") or None
            interval_days = int(interval_days) if interval_days else None
            add_task(title, category, due_date, interval_days)
        elif choix == "3":
            task_title = input("✅ Tâche à marquer comme faite : ")
            mark_task_done(task_title)
        elif choix == "4":
            check_recurring_tasks()
        elif choix == "5":
            print("👋 Bye !")
            break
        else:
            print("⚠️ Choix invalide, essaie encore.")