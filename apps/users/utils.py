from collections import Counter

from songs.models import Mood, Tempo
from users.models import User


def getFavoriteSongs(userid: str, number_of_songs: int):
    if number_of_songs < -1 or number_of_songs == 0:
        return None
    user = User.objects.get(id=userid)
    if number_of_songs == -1:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at').all()
    else:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[
                             :number_of_songs]
    songs = [song_rating.song for song_rating in user_songs_ratings]
    serialized_songs = [
        {
            'id': song.id,
            'name': song.name,
            'release_year': song.release_year,
            'main_artist': song.artists.first().name if song.artists.exists() else "Unknown",
            'img_url': song.img_url
        }
        for song in songs
    ]
    return serialized_songs


def getFavoriteGenres(userid: str, number_of_songs: int):
    if number_of_songs < -1 or number_of_songs == 0:
        return None
    user = User.objects.get(id=userid)
    if number_of_songs == -1:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at').all()
    else:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[
                             :number_of_songs]
    songs = [song_rating.song for song_rating in user_songs_ratings]
    genre_counts = Counter()
    for song in songs:
        song_genre_table = song.genresong_set.prefetch_related('genre').all()
        all_genres = [genre_song.genre for genre_song in song_genre_table]
        for genre in all_genres:
            genre_counts[genre.name] += 1
    genre_counts = genre_counts.most_common()
    return genre_counts  # returns a list of genre names and their counts, we can call
    # .most_common() on genre_counts to get the most common genres


def getFavoriteArtists(userid: str, number_of_songs: int):
    if number_of_songs < -1 or number_of_songs == 0:
        return None
    user = User.objects.get(id=userid)
    if number_of_songs == -1:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at').all()
    else:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[
                             :number_of_songs]
    songs = [song_rating.song for song_rating in user_songs_ratings]
    artist_counts = Counter()
    for song in songs:
        song_artist_table = song.artistsong_set.prefetch_related('artist').all()
        all_artists = [artist_song.artist for artist_song in song_artist_table]
        for artist in all_artists:
            artist_counts[artist.name] += 1
    artist_counts = artist_counts.most_common()
    return artist_counts  # returns a list of artist names and their counts, we can call
    # .most_common() on artist_counts to get the most common artists


def getFavoriteMoods(userid: str, number_of_songs: int):
    if number_of_songs < -1 or number_of_songs == 0:
        return None
    user = User.objects.get(id=userid)
    if number_of_songs == -1:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at').all()
    else:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[
                             :number_of_songs]
    songs = [song_rating.song for song_rating in user_songs_ratings]
    mood_counts = Counter()
    for song in songs:
        mood_label = Mood(song.mood).label
        mood_counts[mood_label] += 1
    mood_counts = mood_counts.most_common()
    return mood_counts  # returns a list of mood names and their counts, we can call
    # .most_common(n) on mood_counts to get the most common n moods


def getFavoriteTempos(userid: str, number_of_songs: int):
    if number_of_songs < -1 or number_of_songs == 0:
        return None
    user = User.objects.get(id=userid)
    if number_of_songs == -1:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating',
                                                                                       '-updated_at').all()
    else:
        user_songs_ratings = user.usersongrating_set.prefetch_related('song').order_by('-rating', '-updated_at')[
                             :number_of_songs]
    songs = [song_rating.song for song_rating in user_songs_ratings]
    tempo_counts = Counter()
    for song in songs:
        tempo_label = Tempo(song.tempo).label
        tempo_counts[tempo_label] += 1
    tempo_counts = tempo_counts.most_common()
    return tempo_counts  # returns a list of tempo names and their counts, we can call
    # .most_common(n) on tempo_counts to get the most common n tempos

def recommendation_creator(spotify_recommendations):
    tracks_info = []

    if not spotify_recommendations:
        return tracks_info

    for track in spotify_recommendations['tracks']:
        track_name = track['name'].title()
        release_year = track['album']['release_date'][:4]  # Extracting the first 4 characters for the release year
        spotify_id = track['id']
        album_name = album_name = track['album']['name'].title() if 'album' in track and 'name' in track['album'] else track['name'].title() + ' - Single'
        album_image_url = track['album']['images'][0]['url']

        artists_list = ', '.join([artist['name'].title() for artist in track['artists']])

        track_info = {
            'name': track_name,
            'main_artist': artists_list,
            'release_year': release_year,
            'id': spotify_id,
            'img_url': album_image_url,
        }
        tracks_info.append(track_info)
    
    return tracks_info