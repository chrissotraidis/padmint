import PhotosUI
import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @State private var search = ""
    @State private var onlyInstalled = false
    @State private var missing: Game?
    @State private var coverTarget: Game?
    @State private var pickingCover = false
    @State private var picked: PhotosPickerItem?
    @State private var askBoxArt = false

    private var shown: [Game] {
        library.games.filter { game in
            (!onlyInstalled || library.installed.contains(game.id))
                && (search.isEmpty || game.name.localizedCaseInsensitiveContains(search)
                    || game.game.localizedCaseInsensitiveContains(search))
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    if search.isEmpty {
                        if library.installedGames.isEmpty {
                            EmptyShelf()
                        } else {
                            Text("Your games").font(.title2.bold()).padding(.horizontal)
                            CoverRow(games: library.installedGames, play: play, chooseCover: chooseCover)
                        }
                    }
                    HStack {
                        Text(search.isEmpty ? "All games" : "Results").font(.title2.bold())
                        Spacer()
                        Picker("Show", selection: $onlyInstalled) {
                            Text("All").tag(false)
                            Text("Installed").tag(true)
                        }
                        .pickerStyle(.segmented)
                        .frame(maxWidth: 220)
                    }
                    .padding(.horizontal)
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 130), spacing: 16)], spacing: 22) {
                        ForEach(shown) { game in
                            NavigationLink(value: game) { GameTile(game: game) }
                                .buttonStyle(.plain)
                                .contextMenu { GameMenu(game: game, play: play, chooseCover: chooseCover) }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("PadMint")
            .navigationDestination(for: Game.self) { GameDetail(game: $0, play: play, chooseCover: chooseCover) }
            .searchable(text: $search, prompt: "Search games")
            .refreshable { await library.refresh() }
            .toolbar {
                ToolbarItem {
                    Menu {
                        Section("Box art") {
                            Button { Task { await covers.setBoxArt(.download, games: library.games) } } label: {
                                Label("Download Box Art", systemImage: covers.boxArt == .download ? "checkmark" : "arrow.down.circle")
                            }
                            Button { Task { await covers.setBoxArt(.off, games: library.games) } } label: {
                                Label("Use PadMint Art", systemImage: covers.boxArt == .download ? "square.grid.2x2" : "checkmark")
                            }
                        }
                    } label: {
                        Label("Covers", systemImage: covers.downloading ? "arrow.down.circle.dotted" : "photo.on.rectangle")
                    }
                }
            }
            .sheet(item: $missing) { GetGameSheet(game: $0) }
            .sheet(isPresented: $askBoxArt) { BoxArtSheet() }
            .photosPicker(isPresented: $pickingCover, selection: $picked, matching: .images)
            .onChange(of: picked) { _, item in
                guard let item, let game = coverTarget else { return }
                Task {
                    if let data = try? await item.loadTransferable(type: Data.self) { covers.choose(data, for: game) }
                    picked = nil
                    coverTarget = nil
                }
            }
            .task { if covers.boxArt == .ask { askBoxArt = true } }
        }
    }

    private func play(_ game: Game) {
        guard library.canTry(game) else {
            missing = game
            return
        }
        Task { if await !library.play(game) { missing = game } }
    }

    private func chooseCover(_ game: Game) {
        coverTarget = game
        pickingCover = true
    }
}

/// Installed games as large covers you swipe through, the most recently played first.
private struct CoverRow: View {
    let games: [Game]
    let play: (Game) -> Void
    let chooseCover: (Game) -> Void
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.horizontalSizeClass) private var sizeClass

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(alignment: .top, spacing: 20) {
                ForEach(games) { game in
                    Button { play(game) } label: {
                        VStack(spacing: 8) {
                            CoverView(game: game, corner: 20)
                                .shadow(color: .black.opacity(0.25), radius: 12, y: 6)
                            Text(game.name).font(.headline).lineLimit(1)
                            Text(lastPlayedText(library.lastPlayed[game.id]))
                                .font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                        }
                    }
                    .buttonStyle(.plain)
                    .contextMenu { GameMenu(game: game, play: play, chooseCover: chooseCover) }
                    // Four covers across an iPad, one and a half on an iPhone.
                    .containerRelativeFrame(.horizontal, count: sizeClass == .regular ? 4 : 5,
                                            span: sizeClass == .regular ? 1 : 3, spacing: 20)
                    .scrollTransition { content, phase in
                        content.scaleEffect(phase.isIdentity ? 1 : 0.9).opacity(phase.isIdentity ? 1 : 0.7)
                    }
                }
            }
            .scrollTargetLayout()
        }
        .scrollTargetBehavior(.viewAligned)
        .contentMargins(.horizontal, 20, for: .scrollContent)
    }
}

func lastPlayedText(_ date: Date?) -> String {
    guard let date else { return "Not played from here yet" }
    return "Played \(date.formatted(.relative(presentation: .named)))"
}

private struct GameTile: View {
    @EnvironmentObject private var library: LibraryModel
    let game: Game

    var body: some View {
        let installed = library.installed.contains(game.id)
        VStack(alignment: .leading, spacing: 6) {
            CoverView(game: game)
                .saturation(installed ? 1 : 0)
                .opacity(installed ? 1 : 0.6)
            Text(game.name).font(.subheadline.bold()).lineLimit(1)
            Text(library.status(game))
                .font(.caption)
                .foregroundStyle(installed ? Color.green : Color.secondary)
                .lineLimit(1)
        }
    }
}

/// Long-press menu for a game.
private struct GameMenu: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    let game: Game
    let play: (Game) -> Void
    let chooseCover: (Game) -> Void

    var body: some View {
        if library.canTry(game) {
            Button { play(game) } label: { Label("Play", systemImage: "play.fill") }
        }
        Button { chooseCover(game) } label: { Label("Choose Cover…", systemImage: "photo") }
        if covers.hasChosen(game) {
            Button(role: .destructive) { covers.removeChosen(game) } label: {
                Label("Remove Chosen Cover", systemImage: "arrow.uturn.backward")
            }
        }
    }
}

private struct GameDetail: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    let game: Game
    let play: (Game) -> Void
    let chooseCover: (Game) -> Void

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                CoverView(game: game, corner: 24)
                    .frame(maxWidth: 300)
                    .shadow(color: .black.opacity(0.25), radius: 16, y: 8)
                VStack(spacing: 6) {
                    Text(game.name).font(.largeTitle.bold())
                    Text(game.game).font(.title3).foregroundStyle(.secondary).multilineTextAlignment(.center)
                    Text(library.installed.contains(game.id) ? lastPlayedText(library.lastPlayed[game.id]) : library.status(game))
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                if library.canTry(game) {
                    Button { play(game) } label: {
                        Label("Play", systemImage: "play.fill").font(.title3.bold()).frame(maxWidth: 260)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                } else {
                    HowToGet(game: game)
                }
                HStack {
                    Button("Choose Cover…") { chooseCover(game) }
                    if covers.hasChosen(game) {
                        Button("Remove Chosen Cover", role: .destructive) { covers.removeChosen(game) }
                    }
                }
                .buttonStyle(.bordered)
                Link("\(game.name) on GitHub", destination: game.repo).font(.footnote)
                if game.boxArt != nil, covers.boxArt == .download, !covers.hasChosen(game) {
                    Text("Box art from libretro-thumbnails").font(.footnote).foregroundStyle(.secondary)
                }
            }
            .padding(24)
            .frame(maxWidth: .infinity)
        }
        .background(Color(.systemGroupedBackground))
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct HowToGet: View {
    let game: Game

    var body: some View {
        VStack(spacing: 12) {
            Text(game.link == nil
                 ? "\(game.name) is a ready-made app. Install it from its page; PadMint can't see it on this device yet."
                 : "Build \(game.name) with PadMint on your computer and install it on this device. It then shows up here.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Link(game.link == nil ? "Open \(game.name)'s page" : "How to get it with PadMint",
                 destination: game.link == nil ? game.repo : URL(string: "https://github.com/chrissotraidis/padmint")!)
                .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: 420)
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
                CoverView(game: game, corner: 24).frame(width: 180)
                Text(game.game).font(.headline).multilineTextAlignment(.center)
                HowToGet(game: game)
                Spacer()
            }
            .padding(24)
            .navigationTitle(game.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
        }
    }
}

/// Asked once: box art comes from outside PadMint, so the player chooses.
private struct BoxArtSheet: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: "photo.stack").font(.system(size: 48)).foregroundStyle(.tint)
            Text("Download box art?").font(.title.bold())
            Text("PadMint can download box art for \(library.games.filter { $0.boxArt != nil }.count) console games from libretro's thumbnail collection (thumbnails.libretro.com) and keep it on this device. PadMint doesn't include box art itself.\n\nYou can change this later from the covers menu, or choose your own picture for any game.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button {
                dismiss()
                Task { await covers.setBoxArt(.download, games: library.games) }
            } label: { Text("Download Box Art").frame(maxWidth: 280) }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            Button("Use PadMint Art") {
                dismiss()
                Task { await covers.setBoxArt(.off, games: library.games) }
            }
        }
        .padding(32)
        .frame(maxWidth: 520)
        .interactiveDismissDisabled()
    }
}

