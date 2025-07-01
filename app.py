# app.py (Versão 10 - Aba "Similar" funcional)
import streamlit as st
import random
from datetime import datetime
from tmdb_api import (
    discover_media, get_media_details, get_genres, get_list_on_streaming,
    search_media, get_similar_media # Nossas novas funções
)
from data_manager import (
    load_data, save_data,
    WATCHED_FILE
)

# --- Configuração da Página e Cache ---
st.set_page_config(page_title="Cine-Nós", page_icon="🎬", layout="wide")
@st.cache_data(ttl=3600)
def cached_get_genres(media_type): return get_genres(media_type)
@st.cache_data(ttl=3600)
def cached_get_list_on_streaming(media_type, sort_by): return get_list_on_streaming(media_type, sort_by)
@st.cache_data(ttl=3600)
def cached_get_media_details(media_type, media_id): return get_media_details(media_type, media_id)
@st.cache_data(ttl=3600)
def cached_get_similar_media(media_type, media_id): return get_similar_media(media_type, media_id)

# --- Componentes de UI ---
def display_horizontal_media_list(media_list, list_title):
    st.subheader(list_title)
    if not media_list:
        st.warning("Nenhum item encontrado.")
        return
    cols = st.columns(10)
    for i, media in enumerate(media_list[:10]):
        with cols[i]:
            if media.get('poster_path'):
                st.image(f"https://image.tmdb.org/t/p/w200{media.get('poster_path')}", use_container_width=True)
            title = media.get('title') or media.get('name')
            st.caption(f"**{title}**")

# --- Barra Lateral ---
st.sidebar.header("⚙️ Opções de Sorteio")
# (código da sidebar sem alterações)
special_options = ["Populares no Streaming", "Bem Avaliados no Streaming"]
sort_option = st.sidebar.radio("Escolha o tipo de sorteio:", ["Por Gênero", *special_options], horizontal=True, label_visibility="collapsed")
if sort_option == "Por Gênero":
    st.sidebar.caption("Sorteio por gênero filtra por: Netflix, Prime Video e Max.")
    all_movie_genres_map = cached_get_genres('movie')
    our_initial_genre_names = ["Ação", "Comédia", "Romance", "Aventura", "Drama", "Ficção Científica", "Thriller", "Mistério", "Crime"]
    available_genres = {name: id for id, name in all_movie_genres_map.items() if name in our_initial_genre_names}
    selected_genre_names = st.sidebar.multiselect("Selecione os gêneros:", options=list(available_genres.keys()), default=list(available_genres.keys()))
    selected_genre_ids = [available_genres[name] for name in selected_genre_names]
else:
    st.sidebar.info(f"O sorteio usará a lista de **{sort_option.replace(' no Streaming', '')}** filtrada para Netflix, Prime Video e Max.")

# --- Layout Principal ---
st.title("🎬 Cine-Nós")
tab_sorteio, tab_descobrir, tab_assistidos, tab_similar = st.tabs(["Sorteio 🎲", "Descobrir 🧭", "Já Assistimos ✔️", "Encontrar Similares 🔎"])

# --- ABA SORTEIO ---
with tab_sorteio:
    # (código da aba de sorteio sem alterações)
    st.header("Não sabem o que assistir? Deixem a sorte decidir!")
    def handle_sort(media_type):
        with st.spinner(f"Sorteando..."):
            media_item = None
            if sort_option == "Por Gênero":
                if not selected_genre_ids: st.warning("Selecione ao menos um gênero na barra lateral."); return
                genre_ids_to_use = selected_genre_ids
                if media_type == 'tv':
                    all_tv_genres_map = cached_get_genres('tv'); tv_genre_names = [name for name, id_ in available_genres.items() if id_ in selected_genre_ids]
                    genre_ids_to_use = [id_ for name, id_ in all_tv_genres_map.items() if name in tv_genre_names]
                media_item = discover_media(media_type, genre_ids_to_use)
            elif sort_option == "Populares no Streaming":
                media_list = cached_get_list_on_streaming(media_type, 'popularity.desc');
                if media_list: media_item = random.choice(media_list)
            elif sort_option == "Bem Avaliados no Streaming":
                media_list = cached_get_list_on_streaming(media_type, 'vote_average.desc');
                if media_list: media_item = random.choice(media_list)
            if media_item: st.session_state.sorted_media = {'type': media_type, 'data': media_item}
            else: st.error("Não foi possível sortear um item com as opções selecionadas.")
    with st.expander("**Sorteio de Filme 🍿**", expanded=True):
        c1, c2 = st.columns(2);
        if c1.button("Vez de Gustavo", use_container_width=True, key="gustavo_movie"): handle_sort('movie')
        if c2.button("Vez de Marina", type="primary", use_container_width=True, key="marina_movie"): handle_sort('movie')
    with st.expander("**Sorteio de Série 📺**"):
        if st.button("Sortear uma Série!", use_container_width=True): handle_sort('tv')
    if 'sorted_media' in st.session_state and st.session_state.sorted_media:
        details = cached_get_media_details(st.session_state.sorted_media['type'], st.session_state.sorted_media['data']['id'])
        if details:
            st.divider(); st.subheader("O resultado é..."); info_col, poster_col = st.columns([2, 1]); title = details.get('title') or details.get('name')
            with info_col:
                st.header(title); st.write(details.get('overview', "Sinopse não disponível."))
                providers = details.get('watch/providers', {}).get('results', {}).get('BR', {});
                if providers and 'flatrate' in providers:
                    st.write("**Disponível em:**"); logos = "".join([f"<img src='https://image.tmdb.org/t/p/w45{p['logo_path']}' style='margin-right: 10px; border-radius: 7px;'>" for p in providers['flatrate']]); st.markdown(logos, unsafe_allow_html=True)
            with poster_col:
                if details.get('poster_path'): st.image(f"https://image.tmdb.org/t/p/w500{details['poster_path']}")
            st.divider(); st.subheader("O que fazer agora?"); cols = st.columns(3)
            if cols[0].button("✅ Marcar como assistido", key=f"watch_{details['id']}", use_container_width=True):
                watched_list = load_data(WATCHED_FILE, default_data=[]);
                if not any(item['id'] == details['id'] for item in watched_list):
                    watched_list.append({"id": details['id'], "type": st.session_state.sorted_media['type'], "title": title, "poster_path": details.get('poster_path'), "watched_date": datetime.now().isoformat()})
                    save_data(WATCHED_FILE, watched_list); st.success(f"'{title}' foi adicionado à sua lista de assistidos!"); del st.session_state.sorted_media; st.rerun()
                else: st.info(f"'{title}' já está na sua lista de assistidos.")
            if cols[1].button("❤️ Adicionar aos favoritos", key=f"fav_{details['id']}", use_container_width=True): st.info("Funcionalidade de Favoritos em breve!")
            if cols[2].button("🔎 Ver similares", key=f"sim_{details['id']}", use_container_width=True): st.info("Funcionalidade de Similares em breve!")

# --- ABA "JÁ ASSISTIMOS" ---
with tab_assistidos:
    # (código da aba de assistidos sem alterações)
    st.header("Filmes e Séries que já assistimos"); watched_list = load_data(WATCHED_FILE, default_data=[])
    if not watched_list: st.info("A sua lista de assistidos está vazia. Marque um filme ou série como assistido para começar!")
    else:
        watched_list.reverse()
        for item in watched_list:
            c1, c2 = st.columns([1, 4])
            with c1:
                if item.get('poster_path'): st.image(f"https://image.tmdb.org/t/p/w200{item['poster_path']}", use_container_width=True)
            with c2:
                st.subheader(f"{'🍿' if item['type'] == 'movie' else '📺'} {item['title']}"); st.caption(f"Assistido em: {datetime.fromisoformat(item['watched_date']).strftime('%d/%m/%Y às %H:%M')}")
            st.divider()

# --- ABA DESCOBRIR ---
with tab_descobrir:
    # (código da aba descobrir sem alterações)
    st.header("Explore Filmes e Séries nos Seus Streamings"); st.header("Filmes")
    display_horizontal_media_list(cached_get_list_on_streaming('movie', 'popularity.desc'), "Populares")
    display_horizontal_media_list(cached_get_list_on_streaming('movie', 'vote_average.desc'), "Bem Avaliados")
    st.divider(); st.header("Séries")
    display_horizontal_media_list(cached_get_list_on_streaming('tv', 'popularity.desc'), "Populares")
    display_horizontal_media_list(cached_get_list_on_streaming('tv', 'vote_average.desc'), "Bem Avaliadas")

# --- ABA SIMILAR ---
with tab_similar:
    st.header("Encontrar Filmes e Séries Similares")
    query = st.text_input("Digite o nome de um filme ou série que você gosta:", key="similar_query")

    if query:
        search_results = search_media(query)
        if search_results:
            st.write("Encontramos os seguintes títulos. Selecione um para ver os similares:")
            
            for result in search_results[:5]: # Mostra os 5 primeiros resultados
                media_type = result.get('media_type')
                title = result.get('title') or result.get('name')
                year = (result.get('release_date') or result.get('first_air_date', ''))[:4]
                
                # Botão para o usuário selecionar o item correto
                if st.button(f"{'🍿' if media_type == 'movie' else '📺'} {title} ({year})", key=f"select_{result['id']}"):
                    st.session_state.selected_for_similar = result
        else:
            st.warning("Nenhum resultado encontrado para a sua busca.")

    # Se um item foi selecionado, busca e exibe os similares
    if 'selected_for_similar' in st.session_state:
        selected = st.session_state.selected_for_similar
        media_type = selected.get('media_type')
        title = selected.get('title') or selected.get('name')
        
        st.divider()
        st.subheader(f"Recomendações similares a '{title}':")
        
        similar_list = cached_get_similar_media(media_type, selected['id'])
        if similar_list:
            # Reutiliza nosso componente de lista horizontal
            display_horizontal_media_list(similar_list, "")
        else:
            st.info("Não encontramos recomendações similares para este título.")