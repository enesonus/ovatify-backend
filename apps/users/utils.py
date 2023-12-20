from collections import Counter
import json

import math
import random
from django.core import serializers

from songs.models import Mood, Tempo, Genre, Song, Artist
from users.models import User, FriendGroup


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


def get_recommendations(seed_artists=None,
                        seed_tracks=None,
                        seed_genres=None,
                        limit=10,
                        lower_limit=0):
    try:
        if (seed_artists is None
                and seed_tracks is None
                and seed_genres is None):
            return {"items": None,
                    "error": "Invalid parameters"}

        valid_seeds = {"seed_artists": seed_artists,
                       "seed_tracks": seed_tracks,
                       "seed_genres": seed_genres}

        for key in list(valid_seeds):
            if valid_seeds[key] is None:
                del valid_seeds[key]

        recommendations = []
        per_type_limit = math.ceil((limit * 1.5) / len(valid_seeds))
        for key in valid_seeds:
            if key == "seed_genres":
                per_genre_limit = math.ceil(per_type_limit / len(valid_seeds[key]))
                for seed_genre in valid_seeds[key]:
                    db_genre = Genre.objects.filter(name__iexact=seed_genre).first()
                    if db_genre is None:
                        return {"items": None,
                                "error": f"Invalid genre name: {seed_genre}"}
                    ids = db_genre.song_set.values_list('id', flat=True)
                    if len(ids) > per_genre_limit:
                        ids = random.sample(list(ids), per_genre_limit)
                    random_songs_genre = Song.objects.filter(id__in=ids)
                    recommendations.extend(random_songs_genre)
            elif key == "seed_artists":
                per_artist_limit = math.ceil(per_type_limit / len(valid_seeds[key]))
                for seed_artist in valid_seeds[key]:
                    db_artist = Artist.objects.filter(name__iexact=seed_artist).first()
                    if db_artist is None:
                        return {"items": None,
                                "error": f"Invalid artist name: {seed_artist}"}
                    artist_genre = db_artist.song_set.first().genres.first()
                    if artist_genre is None:
                        continue
                    ids = artist_genre.song_set.values_list('id', flat=True)
                    if len(ids) > per_artist_limit:
                        ids = random.sample(list(ids), per_artist_limit)
                    random_songs_artist = Song.objects.filter(id__in=ids)
                    recommendations.extend(random_songs_artist)
            elif key == "seed_tracks":
                if len(valid_seeds[key]) == 0:
                    per_track_limit = math.ceil(per_type_limit / len(valid_seeds))
                else:
                    per_track_limit = math.ceil(per_type_limit / len(valid_seeds[key]))

                if len(valid_seeds[key]) == 0:
                    song_ids = Song.objects.all().values_list('id', flat=True)
                    random_ids = random.sample(list(song_ids), per_track_limit)
                    random_songs = Song.objects.filter(id__in=random_ids)
                    recommendations.extend(random_songs)
                for seed_track in valid_seeds[key]:
                    db_track = Song.objects.filter(id=seed_track).first()
                    if db_track is None:
                        return {"items": None,
                                "error": f"Invalid track id: {seed_track}"}
                    track_genre = db_track.genres.first()
                    if track_genre is None:
                        continue
                    ids = track_genre.song_set.values_list('id', flat=True)
                    if len(ids) > per_track_limit:
                        ids = random.sample(list(ids), per_track_limit)
                    random_songs_track = Song.objects.filter(id__in=ids)
                    recommendations.extend(random_songs_track)

        recommendations = list(set(recommendations))

        if len(recommendations) > limit:
            recommendations = random.sample(list(recommendations), limit)

        serialized_songs = [
            {
                'id': song.id,
                'name': song.name,
                'release_year': song.release_year,
                'main_artist': song.artists.first().name if song.artists.exists() else "Unknown",
                'img_url': song.img_url
            }
            for song in recommendations
        ]

        if len(serialized_songs) < lower_limit:
            return {"items": serialized_songs,
                    "error": "Not enough songs to recommend."}

        return {"items": serialized_songs, "error": None}
    except Exception as e:
        return {"items": None,
                "error": f"Unknown Error: {e}"}


def serializeFriendGroupSimple(friend_group: FriendGroup):
    return {
        'id': friend_group.id,
        'name': friend_group.name,
        'description': friend_group.description,
        'img_url': friend_group.img_url,
        'admin': friend_group.created_by.username,
    }


def serializeFriendGroupExtended(friend_group: FriendGroup):
    return {
        'id': friend_group.id,
        'name': friend_group.name,
        'description': friend_group.description,
        'img_url': friend_group.img_url,
        'admin': friend_group.created_by.username,
        'members': [{'id': member.id, 'username': member.username, 'img_url': member.img_url}
                    for member in friend_group.friends.all()]
    }