import XCTest

/// Smoke test: the library opens, and a game's tile opens its page.
/// Set PADMINT_HOLD=seconds to keep the page open for a screenshot.
final class LibraryUITests: XCTestCase {
    func testOpenGamePage() throws {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "off", "-layout", "grid"]
        app.launch()
        let tile = app.buttons["tile-bluewake"]
        XCTAssertTrue(tile.waitForExistence(timeout: 10))
        tile.tap()
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5))
        if let hold = ProcessInfo.processInfo.environment["PADMINT_HOLD"].flatMap(Double.init) {
            Thread.sleep(forTimeInterval: hold)
        }
    }

    /// Swiping the 3D carousel moves to the next game; tapping the front box opens it.
    func testCarouselSwipe() throws {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "off", "-officialTitles", "1", "-layout", "carousel",
                                "-carouselStyle", "boxes", "-sort", "title", "-console", "", "-onlyInstalled", "0"]
        app.launch()
        let title = app.staticTexts["carousel-title"]
        XCTAssertTrue(title.waitForExistence(timeout: 10))
        let first = title.label
        let stage = app.coordinate(withNormalizedOffset: CGVector(dx: 0.75, dy: 0.42))
        stage.press(forDuration: 0.05, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.45, dy: 0.42)))
        let moved = NSPredicate(format: "label != %@", first)
        expectation(for: moved, evaluatedWith: title)
        waitForExpectations(timeout: 5)
        let second = title.label
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.42)).tap()
        let detail = app.staticTexts["detail-title"]
        XCTAssertTrue(detail.waitForExistence(timeout: 5))
        XCTAssertEqual(detail.label, second)
    }
}
