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

    /// A launch argument outranks what the app saves: pass nil for a setting the test changes.
    private func launch(_ layout: String?, console: String? = "", _ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "download", "-officialTitles", "1", "-sort", "title",
                                "-onlyInstalled", "0", "-appearance", "dark", "-carouselStyle", "boxes",
                                "-demoInstalled", ShowcaseUITests.installed, "-demoLastPlayed", "vaultpad"]
            + (layout.map { ["-layout", $0] } ?? []) + (console.map { ["-console", $0] } ?? []) + extra
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
    /// Its D-pad, shoulder buttons and triggers sit on the left, A/B/X/Y on the right.
    private func press(_ app: XCUIApplication, _ button: String, times: Int = 1) {
        let spots: [String: CGVector] = ["right": CGVector(dx: 0.1345, dy: 0.761), "left": CGVector(dx: 0.0745, dy: 0.761),
                                         "down": CGVector(dx: 0.1045, dy: 0.8024), "up": CGVector(dx: 0.1045, dy: 0.721),
                                         "LT": CGVector(dx: 0.0573, dy: 0.699), "RT": CGVector(dx: 0.1518, dy: 0.699),
                                         "LB": CGVector(dx: 0.0573, dy: 0.824), "RB": CGVector(dx: 0.1518, dy: 0.824),
                                         "A": CGVector(dx: 0.8936, dy: 0.8145), "B": CGVector(dx: 0.9336, dy: 0.7624),
                                         "X": CGVector(dx: 0.8536, dy: 0.7624), "Y": CGVector(dx: 0.8936, dy: 0.709)]
        for _ in 0..<times {
            app.coordinate(withNormalizedOffset: spots[button]!).tap()
            Thread.sleep(forTimeInterval: 0.6)
        }
    }

    private func chosen(_ app: XCUIApplication, _ chip: String) -> Bool {
        let button = app.buttons[chip].firstMatch
        return button.waitForExistence(timeout: 3) && button.isSelected
    }

    func testVirtualController() {
        let app = launch(nil, console: nil, ["-virtualController", "1"])
        Thread.sleep(forTimeInterval: 3)
        // Start from Grid and All consoles, whatever was saved.
        app.navigationBars.buttons["Layout"].tap()
        app.buttons["Grid"].firstMatch.tap()
        app.buttons["All consoles"].firstMatch.tap()
        Thread.sleep(forTimeInterval: 1)
        shot("13-controller-start")
        press(app, "up")
        shot("14-controller-up-stays-on-games")
        press(app, "right")
        shot("15-controller-right-to-play")
        press(app, "down", times: 3)
        shot("16-controller-down-into-grid")
        press(app, "A")
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5), "A opened the selected game")
        shot("17-controller-A-opened-page")
        press(app, "B")
        XCTAssertFalse(app.staticTexts["detail-title"].waitForExistence(timeout: 2), "B went back")

        // LB/RB change console; the selection stays on a game.
        press(app, "RB")
        XCTAssertTrue(chosen(app, "Nintendo 64"), "RB: the next console")
        shot("18-controller-RB-console")
        press(app, "LB")
        XCTAssertTrue(chosen(app, "All consoles"), "LB: back to All")
        press(app, "RT")
        shot("19-controller-RT-page")

        // Y changes layout; in the carousel left/right turn it and RT jumps five.
        press(app, "Y")
        let title = app.staticTexts["carousel-title"]
        XCTAssertTrue(title.waitForExistence(timeout: 5), "Y: carousel")
        let position = app.staticTexts.matching(NSPredicate(format: "label MATCHES %@", "[0-9]+ of [0-9]+")).firstMatch
        XCTAssertTrue(position.waitForExistence(timeout: 5))
        press(app, "LB"); press(app, "RB")
        XCTAssertTrue(position.label.hasPrefix("1 of"), position.label)
        press(app, "right")
        XCTAssertTrue(position.label.hasPrefix("2 of"), position.label)
        press(app, "RT")
        XCTAssertTrue(position.label.hasPrefix("7 of"), "RT jumps five: \(position.label)")
        shot("20-controller-carousel-RT-jump")
        press(app, "A")
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5), "A opened the carousel's game")
        press(app, "B")

        press(app, "Y")  // list
        press(app, "down", times: 3)
        press(app, "right")
        shot("21-controller-list-play")

        press(app, "Y")  // grid again
        press(app, "X")
        XCTAssertTrue(app.searchFields.firstMatch.waitForExistence(timeout: 5), "X opens search")
        shot("22-controller-X-search")
        // The keyboard covers the on-screen controller here, so close the search by touch.
        app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'installed'")).firstMatch.tap()
        XCTAssertFalse(app.searchFields.firstMatch.waitForExistence(timeout: 2), "the field goes again")
        app.buttons["All consoles"].firstMatch.tap()
    }
}
