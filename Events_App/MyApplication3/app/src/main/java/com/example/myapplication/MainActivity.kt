package com.example.myapplication

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.myapplication.screens.EventDetailsScreen
import com.example.myapplication.screens.HomeScreen
import com.example.myapplication.screens.SearchScreen
import com.example.myapplication.ui.theme.MyApplicationTheme
import com.example.myapplication.viewmodel.EventDetailsViewModel
import com.example.myapplication.viewmodel.FavoriteViewModel
import com.example.myapplication.viewmodel.SearchViewModel
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationTheme {
                EventFinderApp()
            }
        }
    }
}

@Composable
fun EventFinderApp() {
    var currentScreen by remember { mutableStateOf("home") }
    var previousScreen by remember { mutableStateOf("home") } // Remember the last screen
    var selectedEventId by remember { mutableStateOf<String?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    // ViewModels
    val favoriteViewModel: FavoriteViewModel = viewModel()
    val searchViewModel: SearchViewModel = viewModel()
    val eventDetailsViewModel: EventDetailsViewModel = viewModel()

    // State flows
    val favorites by favoriteViewModel.favorites.collectAsState()
    val favoritesLoading by favoriteViewModel.loading.collectAsState()
    val searchResults by searchViewModel.results.collectAsState()
    val searchLoading by searchViewModel.loading.collectAsState()

    // Event details states
    val eventDetails by eventDetailsViewModel.eventDetails.collectAsState()
    val artistData by eventDetailsViewModel.artistData.collectAsState()
    val venueDetails by eventDetailsViewModel.venueDetails.collectAsState()
    val eventDetailsLoading by eventDetailsViewModel.loading.collectAsState()
    val artistLoading by eventDetailsViewModel.artistLoading.collectAsState()
    val venueLoading by eventDetailsViewModel.venueLoading.collectAsState()

    // Listen for errors from FavoriteViewModel
    LaunchedEffect(Unit) {
        favoriteViewModel.error.collectLatest { message ->
            scope.launch {
                snackbarHostState.showSnackbar(message)
            }
        }
    }

    // Listen for errors from EventDetailsViewModel
    LaunchedEffect(Unit) {
        eventDetailsViewModel.error.collectLatest { message ->
            message?.let {
                scope.launch {
                    snackbarHostState.showSnackbar(it)
                }
                eventDetailsViewModel.clearError()
            }
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
    ) { padding ->
        when (currentScreen) {
            "home" -> HomeScreen(
                modifier = Modifier.padding(padding),
                onSearchClick = { currentScreen = "search" },
                favorites = favorites,
                onRemoveFavorite = { event ->
                    favoriteViewModel.removeFavorite(event.id)
                },
                onEventClick = { eventId ->
                    previousScreen = "home" // Set previous screen
                    selectedEventId = eventId
                    eventDetailsViewModel.loadEventDetails(eventId)
                    currentScreen = "eventDetails"
                }
            )

            "search" -> SearchScreen(
                modifier = Modifier.padding(padding),
                results = searchResults,
                isLoading = searchLoading,
                favorites = favorites.mapNotNull { it.eventId },
                favoritesLoading = favoritesLoading,
                onBack = { currentScreen = "home" },
                onSearch = { query -> searchViewModel.searchEvents(query) },
                onEventClick = { eventId ->
                    previousScreen = "search" // Set previous screen
                    selectedEventId = eventId
                    eventDetailsViewModel.loadEventDetails(eventId)
                    currentScreen = "eventDetails"
                },
                onToggleFavorite = { event ->
                    val isCurrentlyFavorite = favorites.any { it.eventId == event.id }
                    if (isCurrentlyFavorite) {
                        val favoriteToRemove = favorites.find { it.eventId == event.id }
                        favoriteToRemove?.let { favoriteViewModel.removeFavorite(it.id) }
                    } else {
                        favoriteViewModel.addFavorite(event)
                    }
                }
            )

            "eventDetails" -> {
                selectedEventId?.let { eventId ->
                    val isFavorite = favorites.any { it.eventId == eventId }

                    EventDetailsScreen(
                        eventId = eventId,
                        eventDetails = eventDetails,
                        artistData = artistData,
                        venueDetails = venueDetails,
                        isLoading = eventDetailsLoading,
                        artistLoading = artistLoading,
                        venueLoading = venueLoading,
                        isFavorite = isFavorite,
                        onBack = { currentScreen = previousScreen }, // Go back to the previous screen
                        onToggleFavorite = {
                            if (isFavorite) {
                                val favoriteToRemove = favorites.find { it.eventId == eventId }
                                favoriteToRemove?.let { favoriteViewModel.removeFavorite(it.id) }
                            } else {
                                // Try to find event in search results first
                                val eventFromSearch = searchResults.find { it.id == eventId }
                                if (eventFromSearch != null) {
                                    favoriteViewModel.addFavorite(eventFromSearch)
                                } else {
                                    // If not in search results, show an error
                                    scope.launch {
                                        snackbarHostState.showSnackbar("Cannot add to favorites from here.")
                                    }
                                }
                            }
                        },
                        modifier = Modifier.padding(padding)
                    )
                }
            }
        }
    }
}
