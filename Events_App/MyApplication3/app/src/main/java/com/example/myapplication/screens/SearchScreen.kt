package com.example.myapplication.screens

import android.util.Log
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.example.myapplication.data.EventDetails
import com.example.myapplication.data.SearchQuery
import com.example.myapplication.data.SuggestionItem
import com.example.myapplication.network.RetrofitInstance
import kotlinx.coroutines.*
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

private const val TAG = "SearchScreen"

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    results: List<EventDetails>,
    isLoading: Boolean,
    favorites: List<String>,
    favoritesLoading: Boolean,
    onBack: () -> Unit,
    onSearch: (SearchQuery) -> Unit,
    onEventClick: (String) -> Unit,
    onToggleFavorite: (EventDetails) -> Unit,
    modifier: Modifier = Modifier
) {
    var keyword by remember { mutableStateOf("") }
    var distance by remember { mutableStateOf("10") }
    var locationDropdownExpanded by remember { mutableStateOf(false) }
    var useCurrentLocation by remember { mutableStateOf(true) }
    var manualLocation by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf(0) }

    // Error states
    var keywordError by remember { mutableStateOf(false) }
    var locationError by remember { mutableStateOf(false) }

    // Autocomplete state
    var suggestions by remember { mutableStateOf<List<SuggestionItem>>(emptyList()) }
    var showSuggestions by remember { mutableStateOf(false) }
    var loadingSuggestions by remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()
    var debounceJob by remember { mutableStateOf<Job?>(null) }

    val categories = listOf("All", "Music", "Sports", "Arts & Theatre", "Film", "Miscellaneous")

    // Fetch suggestions function
    fun fetchSuggestions(query: String) {
        if (query.isBlank()) {
            suggestions = emptyList()
            showSuggestions = false
            return
        }

        loadingSuggestions = true
        coroutineScope.launch {
            try {
                val response = RetrofitInstance.api.getSuggestions(query)
                if (response.isSuccessful) {
                    suggestions = response.body()?._embedded?.attractions ?: emptyList()
                    showSuggestions = true
                } else {
                    suggestions = emptyList()
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error fetching suggestions", e)
                suggestions = emptyList()
            } finally {
                loadingSuggestions = false
            }
        }
    }

    // Debounced keyword change handler
    fun handleKeywordChange(value: String) {
        keyword = value
        if (value.isNotBlank()) {
            keywordError = false
        }

        // Cancel previous debounce
        debounceJob?.cancel()

        if (value.isBlank()) {
            suggestions = emptyList()
            showSuggestions = false
            return
        }

        // Start new debounce
        debounceJob = coroutineScope.launch {
            delay(300) // 300ms debounce
            fetchSuggestions(value)
        }
    }

    // Filter results based on selected category
    val filteredResults = if (selectedCategory == 0) {
        results
    } else {
        results.filter {
            it.classifications?.firstOrNull()?.segment?.name == categories[selectedCategory]
        }
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            Column {
                // Blue TopAppBar with search field
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 4.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onBack) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back",
                                tint = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }

                        TextField(
                            value = keyword,
                            onValueChange = { handleKeywordChange(it) },
                            placeholder = { Text("Search events...") },
                            colors = TextFieldDefaults.colors(
                                focusedContainerColor = MaterialTheme.colorScheme.surface,
                                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                                focusedIndicatorColor = Color.Transparent,
                                unfocusedIndicatorColor = Color.Transparent,
                                errorContainerColor = MaterialTheme.colorScheme.surface,
                                errorIndicatorColor = Color.Transparent
                            ),
                            modifier = Modifier.weight(1f),
                            singleLine = true,
                            isError = keywordError,
                            trailingIcon = {
                                if (loadingSuggestions) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(20.dp),
                                        strokeWidth = 2.dp
                                    )
                                } else if (keyword.isNotBlank()) {
                                    IconButton(onClick = {
                                        keyword = ""
                                        suggestions = emptyList()
                                        showSuggestions = false
                                        debounceJob?.cancel()
                                        keywordError = false
                                    }) {
                                        Icon(Icons.Default.Close, contentDescription = "Clear")
                                    }
                                }
                            },
                            shape = MaterialTheme.shapes.small
                        )

                        IconButton(onClick = {
                            // Validate inputs
                            var hasError = false

                            if (keyword.isBlank()) {
                                keywordError = true
                                hasError = true
                            }

                            if (!useCurrentLocation && manualLocation.isBlank()) {
                                locationError = true
                                hasError = true
                            }

                            if (!hasError) {
                                showSuggestions = false
                                onSearch(
                                    SearchQuery(
                                        keyword = keyword,
                                        distance = distance.toIntOrNull() ?: 10,
                                        category = categories[selectedCategory],
                                        location = if (useCurrentLocation) "" else manualLocation,
                                        useCurrentLocation = useCurrentLocation
                                    )
                                )
                            }
                        }) {
                            Icon(
                                Icons.Default.Search,
                                contentDescription = "Search",
                                tint = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                    }
                }

                // Error message row
                if (keywordError) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.colorScheme.errorContainer
                    ) {
                        Text(
                            text = "Keyword is required",
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                        )
                    }
                }

                // Suggestions dropdown
                Box(modifier = Modifier.fillMaxWidth()) {
                    DropdownMenu(
                        expanded = showSuggestions && suggestions.isNotEmpty(),
                        onDismissRequest = { showSuggestions = false },
                        modifier = Modifier.fillMaxWidth(0.9f)
                    ) {
                        suggestions.forEach { attraction ->
                            DropdownMenuItem(
                                text = { Text(attraction.name) },
                                onClick = {
                                    keyword = attraction.name
                                    showSuggestions = false
                                    debounceJob?.cancel()
                                }
                            )
                        }
                    }
                }

                // Location and distance row
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            // Location dropdown
                            Box(modifier = Modifier.weight(1f)) {
                                TextButton(
                                    onClick = { locationDropdownExpanded = true },
                                    modifier = Modifier.fillMaxWidth(),
                                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Icon(Icons.Default.LocationOn, contentDescription = null, modifier = Modifier.size(20.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
                                    Spacer(Modifier.width(4.dp))
                                    Text(
                                        if (useCurrentLocation) "Current Location" else (manualLocation.ifBlank { "Manual Location" }),
                                        modifier = Modifier.weight(1f),
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                        color = MaterialTheme.colorScheme.onPrimaryContainer
                                    )
                                    Icon(
                                        if (locationDropdownExpanded) Icons.Default.ArrowDropUp else Icons.Default.ArrowDropDown,
                                        contentDescription = null,
                                        modifier = Modifier.size(20.dp),
                                        tint = MaterialTheme.colorScheme.onPrimaryContainer
                                    )
                                }

                                DropdownMenu(
                                    expanded = locationDropdownExpanded,
                                    onDismissRequest = { locationDropdownExpanded = false }
                                ) {
                                    DropdownMenuItem(
                                        text = { Text("Current Location") },
                                        onClick = {
                                            useCurrentLocation = true
                                            locationDropdownExpanded = false
                                            locationError = false
                                        },
                                        leadingIcon = { Icon(Icons.Default.MyLocation, contentDescription = null) }
                                    )
                                    DropdownMenuItem(
                                        text = { Text("Manual Location") },
                                        onClick = {
                                            useCurrentLocation = false
                                            locationDropdownExpanded = false
                                        },
                                        leadingIcon = { Icon(Icons.Default.EditLocation, contentDescription = null) }
                                    )
                                }
                            }

                            Icon(Icons.Default.SwapHoriz, contentDescription = null, modifier = Modifier.size(20.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
                            Spacer(Modifier.width(4.dp))

                            // Distance
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                BasicTextField(
                                    value = distance,
                                    onValueChange = { if (it.all { char -> char.isDigit() }) { distance = it } },
                                    modifier = Modifier.width(30.dp),
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    singleLine = true,
                                    textStyle = MaterialTheme.typography.bodyMedium.copy(color = MaterialTheme.colorScheme.onPrimaryContainer)
                                )
                                Spacer(Modifier.width(4.dp))
                                Text("mi", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onPrimaryContainer)
                            }
                        }

                        // Manual location input
                        if (!useCurrentLocation) {
                            Spacer(Modifier.height(8.dp))
                            Column {
                                OutlinedTextField(
                                    value = manualLocation,
                                    onValueChange = {
                                        manualLocation = it
                                        if (it.isNotBlank()) {
                                            locationError = false
                                        }
                                    },
                                    placeholder = { Text("Enter location") },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                    isError = locationError,
                                    leadingIcon = { Icon(Icons.Default.Place, contentDescription = null) },
                                    colors = TextFieldDefaults.colors(
                                        focusedContainerColor = MaterialTheme.colorScheme.surface,
                                        unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                                        errorContainerColor = MaterialTheme.colorScheme.surface
                                    )
                                )
                                if (locationError) {
                                    Text(
                                        text = "Location is required",
                                        color = MaterialTheme.colorScheme.error,
                                        style = MaterialTheme.typography.bodySmall,
                                        modifier = Modifier.padding(start = 16.dp, top = 4.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                // Category tabs
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    ScrollableTabRow(
                        selectedTabIndex = selectedCategory,
                        modifier = Modifier.fillMaxWidth(),
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                    ) {
                        categories.forEachIndexed { index, title ->
                            Tab(
                                selected = selectedCategory == index,
                                onClick = { selectedCategory = index },
                                text = { Text(title) }
                            )
                        }
                    }
                }
            }
        }
    ) { padding ->
        // Results
        if (isLoading) {
            Box(
                Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) {
                if (filteredResults.isEmpty() && results.isNotEmpty()) {
                    item {
                        Box(
                            Modifier
                                .fillParentMaxSize()
                                .padding(16.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("No results in this category.")
                        }
                    }
                } else if (results.isEmpty()) {
                    item {
                        Box(
                            Modifier
                                .fillParentMaxSize()
                                .padding(16.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("Start searching for events")
                        }
                    }
                } else {
                    items(filteredResults) { event ->
                        EventCard(
                            event = event,
                            isFavorite = favorites.contains(event.id),
                            onEventClick = { onEventClick(event.id) },
                            onFavoriteClick = { onToggleFavorite(event) },
                            isToggleEnabled = !favoritesLoading
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun EventCard(
    event: EventDetails,
    isFavorite: Boolean,
    onEventClick: () -> Unit,
    onFavoriteClick: () -> Unit,
    isToggleEnabled: Boolean
) {
    val venueName = event._embedded?.venues?.firstOrNull()?.name ?: "Unknown Venue"
    val imageUrl = event.images?.firstOrNull()?.url
    val date = event.dates?.start?.localDate ?: "TBD"
    val time = event.dates?.start?.localTime
    val category = event.classifications?.firstOrNull()?.segment?.name ?: "Unknown"

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onEventClick)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Box {
            Column {
                // Event image with badges
                Box {
                    imageUrl?.let {
                        AsyncImage(
                            model = it,
                            contentDescription = event.name,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(200.dp)
                                .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp)),
                            contentScale = ContentScale.Crop
                        )
                    } ?: Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                            .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            Icons.Default.Event,
                            contentDescription = null,
                            modifier = Modifier.size(48.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    // Category badge
                    Surface(
                        modifier = Modifier
                            .padding(12.dp)
                            .align(Alignment.TopStart),
                        shape = RoundedCornerShape(16.dp),
                        color = MaterialTheme.colorScheme.primaryContainer,
                        tonalElevation = 2.dp
                    ) {
                        Text(
                            text = category,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelMedium
                        )
                    }

                    // Date badge
                    Surface(
                        modifier = Modifier
                            .padding(12.dp)
                            .align(Alignment.TopEnd),
                        shape = RoundedCornerShape(16.dp),
                        color = MaterialTheme.colorScheme.primaryContainer,
                        tonalElevation = 2.dp
                    ) {
                        Text(
                            text = formatDateTime(date, time),
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelMedium
                        )
                    }
                }

                // Event info
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = event.name,
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = venueName,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }

            // Favorite button
            IconButton(
                onClick = onFavoriteClick,
                enabled = isToggleEnabled,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(8.dp)
            ) {
                Icon(
                    imageVector = if (isFavorite) Icons.Filled.Favorite else Icons.Outlined.FavoriteBorder,
                    contentDescription = "Favorite",
                    tint = if (isFavorite) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
                )
            }
        }
    }
}

private fun formatDateTime(date: String, time: String?): String {
    return try {
        // Parse the date (format: 2026-08-08)
        val parsedDate = LocalDate.parse(date, DateTimeFormatter.ISO_LOCAL_DATE)
        val monthDay = parsedDate.format(DateTimeFormatter.ofPattern("MMM d, yyyy"))

        if (time != null) {
            // Parse the time (format: 17:30:00)
            val parsedTime = LocalTime.parse(time, DateTimeFormatter.ISO_LOCAL_TIME)
            val formattedTime = parsedTime.format(DateTimeFormatter.ofPattern("h:mm a"))
            "$monthDay, $formattedTime"
        } else {
            monthDay
        }
    } catch (e: DateTimeParseException) {
        // Fallback if parsing fails
        if (time != null) {
            "$date, $time"
        } else {
            date
        }
    }
}