import XCTest

/// Smoke test: the library opens, and a game's page has its Play button.
/// Set PADMINT_HOLD=seconds to keep the page open for a screenshot.
final class LibraryUITests: XCTestCase {
    func testOpenGamePage() throws {
        let app = XCUIApplication()
        app.launch()
        // The grid tile ("… Installed") opens the game's page; the cover row plays the game.
        let game = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'BlueWake' AND label CONTAINS 'Installed'")).firstMatch
        XCTAssertTrue(game.waitForExistence(timeout: 10))
        game.tap()
        XCTAssertTrue(app.buttons["Play"].waitForExistence(timeout: 5))
        if let hold = ProcessInfo.processInfo.environment["PADMINT_HOLD"].flatMap(Double.init) {
            Thread.sleep(forTimeInterval: hold)
        }
    }
}
