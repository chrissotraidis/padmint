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
}
