import XCTest

final class FitnessUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testTabBarShowsMainSections() throws {
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.tabBars.firstMatch.waitForExistence(timeout: 5))
        XCTAssertTrue(app.tabBars.buttons["Dashboard"].exists)
        XCTAssertTrue(app.tabBars.buttons["Log"].exists)
        XCTAssertTrue(app.tabBars.buttons["Goals"].exists)
        XCTAssertTrue(app.tabBars.buttons["Health"].exists)
    }

    @MainActor
    func testSaveWorkoutShowsInRecentList() throws {
        let app = XCUIApplication()
        app.launch()
        app.tabBars.buttons["Log"].tap()
        let save = app.buttons["Save workout"]
        XCTAssertTrue(save.waitForExistence(timeout: 5))
        save.tap()
        XCTAssertTrue(app.staticTexts["Cardio"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testAddGoalShowsInGoalsList() throws {
        let app = XCUIApplication()
        app.launch()
        app.tabBars.buttons["Goals"].tap()
        let add = app.buttons["Add goal"]
        XCTAssertTrue(add.waitForExistence(timeout: 5))
        add.tap()
        XCTAssertTrue(app.staticTexts["Strength"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testDashboardAccessibilityRoot() throws {
        let app = XCUIApplication()
        app.launch()
        app.tabBars.buttons["Dashboard"].tap()
        XCTAssertTrue(app.otherElements["dashboard_root"].waitForExistence(timeout: 5))
    }
}
