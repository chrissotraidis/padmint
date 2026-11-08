import ImageIO
import SwiftUI
import UIKit

/// Covers kept on this device: a picture the player chose, box art downloaded after the
/// player agreed, and PadMint's own card art. Nothing is uploaded, and the repository
/// holds no game art.
@MainActor
final class CoverStore: ObservableObject {
    enum BoxArt: String { case ask, download, off }

    @Published var boxArt: BoxArt {
        didSet { UserDefaults.standard.set(boxArt.rawValue, forKey: "boxArt") }
    }
    @Published private(set) var downloading = false
    private var images: [String: UIImage] = [:]
    /// Files known not to exist, so a redraw doesn't ask the disk again.
    private var missing: Set<String> = []
    private var chosen: Set<String> = []
    private var glows: [String: UIImage] = [:]
    private let folder: URL

    init() {
        boxArt = BoxArt(rawValue: UserDefaults.standard.string(forKey: "boxArt") ?? "") ?? .ask
        folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Covers", isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let files = (try? FileManager.default.contentsOfDirectory(atPath: folder.path)) ?? []
        chosen = Set(files.filter { $0.hasPrefix("chosen-") }.map { String($0.dropFirst("chosen-".count)) })
        // Official titles come with official covers. Earlier versions kept them apart, so
        // anyone who already chose box art gets the titles too, once.
        if boxArt == .download, UserDefaults.standard.object(forKey: "officialTitles") == nil {
            UserDefaults.standard.set(true, forKey: "officialTitles")
        }
    }

    private func file(_ kind: String, _ game: Game) -> URL { folder.appendingPathComponent("\(kind)-\(game.id)") }

    private func load(_ kind: String, _ game: Game) -> UIImage? {
        let key = kind + "-" + game.id
        if let image = images[key] { return image }
        if missing.contains(key) { return nil }
        guard let image = Self.decode(file(kind, game)) else {
            missing.insert(key)
            return nil
        }
        images[key] = image
        return image
    }

    /// Reads a cover already decoded and no larger than needed, so drawing it later
    /// doesn't decode it on the main thread mid-scroll.
    nonisolated static func decode(_ url: URL, maxPixels: Int = 1200) -> UIImage? {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceShouldCacheImmediately: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixels,
        ]
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else { return nil }
        return UIImage(cgImage: image)
    }

    /// Decodes every game's cover in the background, then redraws once.
    func warm(_ games: [Game]) async {
        let wanted = games.flatMap { game in ["chosen", "boxart", "card"].map { ($0 + "-" + game.id, file($0, game)) } }
            .filter { images[$0.0] == nil && !missing.contains($0.0) }
        let decoded = await Task.detached(priority: .userInitiated) {
            wanted.map { key, url in (key, FileManager.default.fileExists(atPath: url.path) ? Self.decode(url) : nil) }
        }.value
        for (key, image) in decoded {
            if let image { images[key] = image } else { missing.insert(key) }
        }
        objectWillChange.send()
    }

    /// A 24-pixel copy of the cover: scaled up behind the screen it is already a soft glow,
    /// so the background needs only a light blur instead of re-blurring a full cover.
    func glow(for game: Game) -> UIImage? {
        guard let image = image(for: game) else { return nil }
        let key = game.id + "-\(ObjectIdentifier(image).hashValue)"
        if let glow = glows[key] { return glow }
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let glow = UIGraphicsImageRenderer(size: CGSize(width: 24, height: 24), format: format)
            .image { _ in image.draw(in: CGRect(x: 0, y: 0, width: 24, height: 24)) }
        glows[key] = glow
        return glow
    }

    /// The chosen picture, then box art (when allowed), then PadMint's card art.
    func image(for game: Game) -> UIImage? {
        load("chosen", game) ?? (boxArt == .download ? load("boxart", game) : nil) ?? load("card", game)
    }

    /// Width over height of the cover shown for a game.
    func aspect(for game: Game) -> CGFloat {
        guard let size = image(for: game)?.size, size.height > 0 else { return 0.71 }
        return size.width / size.height
    }

    func hasChosen(_ game: Game) -> Bool { chosen.contains(game.id) }

    /// Where the shown cover comes from, for the credit on a game's page.
    func source(for game: Game) -> String? {
        guard !hasChosen(game), boxArt == .download, load("boxart", game) != nil, let host = game.boxArt?.host else { return nil }
        if host.contains("libretro") { return "libretro-thumbnails" }
        if host.contains("steam") { return "Steam" }
        if host.contains("gog") { return "GOG" }
        if host.contains("wiki") { return "Wikipedia" }
        return host
    }

    func choose(_ data: Data, for game: Game) {
        guard let jpeg = UIImage(data: data)?.jpegData(compressionQuality: 0.9) else { return }
        try? jpeg.write(to: file("chosen", game), options: .atomic)
        chosen.insert(game.id)
        changed("chosen", game)
    }

    func removeChosen(_ game: Game) {
        try? FileManager.default.removeItem(at: file("chosen", game))
        chosen.remove(game.id)
        changed("chosen", game)
    }

    func setBoxArt(_ choice: BoxArt, games: [Game]) async {
        boxArt = choice
        // The titles follow the covers; either can still be changed on its own in Settings.
        UserDefaults.standard.set(choice == .download, forKey: "officialTitles")
        objectWillChange.send()
        await fetch(games)
    }

    /// Downloads what the device doesn't have yet: card art always (it's PadMint's own),
    /// box art only once the player agreed. Missing or broken files are skipped.
    func fetch(_ games: [Game]) async {
        guard !downloading else { return }
        downloading = true
        defer { downloading = false }
        var wanted: [(String, Game, URL)] = games.map { ("card", $0, $0.art) }
        if boxArt == .download { wanted += games.compactMap { game in game.boxArt.map { ("boxart", game, $0) } } }
        wanted = wanted.filter { !FileManager.default.fileExists(atPath: file($0.0, $0.1).path) }
        await withTaskGroup(of: (String, Game, Data?).self) { group in
            for (kind, game, url) in wanted {
                group.addTask {
                    var request = URLRequest(url: url)
                    request.setValue("PadMintLibrary", forHTTPHeaderField: "User-Agent")
                    guard let (data, response) = try? await URLSession.shared.data(for: request),
                          (response as? HTTPURLResponse)?.statusCode == 200 else { return (kind, game, nil) }
                    return (kind, game, data)
                }
            }
            // Redraw every eight covers instead of after each one.
            var pending = 0
            for await (kind, game, data) in group {
                guard let data, UIImage(data: data) != nil else { continue }
                try? data.write(to: file(kind, game), options: .atomic)
                images[kind + "-" + game.id] = nil
                missing.remove(kind + "-" + game.id)
                pending += 1
                if pending >= 8 {
                    pending = 0
                    objectWillChange.send()
                }
            }
            objectWillChange.send()
        }
    }

    private func changed(_ kind: String, _ game: Game) {
        images[kind + "-" + game.id] = nil
        missing.remove(kind + "-" + game.id)
        objectWillChange.send()
    }
}

/// A game's cover at its own shape (wide N64 boxes, square PlayStation cases, tall
/// GameCube boxes), fitted into the space it's given. Installed games get a check mark.
struct CoverArt: View {
    @EnvironmentObject private var covers: CoverStore
    @EnvironmentObject private var library: LibraryModel
    let game: Game
    var corner: CGFloat = 8
    var badge = true

    var body: some View {
        picture
            .clipShape(RoundedRectangle(cornerRadius: corner, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: corner, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5)
            }
            .overlay(alignment: .topTrailing) {
                if badge, library.installed.contains(game.id) {
                    Image(systemName: "checkmark.circle.fill")
                        .symbolRenderingMode(.palette)
                        .foregroundStyle(.white, .green)
                        .font(.title2)
                        .shadow(color: .black.opacity(0.4), radius: 3)
                        .padding(6)
                        .accessibilityLabel("Installed")
                }
            }
            .shadow(color: .black.opacity(0.32), radius: 7, y: 5)
    }

    @ViewBuilder private var picture: some View {
        if let image = covers.image(for: game) {
            Image(uiImage: image).resizable().interpolation(.high).scaledToFit()
        } else {
            LinearGradient(colors: [.mint, .teal], startPoint: .topLeading, endPoint: .bottomTrailing)
                .aspectRatio(0.71, contentMode: .fit)
                .overlay { Text(game.name).font(.headline).foregroundStyle(.white).padding(8) }
        }
    }
}

/// A cover standing on the bottom of a fixed-height slot, so a row of mixed shapes lines up.
struct CoverSlot: View {
    let game: Game
    let height: CGFloat

    var body: some View {
        CoverArt(game: game)
            .frame(maxWidth: .infinity, maxHeight: height, alignment: .bottom)
            .frame(height: height, alignment: .bottom)
    }
}

/// The current game's art, blurred behind everything.
struct Backdrop: View {
    @EnvironmentObject private var covers: CoverStore
    @AppStorage("backdrop") private var style: BackdropStyle = .glow
    let game: Game?

    var body: some View {
        Color.clear
            .overlay {
                if style == .glow, let game, let image = covers.glow(for: game) {
                    Image(uiImage: image).resizable().interpolation(.medium).scaledToFill()
                        .blur(radius: 18)
                        .opacity(0.6)
                        .id(game.id)
                        .transition(.opacity)
                }
            }
            .clipped()
            .background(Color(.systemBackground))
            .ignoresSafeArea()
            .animation(.easeInOut(duration: 0.45), value: game?.id)
    }
}

enum BackdropStyle: String, CaseIterable, Identifiable {
    case glow, plain
    var id: Self { self }
    var label: String { self == .glow ? "Cover colours" : "Plain" }
}

/// Covers shrink a little under the finger.
struct PressableStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.95 : 1)
            .animation(.spring(response: 0.25, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

