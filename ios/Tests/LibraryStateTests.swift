import XCTest
@testable import PadMint

/// The library's own state: saved layouts, the console badge, and the controller's selection.
final class LibraryStateTests: XCTestCase {
    private func game(_ id: String, _ platform: String, link: String? = "padmint-x") -> Game {
        let url = URL(string: "https://example.com/\(id)")!
        return Game(id: id, name: id, title: id.uppercased(), platform: platform, game: id, repo: url, art: url,
                    boxArt: nil, boxBack: nil, boxSpine: nil, link: link)
    }

    func testSavedLayoutsOpenAKnownLayout() {
        XCTAssertEqual(Layout(rawValue: "shelf"), .grid, "0.6.5's Shelf became Grid")
        XCTAssertEqual(Layout(rawValue: "grid"), .grid)
        XCTAssertEqual(Layout(rawValue: "carousel"), .carousel)
        XCTAssertEqual(Layout(rawValue: "list"), .list)
        XCTAssertEqual(Layout(rawValue: "spiral"), .grid, "a value from another version")
        XCTAssertEqual(Layout(rawValue: ""), .grid)
        for layout in Layout.allCases { XCTAssertEqual(Layout(rawValue: layout.rawValue), layout) }
    }

    func testSavedLayoutReadsThroughUserDefaults() throws {
        let defaults = try XCTUnwrap(UserDefaults(suiteName: "LibraryStateTests"))
        defer { defaults.removePersistentDomain(forName: "LibraryStateTests") }
        defaults.set("shelf", forKey: "layout")
        XCTAssertEqual(defaults.string(forKey: "layout").map(Layout.init(rawValue:)), .grid)
    }

    func testConsoleBadgeClearsWhatWouldHideThatConsole() {
        let games = [game("jak", "PlayStation 2"), game("kart", "Nintendo 64"), game("halo", "Xbox")]
        var filter = LibraryFilter(console: "Xbox", search: "kart", onlyInstalled: true)
        filter.show(console: "PlayStation 2", in: games, installed: ["kart"])
        XCTAssertEqual(filter, LibraryFilter(console: "PlayStation 2", search: "", onlyInstalled: false))
        XCTAssertEqual(games.filter { filter.matches($0, installed: ["kart"]) }.map(\.id), ["jak"])
    }

    func testConsoleBadgeKeepsInstalledWhenSomeAreInstalled() {
        let games = [game("jak", "PlayStation 2"), game("sly", "PlayStation 2")]
        var filter = LibraryFilter(onlyInstalled: true)
        filter.show(console: "PlayStation 2", in: games, installed: ["sly"])
        XCTAssertTrue(filter.onlyInstalled)
        XCTAssertEqual(games.filter { filter.matches($0, installed: ["sly"]) }.map(\.id), ["sly"])
    }

    func testStickNeedsAFirmPushAndHoldsUntilNearlyCentred() {
        XCTAssertNil(MoveDirection.resolve(x: 0.4, y: 0, holding: nil), "inside the dead zone")
        XCTAssertEqual(MoveDirection.resolve(x: 0.8, y: 0.2, holding: nil), .right)
        XCTAssertEqual(MoveDirection.resolve(x: 0, y: -1, holding: nil), .down)
        XCTAssertEqual(MoveDirection.resolve(x: 0, y: 1, holding: nil), .up)
        XCTAssertEqual(MoveDirection.resolve(x: -0.4, y: 0, holding: .left), .left, "still held")
        XCTAssertNil(MoveDirection.resolve(x: -0.2, y: 0, holding: .left), "let go")
        XCTAssertNil(MoveDirection.resolve(x: 0, y: 0.4, holding: .left), "a weak push another way")
    }

    /// Three covers in a row and two below, the second row starting under the first.
    private let grid: [(id: String, frame: CGRect)] = [
        ("a", CGRect(x: 0, y: 0, width: 100, height: 140)),
        ("b", CGRect(x: 120, y: 40, width: 100, height: 100)),  // a shorter cover on the same line
        ("c", CGRect(x: 240, y: 0, width: 100, height: 140)),
        ("d", CGRect(x: 0, y: 170, width: 100, height: 140)),
        ("e", CGRect(x: 120, y: 170, width: 100, height: 140)),
    ]

    private func from(_ id: String, _ direction: MoveDirection) -> String? {
        let frame = grid.first { $0.id == id }!.frame
        return direction.nearest(from: frame, among: grid.filter { $0.id != id })
    }

    func testSelectionMovesToTheNeighbourOnScreen() {
        XCTAssertEqual(from("a", .right), "b")
        XCTAssertEqual(from("b", .right), "c")
        XCTAssertEqual(from("b", .down), "e")
        XCTAssertEqual(from("c", .down), "e", "the last row is shorter")
        XCTAssertEqual(from("e", .up), "b")
        XCTAssertEqual(from("d", .right), "e")
        XCTAssertNil(from("c", .right))
        XCTAssertNil(from("a", .up))
    }

    @MainActor
    func testFocusStaysOnItsScreenAndCarouselsTurnThemselves() {
        let focus = ControllerFocus()
        focus.scope = "library"
        for item in grid { focus.update("library/\(item.id)", .init(frame: item.frame, scope: "library", isDefault: true)) }
        // A game's page lies under the library; its items mustn't take the library's focus.
        focus.update("detail:x/play", .init(frame: CGRect(x: 120, y: 330, width: 100, height: 50), scope: "detail:x"))
        focus.move(.down)
        XCTAssertEqual(focus.selected, "library/a", "the first press shows the selection")
        focus.move(.down)
        XCTAssertEqual(focus.selected, "library/d")
        focus.move(.down)
        XCTAssertEqual(focus.selected, "library/d", "nothing below on this screen")

        focus.update("library/carousel", .init(frame: CGRect(x: 0, y: 330, width: 340, height: 60), scope: "library",
                                               handles: .horizontal))
        focus.select("library/carousel")
        var sent: [ControllerFocus.Command] = []
        let watch = focus.commands.sink { sent.append($0.command) }
        focus.move(.right)
        focus.activate()
        XCTAssertEqual(sent, [.move(.right), .activate])
        XCTAssertEqual(focus.selected, "library/carousel")
        watch.cancel()

        focus.scope = "detail:x"
        XCTAssertNil(focus.selected)
        focus.scope = "library"
        XCTAssertEqual(focus.selected, "library/carousel", "back from a game's page, the selection returns")
    }

    /// The D-pad and left stick pushed the same way are one push: one move, one repeat.
    @MainActor
    func testDpadAndStickTogetherMoveOnce() async throws {
        let focus = ControllerFocus()
        focus.scope = "library"
        for index in 0..<8 {
            focus.update("library/\(index)", .init(frame: CGRect(x: index * 120, y: 0, width: 100, height: 140), scope: "library"))
        }
        focus.select("library/0")
        focus.timing = RepeatTiming(delay: .milliseconds(300), first: .milliseconds(300), fastest: .milliseconds(300), step: .zero)
        // Kept alive to the end, so no two of them can share an identifier.
        let objects = (0..<4).map { _ in NSObject() }
        let (pad, dpad, stick, other) = (ObjectIdentifier(objects[0]), ObjectIdentifier(objects[1]),
                                         ObjectIdentifier(objects[2]), ObjectIdentifier(objects[3]))

        focus.point(dpad, on: pad, x: 1, y: 0)
        focus.point(stick, on: pad, x: 1, y: 0)
        XCTAssertEqual(focus.selected, "library/1", "one move for both")
        try await Task.sleep(for: .milliseconds(450))
        XCTAssertEqual(focus.selected, "library/2", "one repeat at 300 ms, not two")

        // Letting go of the D-pad while the stick still points right keeps the same push going.
        focus.point(dpad, on: pad, x: 0, y: 0)
        XCTAssertEqual(focus.selected, "library/2")
        focus.point(stick, on: pad, x: 0, y: 0)
        try await Task.sleep(for: .milliseconds(400))
        XCTAssertEqual(focus.selected, "library/2", "released: no more repeats")

        // Another gamepad is its own push.
        focus.point(dpad, on: other, x: 1, y: 0)
        XCTAssertEqual(focus.selected, "library/3")
        focus.point(dpad, on: other, x: 0, y: 0)
        withExtendedLifetime(objects) {}
    }

    /// Only the outlined item hears about a move: the highlight changes once per move, and
    /// nothing redraws the rest of the library.
    @MainActor
    func testHighlightFollowsTheSelectionOnly() {
        let focus = ControllerFocus()
        focus.scope = "library"
        for index in 0..<3 {
            focus.update("library/\(index)", .init(frame: CGRect(x: index * 120, y: 0, width: 100, height: 140), scope: "library"))
        }
        var heard: [String?] = []
        let watch = focus.highlight.dropFirst().sink { heard.append($0?.key) }
        var redraws = 0
        let whole = focus.objectWillChange.sink { redraws += 1 }
        focus.select("library/0")
        focus.select("library/0")
        focus.move(.right)
        let lit: (String) -> String? = { focus.connected ? $0 : nil }
        XCTAssertEqual(focus.selected, "library/1")
        XCTAssertEqual(focus.highlight.value?.key, lit("library/1"))
        XCTAssertEqual(heard, focus.connected ? ["library/0", "library/1"] : [], "once per change, only with a controller")
        XCTAssertEqual(redraws, 0, "a move doesn't redraw every view holding ControllerFocus")
        watch.cancel()
        whole.cancel()
    }

    /// D-pad up from the top row stays there: nothing above the games takes the selection.
    @MainActor
    func testUpFromTheTopRowStays() {
        let focus = ControllerFocus()
        focus.scope = "library"
        for item in grid { focus.update("library/\(item.id)", .init(frame: item.frame, scope: "library", isDefault: true)) }
        focus.select("library/b")
        focus.move(.up)
        XCTAssertEqual(focus.selected, "library/b")
        focus.select("library/c")
        focus.move(.right)
        XCTAssertEqual(focus.selected, "library/c", "edges don't wrap")
    }

    func testShouldersCycleConsolesThroughAll() {
        let consoles = ["Nintendo 64", "GameCube", "PC"]
        XCTAssertEqual(LibraryFilter.console(after: "", step: 1, in: consoles), "Nintendo 64")
        XCTAssertEqual(LibraryFilter.console(after: "Nintendo 64", step: 1, in: consoles), "GameCube")
        XCTAssertEqual(LibraryFilter.console(after: "PC", step: 1, in: consoles), "", "RB wraps to All")
        XCTAssertEqual(LibraryFilter.console(after: "", step: -1, in: consoles), "PC", "LB wraps to the last")
        XCTAssertEqual(LibraryFilter.console(after: "Wii", step: 1, in: consoles), "Nintendo 64", "a hidden console counts as All")
    }

    func testHeldDirectionRepeatsSoonThenFaster() {
        let waits = (0..<8).map { RepeatTiming().wait(before: $0) }
        XCTAssertEqual(waits, [280, 110, 100, 90, 80, 70, 60, 60].map { Duration.milliseconds($0) })
    }

    func testStickKeepsItsDirectionThroughADiagonal() {
        XCTAssertEqual(MoveDirection.resolve(x: 0.6, y: 0.55, holding: .right), .right)
        XCTAssertEqual(MoveDirection.resolve(x: 0.35, y: 0.5, holding: .right), .right, "a slight turn")
        XCTAssertEqual(MoveDirection.resolve(x: 0.3, y: 0.8, holding: .right), .up, "a clear turn")
        XCTAssertEqual(MoveDirection.resolve(x: 0.6, y: 0.55, holding: nil), .right)
    }

    func testTriggersPageAboutAScreen() {
        let rows = (0..<10).map { (id: $0, frame: CGRect(x: 0, y: CGFloat($0) * 100, width: 100, height: 80)) }
        XCTAssertEqual(MoveDirection.down.page(from: rows[0].frame, among: Array(rows.dropFirst()), distance: 350), 3)
        XCTAssertEqual(MoveDirection.up.page(from: rows[9].frame, among: Array(rows.dropLast()), distance: 350), 6)
        XCTAssertEqual(MoveDirection.down.page(from: rows[8].frame, among: rows.filter { $0.id != 8 }, distance: 350), 9, "stops at the end")
        XCTAssertNil(MoveDirection.down.page(from: rows[9].frame, among: Array(rows.dropLast()), distance: 350))
    }

    /// Exactly one view shows the selection, through scope changes, a second copy of an item
    /// and the item going away.
    @MainActor
    func testExactlyOneViewShowsTheSelection() {
        let focus = ControllerFocus()
        focus.connected = true
        focus.scope = "library"
        let first = UUID(), second = UUID()
        focus.update("library/a", .init(frame: CGRect(x: 0, y: 0, width: 100, height: 100), scope: "library", token: first))
        focus.update("library/b", .init(frame: CGRect(x: 120, y: 0, width: 100, height: 100), scope: "library"))
        focus.select("library/a")
        XCTAssertEqual(focus.highlight.value, .init(key: "library/a", token: first))
        // A second copy (a caption fading in for the next game) takes over; the old one goes dark.
        focus.update("library/a", .init(frame: CGRect(x: 0, y: 0, width: 100, height: 100), scope: "library", token: second))
        XCTAssertEqual(focus.highlight.value, .init(key: "library/a", token: second))
        focus.remove("library/a", token: first)
        XCTAssertEqual(focus.highlight.value?.token, second, "the old copy leaving changes nothing")
        // A page opens over the library: nothing in the library stays lit.
        focus.scope = "detail:x"
        XCTAssertNil(focus.highlight.value)
        focus.scope = "library"
        XCTAssertEqual(focus.highlight.value?.key, "library/a")
        // A filter removes the selected game: no highlight, then the nearest game takes it.
        focus.remove("library/a", token: second)
        XCTAssertNil(focus.highlight.value)
        focus.reselect()
        XCTAssertEqual(focus.highlight.value?.key, "library/b")
        focus.connected = false
        XCTAssertNil(focus.highlight.value, "no controller, no highlight")
    }

    /// A plays the selected game; View opens its page.
    @MainActor
    func testAPlaysAndViewOpensDetails() {
        let focus = ControllerFocus()
        focus.scope = "library"
        focus.update("library/tile", .init(frame: CGRect(x: 0, y: 0, width: 100, height: 100), scope: "library"))
        focus.select("library/tile")
        var sent: [ControllerFocus.Command] = []
        let watch = focus.commands.sink { sent.append($0.command) }
        focus.activate()
        focus.details()
        XCTAssertEqual(sent, [.activate, .details])
        watch.cancel()
    }

    /// A touch hides the selection; the next controller input brings it back on the item nearest
    /// the middle of the screen, without moving or pressing anything.
    @MainActor
    func testTouchHidesTheSelectionUntilTheNextInput() {
        let focus = ControllerFocus()
        focus.connected = true
        focus.scope = "library"
        focus.viewport = CGRect(x: 0, y: 0, width: 400, height: 400)
        let frames = ["top": CGRect(x: 150, y: 0, width: 100, height: 60), "middle": CGRect(x: 150, y: 170, width: 100, height: 60),
                      "below": CGRect(x: 150, y: 500, width: 100, height: 60)]
        for (id, frame) in frames { focus.update("library/\(id)", .init(frame: frame, scope: "library")) }
        focus.select("library/top")
        var sent: [ControllerFocus.Command] = []
        let watch = focus.commands.sink { sent.append($0.command) }
        focus.touch()
        XCTAssertNil(focus.highlight.value, "a finger hides the selection")
        focus.remove("library/top", token: focus.targets["library/top"]!.token)
        focus.reselect()
        XCTAssertNil(focus.highlight.value, "nothing re-selects (or scrolls) while the finger is in charge")
        focus.activate()
        XCTAssertEqual(focus.selected, "library/middle", "back on the item nearest the middle of the screen")
        XCTAssertEqual(focus.highlight.value?.key, "library/middle")
        XCTAssertEqual(sent, [], "that first press only shows the selection")
        focus.move(.down)
        XCTAssertEqual(focus.selected, "library/below", "then the D-pad moves as usual")
        watch.cancel()
    }

    /// A held direction stops on a new screen and on a touch: nothing keeps moving by itself.
    @MainActor
    func testHeldDirectionStopsOnScreenChangeAndTouch() async throws {
        let focus = ControllerFocus()
        focus.connected = true
        focus.scope = "library"
        for index in 0..<12 {
            focus.update("library/\(index)", .init(frame: CGRect(x: index * 120, y: 0, width: 100, height: 100), scope: "library"))
        }
        focus.timing = RepeatTiming(delay: .milliseconds(100), first: .milliseconds(100), fastest: .milliseconds(100), step: .zero)
        let objects = [NSObject(), NSObject()]
        let (pad, dpad) = (ObjectIdentifier(objects[0]), ObjectIdentifier(objects[1]))

        focus.select("library/0")
        focus.point(dpad, on: pad, x: 1, y: 0)
        XCTAssertEqual(focus.selected, "library/1")
        focus.scope = "detail:x"
        focus.scope = "library"
        try await Task.sleep(for: .milliseconds(350))
        XCTAssertEqual(focus.selected, "library/1", "the page opening stopped the repeat")
        // The D-pad is still down after the screen change: a new push is needed to move again.
        focus.point(dpad, on: pad, x: 0, y: 0)
        focus.point(dpad, on: pad, x: 1, y: 0)
        XCTAssertEqual(focus.selected, "library/2")
        focus.touch()
        try await Task.sleep(for: .milliseconds(350))
        XCTAssertEqual(focus.selected, "library/2", "the touch stopped the repeat")
        withExtendedLifetime(objects) {}
    }

    /// When the selected game goes away (a filter, a lazy row), the nearest game on screen takes
    /// the selection; one off screen never does, so the page isn't pulled anywhere.
    @MainActor
    func testReselectStaysOnScreen() {
        let focus = ControllerFocus()
        focus.connected = true
        focus.scope = "library"
        focus.viewport = CGRect(x: 0, y: 0, width: 400, height: 400)
        let gone = UUID()
        focus.update("library/gone", .init(frame: CGRect(x: 0, y: 380, width: 100, height: 100), scope: "library", token: gone))
        focus.update("library/far", .init(frame: CGRect(x: 0, y: 500, width: 100, height: 100), scope: "library"))
        focus.update("library/shown", .init(frame: CGRect(x: 250, y: 200, width: 100, height: 100), scope: "library"))
        focus.select("library/gone")
        focus.remove("library/gone", token: gone)
        focus.reselect()
        XCTAssertEqual(focus.selected, "library/shown", "the nearest game on screen, not the closer one below it")
    }

    /// Covers decode no larger than they're shown: fronts at 1000 px, spines 768, the rest 512,
    /// and a small picture isn't scaled up.
    func testCoversDecodeAtTheirShownSize() throws {
        XCTAssertEqual(CoverStore.maxPixels("boxart-bluewake"), 1000)
        XCTAssertEqual(CoverStore.maxPixels("chosen-bluewake"), 1000)
        XCTAssertEqual(CoverStore.maxPixels("spine-bluewake"), 768)
        XCTAssertEqual(CoverStore.maxPixels("back-bluewake"), 512)
        XCTAssertEqual(CoverStore.maxPixels("card-bluewake"), 512)
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        func write(_ size: CGSize, _ name: String) throws -> URL {
            let format = UIGraphicsImageRendererFormat()
            format.scale = 1
            let data = UIGraphicsImageRenderer(size: size, format: format).pngData { context in
                UIColor.systemTeal.setFill()
                context.fill(CGRect(origin: .zero, size: size))
            }
            let url = folder.appendingPathComponent(name)
            try data.write(to: url)
            return url
        }
        let big = try XCTUnwrap(CoverStore.decode(write(CGSize(width: 1400, height: 2000), "big"), maxPixels: 1000))
        XCTAssertEqual(max(big.size.width, big.size.height), 1000)
        XCTAssertEqual(big.size.width / big.size.height, 0.7, accuracy: 0.01, "keeps its shape")
        let small = try XCTUnwrap(CoverStore.decode(write(CGSize(width: 300, height: 400), "small"), maxPixels: 1000))
        XCTAssertEqual(small.size, CGSize(width: 300, height: 400))
    }
}
