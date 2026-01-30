package com.example.myapplication.data

data class GeocodingResponse(
    val results: List<GeocodingResult>,
    val status: String
)

data class GeocodingResult(
    val geometry: Geometry,
)

data class Geometry(
    val location: LatLng,
)

data class LatLng(
    val lat: Double,
    val lng: Double
)
