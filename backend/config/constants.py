"""
Constantes de l'application
"""

# Mapping des genres TMDB ID → Nom
TMDB_GENRE_ID_TO_NAME = {
    12: 'Adventure', 14: 'Fantasy', 16: 'Animation', 18: 'Drama', 27: 'Horror',
    28: 'Action', 35: 'Comedy', 36: 'History', 37: 'Western', 53: 'Thriller',
    80: 'Crime', 99: 'Documentary', 878: 'Science Fiction', 9648: 'Mystery',
    10402: 'Music', 10749: 'Romance', 10751: 'Family', 10752: 'War',
    10759: 'Action & Adventure', 10762: 'Kids', 10763: 'News',
    10764: 'Reality', 10765: 'Sci-Fi & Fantasy', 10766: 'Soap',
    10767: 'Talk', 10768: 'War & Politics', 10770: 'TV Movie'
}

# Langues françaises
FRENCH_LANGUAGE_CODES = ['fr', 'fra', 'fre']
FRENCH_VARIANT_CODES = ['vfq', 'vff', 'vf']  # Québécois, Français France

# Types de média
MEDIA_TYPE_MOVIE = 'Movie'
MEDIA_TYPE_SERIES = 'Series'
MEDIA_TYPE_EPISODE = 'Episode'
MEDIA_TYPE_SEASON = 'Season'

# Codecs
CODEC_HEVC = ['hevc', 'h265', 'hvc1', 'hev1']
CODEC_H264 = ['h264', 'avc', 'avc1']

# Statut de disponibilité des médias
MEDIA_STATUS = {
    5: 'Disponible',
    4: 'Partiel',
    3: 'En cours',
    2: 'En attente',
    1: 'Non disponible',
    0: 'Non disponible'
}
