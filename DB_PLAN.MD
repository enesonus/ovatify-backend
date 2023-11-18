# Entities and Attributes

## 1. User

      - FirebaseUID (Primary Key)
      - Username
      - Email
      - DateJoined
      - LastLogin

## 2. Song

      - SongID (Primary Key)
      - TrackName
      - ReleaseYear
      - Duration
      - Tempo (with Enum)
      - GenreID (Foreign Key)
      - Mood (with Enum)
      - Recorded Env. (with Enum)
      - ReplayCount
      - Version

## 3. Album

      - AlbumID (Primary Key)
      - Title
      - ReleaseDate

## 4. Artist

      - ArtistID (Primary Key)
      - Name
      - Bio

## 5. UserSongRating

      - RatingID (Primary Key)
      - FirebaseUID (Foreign Key)
      - SongID (Foreign Key)
      - Rating
      - DateRated

## 6. Genre

      - GenreID (Primary Key)
      - GenreName

## 7. GenreSong

      - GenreID (Foreign Key)
      - SongID (Foreign Key)

## 8. SongArtist

      - SongID (Foreign Key)
      - ArtistID (Foreign Key)

## 9. AlbumSong

      - AlbumID (Foreign Key)
      - SongID (Foreign Key)

## 10. UserPreferences

      - PreferenceID (Primary Key)
      - FirebaseUID (Foreign Key)
      - DataProcessingConsent
      - DataSharingConsent

## 11. Friend

      - UserID (Foreign Key, references User.FirebaseUID)
      - FriendID (Foreign Key, references User.FirebaseUID)

## 12. Instrument

      - InstrumentID (Primary Key)
      - InstrumentType
      - InstrumentName

## 13. InstrumentSong

      - InstrumentID (Foreign Key)
      - SongID (Foreign Key)

Relationships:

- A User can have multiple UserSongRating (One-to-Many)
- A Song can have multiple UserSongRating (One-to-Many)
- A Song can belong to multiple Albums (Many-to-Many), represented by AlbumSong
- A Song can be by multiple Artists (Many-to-Many), represented by SongArtist
- A Genre can include many Songs (One-to-Many)
- A User can have one UserPreferences (One-to-One)
- A User can have multiple Friends (One-to-Many)
- An Album can include many Songs (One-to-Many)

Note: The Many-to-Many relationships are represented through junction tables like SongArtist and AlbumSong, as typical in relational database design.
