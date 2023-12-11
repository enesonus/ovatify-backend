import time
from typing import Tuple, List
from django.db.models import Model
import requests
from bs4 import BeautifulSoup
import os
import spotipy

from songs.models import (Album, Artist,
                          Genre, Mood,
                          RecordedEnvironment,
                          Song, Tempo,
                          Instrument)

from spotipy.oauth2 import SpotifyClientCredentials

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
            new_song, created = Song.objects.get_or_create(
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
            if created:
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
            else:
                if created:
                    return {'message': 'Song added successfully'}
                else:
                    return {'error': "You have already added this song"}


def addSongPerArtistFromSpotify():

    client_credentials = SpotifyClientCredentials(client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'))
    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    # Use the provided Spotify ID to get track information directly
    all_artists = Artist.objects.all()
    for artist in all_artists:
        print(f"----------------------\nArtist: {artist.name}")
        top_tracks = sp.artist_top_tracks(artist_id=artist.id,
                                          country='TR')
        for track in top_tracks['tracks']:
            return_data = add_song_helper(track=track)

            if return_data is None:
                print("error: return_data is None")
                continue
            if return_data.get("error") is not None:
                print(f"error: {return_data['error']}")
        time.sleep(3)
    return JsonResponse({'message': 'Songs added successfully'}, status=201)