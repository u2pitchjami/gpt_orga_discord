import os
import mysql.connector
import re
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Connexion à la BDD
def connect_db():
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }
    return mysql.connector.connect(**DB_CONFIG)

# 🔹 Scanner les dossiers et récupérer les tâches
BASE_PATH = "/mnt/user/Documents/Obsidian/notes"

def get_todos_from_markdown():
    todos = []
    
    for root, _, files in os.walk(BASE_PATH):
        if "Objectives" in root:  # On ne prend que les fichiers dans Objectives/
            category = "projet" if "Projects" in root else "quotidien"
            project_name = root.split("/")[-2]  # Récupère NOM_DU_PROJET

            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.readlines()

                    parent_task = None  # Stocke la tâche principale actuelle

                    for line in content:
                        # Détecte une tâche globale (sans indentation)
                        match_main = re.match(r"^-\s\[\s\]\s(.+)", line)
                        if match_main:
                            parent_task = match_main.group(1).strip()  # Nouvelle tâche principale
                            todos.append((parent_task, category, project_name, None))

                        # Détecte une sous-tâche (indentée)
                        match_sub = re.match(r"^\s+[-*]\s\[\s\]\s(.+)", line)
                        if match_sub and parent_task:
                            sub_task = match_sub.group(1).strip()
                            todos.append((sub_task, category, project_name, parent_task))

    return todos

# 🔹 Importer les tâches en base avec gestion des doublons
def import_todos_to_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    todos = get_todos_from_markdown()
    task_id_map = {}  # Stocke les IDs des tâches principales

    for title, category, project, parent in todos:
        print(f"📌 Vérification : {title} ({category}, projet : {project}, parent: {parent})")

        # Vérifier si la tâche existe déjà
        cursor.execute(
            "SELECT id FROM tasks WHERE title=%s AND category=%s AND project_name=%s",
            (title, category, project)
        )
        existing_task = cursor.fetchone()

        if existing_task:
            print(f"⚠️ Doublon détecté, tâche ignorée : {title}")
            continue  # Ignore la tâche si elle existe déjà

        if parent is None:  # Tâche principale
            cursor.execute(
                "INSERT INTO tasks (title, category, project_name, status) VALUES (%s, %s, %s, 'todo')",
                (title, category, project)
            )
            conn.commit()
            task_id_map[title] = cursor.lastrowid  # Stocke l'ID de la tâche principale

        else:  # Sous-tâche
            parent_id = task_id_map.get(parent)  # Récupère l'ID du parent
            cursor.execute(
                "INSERT INTO tasks (title, category, project_name, status, parent_task_id) VALUES (%s, %s, %s, 'todo', %s)",
                (title, category, project, parent_id)
            )
            conn.commit()

    cursor.close()
    conn.close()
    print("✅ Import terminé, doublons évités !")

# Exécuter l'import
if __name__ == "__main__":
    import_todos_to_db()

