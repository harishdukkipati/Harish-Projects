package com.example.myapplication.screens
import coil.compose.AsyncImage
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.FavoriteEvent
import java.text.SimpleDateFormat
import java.util.*
import android.content.Intent
import android.net.Uri
import androidx.compose.ui.platform.LocalContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onSearchClick: () -> Unit,
    favorites: List<FavoriteEvent> = emptyList(),
    onRemoveFavorite: (FavoriteEvent) -> Unit,
    onEventClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = { Text("Event Search") },  // Changed from "Event Finder"
                actions = {
                    IconButton(onClick = onSearchClick) {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Search"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        },
        bottomBar = {
            // Powered by Ticketmaster
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://www.ticketmaster.com"))
                        context.startActivity(intent)
                    },
                color = MaterialTheme.colorScheme.surfaceVariant
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Powered by Ticketmaster",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    ) { padding ->
        if (favorites.isEmpty()) {
            // Empty state
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Favorite,
                    contentDescription = null,
                    modifier = Modifier.size(80.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "No Favorites",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = getCurrentDate(),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            // List of favorites
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text(
                        text = getCurrentDate(),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                }
                item {
                    Text(
                        text = "Favorites",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                }
                items(favorites) { event ->
                    FavoriteEventCard(
                        event = event,
                        onEventClick = { event.eventId?.let(onEventClick) },
                        onFavoriteClick = { onRemoveFavorite(event) }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FavoriteEventCard(
    event: FavoriteEvent,
    onEventClick: () -> Unit,
    onFavoriteClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onEventClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Event image - circular/square
            if (!event.imageUrl.isNullOrBlank()) {
                AsyncImage(
                    model = event.imageUrl,
                    contentDescription = event.name,
                    modifier = Modifier
                        .size(60.dp)
                        .clip(CircleShape),  // Circular image like in image
                    contentScale = ContentScale.Crop
                )
            } else {
                // Fallback placeholder
                Surface(
                    modifier = Modifier.size(60.dp),
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shape = CircleShape
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = event.category.take(1),
                            style = MaterialTheme.typography.headlineMedium
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                // Event name
                Text(
                    text = event.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(4.dp))
                // Format date as "Aug 8, 2026, 5:30 PM"
                Text(
                    text = formatEventDateTime(event.date, event.time),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Right side: Relative time and arrow
            Column(
                horizontalAlignment = Alignment.End,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.padding(start = 8.dp)
            ) {
                // Relative time (e.g., "31 seconds ago")
                Text(
                    text = getRelativeTime(event.addedAt),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                // Arrow icon
                Icon(
                    imageVector = Icons.Default.ArrowForward,
                    contentDescription = "View details",
                    modifier = Modifier.size(20.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

// Helper function to get current date - format as "11 November 2025"
private fun getCurrentDate(): String {
    val dateFormat = SimpleDateFormat("d MMMM yyyy", Locale.getDefault())
    return dateFormat.format(Date())
}

// Format event date/time as "Aug 8, 2026, 5:30 PM"
private fun formatEventDateTime(dateStr: String, timeStr: String?): String {
    return try {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val date = dateFormat.parse(dateStr) ?: return dateStr

        if (timeStr != null && timeStr.isNotBlank()) {
            // Parse time and combine with date
            val timeParts = timeStr.split(":")
            if (timeParts.size >= 2) {
                val hour = timeParts[0].toIntOrNull() ?: 0
                val minute = timeParts[1].toIntOrNull() ?: 0
                val calendar = Calendar.getInstance()
                calendar.time = date
                calendar.set(Calendar.HOUR_OF_DAY, hour)
                calendar.set(Calendar.MINUTE, minute)

                val outputFormat = SimpleDateFormat("MMM d, yyyy, h:mm a", Locale.getDefault())
                outputFormat.format(calendar.time)
            } else {
                val outputFormat = SimpleDateFormat("MMM d, yyyy", Locale.getDefault())
                outputFormat.format(date)
            }
        } else {
            val outputFormat = SimpleDateFormat("MMM d, yyyy", Locale.getDefault())
            outputFormat.format(date)
        }
    } catch (e: Exception) {
        // Fallback to original format if parsing fails
        if (timeStr != null && timeStr.isNotBlank()) {
            "$dateStr, $timeStr"
        } else {
            dateStr
        }
    }
}

// Helper function to get relative time
private fun getRelativeTime(addedAtString: String?): String {
    if (addedAtString == null) return "Recently added"

    return try {
        // Try parsing as ISO 8601 date string (e.g., "2024-12-09T10:30:00.000Z")
        val formatter = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.getDefault())
        formatter.timeZone = TimeZone.getTimeZone("UTC")
        val addedDate = formatter.parse(addedAtString)
        val timestamp = addedDate?.time ?: return "Recently added"

        val now = System.currentTimeMillis()
        val diff = now - timestamp

        when {
            diff < 0 -> "Just now"
            diff < 60000 -> {
                val seconds = diff / 1000
                if (seconds <= 1) "1 second ago" else "$seconds seconds ago"
            }
            diff < 3600000 -> {
                val minutes = diff / 60000
                if (minutes <= 1) "1 minute ago" else "$minutes minutes ago"
            }
            diff < 86400000 -> {
                val hours = diff / 3600000
                if (hours <= 1) "1 hour ago" else "$hours hours ago"
            }
            diff < 604800000 -> {
                val days = diff / 86400000
                if (days <= 1) "1 day ago" else "$days days ago"
            }
            diff < 2592000000 -> {
                val weeks = diff / 604800000
                if (weeks <= 1) "1 week ago" else "$weeks weeks ago"
            }
            diff < 31536000000 -> {
                val months = diff / 2592000000
                if (months <= 1) "1 month ago" else "$months months ago"
            }
            else -> {
                val years = diff / 31536000000
                if (years <= 1) "1 year ago" else "$years years ago"
            }
        }
    } catch (e: Exception) {
        // Fallback if parsing fails
        "Recently added"
    }
}