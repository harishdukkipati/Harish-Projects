const express = require('express');
const cors = require('cors');
const { MongoClient, ObjectId } = require('mongodb');
const app = express();
const path = require('path');
const fs = require('fs');
const detectPort = require('detect-port');

// Load environment variables
require('dotenv').config();

// Middleware
app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Your API keys from .env file
const TICKETMASTER_API_KEY = process.env.TICKETMASTER_API_KEY || '';
const MONGODB_URI = process.env.MONGODB_URI;
const SPOTIFY_CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const SPOTIFY_CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const IPAPI_KEY = process.env.IPAPI_KEY;

let db;
let favoritesCollection;
let mongoClient;
let spotifyAccessToken = null;
let spotifyTokenExpiry = 0;
let isMongoAvailable = false;

async function getSpotifyAccessToken() {
  if (!SPOTIFY_CLIENT_ID || !SPOTIFY_CLIENT_SECRET) {
    throw new Error('Spotify credentials are not configured');
  }

  const now = Date.now();
  if (spotifyAccessToken && spotifyTokenExpiry > now + 60_000) {
    return spotifyAccessToken;
  }

  const authHeader = Buffer.from(
    `${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`
  ).toString('base64');

  const response = await fetch('https://accounts.spotify.com/api/token', {
    method: 'POST',
    headers: {
      Authorization: `Basic ${authHeader}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'grant_type=client_credentials',
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to fetch Spotify token: ${response.status} ${errorBody}`
    );
  }

  const data = await response.json();
  spotifyAccessToken = data.access_token;
  spotifyTokenExpiry = now + data.expires_in * 1000;

  return spotifyAccessToken;
}

async function connectToMongoDB() {
  try {
    if (!MONGODB_URI) {
      console.warn(
        'MongoDB favorites store is disabled: MONGODB_URI is not set in environment variables.'
      );
      return false;
    }

    // Ensure connection string has proper SSL/TLS parameters
    let connectionString = MONGODB_URI;
    if (!connectionString.includes('ssl=') && !connectionString.includes('tls=')) {
      // Add SSL parameter if not present
      const separator = connectionString.includes('?') ? '&' : '?';
      connectionString = `${connectionString}${separator}tls=true`;
    }

    mongoClient = new MongoClient(connectionString, {
      serverSelectionTimeoutMS: 10000, // 10 second timeout
      socketTimeoutMS: 45000,
      retryWrites: true,
    });
    
    // Try connecting with retry logic
    let retries = 3;
    while (retries > 0) {
      try {
        await mongoClient.connect();
        console.log('✅ Connected to MongoDB Atlas successfully');
        break;
      } catch (err) {
        retries--;
        if (retries === 0) {
          console.error('❌ MongoDB connection failed after all retries:', err.message);
          throw err;
        }
        console.log(`⚠️  MongoDB connection attempt failed, retrying... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
      }
    }
    
    db = mongoClient.db('ticketmaster_db'); // Your database name
    favoritesCollection = db.collection('favorites');
    
    // Create index on eventId for faster queries
    await favoritesCollection.createIndex({ eventId: 1 });
    isMongoAvailable = true;
    return true;
  } catch (error) {
    console.error('MongoDB connection error:', error);
    isMongoAvailable = false;
    return false;
  }
}

// Initialize MongoDB connection
connectToMongoDB();

function ensureFavoritesCollection(res) {
  if (!isMongoAvailable || !favoritesCollection) {
    res
      .status(503)
      .json({ error: 'Favorites service temporarily unavailable' });
    return false;
  }
  return true;
}

async function fetchSpotifyArtistData(artistName) {
  const accessToken = await getSpotifyAccessToken();

  const searchParams = new URLSearchParams({
    q: artistName,
    type: 'artist',
    limit: '1',
  });

  const searchResponse = await fetch(
    `https://api.spotify.com/v1/search?${searchParams.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!searchResponse.ok) {
    const errorBody = await searchResponse.text();
    throw new Error(
      `Spotify search failed: ${searchResponse.status} ${errorBody}`
    );
  }

  const searchData = await searchResponse.json();
  const artist = searchData?.artists?.items?.[0];

  if (!artist) {
    return null;
  }

  const albumsResponse = await fetch(
    `https://api.spotify.com/v1/artists/${artist.id}/albums?include_groups=album,single&limit=24`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!albumsResponse.ok) {
    const errorBody = await albumsResponse.text();
    throw new Error(
      `Spotify albums request failed: ${albumsResponse.status} ${errorBody}`
    );
  }

  const albumsData = await albumsResponse.json();

  const uniqueAlbums = [];
  const seenAlbumIds = new Set();

  for (const album of albumsData.items || []) {
    if (!album?.id || seenAlbumIds.has(album.id)) {
      continue;
    }
    seenAlbumIds.add(album.id);
    uniqueAlbums.push(album);

    if (uniqueAlbums.length >= 12) {
      break;
    }
  }

  const detailedAlbums = await Promise.all(
    uniqueAlbums.map(async (album) => {
      const albumResponse = await fetch(
        `https://api.spotify.com/v1/albums/${album.id}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (!albumResponse.ok) {
        console.warn(
          `Failed to fetch album details for ${album.id}: ${albumResponse.status}`
        );
        return {
          id: album.id,
          name: album.name,
          releaseDate: album.release_date || null,
          totalTracks: album.total_tracks || 0,
          images: album.images || [],
          spotifyUrl: album.external_urls?.spotify || null,
        };
      }

      const albumDetails = await albumResponse.json();

      return {
        id: albumDetails.id,
        name: albumDetails.name,
        releaseDate: albumDetails.release_date || album.release_date || null,
        totalTracks: albumDetails.total_tracks || album.total_tracks || 0,
        images: albumDetails.images?.length ? albumDetails.images : album.images || [],
        spotifyUrl: albumDetails.external_urls?.spotify || album.external_urls?.spotify || null,
        label: albumDetails.label || null,
        tracks: albumDetails.tracks?.items?.slice(0, 5).map((track) => ({
          id: track.id,
          name: track.name,
          previewUrl: track.preview_url,
          spotifyUrl: track.external_urls?.spotify || null,
        })) || [],
      };
    })
  );

  return {
    artist: {
      id: artist.id,
      name: artist.name,
      followers: artist.followers?.total || 0,
      popularity: artist.popularity || 0,
      genres: artist.genres || [],
      images: artist.images || [],
      spotifyUrl: artist.external_urls?.spotify || null,
    },
    albums: detailedAlbums,
  };
}

// ==================== HEALTH CHECK ====================

app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    mongodb: db ? 'connected' : 'disconnected' 
  });
});

// Debug endpoint to check what assets are actually deployed
app.get('/api/debug/assets', (req, res) => {
  const distPath = path.resolve(__dirname, 'dist');
  const indexPath = path.join(distPath, 'index.html');
  
  if (!fs.existsSync(indexPath)) {
    return res.json({ error: 'index.html not found', distPath });
  }
  
  const indexContent = fs.readFileSync(indexPath, 'utf-8');
  const jsMatch = indexContent.match(/src="\/assets\/([^"]+)"/);
  const cssMatch = indexContent.match(/href="\/assets\/([^"]+)"/);
  
  const assetsDir = path.join(distPath, 'assets');
  const availableAssets = fs.existsSync(assetsDir) 
    ? fs.readdirSync(assetsDir) 
    : [];
  
  res.json({
    distPath,
    indexHtmlExists: fs.existsSync(indexPath),
    referencedAssets: {
      js: jsMatch ? jsMatch[1] : null,
      css: cssMatch ? cssMatch[1] : null
    },
    availableAssets,
    jsExists: jsMatch ? fs.existsSync(path.join(assetsDir, jsMatch[1])) : false,
    cssExists: cssMatch ? fs.existsSync(path.join(assetsDir, cssMatch[1])) : false,
    indexHtmlContent: indexContent.substring(0, 500) // First 500 chars
  });
});

// ==================== LOCATION ENDPOINTS ====================

// Get user location from IP
app.get('/api/location', async (req, res) => {
  try {
    if (!IPAPI_KEY) {
      return res.status(500).json({ error: 'IPAPI key not configured' });
    }

    // Get the client's real IP address from headers
    // App Engine sets X-Forwarded-For with the original client IP
    const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim() 
      || req.headers['x-real-ip'] 
      || req.connection.remoteAddress 
      || req.ip;

    // Use the client's IP, or if not available, let IPAPI detect from the request
    const ipapiUrl = clientIp && clientIp !== '::1' && !clientIp.startsWith('127.')
      ? `https://api.ipapi.com/${clientIp}?access_key=${IPAPI_KEY}`
      : `https://api.ipapi.com/api/check?access_key=${IPAPI_KEY}`;

    console.log(`Fetching location for IP: ${clientIp || 'auto-detect'}`);

    const response = await fetch(ipapiUrl);

    if (!response.ok) {
      throw new Error(`IPAPI error: ${response.status}`);
    }

    const data = await response.json();

    // Check for API errors (like usage limit)
    if (data.success === false && data.error) {
      return res.status(400).json({ 
        error: data.error.type,
        message: data.error.info || data.error.message || 'Unknown error'
      });
    }

    if (data.latitude && data.longitude) {
      res.json({
        latitude: parseFloat(data.latitude),
        longitude: parseFloat(data.longitude),
        city: data.city || null,
        region: data.region || null,
        country: data.country_name || null
      });
    } else {
      res.status(404).json({ error: 'Location not found in IPAPI response' });
    }
  } catch (error) {
    console.error('Error fetching location:', error);
    res.status(500).json({ error: 'Failed to fetch location', message: error.message });
  }
});

// ==================== SPOTIFY ENDPOINTS ====================

app.get('/api/spotify/artist', async (req, res) => {
  try {
    const { name } = req.query;

    if (!name) {
      return res.status(400).json({ error: 'Artist name is required' });
    }

    const data = await fetchSpotifyArtistData(name);

    if (!data) {
      return res.status(404).json({ error: 'Artist not found on Spotify' });
    }

    res.json(data);
  } catch (error) {
    console.error('Spotify endpoint error:', error);
    res.status(500).json({ error: 'Failed to fetch artist data from Spotify' });
  }
});

// ==================== FAVORITES ENDPOINTS ====================

// GET all favorites
app.get('/api/favorites', async (req, res) => {
  if (!ensureFavoritesCollection(res)) {
    return;
  }
  try {
    const favorites = await favoritesCollection
      .find({})
      .sort({ addedAt: -1 }) // Sort by most recently added
      .toArray();
    
    res.json(favorites);
  } catch (error) {
    console.error('Error fetching favorites:', error);
    res.status(500).json({ error: 'Failed to fetch favorites' });
  }
});

// POST add to favorites
app.post('/api/favorites', async (req, res) => {
  if (!ensureFavoritesCollection(res)) {
    return;
  }
  try {
    const eventData = req.body;
    
    // Check if already exists
    const existing = await favoritesCollection.findOne({ 
      eventId: eventData.id 
    });
    
    if (existing) {
      return res.status(409).json({ 
        error: 'Event already in favorites',
        favorite: existing 
      });
    }
    
    // Create favorite object
    const favorite = {
      eventId: eventData.id,
      name: eventData.name,
      date: eventData.dates?.start?.localDate || '',
      time: eventData.dates?.start?.localTime || '',
      category: eventData.classifications?.[0]?.segment?.name || '',
      venue: eventData._embedded?.venues?.[0]?.name || '',
      image: eventData.images?.[0]?.url || '',
      url: eventData.url || '',
      addedAt: new Date()
    };
    
    const result = await favoritesCollection.insertOne(favorite);
    
    res.status(201).json({
      message: 'Added to favorites',
      favorite: { ...favorite, _id: result.insertedId }
    });
  } catch (error) {
    console.error('Error adding favorite:', error);
    res.status(500).json({ error: 'Failed to add favorite' });
  }
});

// DELETE remove from favorites
app.delete('/api/favorites/:id', async (req, res) => {
  if (!ensureFavoritesCollection(res)) {
    return;
  }
  try {
    const { id } = req.params;
    
    // Try to find by eventId first (the Ticketmaster event ID)
    let result = await favoritesCollection.deleteOne({ eventId: id });
    
    // If not found, try by MongoDB _id
    if (result.deletedCount === 0) {
      result = await favoritesCollection.deleteOne({ 
        _id: new ObjectId(id) 
      });
    }
    
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Favorite not found' });
    }
    
    res.json({ 
      message: 'Removed from favorites',
      deletedCount: result.deletedCount 
    });
  } catch (error) {
    console.error('Error removing favorite:', error);
    res.status(500).json({ error: 'Failed to remove favorite' });
  }
});

// GET check if event is favorited
app.get('/api/favorites/check/:eventId', async (req, res) => {
  if (!ensureFavoritesCollection(res)) {
    return;
  }
  try {
    const { eventId } = req.params;
    const favorite = await favoritesCollection.findOne({ eventId });
    
    res.json({ 
      isFavorite: !!favorite,
      favorite: favorite || null
    });
  } catch (error) {
    console.error('Error checking favorite:', error);
    res.status(500).json({ error: 'Failed to check favorite status' });
  }
});

// ==================== TICKETMASTER API ENDPOINTS ====================

// Event search endpoint
app.get('/api/events', async (req, res) => {
  try {
    const { keyword, segmentId, radius, geoPoint, unit = 'miles' } = req.query;
    
    if (!TICKETMASTER_API_KEY) {
      return res.status(500).json({ error: 'Ticketmaster API key not configured' });
    }

    // Build Ticketmaster API URL
    const params = new URLSearchParams({
      apikey: TICKETMASTER_API_KEY,
      size: '20',
      sort: 'date,asc', // Ascending order of date/time
    });

    if (keyword) params.append('keyword', keyword);
    if (segmentId) params.append('segmentId', segmentId);
    if (radius) params.append('radius', radius);
    if (unit) params.append('unit', unit);
    if (geoPoint) params.append('geoPoint', geoPoint);

    const response = await fetch(
      `https://app.ticketmaster.com/discovery/v2/events.json?${params.toString()}`
    );

    if (!response.ok) {
      throw new Error(`Ticketmaster API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Sort events by local date/time (ascending)
    if (data._embedded && data._embedded.events) {
      data._embedded.events.sort((a, b) => {
        const dateA = a.dates?.start?.localDate + ' ' + (a.dates?.start?.localTime || '00:00:00');
        const dateB = b.dates?.start?.localDate + ' ' + (b.dates?.start?.localTime || '00:00:00');
        return new Date(dateA) - new Date(dateB);
      });
    }

    res.json(data);
  } catch (error) {
    console.error('Error fetching events:', error);
    res.status(500).json({ error: 'Failed to fetch events' });
  }
});

// Event details endpoint
app.get('/api/events/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    if (!TICKETMASTER_API_KEY) {
      return res.status(500).json({ error: 'Ticketmaster API key not configured' });
    }

    const response = await fetch(
      `https://app.ticketmaster.com/discovery/v2/events/${id}.json?apikey=${TICKETMASTER_API_KEY}`
    );
    
    if (!response.ok) {
      throw new Error('Event not found');
    }
    
    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching event details:', error);
    res.status(500).json({ error: 'Failed to fetch event details' });
  }
});

// Venue details endpoint
app.get('/api/venues/:id', async (req, res) => {
  try {
    const { id } = req.params;

    if (!TICKETMASTER_API_KEY) {
      return res.status(500).json({ error: 'Ticketmaster API key not configured' });
    }

    const response = await fetch(
      `https://app.ticketmaster.com/discovery/v2/venues/${id}.json?apikey=${TICKETMASTER_API_KEY}`
    );

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Venue not found' });
      }
      throw new Error(`Ticketmaster venue error: ${response.statusText}`);
    }

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching venue details:', error);
    res.status(500).json({ error: 'Failed to fetch venue details' });
  }
});

// Keyword suggestions endpoint
app.get('/api/suggest', async (req, res) => {
  try {
    const { keyword } = req.query;
    
    if (!keyword || !TICKETMASTER_API_KEY) {
      return res.json({ _embedded: { attractions: [] } });
    }

    const response = await fetch(
      `https://app.ticketmaster.com/discovery/v2/attractions.json?apikey=${TICKETMASTER_API_KEY}&keyword=${encodeURIComponent(keyword)}&size=10`
    );

    if (!response.ok) {
      return res.json({ _embedded: { attractions: [] } });
    }

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    res.json({ _embedded: { attractions: [] } });
  }
});

// ==================== FRONTEND STATIC ASSETS ====================

const distPath = path.resolve(__dirname, 'dist');

// Verify dist folder exists and has required files
if (!fs.existsSync(distPath)) {
  console.error(`❌ ERROR: dist folder not found at ${distPath}`);
  console.error('   Please run: npm run build:frontend');
  process.exit(1);
}

const indexPath = path.join(distPath, 'index.html');
if (!fs.existsSync(indexPath)) {
  console.error(`❌ ERROR: index.html not found in dist folder`);
  console.error('   Please run: npm run build:frontend');
  process.exit(1);
}

// Verify assets match what's in index.html
const indexContent = fs.readFileSync(indexPath, 'utf-8');
// Extract asset filenames from index.html
const jsMatch = indexContent.match(/src="\/assets\/([^"]+)"/);
const cssMatch = indexContent.match(/href="\/assets\/([^"]+)"/);

console.log(`✅ Serving static files from: ${distPath}`);
if (jsMatch) {
  const jsFile = path.join(distPath, 'assets', jsMatch[1]);
  if (fs.existsSync(jsFile)) {
    console.log(`   ✓ JS asset found: ${jsMatch[1]}`);
  } else {
    console.error(`   ✗ JS asset missing: ${jsMatch[1]} - Expected file: ${jsFile}`);
    console.error(`   Available assets:`, fs.readdirSync(path.join(distPath, 'assets')).join(', '));
  }
}
if (cssMatch) {
  const cssFile = path.join(distPath, 'assets', cssMatch[1]);
  if (fs.existsSync(cssFile)) {
    console.log(`   ✓ CSS asset found: ${cssMatch[1]}`);
  } else {
    console.error(`   ✗ CSS asset missing: ${cssMatch[1]} - Expected file: ${cssFile}`);
    console.error(`   Available assets:`, fs.readdirSync(path.join(distPath, 'assets')).join(', '));
  }
}

// Serve static files with NO CACHING for JS/CSS - changes should be immediate
app.use(express.static(distPath, {
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.js')) {
      res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
      // NO CACHE - force browser to always fetch latest
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
    } else if (filePath.endsWith('.css')) {
      res.setHeader('Content-Type', 'text/css; charset=utf-8');
      // NO CACHE - force browser to always fetch latest
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
    }
  }
}));

  // Catch-all route for SPA - only serve index.html for non-API, non-asset routes
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api/')) {
      return next();
    }
    // Don't serve index.html for asset requests (they should be handled by static middleware)
    if (req.path.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
      return res.status(404).send('Not found');
    }
    // AGGRESSIVE cache busting for index.html - multiple headers to ensure no caching
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Last-Modified', new Date().toUTCString());
    res.setHeader('ETag', `"${Date.now()}"`);
    res.sendFile(path.join(distPath, 'index.html'));
  });

// ==================== START SERVER ====================

async function startServer() {
  const preferredPort = Number(process.env.PORT) || 8080;
  const isAppEngine = Boolean(
    process.env.GAE_ENV || process.env.GAE_INSTANCE || process.env.K_SERVICE
  );

  let portToUse = preferredPort;

  if (!isAppEngine) {
    const detectedPort = await detectPort(preferredPort);
    if (detectedPort !== preferredPort) {
      console.warn(
        `⚠️  Port ${preferredPort} already in use. Falling back to ${detectedPort}.`
      );
      portToUse = detectedPort;
    }
  }

  app.listen(portToUse, () => {
    console.log(`Server running on port ${portToUse}`);
    if (!TICKETMASTER_API_KEY) {
      console.warn('⚠️  WARNING: TICKETMASTER_API_KEY not set in environment variables!');
    }
    if (!MONGODB_URI) {
      console.warn('⚠️  WARNING: MONGODB_URI not set in environment variables!');
    }
    if (!SPOTIFY_CLIENT_ID || !SPOTIFY_CLIENT_SECRET) {
      console.warn('⚠️  WARNING: Spotify credentials not set in environment variables!');
    }
  });
}

startServer().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\nShutting down gracefully...');
  if (mongoClient) {
    await mongoClient.close();
    console.log('MongoDB connection closed');
  }
  process.exit(0);
});
