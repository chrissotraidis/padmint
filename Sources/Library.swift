import SwiftUI
import UIKit

/// One game from PadMint's catalog (library.json, made by scripts/sync-catalog.py).
struct Game: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let game: String
    let repo: URL
    let art: URL
    /// The link a PadMint-built copy answers to (padmint-<game>://); nil for ready-made apps.
    let link: String?
    /// Whether this app can ask iOS if the game is installed (its link is one of the
    /// first 25 in Info.plist); other games are found when the player opens them.
    let checked: Bool

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

    var installedGames: [Game] { games.filter { installed.contains($0.id) } }

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

    /// Opens the game; false when no app answers to its link.
    func play(_ game: Game) async -> Bool {
        guard let url = game.linkURL else { return false }
        let success = await UIApplication.shared.open(url)
        if !game.checked {
            if success { opened.insert(game.id) } else { opened.remove(game.id) }
            checkInstalled()
        }
        return success
    }
}
