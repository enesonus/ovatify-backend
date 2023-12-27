import random
import time
from typing import Tuple, List
from django.db.models import Model, Count, Sum
import requests
from bs4 import BeautifulSoup
import os
import spotipy
from users.models import User, UserSongRating

from songs.models import (Album, Artist,
                          Genre, Mood,
                          RecordedEnvironment,
                          Song, Tempo,
                          Instrument, Playlist,)

from spotipy.oauth2 import SpotifyClientCredentials

from spotipy.exceptions import SpotifyException

from datetime import timedelta

from django.http import JsonResponse



def bulk_get_or_create(model: Model, data: List, unique_field: str) -> Tuple[List[Model], List[Model]]:
    # Step 1: Fetch existing records
    existing_records = model.objects.filter(**{f"{unique_field}__in": data})

    # Create a set of existing values for quick look-up
    existing_values = {getattr(record, unique_field) for record in existing_records}

    # Step 2: Determine new records
    new_records_data = [value for value in data if value not in existing_values]

    # Create new model instances
    new_records = [model(**{unique_field: value}) for value in new_records_data]

    # Step 3: Bulk create new records
    model.objects.bulk_create(new_records)

    # Step 4: Combine existing and new records
    return existing_records, new_records

def get_artist_bio(artist_name):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    
    # Specify the Last.fm API method for artist.getInfo
    method = "artist.getInfo"
    
    # Make a request to the Last.fm API
    response = requests.get(base_url, params={
        'method': method,
        'artist': artist_name,
        'api_key': os.getenv('LAST_FM_API_KEY'),
        'format': 'json'
    })

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        artist_info = response.json()

        # Extract the biography from the response
        if 'artist' in artist_info and 'bio' in artist_info['artist']:
            bio = artist_info['artist']['bio']['summary']
            return clean_html_tags(bio)

    else:
        return ""

def clean_html_tags(text_with_tags):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(text_with_tags, 'html.parser')

    # Extract the text without HTML tags
    cleaned_text = soup.get_text()

    # Remove the specific text "Read more on Last.fm"
    cleaned_text = cleaned_text.replace('Read more on Last.fm', '').strip()

    return cleaned_text

def get_genres_and_artist_info(track_data, sp):
    artist_ids = [artist['id'] for artist in track_data['artists']]
    artist_data = sp.artists(artist_ids)

    genres = []
    artist_images = {}

    for artist in artist_data['artists']:

        artist_name = artist['name']
        # Check if genres exist for the artist
        if 'genres' in artist and artist['genres']:
            # Capitalize the first letter of each genre and add to the list
            genres += [genre.title() for genre in artist['genres']]

        # Check if images exist for the artist
        if 'images' in artist and artist['images']:
            image_url = artist['images'][0]['url']
            # Get the URL of the first image
            artist_images[artist_name.title()] = image_url

    # Remove duplicate genres
    unique_genres = list(set(genres))

    return unique_genres, artist_images

def flush_database():
            all_albums = Album.all_objects.all()
            for album in all_albums:
                album.hard_delete()

            # Fetch all instances of Genre and perform hard delete
            all_genres = Genre.all_objects.all()
            for genre in all_genres:
                genre.hard_delete()

            # Fetch all instances of Instrument and perform hard delete
            all_instruments = Instrument.all_objects.all()
            for instrument in all_instruments:
                instrument.hard_delete()

            all_songs = Song.all_objects.all()
            for songs in all_songs:
                songs.hard_delete()
            
            all_artist = Artist.all_objects.all()
            for artist in all_artist:
                artist.hard_delete()


def getFirstRelatedSong(genre_id):
    genre = Genre.objects.get(id=genre_id)
    genre_song = genre.genresong_set.order_by('-created_at').first()
    return genre_song.song.img_url


def add_song_helper(track=None):
    client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    if track is None:
        return {'error': 'Song not found'}
    else:
        time.sleep(0.1)
        audio_features = sp.audio_features([track['id']])
        genres, artist_img = get_genres_and_artist_info(track, sp)

        if audio_features is None:
            return {'error': 'No audio features found for the song'}
        else:
            audio_features = audio_features[0]
            recorded_environment = RecordedEnvironment.LIVE if audio_features['liveness'] >= 0.8 else RecordedEnvironment.STUDIO
            tempo = Tempo.FAST if audio_features['tempo'] >= 120 else (Tempo.MEDIUM if 76 <= audio_features['tempo'] < 120 else Tempo.SLOW)
            energy = audio_features['energy']
            if 0 <= energy < 0.25:
                mood = Mood.SAD
            elif 0.25 <= energy < 0.5:
                mood = Mood.RELAXED
            elif 0.5 <= energy < 0.75:
                mood = Mood.HAPPY
            else:
                mood = Mood.EXCITED
            # Create necessary objects in the database
            new_song, is_created = Song.objects.get_or_create(
                id=track['id'],
                name=track['name'].title(),
                release_year=track['album']['release_date'][:4],
                tempo=tempo,
                duration=str(timedelta(seconds=int(track['duration_ms']/1000))),
                recorded_environment=recorded_environment,
                mood=mood,
                img_url=track['album']['images'][0]['url'],
                version=track['album']['release_date'],
            )
            if is_created:
                for genre_name in genres:
                    if genre_name:
                        genre, genre_created = Genre.objects.get_or_create(name=genre_name)
                        new_song.genres.add(genre)

                for artist in track['artists']:
                    artist_name = artist['name'].title()
                    artist_bio = get_artist_bio(artist_name)
                    artist_img_url = artist_img if artist_img is not None else None

                    db_artist = Artist.objects.filter(id=artist['id']).first()
                    if db_artist is None:
                        artist = Artist.objects.create(
                                        id=artist['id'],
                                        name=artist_name.title(),
                                        img_url=artist_img_url,
                                        bio=artist_bio)
                        db_artist = artist
                    if (db_artist.bio != artist_bio or
                            db_artist.img_url != artist_img_url):
                        db_artist.bio = artist_bio
                        db_artist.img_url = artist_img_url
                        db_artist.save()
                    new_song.artists.add(db_artist)

                album_name = track['album']['name'].title() if 'album' in track and 'name' in track['album'] else track['name'].title() + ' - Single'
                album_instance, album_created = Album.objects.get_or_create(id= track['album']['id'],
                                                                            name=album_name,
                                                                            release_year=track['album']['release_date'][:4],
                                                                            img_url=track['album']['images'][0]['url'])
                new_song.albums.add(album_instance)
                return {'message': 'Song added successfully'}
            else:
                return {'error': "You have already added this song"}


def addBatchSongFromSpotify(genres=None, artists=None, is_from_album=False):

    client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    # Use the provided Spotify ID to get track information directly
    all_artists = []
    if genres is not None:
        for genre in genres:
            genre_songs = genre.song_set.all()
            for song in genre_songs:
                all_artists.extend(song.artists.all())

    if artists is not None:
        artists = Artist.objects.filter(name__in=artists)
        all_artists.extend(artists)

    all_artists = list(set(all_artists))
    print(f"Total artists: {len(all_artists)}")

    random.shuffle(all_artists)
    for artist in all_artists:
        print(f"----------------------\nArtist: {artist.name}")
        top_tracks = []
        if is_from_album:
            albums = sp.artist_albums(artist_id=artist.id,
                                      country='TR',
                                      limit=10)
            for album in albums['items']:
                album_tracks = sp.album_tracks(album_id=album['id'],
                                               limit=15)
                album_tracks = album_tracks['items']

                for track in album_tracks:
                    track['album'] = album
                top_tracks.extend(album_tracks)
            if len(top_tracks) > 50:
                top_tracks = random.sample(top_tracks, 50)

        if is_from_album is False:
            top_tracks = sp.artist_top_tracks(artist_id=artist.id,
                                          country='TR')
            top_tracks = top_tracks['tracks']

        print(f"Total tracks: {len(top_tracks)}\n")
        for track in top_tracks:
            try:
                return_data = add_song_helper(track=track)

                if return_data is None:
                    print("error: return_data is None")
                    continue
                if return_data.get("error") is not None:
                    print(f"error: {return_data['error']}")
            except Exception as e:
                print(f"error: {e}")
                continue
        n=10
        print(f"Sleeping for {n} seconds")
        time.sleep(n)
    return JsonResponse({'message': 'Songs added successfully'}, status=201)


def addArtistsToSongsWithoutArtists():
    songs = Song.objects.filter(artists__isnull=True)
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    client_credentials = SpotifyClientCredentials(client_id=client_id,
                                                  client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    for song in songs:
        try:
            id = song.id
            print(f"Adding song: {song.name}")
            song.hard_delete()
            new_song = sp.track(track_id=id)
            add_song_helper(track=new_song)
            print("Sleeping for 2 seconds")
            time.sleep(2)
        except SpotifyException as e:
            status, _, _ = e.http_status, e.code, e.reason
            if status == 429:
                print(f"ABORTING {str(e)}")
                song.save()
                return
            if status == 400:
                print(f"Invalid song ID {str(e)}")
                continue
        except Exception as e:
            print(f"Exception {str(e)}")

    return print('message: Songs added successfully')


def serializePlaylistInfo(playlist: Playlist):
    count = 4
    if playlist.songs.count() < 4:
        count = playlist.songs.count()
    song_imgs = [song.img_url
                 for song in
                 playlist.songs.all()[:count]]
    return {
        'id': playlist.id,
        'name': playlist.name,
        'description': playlist.description,
        'song_imgs': song_imgs,
        'user_id': playlist.user.id if playlist.user is not None else None,
        'friend_group_id':
            playlist.friend_group.id if
            playlist.friend_group is not None else None,
    }


def serializePlaylist(playlist: Playlist):
    return {
        'id': playlist.id,
        'name': playlist.name,
        'description': playlist.description,
        'songs': [serializeSongMinimum(song) for song in playlist.songs.all()],
        'user_id': playlist.user.id if playlist.user is not None else None,
        'friend_group_id':
            playlist.friend_group.id if
            playlist.friend_group is not None else None,
    }


def serializeSongMinimum(song: Song):
    return {
        'id': song.id,
        'name': song.name,
        'release_year': song.release_year,
        'img_url': song.img_url,
        'main_artist': song.artists.all().first().name if song.artists.all().first() is not None else None,
    }


def serializeSong(song: Song):
    return {
        'id': song.id,
        'name': song.name,
        'release_year': song.release_year,
        'tempo': song.tempo,
        'duration': song.duration,
        'recorded_environment': song.recorded_environment,
        'mood': song.mood,
        'img_url': song.img_url,
        'version': song.version,
        'genres': [genre.name for genre in song.genres.all()],
        'artists': [artist.name for artist in song.artists.all()],
        'albums': [album.name for album in song.albums.all()],
    }


def serializeSongExtended(song: Song):
    genres = song.genres.all()
    genre_names = [genre.name for genre in genres]

    artists = song.artists.all()
    artist_names = [artist.name for artist in artists]

    albums = song.albums.all()
    album_names = [album.name for album in albums]

    instruments = song.instruments.all()
    instrument_names = [instrument.name for instrument in instruments]

    tempo_long_form = dict(Tempo.choices)[song.tempo]
    mood_long_form = dict(Mood.choices)[song.mood]
    recorded_environment_long_form = dict(RecordedEnvironment.choices)[song.recorded_environment]

    data = {
        'id': song.id,
        'name': song.name,
        'genres': genre_names,
        'artists': artist_names,
        'albums': album_names,
        'instruments': instrument_names,
        'release_year': song.release_year,
        'duration': song.duration.total_seconds(),
        'tempo': tempo_long_form,
        'mood': mood_long_form,
        'recorded_environment': recorded_environment_long_form,
        'replay_count': song.replay_count,
        'version': song.version,
        'img_url': song.img_url
    }
    return data


def serializeSongExtendedWithRating(song: Song, user: User):
    data = serializeSongExtended(song)

    rating_aggregation = UserSongRating.objects.filter(song=song).aggregate(
        total_ratings=Count('rating'),
        sum_ratings=Sum('rating')
    )
    total_ratings = rating_aggregation['total_ratings']
    sum_ratings = rating_aggregation['sum_ratings']

    if total_ratings > 0:
        average_rating = sum_ratings / total_ratings
    else:
        average_rating = 0
    try:
        user_rating = UserSongRating.objects.filter(user=user, song=song).first()
        if user_rating is not None:
            user_rating = user_rating.rating
    except UserSongRating.DoesNotExist:
        user_rating = 0

    data['average_rating'] = round(average_rating, 2)
    data['user_rating'] = round(user_rating, 2)

    return data
