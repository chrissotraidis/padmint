import XCTest

/// Scripted tours for the release video, recorded with `xcrun simctl io recordVideo`.
/// Skipped unless PADMINT_SHOWCASE is set (TEST_RUNNER_PADMINT_SHOWCASE=1 for xcodebuild).
/// Debug builds only: -demoInstalled marks games as installed in the simulator.
/// The featured shots show the PC, Xbox and PlayStation ports; Nintendo's own series
/// appear only in the fast scroll behind the title.
final class ShowcaseUITests: XCTestCase {
    /// Games installed on the owner's iPad, leaving out Nintendo's own series.
    static let installed = "bearbirdpad,caesarpad,ctrpad,daggerpad,darkpad,deviltouch,emeraldtablet,goldenpad,kidpad,nightpad,openrct2touch,squirrelpad,vaultpad"

    override func setUpWithError() throws {
        try XCTSkipIf(ProcessInfo.processInfo.environment["PADMINT_SHOWCASE"] == nil, "showcase recordings only")
        XCUIDevice.shared.orientation = .landscapeLeft
    }

    /// A launch argument outranks what the app saves, so pass console: nil when the test taps the filter bar.
    private func launch(_ layout: String, console: String? = "", sort: String = "title", installed: Bool = false, _ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "download", "-officialTitles", "1", "-layout", layout,
                                "-sort", sort, "-onlyInstalled", installed ? "1" : "0", "-appearance", "dark",
                                "-carouselStyle", "boxes", "-coverSize", "medium",
                                "-demoInstalled", Self.installed, "-demoLastPlayed", "vaultpad"]
            + (console.map { ["-console", $0] } ?? []) + extra
        app.launch()
        return app
    }

    private func pause(_ seconds: Double) { Thread.sleep(forTimeInterval: seconds) }

    private func drag(_ app: XCUIApplication, _ from: CGVector, _ to: CGVector, velocity: XCUIGestureVelocity) {
        app.coordinate(withNormalizedOffset: from)
            .press(forDuration: 0.02, thenDragTo: app.coordinate(withNormalizedOffset: to), withVelocity: velocity, thenHoldForDuration: 0)
    }

    /// Loads every cover once so the recorded takes don't wait on the network.
    func test0WarmCovers() {
        let app = launch("grid")
        pause(12)
        for _ in 0..<4 { app.swipeUp(); pause(1.5) }
    }

    /// Behind the title: the whole collection flies past.
    func testATitleScroll() {
        let app = launch("grid", sort: "console")
        pause(3)
        for _ in 0..<4 { drag(app, CGVector(dx: 0.5, dy: 0.85), CGVector(dx: 0.5, dy: 0.2), velocity: 2600); pause(0.5) }
        pause(1)
    }

    /// The PC boxes, one swipe every 1.6 s.
    func testBCarouselPC() {
        let app = launch("carousel", console: "PC")
        XCTAssertTrue(app.staticTexts["carousel-title"].waitForExistence(timeout: 10))
        pause(2.5)
        for _ in 0..<11 { drag(app, CGVector(dx: 0.72, dy: 0.45), CGVector(dx: 0.42, dy: 0.45), velocity: 900); pause(1.6) }
    }

    /// Fallout 2's page; the box turns under a finger.
    func testCDetail() {
        let app = launch("grid", console: "PC")
        let tile = app.buttons["tile-vaultpad"]
        XCTAssertTrue(tile.waitForExistence(timeout: 10))
        pause(1.5)
        tile.tap()
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5))
        pause(1.5)
        drag(app, CGVector(dx: 0.42, dy: 0.3), CGVector(dx: 0.62, dy: 0.3), velocity: 250)
        pause(3)
    }

    /// Picking consoles in the filter bar.
    func testDFilter() {
        let app = launch("grid", console: nil, sort: "title")
        let pc = app.buttons["PC"].firstMatch
        XCTAssertTrue(pc.waitForExistence(timeout: 10))
        pc.tap()
        pause(2.5)
        for console in ["Xbox", "PlayStation", "PlayStation 2", "PC"] {
            app.buttons[console].firstMatch.tap()
            pause(1.6)
        }
        pause(1)
    }

    func testEShelf() {
        let app = launch("shelf", sort: "recent")
        pause(3)
        drag(app, CGVector(dx: 0.8, dy: 0.62), CGVector(dx: 0.3, dy: 0.62), velocity: 700); pause(1.5)
        drag(app, CGVector(dx: 0.5, dy: 0.8), CGVector(dx: 0.5, dy: 0.4), velocity: 400)
        pause(2.5)
    }

    /// The installed games in console order: Rare's N64 games, then PlayStation, Xbox and PC.
    func testFInstalled() {
        let app = launch("carousel", sort: "console", installed: true)
        XCTAssertTrue(app.staticTexts["carousel-title"].waitForExistence(timeout: 10))
        pause(2.5)
        for _ in 0..<8 { drag(app, CGVector(dx: 0.72, dy: 0.45), CGVector(dx: 0.42, dy: 0.45), velocity: 900); pause(1.4) }
    }
}
