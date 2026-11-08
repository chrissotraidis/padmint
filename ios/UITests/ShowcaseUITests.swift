import XCTest

/// Scripted tours for the release video, recorded with `xcrun simctl io recordVideo`.
/// Skipped unless PADMINT_SHOWCASE is set (TEST_RUNNER_PADMINT_SHOWCASE=1 for xcodebuild).
/// Debug builds only: -demoInstalled marks the games installed on the owner's iPad.
final class ShowcaseUITests: XCTestCase {
    static let installed = "annepad,bananapad,barrelpad,bearbirdpad,ctrpad,caesarpad,daggerpad,darkpad,deviltouch,dinopad,emeraldtablet,f0x,goldenpad,harkinianpad,kidpad,maskpad,nightpad,openrct2touch,paperpad,snappad,spaghettipad,squirrelpad,starshippad,vaultpad"

    override func setUpWithError() throws {
        try XCTSkipIf(ProcessInfo.processInfo.environment["PADMINT_SHOWCASE"] == nil, "showcase recordings only")
        XCUIDevice.shared.orientation = .landscapeLeft
    }

    private func launch(_ layout: String, _ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments += ["-boxArt", "download", "-officialTitles", "1", "-layout", layout,
                                "-console", "", "-onlyInstalled", "0", "-appearance", "dark",
                                "-demoInstalled", Self.installed, "-demoLastPlayed", "harkinianpad"] + extra
        app.launch()
        return app
    }

    private func pause(_ seconds: Double) { Thread.sleep(forTimeInterval: seconds) }

    private func swipe(_ app: XCUIApplication, from: CGFloat, to: CGFloat, y: CGFloat = 0.45, velocity: XCUIGestureVelocity = 900) {
        app.coordinate(withNormalizedOffset: CGVector(dx: from, dy: y))
            .press(forDuration: 0.02, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: to, dy: y)),
                   withVelocity: velocity, thenHoldForDuration: 0)
    }

    /// Loads every cover once so the recorded takes don't wait on the network.
    func test0WarmCovers() {
        let app = launch("grid", ["-sort", "title"])
        pause(12)
        for _ in 0..<4 { app.swipeUp(); pause(1.5) }
    }

    func test1Carousel() {
        let app = launch("carousel", ["-carouselStyle", "boxes", "-sort", "console"])
        XCTAssertTrue(app.staticTexts["carousel-title"].waitForExistence(timeout: 10))
        pause(2.5)
        for _ in 0..<5 { swipe(app, from: 0.72, to: 0.42); pause(1.3) }
        swipe(app, from: 0.85, to: 0.15, velocity: 2500); pause(2.4)
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.45)).tap()
        XCTAssertTrue(app.staticTexts["detail-title"].waitForExistence(timeout: 5))
        pause(3.5)
    }

    func test3GridScroll() {
        let app = launch("grid", ["-sort", "console", "-coverSize", "medium"])
        pause(2.5)
        for _ in 0..<3 {
            app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.8))
                .press(forDuration: 0.02, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.35)),
                       withVelocity: 450, thenHoldForDuration: 0)
            pause(1.2)
        }
    }

    func test4Shelf() {
        let app = launch("shelf", ["-sort", "recent"])
        pause(3)
        swipe(app, from: 0.8, to: 0.3, y: 0.62, velocity: 700); pause(1.5)
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.8))
            .press(forDuration: 0.02, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.4)),
                   withVelocity: 400, thenHoldForDuration: 0)
        pause(2.5)
    }
}
