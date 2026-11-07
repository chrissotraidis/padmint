import SwiftUI

/// Long-press menu for a game.
struct GameMenu: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.gameActions) private var actions
    let game: Game

    var body: some View {
        if library.canTry(game) {
            Button { actions.play(game) } label: { Label("Play", systemImage: "play.fill") }
        }
        Button { actions.open(game) } label: { Label("Details", systemImage: "info.circle") }
        Button { actions.chooseCover(game) } label: { Label("Choose Cover…", systemImage: "photo") }
        if covers.hasChosen(game) {
            Button(role: .destructive) { covers.removeChosen(game) } label: {
                Label("Remove Chosen Cover", systemImage: "arrow.uturn.backward")
            }
        }
    }
}

struct GameDetail: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.gameActions) private var actions
    @Environment(\.horizontalSizeClass) private var sizeClass
    @AppStorage("officialTitles") private var official = false
    let game: Game

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                SpinningBox(game: game, image: covers.image(for: game))
                    .frame(height: sizeClass == .regular ? 440 : 330)
                    .overlay(alignment: .bottom) {
                        Text("Drag to turn the box").font(.caption).foregroundStyle(.secondary).padding(.bottom, 4)
                    }
                VStack(spacing: 8) {
                    Text(game.heading(official: official))
                        .font(.largeTitle.bold()).multilineTextAlignment(.center)
                        .accessibilityIdentifier("detail-title")
                    HStack(spacing: 8) {
                        Chip(text: game.platform, symbol: "gamecontroller")
                        Chip(text: official ? game.name : game.title, symbol: official ? "app" : "text.book.closed")
                        if library.installed.contains(game.id) {
                            Chip(text: "Installed", symbol: "checkmark.circle.fill", selected: true)
                        }
                    }
                    Text(library.installed.contains(game.id) ? library.status(game) : library.status(game))
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                if library.canTry(game) {
                    Button { actions.play(game) } label: {
                        Label("Play", systemImage: "play.fill").font(.title3.bold()).frame(maxWidth: 280)
                    }
                    .buttonStyle(PrimaryButtonStyle())
                } else {
                    HowToGet(game: game)
                }
                HStack {
                    Button { actions.chooseCover(game) } label: { Label("Choose Cover…", systemImage: "photo") }
                    if covers.hasChosen(game) {
                        Button(role: .destructive) { covers.removeChosen(game) } label: {
                            Label("Remove Chosen Cover", systemImage: "arrow.uturn.backward")
                        }
                    }
                }
                .buttonStyle(SecondaryButtonStyle())
                Link("\(game.name) on GitHub", destination: game.repo).font(.footnote)
                if let source = covers.source(for: game) {
                    Text("Box art from \(source)").font(.footnote).foregroundStyle(.secondary)
                }
            }
            .padding(24)
            .frame(maxWidth: 680)
            .frame(maxWidth: .infinity)
        }
        .background { Backdrop(game: game) }
        .navigationTitle(game.heading(official: official))
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct HowToGet: View {
    let game: Game

    var body: some View {
        VStack(spacing: 12) {
            Text(game.link == nil
                 ? "\(game.name) is a ready-made app. Install it from its page; PadMint can't see it on this device yet."
                 : "Build \(game.name) with PadMint on your computer and install it on this device. It then shows up here with a check mark.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Link(game.link == nil ? "Open \(game.name)'s page" : "How to get it with PadMint",
                 destination: game.link == nil ? game.repo : URL(string: "https://github.com/chrissotraidis/padmint")!)
                .buttonStyle(PrimaryButtonStyle())
        }
        .frame(maxWidth: 440)
    }
}

struct GetGameSheet: View {
    @AppStorage("officialTitles") private var official = false
    @Environment(\.dismiss) private var dismiss
    let game: Game

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                CoverArt(game: game, corner: 12).frame(maxWidth: 220, maxHeight: 240)
                Text(game.heading(official: official)).font(.title2.bold()).multilineTextAlignment(.center)
                Text(game.subheading(official: official)).foregroundStyle(.secondary)
                HowToGet(game: game)
                Spacer()
            }
            .padding(24)
            .toolbar { Button("Done") { dismiss() } }
        }
    }
}

/// Asked once. Box art and official titles come from outside PadMint, so the player chooses.
struct BoxArtSheet: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 18) {
            PadMintMark(size: 44)
            Text("Use official covers and titles?").font(.title.bold()).multilineTextAlignment(.center)
            Text("PadMint can download box art for all \(library.games.count) games from libretro-thumbnails, Steam, GOG and Wikipedia, keep it on this device, and show each game's official title, such as The Legend of Zelda: The Wind Waker, with its PadMint name underneath. PadMint doesn't include box art itself.\n\nYou can change this in Settings, or choose your own picture for any game.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button {
                dismiss()
                Task { await covers.setBoxArt(.download, games: library.games) }
            } label: { Text("Use Official Covers and Titles").frame(maxWidth: 320) }
                .buttonStyle(PrimaryButtonStyle())
            Button("Keep PadMint Art and Names") {
                dismiss()
                Task { await covers.setBoxArt(.off, games: library.games) }
            }
        }
        .padding(32)
        .frame(maxWidth: 560)
        .interactiveDismissDisabled()
    }
}

struct SettingsView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.dismiss) private var dismiss
    @AppStorage("layout") private var layout: Layout = .shelf
    @AppStorage("carouselStyle") private var carouselStyle: CarouselStyle = .boxes
    @AppStorage("sort") private var sort: SortOrder = .recent
    @AppStorage("startOn") private var startOn: StartOn = .library
    @AppStorage("officialTitles") private var official = false
    @AppStorage("onlyInstalled") private var onlyInstalled = false
    @AppStorage("coverSize") private var coverSize: CoverSize = .medium
    @AppStorage("showNames") private var showNames = true
    @AppStorage("appearance") private var appearance: Appearance = .dark
    @AppStorage("haptics") private var haptics = true

    var body: some View {
        NavigationStack {
            Form {
                Section("Library") {
                    Picker("Layout", selection: $layout) {
                        ForEach(Layout.allCases) { Label($0.label, systemImage: $0.symbol).tag($0) }
                    }
                    Picker("Carousel", selection: $carouselStyle) {
                        ForEach(CarouselStyle.allCases) { Text($0.label).tag($0) }
                    }
                    Picker("Sort by", selection: $sort) {
                        ForEach(SortOrder.allCases) { Text($0.label).tag($0) }
                    }
                    Toggle("Installed games only", isOn: $onlyInstalled)
                    Picker("When PadMint opens", selection: $startOn) {
                        ForEach(StartOn.allCases) { Text($0.label).tag($0) }
                    }
                }
                Section("Look") {
                    Picker("Appearance", selection: $appearance) {
                        ForEach(Appearance.allCases) { Text($0.label).tag($0) }
                    }
                    Picker("Cover size", selection: $coverSize) {
                        ForEach(CoverSize.allCases) { Text($0.label).tag($0) }
                    }
                    Toggle("Names under covers", isOn: $showNames)
                    Toggle("Haptics", isOn: $haptics)
                }
                Section {
                    Toggle("Official box art", isOn: Binding(
                        get: { covers.boxArt == .download },
                        set: { on in Task { await covers.setBoxArt(on ? .download : .off, games: library.games) } }))
                    Toggle("Official game titles", isOn: $official)
                } header: {
                    Text("Covers and titles")
                } footer: {
                    Text("Official titles put the game's real name first, with its PadMint name underneath. Box art comes from libretro-thumbnails, Steam, GOG and Wikipedia and stays on this device. Long-press any game to choose your own picture.")
                }
                Section {
                    LabeledContent("Version", value: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "")
                    LabeledContent("Games", value: "\(library.installed.count) installed of \(library.games.count)")
                    Link("PadMint on GitHub", destination: URL(string: "https://github.com/chrissotraidis/padmint")!)
                } header: {
                    PadMintMark(size: 22).textCase(nil)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
        }
        .tint(.padMint)
    }
}

