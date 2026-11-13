import SwiftUI
import UIKit

extension UserDefaults {
    /// An on/off setting that defaults to on. bool(forKey:) also reads "0"/"NO" text,
    /// which is how a value passed at launch arrives.
    func flag(_ key: String) -> Bool { object(forKey: key) == nil ? true : bool(forKey: key) }
}

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
                .font(.system(size: size * 0.72, weight: .bold, design: .rounded))
                .foregroundStyle(.primary)
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
                .chipFocus("sort") { withAnimation(.snappy) { sort = sort.next } }
                Button { withAnimation(.snappy) { onlyInstalled.toggle() } } label: {
                    Chip(text: "Installed", symbol: "checkmark.circle", selected: onlyInstalled)
                }
                .chipFocus("installed") { withAnimation(.snappy) { onlyInstalled.toggle() } }
                Divider().frame(height: 22)
                Button { withAnimation(.snappy) { console = "" } } label: { Chip(text: "All consoles", selected: console.isEmpty) }
                    .chipFocus("console-all") { withAnimation(.snappy) { console = "" } }
                ForEach(LibraryModel.consoles.filter { name in library.games.contains { $0.platform == name } }, id: \.self) { name in
                    Button { withAnimation(.snappy) { console = console == name ? "" : name } } label: {
                        Chip(text: name, selected: console == name)
                    }
                    .chipFocus("console-\(name)") { withAnimation(.snappy) { console = console == name ? "" : name } }
                }
            }
            .buttonStyle(.plain)
            .padding(.horizontal)
            .padding(.vertical, 4)
        }
    }
}

private extension View {
    func chipFocus(_ id: String, action: @escaping () -> Void) -> some View {
        controllerFocus("chip-\(id)", corner: 20, inset: 3, action: action)
    }
}

struct Chip: View {
    let text: String
    var symbol: String?
    var selected = false
    /// A symbol after the text, such as a chevron on a chip that leads somewhere.
    var trailing: String?

    var body: some View {
        HStack(spacing: 5) {
            if let symbol { Image(systemName: symbol) }
            Text(text)
            if let trailing { Image(systemName: trailing).font(.caption.weight(.bold)).foregroundStyle(.secondary) }
        }
        .font(.subheadline.weight(.semibold))
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .foregroundStyle(selected ? Color(.systemBackground) : Color.primary.opacity(0.85))
        .background {
            Capsule().fill(selected ? AnyShapeStyle(Color.primary) : AnyShapeStyle(Color.primary.opacity(0.07)))
        }
        .overlay { Capsule().strokeBorder(Color.primary.opacity(selected ? 0 : 0.1), lineWidth: 0.5) }
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

/// The main action: a solid, quiet button (white on dark, black on light).
struct PrimaryButtonStyle: ButtonStyle {
    var compact = false

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(compact ? .subheadline.weight(.semibold) : .headline)
            .padding(.horizontal, compact ? 14 : 26)
            .frame(minHeight: compact ? 32 : 50)
            .foregroundStyle(Color(.systemBackground))
            .background(Color.primary, in: RoundedRectangle(cornerRadius: compact ? 9 : 14, style: .continuous))
            .opacity(configuration.isPressed ? 0.8 : 1)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

/// Everything else: frosted, with a hairline edge.
struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .padding(.horizontal, 22)
            .frame(minHeight: 50)
            .foregroundStyle(.primary)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay { RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Color.primary.opacity(0.14), lineWidth: 0.5) }
            .opacity(configuration.isPressed ? 0.75 : 1)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

