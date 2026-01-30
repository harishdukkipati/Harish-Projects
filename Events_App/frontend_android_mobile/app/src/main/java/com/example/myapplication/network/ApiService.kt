package com.example.myapplication.network

import com.example.myapplication.data.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // -----------------------------
    // HEALTH CHECK
    // -----------------------------
    @GET("/api/health")
    suspend fun checkHealth(): Response<HealthResponse>

    // -----------------------------
    // IP-BASED LOCATION
    // -----------------------------
    @GET("/api/location")
    suspend fun getLocation(): Response<LocationResponse>


    // -----------------------------
    // SPOTIFY
    // -----------------------------
    @GET("/api/spotify/artist")
    suspend fun getSpotifyArtist(
        @Query("name") artistName: String
    ): Response<SpotifyArtistResponse>


    // -----------------------------
    // FAVORITES (MongoDB)
    // -----------------------------
    @GET("/api/favorites")
    suspend fun getFavorites(): Response<List<FavoriteEvent>>

    @POST("/api/favorites")
    suspend fun addFavorite(
        @Body event: EventDetails  // ← Changed from FavoriteEvent to EventDetails
    ): Response<FavoriteAddResponse>

    @DELETE("/api/favorites/{id}")
    suspend fun deleteFavorite(
        @Path("id") id: String
    ): Response<FavoriteDeleteResponse>

    @GET("/api/favorites/check/{eventId}")
    suspend fun checkFavorite(
        @Path("eventId") eventId: String
    ): Response<FavoriteCheckResponse>


    // -----------------------------
    // TICKETMASTER EVENTS
    // -----------------------------
    @GET("/api/events")
    suspend fun searchEvents(
        @Query("keyword") keyword: String?,
        @Query("segmentId") segmentId: String?,
        @Query("radius") radius: Int?,
        @Query("geoPoint") geoPoint: String?,
        @Query("unit") unit: String? = "miles"
    ): Response<TicketmasterSearchResponse>


    @GET("/api/events/{id}")
    suspend fun getEventDetails(
        @Path("id") id: String
    ): Response<EventDetailsResponse>

    @GET("/api/venues/{id}")
    suspend fun getVenueDetails(
        @Path("id") id: String
    ): Response<VenueDetailsResponse>


    // -----------------------------
    // AUTOCOMPLETE SUGGESTIONS
    // -----------------------------
    @GET("/api/suggest")
    suspend fun getSuggestions(
        @Query("keyword") keyword: String
    ): Response<SuggestionResponse>

    // -----------------------------
    // GOOGLE GEOCODING
    // -----------------------------
    @GET
    suspend fun geocodeAddress(
        @Url url: String,
        @Query("address") address: String,
        @Query("key") apiKey: String
    ): Response<GeocodingResponse>
}
