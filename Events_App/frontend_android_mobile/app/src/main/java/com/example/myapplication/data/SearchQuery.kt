package com.example.myapplication.data

data class SearchQuery(
    val keyword: String,
    val distance: Int,
    val category: String,
    val location: String,
    val useCurrentLocation: Boolean
)