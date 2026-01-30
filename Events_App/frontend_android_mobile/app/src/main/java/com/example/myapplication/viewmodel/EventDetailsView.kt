package com.example.myapplication.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.*
import com.example.myapplication.network.RetrofitInstance
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch


class EventDetailsViewModel : ViewModel() {

    private val _eventDetails = MutableStateFlow<EventDetailsResponse?>(null)
    val eventDetails: StateFlow<EventDetailsResponse?> = _eventDetails

    private val _artistData = MutableStateFlow<Map<String, SpotifyArtistResponse>>(emptyMap())
    val artistData: StateFlow<Map<String, SpotifyArtistResponse>> = _artistData

    private val _venueDetails = MutableStateFlow<VenueDetailsResponse?>(null)
    val venueDetails: StateFlow<VenueDetailsResponse?> = _venueDetails

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading

    private val _artistLoading = MutableStateFlow(false)
    val artistLoading: StateFlow<Boolean> = _artistLoading

    private val _venueLoading = MutableStateFlow(false)
    val venueLoading: StateFlow<Boolean> = _venueLoading

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    fun loadEventDetails(eventId: String) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null

            try {
                val response = RetrofitInstance.api.getEventDetails(eventId)
                if (response.isSuccessful && response.body() != null) {
                    _eventDetails.value = response.body()

                    // Load venue details if available
                    response.body()?._embedded?.venues?.firstOrNull()?.id?.let { venueId ->
                        loadVenueDetails(venueId)
                    }

                    // Load artist data if music event
                    val artists = response.body()?._embedded?.attractions
                    if (!artists.isNullOrEmpty()) {
                        loadArtistData(artists.map { it.name })
                    }
                } else {
                    _error.value = "Failed to load event details"
                }
            } catch (e: Exception) {
                _error.value = e.message ?: "Unknown error occurred"
            } finally {
                _loading.value = false
            }
        }
    }

    private fun loadArtistData(artistNames: List<String>) {
        viewModelScope.launch {
            _artistLoading.value = true
            Log.d("ArtistDebug", "Starting to load artist data: $artistNames")

            val artistMap = mutableMapOf<String, SpotifyArtistResponse>()

            artistNames.forEach { artistName ->
                Log.d("ArtistDebug", "Requesting artist: $artistName")

                try {
                    val response = RetrofitInstance.api.getSpotifyArtist(artistName)
                    Log.d("ArtistDebug", "Response for $artistName: success=${response.isSuccessful}")

                    if (response.isSuccessful && response.body() != null) {
                        val body = response.body()!!
                        Log.d("ArtistDebug", "Received data for $artistName: $body")

                        artistMap[artistName] = body
                    } else {
                        Log.d("ArtistDebug", "No valid body for $artistName. Response: $response")
                    }
                } catch (e: Exception) {
                    Log.e("ArtistDebug", "Error fetching $artistName", e)
                }
            }

            _artistData.value = artistMap
            Log.d("ArtistDebug", "Finished loading. Final artistMap: $artistMap")

            _artistLoading.value = false
            Log.d("ArtistDebug", "Loading state set to false.")
        }
    }


    private fun loadVenueDetails(venueId: String) {
        viewModelScope.launch {
            _venueLoading.value = true

            try {
                val response = RetrofitInstance.api.getVenueDetails(venueId)
                if (response.isSuccessful && response.body() != null) {
                    _venueDetails.value = response.body()
                }
            } catch (e: Exception) {
                // Venue details are optional, don't show error
            } finally {
                _venueLoading.value = false
            }
        }
    }

    fun clearError() {
        _error.value = null
    }
}