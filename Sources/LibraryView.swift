import PhotosUI
import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @AppStorage("layout") private var layout: Layout = .shelf
    @AppStorage("sort") private var sort: SortOrder = .recent
    @AppStorage("startOn") private var startOn: StartOn = .library
    @AppStorage("officialTitles") private var official = false
    @AppStorage("onlyInstalled") private var onlyInstalled = false
    @State private var path: [Game] = []
    @State private var search = ""
    @State private var missing: Game?
    @State private var coverTarget: Game?
    @State private var pickingCover = false
    @State private var picked: PhotosPickerItem?
    @State private var askBoxArt = false
    @State private var showSettings = false
    @State private var started = false

    private var shown: [Game] {
        let matching = library.games.filter { game in
            (!onlyInstalled || library.installed.contains(game.id))
                && (search.isEmpty || [game.name, game.title, game.platform].contains {
                    $0.localizedCaseInsensitiveContains(search)
                })
        }
        return library.sorted(matching, by: sort, official: official)
    }

    var body: some View {
        NavigationStack(path: $path) {
            content
                .navigationTitle("PadMint")
                .navigationBarTitleDisplayMode(layout == .carousel ? .inline : .large)
                .navigationDestination(for: Game.self) { GameDetail(game: $0) }
                .searchable(text: $search, prompt: "Search games")
                .toolbar {
                    ToolbarItem {
                        Menu {
                            Picker("Layout", selection: $layout.animation(.snappy)) {
                                ForEach(Layout.allCases) { Label($0.label, systemImage: $0.symbol).tag($0) }
                            }
                            Picker("Sort by", selection: $sort.animation(.snappy)) {
                                ForEach(SortOrder.allCases) { Text($0.label).tag($0) }
                            }
                        } label: {
                            Label("Layout", systemImage: layout.symbol)
                        }
                    }
                    ToolbarItem {
                        Button { showSettings = true } label: { Label("Settings", systemImage: "gearshape") }
                    }
                }
        }
        .environment(\.gameActions, GameActions(play: play, open: { path.append($0) }, chooseCover: chooseCover))
        .sheet(item: $missing) { GetGameSheet(game: $0) }
        .sheet(isPresented: $askBoxArt) { BoxArtSheet() }
        .sheet(isPresented: $showSettings) { SettingsView() }
        .photosPicker(isPresented: $pickingCover, selection: $picked, matching: .images)
        .onChange(of: picked) { _, item in
            guard let item, let game = coverTarget else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self) { covers.choose(data, for: game) }
                picked = nil
                coverTarget = nil
            }
        }
        .task {
            guard !started else { return }
            started = true
            if covers.boxArt == .ask { askBoxArt = true }
            if startOn == .lastPlayed, let game = library.lastPlayedGame { path = [game] }
        }
    }

    @ViewBuilder private var content: some View {
        switch layout {
        case .shelf: ShelfLayout(games: shown, sort: sort, searching: !search.isEmpty)
        case .grid: ScrollView { GameGrid(games: shown, sort: sort, heading: nil).padding(.vertical) }
        case .carousel: CarouselLayout(games: shown)
        case .list: ListLayout(games: shown, sort: sort)
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

// MARK: - Shelf

/// A banner for the game you played last, your installed games, then everything.
private struct ShelfLayout: View {
    @EnvironmentObject private var library: LibraryModel
    let games: [Game]
    let sort: SortOrder
    let searching: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 30) {
                if !searching {
                    if let hero = library.installedGames.first {
                        HeroBanner(game: hero)
                        if library.installedGames.count > 1 {
                            CoverRow(title: "Your games", games: library.installedGames)
                        }
                    } else {
                        EmptyShelf()
                    }
                }
                GameGrid(games: games, sort: sort, heading: searching ? "Results" : "All games")
            }
            .padding(.vertical)
        }
    }
}

private struct HeroBanner: View {
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.gameActions) private var actions
    @Environment(\.horizontalSizeClass) private var sizeClass
    @AppStorage("officialTitles") private var official = false
    let game: Game

    var body: some View {
        let height: CGFloat = sizeClass == .regular ? 300 : 220
        HStack(alignment: .bottom, spacing: 24) {
            Button { actions.open(game) } label: { CoverArt(game: game, corner: 12).frame(maxHeight: height) }
                .buttonStyle(PressableStyle())
            VStack(alignment: .leading, spacing: 10) {
                Text(library.lastPlayed[game.id] == nil ? "READY TO PLAY" : "CONTINUE PLAYING")
                    .font(.caption.weight(.bold)).foregroundStyle(.secondary)
                Text(game.heading(official: official))
                    .font(sizeClass == .regular ? .largeTitle.bold() : .title2.bold())
                    .lineLimit(3).minimumScaleFactor(0.7)
                Text(game.subheading(official: official)).font(.headline).foregroundStyle(.secondary)
                Text(library.status(game)).font(.subheadline).foregroundStyle(.secondary)
                Button { actions.play(game) } label: {
                    Label("Play", systemImage: "play.fill").font(.headline).padding(.horizontal, 14)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .padding(.top, 6)
            }
            Spacer(minLength: 0)
        }
        .padding(24)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background { Backdrop(game: game).clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous)) }
        .padding(.horizontal)
    }
}

/// Covers you swipe through, each at its own shape; tap one to play.
private struct CoverRow: View {
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.gameActions) private var actions
    @Environment(\.horizontalSizeClass) private var sizeClass
    @AppStorage("officialTitles") private var official = false
    let title: String
    let games: [Game]

    var body: some View {
        let height: CGFloat = sizeClass == .regular ? 240 : 170
        VStack(alignment: .leading, spacing: 12) {
            Text(title).font(.title2.bold()).padding(.horizontal)
            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(alignment: .bottom, spacing: 22) {
                    ForEach(games) { game in
                        let width = height * covers.aspect(for: game)
                        Button { actions.play(game) } label: {
                            VStack(alignment: .leading, spacing: 8) {
                                CoverArt(game: game).frame(width: width, height: height)
                                Text(game.heading(official: official)).font(.subheadline.weight(.semibold)).lineLimit(1)
                                    .frame(width: width, alignment: .leading)
                            }
                        }
                        .buttonStyle(PressableStyle())
                        .contextMenu { GameMenu(game: game) }
                        .scrollTransition { content, phase in
                            content.scaleEffect(phase.isIdentity ? 1 : 0.92).opacity(phase.isIdentity ? 1 : 0.6)
                        }
                    }
                }
                .padding(.vertical, 8)
                .scrollTargetLayout()
            }
            .scrollTargetBehavior(.viewAligned)
            .contentMargins(.horizontal, 20, for: .scrollContent)
        }
    }
}

// MARK: - Grid

/// Every game in a grid; with console sorting, a heading per console.
struct GameGrid: View {
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.horizontalSizeClass) private var sizeClass
    let games: [Game]
    let sort: SortOrder
    let heading: String?

    var body: some View {
        let regular = sizeClass == .regular
        VStack(alignment: .leading, spacing: 18) {
            if let heading { Text(heading).font(.title2.bold()).padding(.horizontal) }
            ForEach(library.sections(games, by: sort), id: \.title) { section in
                if let title = section.title {
                    Text(title).font(.title3.bold()).foregroundStyle(.secondary).padding(.horizontal).padding(.top, 8)
                }
                // Cells align at the bottom, so covers of mixed shapes stand on one line and a
                // row is only as tall as its tallest cover (a row of wide N64 boxes stays short).
                LazyVGrid(columns: [GridItem(.adaptive(minimum: regular ? 150 : 104), spacing: regular ? 22 : 14,
                                             alignment: .bottom)],
                          alignment: .leading, spacing: 26) {
                    ForEach(section.games) { GameTile(game: $0, coverHeight: regular ? 210 : 140) }
                }
                .padding(.horizontal)
            }
            if games.isEmpty {
                Text("No games match.").foregroundStyle(.secondary).padding(.horizontal)
            }
        }
    }
}

struct GameTile: View {
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.gameActions) private var actions
    @AppStorage("officialTitles") private var official = false
    let game: Game
    let coverHeight: CGFloat

    var body: some View {
        Button { actions.open(game) } label: {
            VStack(alignment: .leading, spacing: 4) {
                CoverArt(game: game)
                    .frame(maxWidth: .infinity, maxHeight: coverHeight, alignment: .bottomLeading)
                    .padding(.bottom, 6)
                Text(game.heading(official: official))
                    .font(.subheadline.weight(.semibold)).lineLimit(2, reservesSpace: true)
                    .multilineTextAlignment(.leading)
                Text(game.subheading(official: official)).font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .buttonStyle(PressableStyle())
        .contextMenu { GameMenu(game: game) }
        .accessibilityIdentifier("tile-\(game.id)")
    }
}

// MARK: - Carousel

/// Cover flow: the focused game sits in the middle with its art blurred behind it.
private struct CarouselLayout: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.gameActions) private var actions
    @Environment(\.horizontalSizeClass) private var sizeClass
    @AppStorage("officialTitles") private var official = false
    let games: [Game]
    @State private var focused: String?

    private var current: Game? { games.first { $0.id == focused } ?? games.first }

    var body: some View {
        GeometryReader { geo in
            let itemWidth = min(geo.size.width * (sizeClass == .regular ? 0.36 : 0.66), 460)
            let height = min(geo.size.height * 0.62, itemWidth * 1.45)
            ZStack {
                Backdrop(game: current)
                VStack(spacing: 22) {
                    Spacer(minLength: 0)
                    ScrollView(.horizontal, showsIndicators: false) {
                        LazyHStack(alignment: .bottom, spacing: 0) {
                            ForEach(games) { game in
                                Button {
                                    if focused == game.id || (focused == nil && game.id == games.first?.id) { actions.open(game) }
                                    else { withAnimation(.snappy) { focused = game.id } }
                                } label: {
                                    CoverSlot(game: game, height: height).padding(.horizontal, 10)
                                }
                                .buttonStyle(PressableStyle())
                                .frame(width: itemWidth)
                                .contextMenu { GameMenu(game: game) }
                                .scrollTransition(.interactive, axis: .horizontal) { content, phase in
                                    content
                                        .rotation3DEffect(.degrees(phase.value * -38), axis: (x: 0, y: 1, z: 0), perspective: 0.6)
                                        .scaleEffect(1 - abs(phase.value) * 0.16)
                                        .opacity(1 - abs(phase.value) * 0.3)
                                }
                                .id(game.id)
                            }
                        }
                        .scrollTargetLayout()
                    }
                    .scrollTargetBehavior(.viewAligned)
                    .scrollPosition(id: $focused, anchor: .center)
                    .contentMargins(.horizontal, max((geo.size.width - itemWidth) / 2, 0), for: .scrollContent)
                    .frame(height: height + 20)
                    .sensoryFeedback(.selection, trigger: focused)
                    if let game = current {
                        VStack(spacing: 8) {
                            Text(game.heading(official: official))
                                .font(sizeClass == .regular ? .largeTitle.bold() : .title.bold())
                                .multilineTextAlignment(.center).lineLimit(2).minimumScaleFactor(0.7)
                            Text("\(game.subheading(official: official)) · \(library.status(game))")
                                .font(.headline).foregroundStyle(.secondary)
                            HStack(spacing: 12) {
                                Button { actions.play(game) } label: {
                                    Label(library.canTry(game) ? "Play" : "Get It", systemImage: library.canTry(game) ? "play.fill" : "arrow.down.circle")
                                        .font(.headline).padding(.horizontal, 12)
                                }
                                .buttonStyle(.borderedProminent)
                                Button { actions.open(game) } label: { Label("Details", systemImage: "info.circle").font(.headline) }
                                    .buttonStyle(.bordered)
                            }
                            .controlSize(.large)
                            .padding(.top, 6)
                        }
                        .padding(.horizontal)
                        .id(game.id)
                        .transition(.opacity)
                    }
                    Spacer(minLength: 0)
                }
                .animation(.easeInOut(duration: 0.25), value: current?.id)
            }
        }
    }
}

// MARK: - List

private struct ListLayout: View {
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.gameActions) private var actions
    @AppStorage("officialTitles") private var official = false
    let games: [Game]
    let sort: SortOrder

    var body: some View {
        List {
            ForEach(library.sections(games, by: sort), id: \.title) { section in
                Section(section.title ?? "") {
                    ForEach(section.games) { game in
                        HStack(spacing: 14) {
                            Button { actions.open(game) } label: {
                                HStack(spacing: 14) {
                                    CoverArt(game: game, corner: 5, badge: false).frame(width: 64, height: 72)
                                    VStack(alignment: .leading, spacing: 3) {
                                        Text(game.heading(official: official)).font(.headline).lineLimit(2)
                                        Text(game.subheading(official: official)).font(.subheadline).foregroundStyle(.secondary)
                                        Text(library.status(game)).font(.caption)
                                            .foregroundStyle(library.installed.contains(game.id) ? Color.green : Color.secondary)
                                    }
                                    Spacer(minLength: 0)
                                }
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            if library.canTry(game) {
                                Button("Play") { actions.play(game) }
                                    .buttonStyle(.borderedProminent)
                                    .controlSize(.small)
                            }
                        }
                        .contextMenu { GameMenu(game: game) }
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
    }
}

private struct EmptyShelf: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("No games here yet", systemImage: "gamecontroller").font(.title2.bold())
            Text("Build a game with PadMint and install it on this device, and it shows up here with a check mark. A game installed before PadMint added launch links shows up after you rebuild it.")
                .foregroundStyle(.secondary)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .padding(.horizontal)
    }
}

