import SwiftUI
import UIKit

/// One game from PadMint's catalog (library.json, made by scripts/sync-catalog.py).
struct Game: Codable, Identifiable, Hashable {
    let id: String
    /// The port's own name, such as BlueWake.
    let name: String
    /// The official title, such as The Legend of Zelda: The Wind Waker.
    let title: String
    let platform: String
    let game: String
    let repo: URL
    /// PadMint's own card art, shown until there is box art or a chosen picture.
    let art: URL
    /// Where box art can be downloaded once the player agrees.
    let boxArt: URL?
    /// The link a PadMint-built copy answers to (padmint-<game>://); nil for ready-made apps.
    let link: String?
    /// Whether this app can ask iOS if the game is installed (its link is one of the
    /// first 25 in Info.plist); other games are found when the player opens them.
    let checked: Bool

    enum CodingKeys: String, CodingKey {
        case id, name, title, platform, game, repo, art, link, checked
        case boxArt = "box_art"
    }

    var linkURL: URL? { link.flatMap { URL(string: "\($0)://") } }

    /// The big name: the official title once the player turns titles on, else the port's name.
    func heading(official: Bool) -> String { official ? title : name }
    /// The small line underneath: the port's name, or the console before titles are on.
    func subheading(official: Bool) -> String { official ? name : platform }
}

enum Layout: String, CaseIterable, Identifiable {
    case shelf, grid, carousel, list
    var id: Self { self }
    var label: String {
        switch self {
        case .shelf: "Shelf"
        case .grid: "Grid"
        case .carousel: "Carousel"
        case .list: "List"
        }
    }
    var symbol: String {
        switch self {
        case .shelf: "rectangle.stack"
        case .grid: "square.grid.3x3"
        case .carousel: "rectangle.portrait.on.rectangle.portrait.angled"
        case .list: "list.bullet"
        }
    }
}

enum SortOrder: String, CaseIterable, Identifiable {
    case recent, title, console
    var id: Self { self }
    var label: String {
        switch self {
        case .recent: "Recently played"
        case .title: "Title"
        case .console: "Console"
        }
    }
}

enum StartOn: String, CaseIterable, Identifiable {
    case library, lastPlayed
    var id: Self { self }
    var label: String { self == .library ? "Library" : "Last game played" }
}

private struct LibraryFile: Codable {
    let games: [Game]
}

@MainActor
final class LibraryModel: ObservableObject {
    @Published private(set) var games: [Game] = []
    @Published private(set) var installed: Set<String> = []
    /// Unchecked games that opened from here before.
    @Published private var opened = Set(UserDefaults.standard.stringArray(forKey: "opened") ?? []) {
        didSet { UserDefaults.standard.set(Array(opened), forKey: "opened") }
    }
    /// When each game was last opened from the library.
    @Published private(set) var lastPlayed: [String: Date] =
        (UserDefaults.standard.dictionary(forKey: "lastPlayed") as? [String: Date]) ?? [:] {
        didSet { UserDefaults.standard.set(lastPlayed, forKey: "lastPlayed") }
    }

    /// The newest list; the copy inside the app is used offline.
    private let remote = URL(string: "https://raw.githubusercontent.com/chrissotraidis/padmint/main/ios/library.json")!
    static let consoles = ["Nintendo 64", "GameCube", "Wii", "PlayStation", "PlayStation 2", "Xbox", "PC"]

    init() {
        if let url = Bundle.main.url(forResource: "library", withExtension: "json"),
           let data = try? Data(contentsOf: url),
           let file = try? JSONDecoder().decode(LibraryFile.self, from: data) {
            games = file.games
        }
        #if DEBUG
        // Demo recordings in the simulator: -demoLastPlayed <id> puts a game in the shelf banner.
        if let id = UserDefaults.standard.string(forKey: "demoLastPlayed") { lastPlayed[id] = Date().addingTimeInterval(-3600) }
        #endif
        checkInstalled()
    }

    /// Installed games, the most recently played first.
    var installedGames: [Game] { sorted(games.filter { installed.contains($0.id) }, by: .recent, official: false) }

    var lastPlayedGame: Game? {
        games.filter { lastPlayed[$0.id] != nil }.max { lastPlayed[$0.id]! < lastPlayed[$1.id]! }
    }

    func sorted(_ list: [Game], by order: SortOrder, official: Bool) -> [Game] {
        let byName = list.sorted {
            $0.heading(official: official).localizedStandardCompare($1.heading(official: official)) == .orderedAscending
        }
        switch order {
        case .title:
            return byName
        case .recent:
            // Played games first (newest first), then installed ones, then the rest by name.
            return byName.enumerated().sorted { a, b in
                let ka = (lastPlayed[a.element.id] ?? .distantPast, installed.contains(a.element.id) ? 1 : 0)
                let kb = (lastPlayed[b.element.id] ?? .distantPast, installed.contains(b.element.id) ? 1 : 0)
                if ka.0 != kb.0 { return ka.0 > kb.0 }
                if ka.1 != kb.1 { return ka.1 > kb.1 }
                return a.offset < b.offset
            }.map(\.element)
        case .console:
            return byName.sorted { (Self.consoles.firstIndex(of: $0.platform) ?? 99) < (Self.consoles.firstIndex(of: $1.platform) ?? 99) }
        }
    }

    /// Sections for a sorted list: one per console when sorting by console.
    func sections(_ list: [Game], by order: SortOrder) -> [(title: String?, games: [Game])] {
        guard order == .console else { return [(nil, list)] }
        var result: [(title: String?, games: [Game])] = []
        for game in list {
            if result.last?.title == game.platform { result[result.count - 1].games.append(game) }
            else { result.append((game.platform, [game])) }
        }
        return result
    }

    func refresh() async {
        checkInstalled()
        guard let (data, response) = try? await URLSession.shared.data(from: remote),
              (response as? HTTPURLResponse)?.statusCode == 200,
              let file = try? JSONDecoder().decode(LibraryFile.self, from: data),
              !file.games.isEmpty else { return }
        games = file.games
        checkInstalled()
    }

    /// iOS answers only for links this app declares in Info.plist (LSApplicationQueriesSchemes).
    func checkInstalled() {
        installed = Set(games.compactMap { game in
            guard let url = game.linkURL else { return nil }
            if game.checked { return UIApplication.shared.canOpenURL(url) ? game.id : nil }
            return opened.contains(game.id) ? game.id : nil
        })
        #if DEBUG
        // Demo recordings in the simulator, where no game is installed: -demoInstalled id,id,...
        if let demo = UserDefaults.standard.string(forKey: "demoInstalled") {
            installed = Set(demo.split(separator: ",").map(String.init))
        }
        #endif
    }

    /// Whether Play can be tried: installed, or a game this app can't check (it may be there).
    func canTry(_ game: Game) -> Bool {
        installed.contains(game.id) || (!game.checked && game.link != nil)
    }

    func status(_ game: Game) -> String {
        if installed.contains(game.id) { return lastPlayedText(lastPlayed[game.id]) }
        if game.link == nil { return "Ready-made app" }
        return game.checked ? "Not installed" : "Tap Play to check"
    }

    /// Opens the game; false when no app answers to its link.
    func play(_ game: Game) async -> Bool {
        guard let url = game.linkURL else { return false }
        let success = await UIApplication.shared.open(url)
        if success { lastPlayed[game.id] = Date() }
        if !game.checked {
            if success { opened.insert(game.id) } else { opened.remove(game.id) }
            checkInstalled()
        }
        return success
    }
}

func lastPlayedText(_ date: Date?) -> String {
    guard let date else { return "Installed" }
    return "Played \(date.formatted(.relative(presentation: .named)))"
}

/// What a game view can ask the library screen to do.
struct GameActions {
    var play: (Game) -> Void = { _ in }
    var open: (Game) -> Void = { _ in }
    var chooseCover: (Game) -> Void = { _ in }
}

private struct GameActionsKey: EnvironmentKey {
    static let defaultValue = GameActions()
}

extension EnvironmentValues {
    var gameActions: GameActions {
        get { self[GameActionsKey.self] }
        set { self[GameActionsKey.self] = newValue }
    }
}

