package com.example.myapplication.screens

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.example.myapplication.data.EventDetailsResponse
import com.example.myapplication.data.SpotifyArtistResponse
import com.example.myapplication.data.VenueDetailsResponse
import androidx.compose.foundation.pager.*
import com.example.myapplication.data.SpotifyAlbum
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.OpenInNew
import com.example.myapplication.data.Venue

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EventDetailsScreen(
    eventId: String,
    eventDetails: EventDetailsResponse?,
    artistData: Map<String, SpotifyArtistResponse>,
    venueDetails: VenueDetailsResponse?,
    isLoading: Boolean,
    artistLoading: Boolean,
    venueLoading: Boolean,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onToggleFavorite: () -> Unit,
    modifier: Modifier = Modifier
) {
    val pagerState = rememberPagerState(pageCount = { 3 })
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    val tabTitles = listOf("Details", "Artist", "Venue")

    Scaffold(
        topBar = {
            Column {
                TopAppBar(
                    title = {
                        Text(
                            text = eventDetails?.name ?: "Event Details",
                            maxLines = 1,
                            style = MaterialTheme.typography.titleMedium
                        )
                    },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
                        }
                    },
                    actions = {
                        IconButton(onClick = onToggleFavorite) {
                            Icon(
                                imageVector = if (isFavorite) Icons.Filled.Favorite else Icons.Outlined.FavoriteBorder,
                                contentDescription = "Favorite",
                                tint = if (isFavorite) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                )

                TabRow(
                    selectedTabIndex = pagerState.currentPage,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    tabTitles.forEachIndexed { index, title ->
                        Tab(
                            selected = pagerState.currentPage == index,
                            onClick = { scope.launch { pagerState.animateScrollToPage(index) } },
                            text = { Text(title) }
                        )
                    }
                }
            }
        }
    ) { padding ->
        if (isLoading && eventDetails == null) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize().padding(padding)
            ) { page ->
                when (page) {
                    0 -> DetailsTab(eventDetails, context)
                    1 -> ArtistTab(eventDetails, artistData, artistLoading, context)
                    2 -> VenueTab(eventDetails, venueDetails, venueLoading, context)
                }
            }
        }
    }
}

@Composable
fun DetailsTab(
    eventDetails: EventDetailsResponse?,
    context: android.content.Context
) {
    if (eventDetails == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("No event details available")
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Event Info Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Event",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Row {
                        // Buy Tickets Icon
                        eventDetails.url?.let { url ->
                            IconButton(onClick = {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                context.startActivity(intent)
                            }) {
                                Icon(Icons.Default.OpenInNew, "Buy Tickets")
                            }
                        }

                        // Share Icon
                        IconButton(onClick = {
                            val shareIntent = Intent().apply {
                                action = Intent.ACTION_SEND
                                putExtra(Intent.EXTRA_TEXT, "Check out ${eventDetails.name ?: "this event"}: ${eventDetails.url ?: ""}")
                                type = "text/plain"
                            }
                            context.startActivity(Intent.createChooser(shareIntent, "Share via"))
                        }) {
                            Icon(Icons.Default.Share, "Share")
                        }
                    }
                }

                Spacer(Modifier.height(12.dp))

                // Date
                DetailRow("Date", formatEventDate(eventDetails.dates?.start?.localDate, eventDetails.dates?.start?.localTime))

                // Artists/Team
                val artists = eventDetails._embedded?.attractions?.joinToString(", ") { it.name } ?: "N/A"
                DetailRow("Artist", artists)

                // Venue
                val venueName = eventDetails._embedded?.venues?.firstOrNull()?.name ?: "N/A"
                DetailRow("Venue", venueName)

                // Genres
                val genres = buildGenresString(eventDetails.classifications?.firstOrNull())
                if (genres.isNotEmpty()) {
                    DetailRow("Genres", genres)
                }

                // Price Ranges
                eventDetails.priceRanges?.firstOrNull()?.let { price ->
                    val priceText = "${price.currency ?: "USD"} ${price.min ?: "N/A"} - ${price.max ?: "N/A"}"
                    DetailRow("Price Ranges", priceText)
                }

                // Ticket Status
                eventDetails.dates?.status?.code?.let { status ->
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Ticket Status",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(4.dp))
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = when (status.lowercase()) {
                            "onsale" -> MaterialTheme.colorScheme.primary
                            "offsale" -> MaterialTheme.colorScheme.secondary
                            "cancelled", "canceled" -> MaterialTheme.colorScheme.error
                            else -> MaterialTheme.colorScheme.surfaceVariant
                        }
                    ) {
                        Text(
                            text = formatTicketStatus(status),
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Seatmap Card
        eventDetails.seatmap?.staticUrl?.let { seatmapUrl ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Seatmap",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(Modifier.height(12.dp))
                    AsyncImage(
                        model = seatmapUrl,
                        contentDescription = "Venue Seatmap",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(300.dp),
                        contentScale = ContentScale.Fit
                    )
                }
            }
        }
    }
}

@Composable
fun DetailRow(label: String, value: String?) {
    val displayValue = value ?: "N/A"

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = displayValue,
            style = MaterialTheme.typography.bodyMedium
        )
        Spacer(Modifier.height(12.dp))
    }
}

@Composable
fun ArtistTab(
    eventDetails: EventDetailsResponse?,
    artistData: Map<String, SpotifyArtistResponse>,
    isLoading: Boolean,
    context: android.content.Context
) {
    val attractions = eventDetails?._embedded?.attractions
    val isMusicEvent = eventDetails?.classifications?.firstOrNull()?.segment?.name?.equals("Music", ignoreCase = true) == true

    if (isLoading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    // If not a music event or no artist data available
    if (!isMusicEvent || artistData.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "No music artist data",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        attractions?.forEach { attraction ->
            val artistInfo = artistData[attraction.name]

            if (artistInfo != null) {
                ArtistCard(
                    artistInfo = artistInfo,
                    context = context
                )
                Spacer(Modifier.height(16.dp))
            }
        }
    }
}

@Composable
fun ArtistCard(
    artistInfo: SpotifyArtistResponse,
    context: android.content.Context
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        // Artist Header with Image and Info
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Artist Image
            artistInfo.artist?.images?.firstOrNull()?.url?.let { imageUrl ->
                AsyncImage(
                    model = imageUrl,
                    contentDescription = artistInfo.artist?.name ?: "Artist",
                    modifier = Modifier
                        .size(100.dp)
                        .clip(MaterialTheme.shapes.medium),
                    contentScale = ContentScale.Crop
                )
                Spacer(Modifier.width(16.dp))
            }

            // Artist Name and Stats
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = artistInfo.artist?.name ?: "Unknown Artist",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.weight(1f)
                    )

                    artistInfo.artist?.spotifyUrl?.let { spotifyUrl ->
                        IconButton(
                            onClick = {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(spotifyUrl))
                                context.startActivity(intent)
                            }
                        ) {
                            Icon(
                                Icons.Default.OpenInNew,
                                contentDescription = "Open in Spotify",
                                tint = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }

                Spacer(Modifier.height(4.dp))

                // Followers and Popularity in one line
                Row {
                    artistInfo.artist?.followers?.let { followers ->
                        Text(
                            text = "Followers: ${formatFollowers(followers)}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    artistInfo.artist?.popularity?.let { popularity ->
                        Text(
                            text = "   Popularity: $popularity%",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Genres
        if (!artistInfo.artist?.genres.isNullOrEmpty()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                artistInfo.artist?.genres?.take(3)?.forEach { genre ->
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = MaterialTheme.colorScheme.secondaryContainer
                    ) {
                        Text(
                            text = genre,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSecondaryContainer
                        )
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
        }

        // Albums Section with Grid Layout
        if (!artistInfo.albums.isNullOrEmpty()) {
            Text(
                text = "Albums",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(12.dp))

            // Sort albums by release date (newest first)
            val sortedAlbums = artistInfo.albums.sortedByDescending { it.releaseDate ?: "" }

            // Grid of albums
            Column(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                sortedAlbums.chunked(2).forEach { rowAlbums ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        rowAlbums.forEach { album ->
                            AlbumGridItem(
                                album = album,
                                context = context,
                                modifier = Modifier.weight(1f)
                            )
                        }
                        // Add empty space if odd number of albums
                        if (rowAlbums.size == 1) {
                            Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AlbumGridItem(
    album: SpotifyAlbum,
    context: Context,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .clickable {
                album.spotifyUrl?.let { url ->
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    context.startActivity(intent)
                }
            }
    ) {
        // Album Cover - Square aspect ratio
        album.images?.firstOrNull()?.url?.let { imageUrl ->
            AsyncImage(
                model = imageUrl,
                contentDescription = album.name,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
                    .clip(MaterialTheme.shapes.medium),
                contentScale = ContentScale.Crop
            )
        }

        Spacer(Modifier.height(8.dp))

        // Album Name
        Text(
            text = album.name,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
            minLines = 2
        )

        Spacer(Modifier.height(4.dp))

        // Release Date and Track Count
        Text(
            text = formatAlbumDate(album.releaseDate),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        album.totalTracks?.let { tracks ->
            Text(
                text = "$tracks tracks",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// Helper function to format followers count
private fun formatFollowers(count: Int): String {
    return when {
        count >= 1_000_000 -> String.format("%.1fM", count / 1_000_000.0)
        count >= 1_000 -> String.format("%.1fK", count / 1_000.0)
        else -> count.toString()
    }
}

// Helper function to format album release date
private fun formatAlbumDate(releaseDate: String?): String {
    if (releaseDate == null) return "Unknown"

    return try {
        when (releaseDate.length) {
            4 -> releaseDate // Just year
            7 -> { // YYYY-MM
                val parts = releaseDate.split("-")
                val month = SimpleDateFormat("MM", Locale.getDefault())
                    .parse(parts[1])
                val monthName = SimpleDateFormat("MMM", Locale.getDefault()).format(month ?: Date())
                "$monthName ${parts[0]}"
            }
            10 -> { // YYYY-MM-DD
                val inputFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                val date = inputFormat.parse(releaseDate)
                val outputFormat = SimpleDateFormat("MMM d, yyyy", Locale.getDefault())
                outputFormat.format(date ?: Date())
            }
            else -> releaseDate
        }
    } catch (e: Exception) {
        releaseDate
    }
}

@Composable
fun VenueTab(
    eventDetails: EventDetailsResponse?,
    venueDetails: VenueDetailsResponse?,
    isLoading: Boolean,
    context: android.content.Context
) {
    if (isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            CircularProgressIndicator()
        }
        return
    }

    // Get venue from event details
    val venue = eventDetails?._embedded?.venues?.firstOrNull()

    if (venue == null && venueDetails == null) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "No venue information available",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(0.dp)
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column {
                // Venue Cover Image at the top of the card
                val coverImage = venueDetails?.images?.firstOrNull()?.url
                    ?: venue?.images?.firstOrNull()?.url

                coverImage?.let { imageUrl ->
                    AsyncImage(
                        model = imageUrl,
                        contentDescription = "Venue Image",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(250.dp),
                        contentScale = ContentScale.Crop
                    )
                }

                // Venue details below the image
                Column(modifier = Modifier.padding(12.dp)) {
                    // Venue Name with External Link
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = venueDetails?.name ?: venue?.name ?: "Unknown Venue",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.weight(1f)
                        )

                        // External link to Ticketmaster venue page
                        val venueUrl = venueDetails?.url
                        venueUrl?.let { url ->
                            IconButton(
                                onClick = {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                    context.startActivity(intent)
                                }
                            ) {
                                Icon(
                                    Icons.Default.OpenInNew,
                                    contentDescription = "Open Venue Page",
                                    tint = MaterialTheme.colorScheme.primary
                                )
                            }
                        }
                    }

                    Spacer(Modifier.height(16.dp))

                    // Address
                    val addressText = buildVenueAddress(venueDetails, venue)
                    if (addressText.isNotEmpty()) {
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = addressText,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 2,
                        )
                    }

                    Spacer(Modifier.height(8.dp))

                    // Contact Info (Phone/Box Office)
                    venueDetails?.let { details ->
                        // Add any additional venue details here if available from API
                    }
                }
            }
        }
    }
}

private fun buildVenueAddress(
    venueDetails: VenueDetailsResponse?,
    venue: Venue?
): String {
    val addressParts = mutableListOf<String>()

    // Try venueDetails first, then fall back to venue
    val address = venueDetails?.address ?: venue?.address
    val city = venueDetails?.city?.name ?: venue?.city?.name
    val state = venueDetails?.state?.name ?: venue?.state?.name
    val postalCode = venueDetails?.postalCode
    val country = venueDetails?.country?.name ?: venue?.country?.name

    // Add address lines
    address?.line1?.let { addressParts.add(it) }
    address?.line2?.let { addressParts.add(it) }
    address?.line3?.let { addressParts.add(it) }

    // Add city, state, postal code
    val cityStateZip = buildString {
        if (city != null) append(city)
        if (state != null) {
            if (isNotEmpty()) append(", ")
            append(state)
        }
        if (postalCode != null) {
            if (isNotEmpty()) append(" ")
            append(postalCode)
        }
    }
    if (cityStateZip.isNotEmpty()) {
        addressParts.add(cityStateZip)
    }

    // Add country
    country?.let { addressParts.add(it) }

    return addressParts.joinToString(", ")
}

// Helper Functions
private fun formatEventDate(date: String?, time: String?): String {
    if (date == null) return "TBD"

    return try {
        // Parse the date (format: 2026-08-08)
        val inputFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val parsedDate = inputFormat.parse(date)
        val outputFormat = SimpleDateFormat("MMM d, yyyy", Locale.getDefault())
        val formattedDate = outputFormat.format(parsedDate ?: Date())

        if (time != null && time.isNotEmpty()) {
            // Parse the time (format: 17:30:00)
            try {
                val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
                val parsedTime = timeFormat.parse(time)
                val outputTimeFormat = SimpleDateFormat("h:mm a", Locale.getDefault())
                val formattedTime = outputTimeFormat.format(parsedTime ?: Date())
                "$formattedDate, $formattedTime"
            } catch (e: Exception) {
                formattedDate
            }
        } else {
            formattedDate
        }
    } catch (e: Exception) {
        if (time != null) {
            "$date, $time"
        } else {
            date
        }
    }
}

private fun buildGenresString(classification: com.example.myapplication.data.Classification?): String {
    if (classification == null) return ""

    val parts = mutableListOf<String>()
    classification.segment?.name?.let { parts.add(it) }
    classification.genre?.name?.let { parts.add(it) }
    classification.subGenre?.name?.let { parts.add(it) }
    classification.type?.name?.let { parts.add(it) }
    classification.subType?.name?.let { parts.add(it) }

    return parts.joinToString(" | ")
}

private fun formatTicketStatus(status: String): String {
    return when (status.lowercase()) {
        "onsale" -> "On Sale"
        "offsale" -> "Off Sale"
        "cancelled", "canceled" -> "Canceled"
        else -> status
    }
}