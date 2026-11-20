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
    // Every cover is decoded once, in the background, at the size it's shown at. The library
    // keeps them all: downsampled, the 41 games' fronts, backs and spines take about a third of
    // the memory they did at 1200 px, and the carousel holds every box's textures anyway, so an
    // evicting cache would only bring back the re-decoding this avoids.
    private var images: [String: UIImage] = [:]
    /// Colours and the backdrop glow of a front, worked out with its decode.
    private var palettes: [String: Palette] = [:]
    /// Files known not to exist, so a redraw doesn't ask the disk again.
    private var missing: Set<String> = []
    private var chosen: Set<String> = []
    /// Cover files on this device, listed once at launch and kept up to date.
    private var onDisk: Set<String> = []
    private let folder: URL
    /// Covers waiting to be decoded, the next first, and how many decodes are running.
    private var queue: [(key: String, url: URL)] = []
    private var queued: Set<String> = []
    private var running = 0
    private var publishing = false

    struct Palette {
        let average: UIColor
        let accent: UIColor?
        let glow: UIImage
    }

    init() {
        boxArt = BoxArt(rawValue: UserDefaults.standard.string(forKey: "boxArt") ?? "") ?? .ask
        folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Covers", isDirectory: true)
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let files = (try? FileManager.default.contentsOfDirectory(atPath: folder.path)) ?? []
        onDisk = Set(files)
        chosen = Set(files.filter { $0.hasPrefix("chosen-") }.map { String($0.dropFirst("chosen-".count)) })
        // Official titles come with official covers. Earlier versions kept them apart, so
        // anyone who already chose box art gets the titles too, once.
        if boxArt == .download, UserDefaults.standard.object(forKey: "officialTitles") == nil {
            UserDefaults.standard.set(true, forKey: "officialTitles")
        }
    }

    private func file(_ kind: String, _ game: Game) -> URL { folder.appendingPathComponent("\(kind)-\(game.id)") }

    /// A decoded cover, or nil while it's being decoded (in the background, never here) or
    /// when there is none.
    private func load(_ kind: String, _ game: Game) -> UIImage? {
        let key = kind + "-" + game.id
        if let image = images[key] { return image }
        if !missing.contains(key) { request(key, file(kind, game), first: false) }
        return nil
    }

    /// The largest side a kind of cover is shown at: a front fills most of a 13-inch iPad's
    /// carousel (about 950 px), a back or a card much less, a spine is a narrow strip.
    nonisolated static func maxPixels(_ key: String) -> Int {
        switch key.prefix(while: { $0 != "-" }) {
        case "chosen", "boxart": 1000
        case "spine": 768
        default: 512
        }
    }

    private func request(_ key: String, _ url: URL, first: Bool) {
        guard onDisk.contains(key) else {
            missing.insert(key)
            return
        }
        if queued.contains(key) {
            guard first, let index = queue.firstIndex(where: { $0.key == key }) else { return }
            queue.insert(queue.remove(at: index), at: 0)
            return
        }
        queued.insert(key)
        if first { queue.insert((key, url), at: 0) } else { queue.append((key, url)) }
        pump()
    }

    /// Decodes up to three covers at a time off the main thread.
    private func pump() {
        while running < 3, !queue.isEmpty {
            let (key, url) = queue.removeFirst()
            running += 1
            Task.detached(priority: .userInitiated) { [weak self] in
                let image = FileManager.default.fileExists(atPath: url.path) ? Self.decode(url, maxPixels: Self.maxPixels(key)) : nil
                let palette = Self.wantsPalette(key) ? image.map(Self.palette) : nil
                await self?.finish(key, image, palette)
            }
        }
    }

    private func finish(_ key: String, _ image: UIImage?, _ palette: Palette?) {
        running -= 1
        queued.remove(key)
        if let image { images[key] = image } else { missing.insert(key) }
        if let palette { palettes[key] = palette }
        pump()
        // One redraw for a batch of covers, not one per cover.
        guard !publishing else { return }
        publishing = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { [weak self] in
            self?.publishing = false
            self?.objectWillChange.send()
        }
    }

    nonisolated private static func wantsPalette(_ key: String) -> Bool {
        ["chosen", "boxart", "card"].contains(String(key.prefix(while: { $0 != "-" })))
    }

    /// A front's average and strongest colours, and a 24-pixel copy for the backdrop: scaled
    /// up behind the screen it's already a soft glow, so it needs only a light blur.
    nonisolated private static func palette(_ image: UIImage) -> Palette {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let glow = UIGraphicsImageRenderer(size: CGSize(width: 24, height: 24), format: format)
            .image { _ in image.draw(in: CGRect(x: 0, y: 0, width: 24, height: 24)) }
        let average = glow.averageColor ?? UIColor(red: 0.13, green: 0.74, blue: 0.48, alpha: 1)
        return Palette(average: average, accent: glow.vividColor, glow: glow)
    }

    /// Covers to decode before the rest: the carousel's front box and its neighbours.
    func prefetch(_ games: [Game]) {
        for game in games.reversed() {
            for kind in ["spine", "back", "card", "boxart", "chosen"] {
                let key = kind + "-" + game.id
                if images[key] == nil, !missing.contains(key) { request(key, file(kind, game), first: true) }
            }
        }
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

    /// Queues every game's covers, a game at a time (front, back, spine together, so a box is
    /// fitted once), so they're ready before they're shown.
    func warm(_ games: [Game]) {
        for game in games {
            for kind in ["chosen", "boxart", "card", "back", "spine"] where images[kind + "-" + game.id] == nil {
                let key = kind + "-" + game.id
                if !missing.contains(key) { request(key, file(kind, game), first: false) }
            }
        }
    }

    /// The backdrop's glow for the cover shown (worked out with its decode).
    func glow(for game: Game) -> UIImage? { front(game).flatMap { palettes[$0] }?.glow }

    /// The chosen picture, then box art (when allowed), then PadMint's card art.
    func image(for game: Game) -> UIImage? { front(game).flatMap { images[$0] } }

    /// The key of the front shown, once it's decoded. While the chosen picture or the box art
    /// is still decoding, nothing is shown (not the card art, which would flash first).
    private func front(_ game: Game) -> String? {
        let order = ["chosen"] + (boxArt == .download ? ["boxart"] : []) + ["card"]
        for kind in order {
            let key = kind + "-" + game.id
            if load(kind, game) != nil { return key }
            if !missing.contains(key) { return nil }
        }
        return nil
    }

    /// Every printed face of the box. The back and spine come with official box art, and
    /// only when the front is the official one too.
    func faces(for game: Game) -> BoxFaces {
        let key = front(game)
        let front = key.flatMap { images[$0] }
        let palette = key.flatMap { palettes[$0] }
        let complete = ["chosen", "boxart", "card", "back", "spine"].allSatisfy { !queued.contains($0 + "-" + game.id) }
        guard boxArt == .download, !hasChosen(game), images["boxart-" + game.id] != nil else {
            return BoxFaces(front: front, average: palette?.average, accent: palette?.accent, complete: complete)
        }
        return BoxFaces(front: front, back: load("back", game), spine: load("spine", game),
                        average: palette?.average, accent: palette?.accent, complete: complete)
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
        let front = host.contains("libretro") ? "libretro-thumbnails"
            : host.contains("steam") ? "Steam" : host.contains("gog") ? "GOG" : host.contains("wiki") ? "Wikipedia"
            : host.contains("launchbox") ? "LaunchBox" : host
        let faces = faces(for: game)
        return front != "LaunchBox" && (faces.back != nil || faces.spine != nil) ? "\(front), back and spine from LaunchBox" : front
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
        if boxArt == .download {
            for (kind, url) in [("boxart", \Game.boxArt), ("back", \Game.boxBack), ("spine", \Game.boxSpine)] {
                wanted += games.compactMap { game in game[keyPath: url].map { (kind, game, $0) } }
            }
        }
        wanted = wanted.filter { !FileManager.default.fileExists(atPath: file($0.0, $0.1).path) }
        await withTaskGroup(of: (String, Game, Data?).self) { group in
            for (kind, game, url) in wanted {
                group.addTask {
                    // libretro's server is sometimes too slow to answer; its GitHub copy is the fallback.
                    for source in [url, Self.libretroMirror(url)].compactMap({ $0 }) {
                        // libretro gets 20 s before its GitHub copy is tried; LaunchBox's big scans get longer.
                        var request = URLRequest(url: source, timeoutInterval: source.host == "thumbnails.libretro.com" ? 20 : 60)
                        request.setValue("PadMintLibrary", forHTTPHeaderField: "User-Agent")
                        if let (data, response) = try? await URLSession.shared.data(for: request),
                           (response as? HTTPURLResponse)?.statusCode == 200, UIImage(data: data) != nil {
                            return (kind, game, data)
                        }
                    }
                    return (kind, game, nil)
                }
            }
            // Redraw every eight covers instead of after each one.
            var pending = 0
            for await (kind, game, data) in group {
                guard let data, UIImage(data: data) != nil else { continue }
                try? data.write(to: file(kind, game), options: .atomic)
                forget(kind + "-" + game.id)
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
        forget(kind + "-" + game.id)
        objectWillChange.send()
    }

    /// A file changed: decode it again next time it's asked for.
    private func forget(_ key: String) {
        images[key] = nil
        palettes[key] = nil
        missing.remove(key)
        if FileManager.default.fileExists(atPath: folder.appendingPathComponent(key).path) { onDisk.insert(key) } else { onDisk.remove(key) }
    }

    /// The same libretro thumbnail on GitHub, where libretro keeps one repository per system:
    /// thumbnails.libretro.com/Nintendo - Nintendo 64/Named_Boxarts/X.png becomes
    /// raw.githubusercontent.com/libretro-thumbnails/Nintendo_-_Nintendo_64/master/Named_Boxarts/X.png
    nonisolated static func libretroMirror(_ url: URL) -> URL? {
        let parts = url.pathComponents.filter { $0 != "/" }
        guard url.host == "thumbnails.libretro.com", parts.count == 3 else { return nil }
        var mirror = URLComponents()
        mirror.scheme = "https"
        mirror.host = "raw.githubusercontent.com"
        mirror.path = "/libretro-thumbnails/\(parts[0].replacingOccurrences(of: " ", with: "_"))/master/\(parts[1])/\(parts[2])"
        return mirror.url
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

