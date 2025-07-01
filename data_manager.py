# data_manager.py
import json
import os

# Define o caminho para a pasta de dados
DATA_DIR = "data"
FAVORITE_GENRES_FILE = os.path.join(DATA_DIR, "favorite_genres.json")
WATCHED_FILE = os.path.join(DATA_DIR, "watched.json")
APP_STATE_FILE = os.path.join(DATA_DIR, "app_state.json")

def _ensure_data_dir():
    """Garante que o diretório 'data' exista."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_data(file_path, default_data=None):
    """
    Carrega dados de um arquivo JSON. Se o arquivo não existir,
    cria ele com os dados padrão.
    """
    _ensure_data_dir()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if default_data is not None:
            save_data(file_path, default_data)
        return default_data

def save_data(file_path, data):
    """Salva dados em um arquivo JSON."""
    _ensure_data_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)