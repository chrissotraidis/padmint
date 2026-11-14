import XCTest

/// Screenshots of each layout and screen for review, saved to PADMINT_SHOTS (a folder);
/// TEST_RUNNER_PADMINT_SHOTS=<folder> for xcodebuild. Skipped otherwise.
final class ShotsUITests: XCTestCase {
    private var folder: URL!

    override func setUpWithError() throws {
        let path = ProcessInfo.processInfo.environment["PADMINT_SHOTS"]
        try XCTSkipIf(path == nil, "review screenshots only")
        folder = URL(fileURLWithPath: path!)
        XCUIDevice.shared.orientation = .landscapeLeft
    }

    private func launch(_ layout: String, console: String? = "", _ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "download", "-officialTitles", "1", "-layout", layout, "-sort", "title",
                                "-onlyInstalled", "0", "-appearance", "dark", "-carouselStyle", "boxes",
                                "-demoInstalled", ShowcaseUITests.installed, "-demoLastPlayed", "vaultpad"]
            + (console.map { ["-console", $0] } ?? []) + extra
        app.launch()
        return app
    }

    private func shot(_ name: String) {
        Thread.sleep(forTimeInterval: 1.5)
        try? XCUIScreen.main.screenshot().pngRepresentation.write(to: folder.appendingPathComponent("\(name).png"))
    }

    func testLayouts() {
        var app = launch("grid")
        Thread.sleep(forTimeInterval: 4)
        shot("01-grid-top")
        app.swipeUp(); app.swipeUp()
        shot("02-grid-scrolled-header")
        app = launch("carousel")
        shot("03-carousel-boxes")
        app = launch("carousel", ["-carouselStyle", "flat"])
        shot("04-carousel-flat")
        app = launch("list")
        shot("05-list")
        app.swipeUp()
        shot("06-list-scrolled")
        app = launch("list", ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityM"])
        shot("07-list-larger-text")
        app = launch("shelf")
        shot("08-saved-shelf-opens-grid")
    }

    func testBadgeAndSettings() {
        let app = launch("grid", console: nil)
        app.buttons["Xbox"].firstMatch.tap()
        XCTAssertTrue(app.buttons["All consoles"].firstMatch.waitForExistence(timeout: 10))
        app.buttons["All consoles"].firstMatch.tap()
        // With a controller connected (the iOS 27 simulator reports one) search opens on
        // request, and tapping elsewhere closes it again, so open it last.
        let open = app.navigationBars.buttons["Search"]
        if open.waitForExistence(timeout: 3) { open.tap() }
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        search.tap()
        search.typeText("Jak")
        let tile = app.buttons["tile-ottsel"]
        XCTAssertTrue(tile.waitForExistence(timeout: 10))
        shot("09-search-before-badge")
        tile.tap()
        XCTAssertTrue(app.buttons["console-badge"].waitForExistence(timeout: 5))
        shot("10-detail-console-badge")
        app.buttons["console-badge"].tap()
        XCTAssertTrue(app.buttons["PlayStation 2"].firstMatch.waitForExistence(timeout: 5))
        shot("11-after-badge-ps2")
        XCTAssertTrue(app.buttons["PlayStation 2"].firstMatch.isSelected)
        app.buttons["Settings"].firstMatch.tap()
        shot("12-settings")
        app.buttons["Done"].firstMatch.tap()
        app.buttons["All consoles"].firstMatch.tap()
    }

    /// Apple's on-screen controller drives the same GameController input as an Xbox controller.
    /// Its D-pad and A/B buttons sit at fixed places in the corners.
    private func press(_ app: XCUIApplication, _ button: String, times: Int = 1) {
        let spots: [String: CGVector] = ["right": CGVector(dx: 0.1345, dy: 0.761), "left": CGVector(dx: 0.0745, dy: 0.761),
                                         "down": CGVector(dx: 0.1045, dy: 0.80), "up": CGVector(dx: 0.1045, dy: 0.721),
                                         "A": CGVector(dx: 0.8655, dy: 0.80), "B": CGVector(dx: 0.922, dy: 0.725)]
        for _ in 0..<times {
            app.coordinate(withNormalizedOffset: spots[button]!).tap()
            Thread.sleep(forTimeInterval: 0.6)
        }
    }

    func testVirtualController() {
        var app = launch("grid", ["-virtualController", "1"])
        Thread.sleep(forTimeInterval: 3)
        shot("13-controller-start")
        press(app, "right")
        shot("14-controller-right-to-play")
        press(app, "down")
        shot("15-controller-down-to-your-games")
        press(app, "down", times: 2)
        shot("16-controller-down-into-grid")
        press(app, "A")
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5), "A opened the selected game")
        shot("17-controller-A-opened-page")
        press(app, "B")
        XCTAssertFalse(app.staticTexts["detail-title"].waitForExistence(timeout: 2), "B went back")
        shot("18-controller-B-back")
        // Settings isn't driven here: the on-screen D-pad lies outside its sheet, and a tap
        // there dismisses the sheet.

        app = launch("carousel", ["-virtualController", "1"])
        Thread.sleep(forTimeInterval: 3)
        let title = app.staticTexts["carousel-title"]
        XCTAssertTrue(title.waitForExistence(timeout: 10))
        let first = title.label
        press(app, "right", times: 2)
        XCTAssertNotEqual(title.label, first, "right turned the carousel")
        shot("19-controller-carousel-right")
        press(app, "down")
        shot("20-controller-carousel-play")

        app = launch("list", ["-virtualController", "1"])
        Thread.sleep(forTimeInterval: 3)
        press(app, "down", times: 3)
        press(app, "right")
        shot("21-controller-list-play")
    }
}
