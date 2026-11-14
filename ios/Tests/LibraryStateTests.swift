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
        focus.repeatDelay = .milliseconds(300)
        focus.repeatInterval = .milliseconds(300)
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
        let watch = focus.highlight.dropFirst().sink { heard.append($0) }
        var redraws = 0
        let whole = focus.objectWillChange.sink { redraws += 1 }
        focus.select("library/0")
        focus.select("library/0")
        focus.move(.right)
        let lit: (String) -> String? = { focus.connected ? $0 : nil }
        XCTAssertEqual(focus.selected, "library/1")
        XCTAssertEqual(focus.highlight.value, lit("library/1"))
        XCTAssertEqual(heard, focus.connected ? ["library/0", "library/1"] : [], "once per change, only with a controller")
        XCTAssertEqual(redraws, 0, "a move doesn't redraw every view holding ControllerFocus")
        watch.cancel()
        whole.cancel()
    }
}
