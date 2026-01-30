package com.example.myapplication.data

import com.google.gson.annotations.SerializedName

// -----------------------------
// HEALTH CHECK
// -----------------------------
data class HealthResponse(
    val status: String
)

// -----------------------------
// LOCATION RESPONSE
// -----------------------------
data class LocationResponse(
    val latitude: Double,
    val longitude: Double,
    val city: String?
)

// -----------------------------
// FAVORITE MODELS
// -----------------------------
data class FavoriteEvent(
    @SerializedName(value = "_id")
    val id: String = "",
    val eventId: String? = "",
    val name: String,
    val venue: String,
    val date: String,
    val time: String,
    val category: String,
    @SerializedName("image")
    val imageUrl: String?,
    val url: String? = null,
    val addedAt: String? = null
)

data class FavoriteAddResponse(
    val message: String,
    val favorite: FavoriteEvent
)

data class FavoriteDeleteResponse(
    val message: String,
    val deletedCount: Int
)

data class FavoriteCheckResponse(
    val isFavorite: Boolean,
    val favorite: FavoriteEvent?
)

// -----------------------------
// TICKETMASTER SEARCH RESPONSE
// -----------------------------
data class TicketmasterSearchResponse(
    val _embedded: EmbeddedEvents?
)

data class EmbeddedEvents(
    val events: List<EventDetails>
)

// Main event model used everywhere
data class EventDetails(
    val id: String,
    val name: String,
    val url: String?,
    val images: List<Image>?,
    val dates: Dates?,
    val classifications: List<Classification>?,
    val priceRanges: List<PriceRange>?,
    val seatmap: Seatmap?,
    val _embedded: EmbeddedVenueAndArtists?
)

data class Image(
    val url: String,
    val width: Int?,
    val height: Int?
)

data class Dates(
    val start: StartDate?,
    val status: Status?
)

data class StartDate(
    val localDate: String?,
    val localTime: String?,
    val dateTime: String?
)

data class Status(
    val code: String?
)

data class Classification(
    val segment: Segment?,
    val genre: Genre?,
    val subGenre: SubGenre?,
    val type: Type?,
    val subType: SubType?
)

data class Segment(
    val name: String?
)

data class Genre(
    val name: String?
)

data class SubGenre(
    val name: String?
)

data class Type(
    val name: String?
)

data class SubType(
    val name: String?
)

data class PriceRange(
    val type: String?,
    val currency: String?,
    val min: Double?,
    val max: Double?
)

data class Seatmap(
    val staticUrl: String?
)

data class EmbeddedVenueAndArtists(
    val venues: List<Venue>?,
    val attractions: List<Attraction>?
)

data class Venue(
    val id: String,
    val name: String,
    val city: City?,
    val state: State?,
    val country: Country?,
    val address: Address?,
    val location: Location?,
    val images: List<Image>?
)

data class City(
    val name: String?
)

data class State(
    val name: String?,
    val stateCode: String?
)

data class Country(
    val name: String?,
    val countryCode: String?
)

data class Address(
    val line1: String?,
    val line2: String?,
    val line3: String?
)

data class Location(
    val latitude: String?,
    val longitude: String?
)

data class Attraction(
    val id: String,
    val name: String,
    val url: String?,
    val images: List<Image>?
)

// -----------------------------
// EVENT DETAILS RESPONSE (for /api/events/:id)
// Same structure as EventDetails
// -----------------------------
typealias EventDetailsResponse = EventDetails

// -----------------------------
// VENUE DETAILS RESPONSE (for /api/venues/:id)
// -----------------------------
data class VenueDetailsResponse(
    val name: String,
    val url: String?,
    val address: Address?,
    val city: City?,
    val state: State?,
    val country: Country?,
    val postalCode: String?,
    val location: Location?,
    val images: List<Image>?,
    val parkingDetail: String?,
    val generalInfo: VenueGeneralInfo?,
)

data class VenueGeneralInfo(
    val generalRule: String?,
    val childRule: String?,
)

// -----------------------------
// SPOTIFY RESPONSE MODELS
// -----------------------------
// Root response wrapper
data class SpotifyArtistResponse(
    val artist: SpotifyArtist,
    val albums: List<SpotifyAlbum>
)

// Artist model - matches backend response
data class SpotifyArtist(
    val id: String,
    val name: String,
    val followers: Int,              // NUMBER, not object!
    val popularity: Int,             // NUMBER
    val genres: List<String>,        // Array (can be empty)
    val images: List<SpotifyImage>,   // Array (can be empty)
    val spotifyUrl: String?          // STRING, not external_urls object!
)

data class SpotifyImage(
    val url: String,
    val height: Int?,
    val width: Int?
)

// Album model - matches backend response
data class SpotifyAlbum(
    val id: String,
    val name: String,
    val releaseDate: String?,         // camelCase, not release_date!
    val totalTracks: Int?,            // camelCase, not total_tracks!
    val images: List<SpotifyImage>,
    val spotifyUrl: String?,          // STRING, not external_urls object!
    val label: String?,
    val tracks: List<SpotifyTrack>?
)

data class SpotifyTrack(
    val id: String,
    val name: String,
    val previewUrl: String?,
    val spotifyUrl: String?
)

// -----------------------------
// AUTOCOMPLETE SUGGESTION RESPONSE
// -----------------------------
data class SuggestionResponse(
    val _embedded: SuggestionEmbedded?
)

data class SuggestionEmbedded(
    val attractions: List<SuggestionItem>
)

data class SuggestionItem(
    val name: String
)