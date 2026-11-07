import SwiftUI
import UIKit

/// One game from PadMint's catalog (library.json, made by scripts/sync-catalog.py).
struct Game: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let game: String
    let repo: URL
    /// PadMint's own card art, shown until there is box art or a chosen picture.
    let art: URL
    /// Where box art can be downloaded once the player agrees; nil when there is none.
    let boxArt: URL?
    /// The link a PadMint-built copy answers to (padmint-<game>://); nil for ready-made apps.
    let link: String?
    /// Whether this app can ask iOS if the game is installed (its link is one of the
    /// first 25 in Info.plist); other games are found when the player opens them.
    let checked: Bool

    enum CodingKeys: String, CodingKey {
        case id, name, game, repo, art, link, checked
        case boxArt = "box_art"
    }

    var linkURL: URL? { link.flatMap { URL(string: "\($0)://") } }
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
    private let remote = URL(string: "https://raw.githubusercontent.com/chrissotraidis/padmint-library/main/library.json")!

    init() {
        if let url = Bundle.main.url(forResource: "library", withExtension: "json"),
           let data = try? Data(contentsOf: url),
           let file = try? JSONDecoder().decode(LibraryFile.self, from: data) {
            games = file.games
        }
        checkInstalled()
    }

    /// Installed games, the most recently played first.
    var installedGames: [Game] {
        games.filter { installed.contains($0.id) }.sorted {
            (lastPlayed[$0.id] ?? .distantPast, $1.name) > (lastPlayed[$1.id] ?? .distantPast, $0.name)
        }
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
    }

    /// Whether Play can be tried: installed, or a game this app can't check (it may be there).
    func canTry(_ game: Game) -> Bool {
        installed.contains(game.id) || (!game.checked && game.link != nil)
    }

    func status(_ game: Game) -> String {
        if installed.contains(game.id) { return "Installed" }
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

