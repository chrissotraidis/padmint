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
    @AppStorage("boxMotion") private var boxMotion = true
    @AppStorage("reflections") private var reflections = true
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.gameActions) private var actions
    @Environment(\.horizontalSizeClass) private var sizeClass
    @Environment(\.openURL) private var openURL
    @AppStorage("officialTitles") private var official = false
    let game: Game

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                SpinningBox(game: game, faces: covers.faces(for: game))
                .id("\(reflections)-\(boxMotion)")
                    .frame(height: sizeClass == .regular ? 440 : 330)
                    .overlay(alignment: .bottom) {
                        Text("Drag to turn the box").font(.caption).foregroundStyle(.secondary).padding(.bottom, 4)
                    }
                VStack(spacing: 8) {
                    Text(game.heading(official: official))
                        .font(.largeTitle.bold()).multilineTextAlignment(.center)
                        .accessibilityIdentifier("detail-title")
                    HStack(spacing: 8) {
                        Button { actions.showConsole(game.platform) } label: {
                            Chip(text: game.platform, symbol: "gamecontroller", trailing: "chevron.right")
                        }
                        .buttonStyle(.plain)
                        .accessibilityHint("Shows every \(game.platform) game")
                        .accessibilityIdentifier("console-badge")
                        .controllerFocus("console", corner: 20, inset: 3) { actions.showConsole(game.platform) }
                        Chip(text: official ? game.name : game.title, symbol: official ? "app" : "text.book.closed")
                        if library.installed.contains(game.id) {
                            Chip(text: "Installed", symbol: "checkmark.circle.fill", selected: true)
                        }
                    }
                    Text(library.status(game))
                        .font(.subheadline).foregroundStyle(.secondary)
                }
                if library.canTry(game) {
                    Button { actions.play(game) } label: {
                        Label("Play", systemImage: "play.fill").font(.title3.bold()).frame(maxWidth: 280)
                    }
                    .buttonStyle(PrimaryButtonStyle())
                    .controllerFocus("play", isDefault: true) { actions.play(game) }
                } else {
                    HowToGet(game: game)
                }
                HStack {
                    Button { actions.chooseCover(game) } label: { Label("Choose Cover…", systemImage: "photo") }
                        .controllerFocus("cover") { actions.chooseCover(game) }
                    if covers.hasChosen(game) {
                        Button(role: .destructive) { covers.removeChosen(game) } label: {
                            Label("Remove Chosen Cover", systemImage: "arrow.uturn.backward")
                        }
                        .controllerFocus("remove-cover") { covers.removeChosen(game) }
                    }
                }
                .buttonStyle(SecondaryButtonStyle())
                Link("\(game.name) on GitHub", destination: game.repo).font(.footnote)
                    .controllerFocus("github", corner: 6) { openURL(game.repo) }
                if let source = covers.source(for: game) {
                    Text("Box art from \(source)").font(.footnote).foregroundStyle(.secondary)
                }
                MoreOnConsole(game: game)
                    .padding(.top, 12)
            }
            .padding(24)
            .frame(maxWidth: 680)
            .frame(maxWidth: .infinity)
        }
        .background { Backdrop(game: game) }
        .navigationTitle(game.heading(official: official))
        .navigationBarTitleDisplayMode(.inline)
        .environment(\.focusScope, "detail:\(game.id)")
    }
}

struct HowToGet: View {
    @Environment(\.openURL) private var openURL
    let game: Game

    private var page: URL { game.link == nil ? game.repo : URL(string: "https://github.com/chrissotraidis/padmint")! }

    var body: some View {
        VStack(spacing: 12) {
            Text(game.link == nil
                 ? "\(game.name) is a ready-made app. Install it from its page; PadMint can't see it on this device yet."
                 : "Build \(game.name) with PadMint on your computer and install it on this device. It then shows up here with a check mark.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Link(game.link == nil ? "Open \(game.name)'s page" : "How to get it with PadMint", destination: page)
                .buttonStyle(PrimaryButtonStyle())
                .controllerFocus("how-to-get", isDefault: true) { openURL(page) }
        }
        .frame(maxWidth: 440)
    }
}

/// Other games on the same console, so a game's page leads somewhere.
private struct MoreOnConsole: View {
    @EnvironmentObject private var library: LibraryModel
    @Environment(\.gameActions) private var actions
    @AppStorage("officialTitles") private var official = false
    @AppStorage("showNames") private var showNames = false
    let game: Game

    var body: some View {
        let others = library.sorted(library.games.filter { $0.platform == game.platform && $0.id != game.id },
                                    by: .recent, official: official)
        if !others.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                Text("More on \(game.platform)").font(.title3.bold())
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(alignment: .bottom, spacing: 16) {
                        ForEach(others) { other in
                            Button { actions.open(other) } label: {
                                VStack(alignment: .leading, spacing: 6) {
                                    CoverArt(game: other).frame(width: 120, height: 150, alignment: .bottom)
                                    if showNames {
                                        Text(other.heading(official: official)).font(.caption.weight(.semibold))
                                            .lineLimit(2, reservesSpace: true).frame(width: 120, alignment: .leading)
                                    }
                                }
                            }
                            .buttonStyle(PressableStyle())
                            .accessibilityLabel(other.heading(official: official))
                            .controllerFocus("more-\(other.id)") { actions.open(other) }
                        }
                    }
                    .padding(.vertical, 6)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
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
        .environment(\.focusScope, "get")
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
            Button { choose(.download) } label: { Text("Use Official Covers and Titles").frame(maxWidth: 320) }
                .buttonStyle(PrimaryButtonStyle())
                .controllerFocus("download", isDefault: true) { choose(.download) }
            Button("Keep PadMint Art and Names") { choose(.off) }
                .padding(.vertical, 6).padding(.horizontal, 10)
                .controllerFocus("keep", corner: 10, inset: 0) { choose(.off) }
        }
        .padding(32)
        .frame(maxWidth: 560)
        .interactiveDismissDisabled()
        .environment(\.focusScope, "boxArt")
    }

    private func choose(_ choice: CoverStore.BoxArt) {
        dismiss()
        Task { await covers.setBoxArt(choice, games: library.games) }
    }
}

struct SettingsView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var covers: CoverStore
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @AppStorage("layout") private var layout: Layout = .grid
    @AppStorage("carouselStyle") private var carouselStyle: CarouselStyle = .boxes
    @AppStorage("sort") private var sort: SortOrder = .recent
    @AppStorage("startOn") private var startOn: StartOn = .library
    @AppStorage("officialTitles") private var official = false
    @AppStorage("onlyInstalled") private var onlyInstalled = false
    @AppStorage("coverSize") private var coverSize: CoverSize = .medium
    @AppStorage("showNames") private var showNames = false
    @AppStorage("appearance") private var appearance: Appearance = .dark
    @AppStorage("haptics") private var haptics = true
    @AppStorage("boxMotion") private var boxMotion = true
    @AppStorage("reflections") private var reflections = true
    @AppStorage("backdrop") private var backdrop: BackdropStyle = .glow
    @AppStorage("showReadyMade") private var showReadyMade = true

    private var officialBoxArt: Binding<Bool> {
        Binding(get: { covers.boxArt == .download },
                set: { on in Task { await covers.setBoxArt(on ? .download : .off, games: library.games) } })
    }

    var body: some View {
        NavigationStack {
                Form {
                    Section("Library") {
                        Picker("Layout", selection: $layout) {
                            ForEach(Layout.allCases) { Label($0.label, systemImage: $0.symbol).tag($0) }
                        }
                        .settingFocus("layout", isDefault: true) { layout = layout.next }
                        if layout == .carousel {
                            Picker("Carousel", selection: $carouselStyle) {
                                ForEach(CarouselStyle.allCases) { Text($0.label).tag($0) }
                            }
                            .settingFocus("carousel") { carouselStyle = carouselStyle.next }
                        }
                        Picker("Sort by", selection: $sort) {
                            ForEach(SortOrder.allCases) { Text($0.label).tag($0) }
                        }
                        .settingFocus("sort") { sort = sort.next }
                        Toggle("Installed games only", isOn: $onlyInstalled)
                            .settingFocus("installed") { onlyInstalled.toggle() }
                        Toggle("Show ready-made apps", isOn: $showReadyMade)
                            .settingFocus("ready-made") { showReadyMade.toggle() }
                        Picker("When PadMint opens", selection: $startOn) {
                            ForEach(StartOn.allCases) { Text($0.label).tag($0) }
                        }
                        .settingFocus("start") { startOn = startOn.next }
                    }
                    Section("Look") {
                        Picker("Appearance", selection: $appearance) {
                            ForEach(Appearance.allCases) { Text($0.label).tag($0) }
                        }
                        .settingFocus("appearance") { appearance = appearance.next }
                        Picker("Cover size", selection: $coverSize) {
                            ForEach(CoverSize.allCases) { Text($0.label).tag($0) }
                        }
                        .settingFocus("cover-size") { coverSize = coverSize.next }
                        Toggle("Names under covers", isOn: $showNames)
                            .settingFocus("names") { showNames.toggle() }
                        Picker("Background", selection: $backdrop) {
                            ForEach(BackdropStyle.allCases) { Text($0.label).tag($0) }
                        }
                        .settingFocus("backdrop") { backdrop = backdrop.next }
                        Toggle("Boxes sway", isOn: $boxMotion)
                            .settingFocus("sway") { boxMotion.toggle() }
                        Toggle("Reflections", isOn: $reflections)
                            .settingFocus("reflections") { reflections.toggle() }
                        Toggle("Haptics", isOn: $haptics)
                            .settingFocus("haptics") { haptics.toggle() }
                    }
                    Section {
                        Toggle("Official box art", isOn: officialBoxArt)
                            .settingFocus("box-art") { officialBoxArt.wrappedValue.toggle() }
                        Toggle("Official game titles", isOn: $official)
                            .settingFocus("titles") { official.toggle() }
                    } header: {
                        Text("Covers and titles")
                    } footer: {
                        Text("Official titles put the game's real name first, with its PadMint name underneath. Box art comes from libretro-thumbnails, Steam, GOG and Wikipedia and stays on this device. Long-press any game to choose your own picture.")
                    }
                    Section {
                        LabeledContent("Version", value: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "")
                        LabeledContent("Games", value: "\(library.installed.count) installed of \(library.games.count)")
                        Link("PadMint on GitHub", destination: URL(string: "https://github.com/chrissotraidis/padmint")!)
                            .settingFocus("github") { openURL(URL(string: "https://github.com/chrissotraidis/padmint")!) }
                    } header: {
                        PadMintMark(size: 22).textCase(nil)
                    }
                }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
        }
        .tint(.padMint)
        .environment(\.focusScope, "settings")
    }
}

private extension View {
    /// A settings row a controller can select; A toggles it or picks the next choice.
    func settingFocus(_ id: String, isDefault: Bool = false, action: @escaping () -> Void) -> some View {
        controllerFocus(id, isDefault: isDefault, corner: 10, inset: 7, action: action)
    }
}
