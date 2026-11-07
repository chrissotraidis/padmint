import SwiftUI
import UIKit

/// Covers kept on this device: a picture the player chose, or box art downloaded after
/// the player agreed. Nothing here is uploaded, and the repository holds no game art.
@MainActor
final class CoverStore: ObservableObject {
    enum BoxArt: String { case ask, download, off }

    @Published var boxArt: BoxArt {
        didSet { UserDefaults.standard.set(boxArt.rawValue, forKey: "boxArt") }
    }
    @Published private(set) var downloading = false
    private var images: [String: UIImage] = [:]
    private let folder: URL

    init() {
        boxArt = BoxArt(rawValue: UserDefaults.standard.string(forKey: "boxArt") ?? "") ?? .ask
        folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Covers", isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
    }

    private func chosenFile(_ game: Game) -> URL { folder.appendingPathComponent("chosen-\(game.id).jpg") }
    private func boxArtFile(_ game: Game) -> URL { folder.appendingPathComponent("boxart-\(game.id).png") }

    /// The chosen picture, then downloaded box art; nil means PadMint's card art.
    func image(for game: Game) -> UIImage? {
        if let image = images[game.id] { return image }
        let image = UIImage(contentsOfFile: chosenFile(game).path)
            ?? (boxArt == .download ? UIImage(contentsOfFile: boxArtFile(game).path) : nil)
        if let image { images[game.id] = image }
        return image
    }

    func hasChosen(_ game: Game) -> Bool { FileManager.default.fileExists(atPath: chosenFile(game).path) }

    func choose(_ data: Data, for game: Game) {
        guard let jpeg = UIImage(data: data)?.jpegData(compressionQuality: 0.9) else { return }
        try? jpeg.write(to: chosenFile(game), options: .atomic)
        changed(game)
    }

    func removeChosen(_ game: Game) {
        try? FileManager.default.removeItem(at: chosenFile(game))
        changed(game)
    }

    func setBoxArt(_ choice: BoxArt, games: [Game]) async {
        boxArt = choice
        images.removeAll()
        objectWillChange.send()
        if choice == .download { await download(games) }
    }

    /// Fetches box art the device doesn't have yet. Missing or broken files are skipped.
    func download(_ games: [Game]) async {
        guard boxArt == .download, !downloading else { return }
        downloading = true
        defer { downloading = false }
        for game in games {
            guard let url = game.boxArt, !FileManager.default.fileExists(atPath: boxArtFile(game).path),
                  let (data, response) = try? await URLSession.shared.data(from: url),
                  (response as? HTTPURLResponse)?.statusCode == 200, UIImage(data: data) != nil else { continue }
            try? data.write(to: boxArtFile(game), options: .atomic)
            changed(game)
        }
    }

    private func changed(_ game: Game) {
        images[game.id] = nil
        objectWillChange.send()
    }
}

/// A game's cover in a 3:4 frame. Pictures of another shape (square card art, wide N64
/// boxes) sit whole on a blurred copy of themselves instead of being cropped.
struct CoverView: View {
    @EnvironmentObject private var covers: CoverStore
    let game: Game
    var corner: CGFloat = 16

    var body: some View {
        Color.clear
            .aspectRatio(3 / 4, contentMode: .fit)
            .overlay { picture }
            .clipShape(RoundedRectangle(cornerRadius: corner, style: .continuous))
            .accessibilityLabel(game.name)
    }

    @ViewBuilder private var picture: some View {
        if let image = covers.image(for: game) {
            let ratio = image.size.width / max(image.size.height, 1)
            if abs(ratio - 0.75) < 0.08 {
                Image(uiImage: image).resizable().scaledToFill()
            } else {
                Backed(image: Image(uiImage: image))
            }
        } else {
            AsyncImage(url: game.art) { image in
                Backed(image: image)
            } placeholder: {
                ZStack {
                    LinearGradient(colors: [.mint, .teal], startPoint: .topLeading, endPoint: .bottomTrailing)
                    Text(game.name).font(.headline).foregroundStyle(.white).padding()
                }
            }
        }
    }
}

private struct Backed: View {
    let image: Image

    var body: some View {
        ZStack {
            image.resizable().scaledToFill().blur(radius: 24).opacity(0.85)
            image.resizable().scaledToFit()
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                .shadow(color: .black.opacity(0.3), radius: 8, y: 4)
                .padding(12)
        }
    }
}

