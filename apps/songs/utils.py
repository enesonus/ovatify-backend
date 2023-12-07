from typing import Tuple, List
from django.db.models import Model
import requests
from bs4 import BeautifulSoup
import os
from songs.models import Album, Genre, Instrument, Song, Artist


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
    genre_song = genre.genresong_set.first()
    return genre_song.song.img_url

