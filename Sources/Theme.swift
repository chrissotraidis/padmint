import SwiftUI
import UIKit

extension Color {
    /// PadMint's mint, from the icon's gradient.
    static let padMint = Color(red: 0.13, green: 0.74, blue: 0.48)
    static let padMintLight = Color(red: 0.37, green: 0.94, blue: 0.69)
}

/// PadMint's logo and wordmark, for the top of the library.
struct PadMintMark: View {
    var size: CGFloat = 30

    var body: some View {
        HStack(spacing: 10) {
            Image("Logo").resizable().frame(width: size, height: size)
                .clipShape(RoundedRectangle(cornerRadius: size * 0.24, style: .continuous))
                .shadow(color: .padMint.opacity(0.45), radius: 6)
            Text("PadMint")
                .font(.system(size: size * 0.8, weight: .heavy, design: .rounded))
                .foregroundStyle(LinearGradient(colors: [.padMintLight, .padMint], startPoint: .topLeading, endPoint: .bottomTrailing))
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("PadMint")
    }
}

enum Appearance: String, CaseIterable, Identifiable {
    case dark, light, system
    var id: Self { self }
    var label: String { rawValue.capitalized }
    var scheme: ColorScheme? {
        switch self {
        case .dark: .dark
        case .light: .light
        case .system: nil
        }
    }
}

enum CoverSize: String, CaseIterable, Identifiable {
    case small, medium, large
    var id: Self { self }
    var label: String { rawValue.capitalized }
    var scale: CGFloat {
        switch self {
        case .small: 0.78
        case .medium: 1
        case .large: 1.3
        }
    }
}

enum CarouselStyle: String, CaseIterable, Identifiable {
    case boxes, flat
    var id: Self { self }
    var label: String { self == .boxes ? "3D boxes" : "Flat covers" }
}

/// The options the filter bar and settings share.
struct FilterBar: View {
    @EnvironmentObject private var library: LibraryModel
    @AppStorage("sort") private var sort: SortOrder = .recent
    @AppStorage("console") private var console = ""
    @AppStorage("onlyInstalled") private var onlyInstalled = false

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                Menu {
                    Picker("Sort by", selection: $sort.animation(.snappy)) {
                        ForEach(SortOrder.allCases) { Text($0.label).tag($0) }
                    }
                } label: {
                    Chip(text: sort.label, symbol: "arrow.up.arrow.down", selected: true)
                }
                Button { withAnimation(.snappy) { onlyInstalled.toggle() } } label: {
                    Chip(text: "Installed", symbol: "checkmark.circle", selected: onlyInstalled)
                }
                Divider().frame(height: 22)
                Button { withAnimation(.snappy) { console = "" } } label: { Chip(text: "All consoles", selected: console.isEmpty) }
                ForEach(LibraryModel.consoles.filter { name in library.games.contains { $0.platform == name } }, id: \.self) { name in
                    Button { withAnimation(.snappy) { console = console == name ? "" : name } } label: {
                        Chip(text: name, selected: console == name)
                    }
                }
            }
            .buttonStyle(.plain)
            .padding(.horizontal)
        }
    }
}

struct Chip: View {
    let text: String
    var symbol: String?
    var selected = false

    var body: some View {
        HStack(spacing: 5) {
            if let symbol { Image(systemName: symbol) }
            Text(text)
        }
        .font(.subheadline.weight(.semibold))
        .padding(.horizontal, 13)
        .padding(.vertical, 7)
        .foregroundStyle(selected ? Color.black : Color.primary)
        .background {
            Capsule().fill(selected ? AnyShapeStyle(Color.padMintLight) : AnyShapeStyle(.thinMaterial))
        }
    }
}

