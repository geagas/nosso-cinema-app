# tmdb_api.py (Versão 4.1 - Correção do datetime)
import requests
import random
import os
# CORREÇÃO AQUI: Importamos o módulo `datetime` e a classe `timedelta` separadamente.
from datetime import datetime, timedelta

# --- Configuração da API ---
API_KEY = os.getenv("TMDB_API_KEY", "1c0f1853e2af2a54877584e697d6e769") 
BASE_URL = "https://api.themoviedb.org/3"

# --- Constantes para Filtros ---
BRAZIL_PROVIDER_IDS = "8|119|1899|384"
ANIMATION_GENRE_ID = "16"

# --- NOVAS FUNÇÕES: Busca e Similares ---

def search_media(query, media_type='multi'):
    """Busca por filmes, séries ou pessoas. 'multi' busca em ambos."""
    url = f"{BASE_URL}/search/{media_type}"
    params = {'api_key': API_KEY, 'language': 'pt-BR', 'query': query, 'page': 1}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        # Filtra resultados que não sejam filme ou tv
        results = response.json().get('results', [])
        return [item for item in results if item.get('media_type') in ['movie', 'tv']]
    except requests.RequestException as e:
        print(f"Erro ao buscar por '{query}': {e}")
        return []

def get_similar_media(media_type, media_id):
    """Busca mídias similares a um filme ou série específico."""
    url = f"{BASE_URL}/{media_type}/{media_id}/similar"
    params = {'api_key': API_KEY, 'language': 'pt-BR', 'page': 1}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.RequestException as e:
        print(f"Erro ao buscar similares para {media_type} {media_id}: {e}")
        return []


# --- Funções existentes (sem alterações) ---

def discover_media(media_type, genre_ids):
    if not genre_ids: return None
    genre_string = ",".join(map(str, genre_ids))
    url = f"{BASE_URL}/discover/{media_type}"
    params = {
        'api_key': API_KEY, 'language': 'pt-BR', 'sort_by': 'popularity.desc',
        'include_adult': 'false', 'watch_region': 'BR',
        'with_watch_providers': BRAZIL_PROVIDER_IDS,
        'with_genres': genre_string, 'without_genres': ANIMATION_GENRE_ID,
        'page': 1
    }
    if media_type == 'movie': params['include_video'] = 'false'
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        total_pages = min(data.get('total_pages', 0), 500)
        if total_pages == 0: return None
        random_page = random.randint(1, total_pages)
        params['page'] = random_page
        final_response = requests.get(url, params=params)
        final_response.raise_for_status()
        results = final_response.json().get('results', [])
        return random.choice(results) if results else None
    except requests.RequestException as e:
        print(f"Erro ao sortear {media_type}: {e}")
        return None

def get_list_on_streaming(media_type, sort_by='popularity.desc'):
    url = f"{BASE_URL}/discover/{media_type}"
    params = {
        'api_key': API_KEY, 'language': 'pt-BR', 'sort_by': sort_by,
        'include_adult': 'false', 'watch_region': 'BR',
        'with_watch_providers': BRAZIL_PROVIDER_IDS,
        'without_genres': ANIMATION_GENRE_ID, 'page': 1
    }
    if sort_by == 'vote_average.desc':
        params['vote_count.gte'] = 500
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.RequestException as e:
        print(f"Erro ao buscar lista de {media_type} com ordenação {sort_by}: {e}")
        return []

def get_media_details(media_type, media_id):
    url = f"{BASE_URL}/{media_type}/{media_id}"
    params = {'api_key': API_KEY, 'language': 'pt-BR', 'append_to_response': 'watch/providers'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erro ao buscar detalhes de {media_type} {media_id}: {e}")
        return None

def get_genres(media_type='movie'):
    url = f"{BASE_URL}/genre/{media_type}/list"
    params = {'api_key': API_KEY, 'language': 'pt-BR'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return {genre['id']: genre['name'] for genre in response.json()['genres']}
    except requests.RequestException as e:
        print(f"Erro ao buscar gêneros de {media_type}: {e}")
        return {}