import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var library: LibraryModel
    @State private var selected: Game?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    if library.installedGames.isEmpty {
                        EmptyShelf()
                    } else {
                        CoverRow(games: library.installedGames) { open($0) }
                    }
                    Text("All games")
                        .font(.title2.bold())
                        .padding(.horizontal)
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 140), spacing: 16)], spacing: 20) {
                        ForEach(library.games) { game in
                            Button { open(game) } label: {
                                GameTile(game: game, installed: library.installed.contains(game.id))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("PadMint")
            .refreshable { await library.refresh() }
            .sheet(item: $selected) { GetGameSheet(game: $0) }
        }
    }

    private func open(_ game: Game) {
        // Checked games are known not to be installed; any other game is tried first.
        if !library.installed.contains(game.id) && (game.checked || game.link == nil) {
            selected = game
            return
        }
        Task { if await !library.play(game) { selected = game } }
    }
}

/// The installed games as large covers you swipe through; tap one to play.
private struct CoverRow: View {
    let games: [Game]
    let play: (Game) -> Void
    @Environment(\.horizontalSizeClass) private var sizeClass

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(spacing: 20) {
                ForEach(games) { game in
                    Button { play(game) } label: {
                        VStack(spacing: 10) {
                            Cover(game: game)
                                .aspectRatio(1, contentMode: .fit)
                                .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                                .shadow(color: .black.opacity(0.25), radius: 12, y: 6)
                            Text(game.name).font(.headline)
                            Text(game.game).font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                        }
                    }
                    .buttonStyle(.plain)
                    // Three covers across an iPad, one and a bit on an iPhone.
                    .containerRelativeFrame(.horizontal, count: sizeClass == .regular ? 3 : 5,
                                            span: sizeClass == .regular ? 1 : 4, spacing: 20)
                    .scrollTransition { content, phase in
                        content.scaleEffect(phase.isIdentity ? 1 : 0.85).opacity(phase.isIdentity ? 1 : 0.6)
                    }
                }
            }
            .scrollTargetLayout()
        }
        .scrollTargetBehavior(.viewAligned)
        .contentMargins(.horizontal, 40, for: .scrollContent)
    }
}

private struct GameTile: View {
    let game: Game
    let installed: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Cover(game: game)
                .aspectRatio(1, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .saturation(installed ? 1 : 0)
                .opacity(installed ? 1 : 0.55)
            Text(game.name).font(.subheadline.bold()).lineLimit(1)
            Text(installed ? "Installed" : game.link == nil ? "Ready-made app"
                 : game.checked ? "Not installed" : "Tap to open")
                .font(.caption)
                .foregroundStyle(installed ? Color.green : Color.secondary)
        }
    }
}

private struct Cover: View {
    let game: Game

    var body: some View {
        AsyncImage(url: game.art) { image in
            image.resizable().interpolation(.high).scaledToFill()
        } placeholder: {
            ZStack {
                LinearGradient(colors: [.mint, .teal], startPoint: .topLeading, endPoint: .bottomTrailing)
                Text(game.name).font(.headline).foregroundStyle(.white).padding()
            }
        }
    }
}

private struct EmptyShelf: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("No games here yet").font(.title2.bold())
            Text("Build a game with PadMint and install it on this device, and it shows up here. A game installed before PadMint added launch links shows up after you rebuild it.")
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal)
    }
}

private struct GetGameSheet: View {
    let game: Game
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Cover(game: game)
                    .frame(width: 180, height: 180)
                    .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                Text(game.game).font(.headline).multilineTextAlignment(.center)
                Text(game.link == nil
                     ? "\(game.name) is a ready-made app. Install it from its page; PadMint can't see it on this device yet."
                     : "Build \(game.name) with PadMint on your computer and install it on this device. It then shows up here.")
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.secondary)
                Link(game.link == nil ? "Open \(game.name)'s page" : "How to get it with PadMint",
                     destination: game.link == nil ? game.repo : URL(string: "https://github.com/chrissotraidis/padmint")!)
                    .buttonStyle(.borderedProminent)
                Spacer()
            }
            .padding(24)
            .navigationTitle(game.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
        }
    }
}
