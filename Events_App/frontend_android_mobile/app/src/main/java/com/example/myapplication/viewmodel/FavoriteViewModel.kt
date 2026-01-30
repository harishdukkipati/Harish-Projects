package com.example.myapplication.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.EventDetails
import com.example.myapplication.network.RetrofitInstance
import com.example.myapplication.data.FavoriteEvent
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch

class FavoriteViewModel : ViewModel() {

    private val _favorites = MutableStateFlow<List<FavoriteEvent>>(emptyList())
    val favorites: StateFlow<List<FavoriteEvent>> = _favorites

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading

    private val _error = MutableSharedFlow<String>()
    val error = _error.asSharedFlow()

    init {
        loadFavorites()
    }

    fun loadFavorites() {
        viewModelScope.launch {
            try {
                _loading.value = true
                val response = RetrofitInstance.api.getFavorites()
                if (response.isSuccessful) {
                    _favorites.value = response.body() ?: emptyList()
                }
            } catch (e: Exception) {
                _error.emit("Failed to load favorites: ${e.message}")
            } finally {
                _loading.value = false
            }
        }
    }

    fun addFavorite(event: EventDetails) {
        viewModelScope.launch {
            if (favorites.value.any { it.eventId == event.id }) return@launch

            // Send the full EventDetails object directly - backend expects this format
            try {
                val response = RetrofitInstance.api.addFavorite(event)  // ← Send event directly, not FavoriteEvent
                if (response.isSuccessful && response.body() != null) {
                    _favorites.value = _favorites.value + response.body()!!.favorite
                } else {
                    _error.emit("Failed to add favorite: ${response.code()} - ${response.errorBody()?.string()}")
                }
            } catch (e: Exception) {
                _error.emit("Error adding favorite: ${e.message}")
            }
        }
    }

    fun removeFavorite(favoriteDatabaseId: String) {
        viewModelScope.launch {
            try {
                val response = RetrofitInstance.api.deleteFavorite(favoriteDatabaseId)
                if (response.isSuccessful) {
                    _favorites.value = _favorites.value.filterNot { it.id == favoriteDatabaseId }
                } else {
                    _error.emit("Failed to remove favorite: ${response.code()} - ${response.errorBody()?.string()}")
                }
            } catch (e: Exception) {
                _error.emit("Error removing favorite: ${e.message}")
            }
        }
    }
}