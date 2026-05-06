import SwiftUI

/// Fitbit-inspired teal / mint accent (approximates classic Fitbit app chrome).
enum FitbitTheme {
    /// Primary “Fitbit teal”
    static let accent = Color(red: 0, green: 176 / 255, blue: 185 / 255)
    /// Brighter mint for gradients and dark mode emphasis
    static let accentBright = Color(red: 32 / 255, green: 218 / 255, blue: 190 / 255)
    static let accentDeep = Color(red: 0, green: 120 / 255, blue: 128 / 255)

    static var chartGradient: LinearGradient {
        LinearGradient(
            colors: [accentBright, accent],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    static var energyGradient: LinearGradient {
        LinearGradient(
            colors: [accent.opacity(0.55), accentDeep.opacity(0.45)],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    static func cardBackground(_ scheme: ColorScheme) -> Color {
        switch scheme {
        case .dark:
            Color(red: 18 / 255, green: 24 / 255, blue: 24 / 255)
        default:
            Color(red: 246 / 255, green: 250 / 255, blue: 249 / 255)
        }
    }

    static func cardStroke(_ scheme: ColorScheme) -> Color {
        switch scheme {
        case .dark:
            Color.white.opacity(0.08)
        default:
            accent.opacity(0.18)
        }
    }
}
