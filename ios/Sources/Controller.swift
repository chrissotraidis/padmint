import Combine
import GameController
import SwiftUI

/// Where the D-pad or left stick points.
enum MoveDirection: CaseIterable {
    case up, down, left, right

    var axis: Axis.Set { self == .left || self == .right ? .horizontal : .vertical }

    /// How far (x, y) points this way, 0 when it points the other way (y is up).
    private func component(x: Float, y: Float) -> Float {
        switch self {
        case .right: max(x, 0)
        case .left: max(-x, 0)
        case .up: max(y, 0)
        case .down: max(-y, 0)
        }
    }

    /// The direction a stick or D-pad points, with a dead zone. A held direction stays held
    /// until the stick is nearly back in the middle, and through a diagonal unless the stick
    /// clearly turns, so it doesn't flicker between neighbours.
    static func resolve(x: Float, y: Float, holding: MoveDirection?) -> MoveDirection? {
        let engage: Float = 0.5, release: Float = 0.3
        let size = max(abs(x), abs(y))
        guard size >= release else { return nil }
        let dominant: MoveDirection = abs(x) > abs(y) ? (x > 0 ? .right : .left) : (y > 0 ? .up : .down)
        if let holding {
            let kept = holding.component(x: x, y: y)
            let other = holding.axis == .horizontal ? abs(y) : abs(x)
            if kept >= release && !(other >= engage && other > kept * 1.5) { return holding }
        }
        return size >= engage ? dominant : nil
    }

    /// The nearest item that way on screen: the closest edge first, then the one most in
    /// line with `frame`. Nil when nothing lies that way, so edges don't wrap.
    func nearest<ID>(from frame: CGRect, among items: [(id: ID, frame: CGRect)]) -> ID? {
        func gap(_ a: ClosedRange<CGFloat>, _ b: ClosedRange<CGFloat>) -> CGFloat {
            max(0, max(a.lowerBound, b.lowerBound) - min(a.upperBound, b.upperBound))
        }
        let rows = frame.minY...frame.maxY, columns = frame.minX...frame.maxX
        let scored = items.compactMap { item -> (id: ID, score: CGFloat)? in
            let r = item.frame
            let along: CGFloat, across: CGFloat, offset: CGFloat
            switch self {
            case .right: along = r.minX - frame.maxX
            case .left: along = frame.minX - r.maxX
            case .down: along = r.minY - frame.maxY
            case .up: along = frame.minY - r.maxY
            }
            if axis == .horizontal {
                across = gap(rows, r.minY...r.maxY); offset = abs(r.midY - frame.midY)
            } else {
                across = gap(columns, r.minX...r.maxX); offset = abs(r.midX - frame.midX)
            }
            guard along >= -2 else { return nil }
            return (item.id, max(along, 0) + across * 4 + offset * 0.25)
        }
        return scored.min { $0.score < $1.score }?.id
    }

    /// LT/RT: step this way item by item until about `distance` has been covered
    /// (a page), stopping at the edge.
    func page<ID: Equatable>(from frame: CGRect, among items: [(id: ID, frame: CGRect)], distance: CGFloat) -> ID? {
        var pool = items, at = frame, found: ID?
        while let next = nearest(from: at, among: pool), let item = pool.first(where: { $0.id == next }) {
            let travelled = axis == .vertical ? abs(item.frame.midY - frame.midY) : abs(item.frame.midX - frame.midX)
            if found != nil && travelled > distance { break }
            found = next
            at = item.frame
            pool.removeAll { $0.id == next }
            if travelled >= distance { break }
        }
        return found
    }
}

/// A held direction: the first move happens at once, the first repeat after `delay`, then
/// the repeats speed up from `first` to `fastest`.
struct RepeatTiming: Equatable {
    var delay = Duration.milliseconds(280)
    var first = Duration.milliseconds(110)
    var fastest = Duration.milliseconds(60)
    var step = Duration.milliseconds(10)

    /// The wait before repeat number `n` (0 is the first repeat).
    func wait(before n: Int) -> Duration { n == 0 ? delay : max(fastest, first - step * (n - 1)) }
}

/// Moves one visible selection around the game content with a game controller, console-style:
/// the D-pad or left stick moves it, A plays or presses, View opens a game's page, B goes back,
/// LB/RB change console, LT/RT page, X searches, Y changes layout, Menu opens Settings and the
/// right stick scrolls and turns boxes. Any touch hides the selection until the next controller
/// input; the selection only shows while a controller is connected.
@MainActor
final class ControllerFocus: ObservableObject {
    enum Command: Equatable { case activate, details, move(MoveDirection), page(Int) }
    /// Buttons the screen in front handles itself.
    enum Press: Equatable { case back, menu, search, layout, console(Int) }

    struct Target {
        var frame: CGRect
        var scope: String
        /// Directions the item handles itself, such as a carousel turning left and right.
        var handles: Axis.Set = []
        /// Whether LT/RT go to the item (a carousel jumps) instead of paging.
        var pages = false
        /// Where the selection starts on its screen (the top-most such item).
        var isDefault = false
        var token = UUID()
    }

    /// The one item showing the selection: its key and the view that registered it.
    struct Lit: Equatable {
        var key: String
        var token: UUID
    }

    // Not @Published: a change would redraw every view holding this object (the whole
    // library). Only the items whose outline changes redraw, through `highlight`.
    // Set by attachAll; tests set it directly.
    var connected = false {
        didSet {
            publishHighlight()
            if connection.value != connected { connection.send(connected) }
        }
    }
    /// The selected item's key (`scope/id`).
    private(set) var selected: String? { didSet { publishHighlight() } }
    let highlight = CurrentValueSubject<Lit?, Never>(nil)
    /// Whether a game controller is connected, for views that change with it.
    let connection = CurrentValueSubject<Bool, Never>(false)
    /// SF Symbols for the connected controller's buttons (A, B, X, Y, LB, RB, LT, RT, Menu).
    private(set) var glyphs: [String: String] = [:]
    /// The screen in front (the library, a game's page, a sheet); only its items take focus.
    var scope = "library" {
        didSet { if scope != oldValue { scopeChanged() } }
    }
    let commands = PassthroughSubject<(key: String, command: Command), Never>()
    /// The right stick turning the box on a screen: radians this frame.
    let spin = PassthroughSubject<(scope: String, radians: CGFloat), Never>()
    /// A finger (or pointer) touched the screen since the last controller input: the selection
    /// hides, and nothing scrolls for the controller until it's used again.
    private(set) var touched = false { didSet { publishHighlight() } }
    /// The visible area, for tests; otherwise the window's bounds.
    var viewport: CGRect?
    let pressed = PassthroughSubject<Press, Never>()
    var timing = RepeatTiming()

    private(set) var targets: [String: Target] = [:]
    private var remembered: [String: String] = [:]
    /// Where the selection was last seen, to pick a neighbour when it goes away.
    private var lastFrame: CGRect?
    /// Where each gamepad's D-pad and stick point, by gamepad and then by source.
    private var pushed: [ObjectIdentifier: [ObjectIdentifier: MoveDirection]] = [:]
    /// The one direction each gamepad holds, and its repeat.
    private var held: [ObjectIdentifier: MoveDirection] = [:]
    private var repeats: [ObjectIdentifier: Task<Void, Never>] = [:]
    private var stick: (link: CADisplayLink, x: CGFloat, y: CGFloat, view: UIScrollView?)?
    private var observers: [NSObjectProtocol] = []
    #if DEBUG
    /// -virtualController 1: Apple's on-screen controller, so the simulator can drive the
    /// same input path as a real one.
    private var virtual: GCVirtualController?
    #endif

    init() {
        let center = NotificationCenter.default
        for name in [Notification.Name.GCControllerDidConnect, .GCControllerDidDisconnect, UIApplication.didBecomeActiveNotification] {
            observers.append(center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.attachAll() }
            })
        }
        // Leaving for a game with a direction held must not keep moving on return.
        observers.append(center.addObserver(forName: UIApplication.willResignActiveNotification, object: nil, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated { self?.release() }
        })
        attachAll()
        #if DEBUG
        if UserDefaults.standard.bool(forKey: "virtualController") {
            let configuration = GCVirtualController.Configuration()
            configuration.elements = [GCInputDirectionPad, GCInputButtonA, GCInputButtonB, GCInputButtonX, GCInputButtonY,
                                      GCInputLeftShoulder, GCInputRightShoulder, GCInputLeftTrigger, GCInputRightTrigger]
            virtual = GCVirtualController(configuration: configuration)
            virtual?.connect()
        }
        #endif
    }

    /// Takes input from every connected controller; run again on connect, disconnect and
    /// on coming back from a game, so a reconnected controller works straight away.
    private func attachAll() {
        release()
        let pads = GCController.controllers().compactMap(\.extendedGamepad)
        for pad in pads {
            let id = ObjectIdentifier(pad)
            for stick in [pad.dpad, pad.leftThumbstick] {
                stick.valueChangedHandler = { [weak self] element, x, y in
                    MainActor.assumeIsolated { self?.point(ObjectIdentifier(element), on: id, x: x, y: y) }
                }
            }
            pad.rightThumbstick.valueChangedHandler = { [weak self] _, x, y in
                MainActor.assumeIsolated { self?.rightStick(x: x, y: y) }
            }
            let buttons: [(GCControllerButtonInput, () -> Void)] = [
                (pad.buttonA, { [weak self] in self?.activate() }),
                (pad.buttonB, { [weak self] in self?.press(.back) }),
                (pad.buttonX, { [weak self] in self?.press(.search) }),
                (pad.buttonY, { [weak self] in self?.press(.layout) }),
                (pad.buttonMenu, { [weak self] in self?.press(.menu) }),
                (pad.leftShoulder, { [weak self] in self?.press(.console(-1)) }),
                (pad.rightShoulder, { [weak self] in self?.press(.console(1)) }),
                (pad.leftTrigger, { [weak self] in self?.page(-1) }),
                (pad.rightTrigger, { [weak self] in self?.page(1) }),
            ] + (pad.buttonOptions.map { [($0, { [weak self] in self?.details() })] } ?? [])
            for (button, action) in buttons {
                button.pressedChangedHandler = { _, _, down in
                    if down { MainActor.assumeIsolated { action() } }
                }
            }
        }
        if let pad = pads.first {
            let named: [(String, GCControllerElement)] = [("A", pad.buttonA), ("B", pad.buttonB), ("X", pad.buttonX), ("Y", pad.buttonY),
                                                          ("LB", pad.leftShoulder), ("RB", pad.rightShoulder), ("LT", pad.leftTrigger),
                                                          ("RT", pad.rightTrigger), ("Menu", pad.buttonMenu)]
                + (pad.buttonOptions.map { [("View", $0)] } ?? [])
            glyphs = Dictionary(uniqueKeysWithValues: named.compactMap { name, element in element.sfSymbolsName.map { (name, $0) } })
        }
        let was = connected
        connected = !pads.isEmpty
        if connected && !was { showSoon() }
    }

    /// Stops every held direction and the right stick: on backgrounding, disconnect, a new
    /// screen and a touch, so nothing keeps moving on its own.
    private func release() {
        repeats.values.forEach { $0.cancel() }
        repeats = [:]
        held = [:]
        pushed = [:]
        rightStick(x: 0, y: 0)
    }

    /// A finger touched the screen: hide the selection and leave the scrolling to the finger.
    func touch() {
        guard !touched else { return }
        touched = true
        release()
    }

    /// The first controller input after a touch: the selection comes back on the item nearest
    /// the middle of what's on screen now. True when it did, so that input does nothing else.
    @discardableResult
    func resume() -> Bool {
        guard touched else { return false }
        touched = false
        let screen = visible
        let mine = targets.filter { $0.value.scope == scope && screen.intersects($0.value.frame) }
        let defaults = mine.filter(\.value.isDefault)
        let pool = defaults.isEmpty ? mine : defaults
        let centre = CGPoint(x: screen.midX, y: screen.midY)
        if let nearest = pool.min(by: { distance($0.value.frame, centre) < distance($1.value.frame, centre) }) {
            select(nearest.key, reveal: false)
        }
        return true
    }

    private func distance(_ frame: CGRect, _ point: CGPoint) -> CGFloat { hypot(frame.midX - point.x, frame.midY - point.y) }

    private var visible: CGRect { viewport ?? window?.bounds ?? .infinite }

    /// B, X, Y, LB/RB and Menu act even right after a touch; the selection comes back too.
    func press(_ press: Press) {
        resume()
        pressed.send(press)
    }

    /// A held direction moves at once, then repeats, faster the longer it's held. A gamepad
    /// holds one direction: its D-pad and stick pushed the same way are one push.
    func point(_ source: ObjectIdentifier, on pad: ObjectIdentifier, x: Float, y: Float) {
        pushed[pad, default: [:]][source] = MoveDirection.resolve(x: x, y: y, holding: pushed[pad]?[source])
        let directions = Set(pushed[pad, default: [:]].values)
        let now = held[pad].flatMap { directions.contains($0) ? $0 : nil }
            ?? MoveDirection.allCases.first(where: directions.contains)
        guard now != held[pad] else { return }
        held[pad] = now
        repeats[pad]?.cancel()
        repeats[pad] = nil
        guard let now else { return }
        move(now)
        let timing = timing
        repeats[pad] = Task { [weak self] in
            var count = 0
            while !Task.isCancelled {
                try? await Task.sleep(for: timing.wait(before: count))
                count += 1
                guard !Task.isCancelled else { return }
                self?.move(now)
            }
        }
    }

    /// The selection, if it's on the screen in front.
    private var current: String? { selected.flatMap { targets[$0]?.scope == scope ? $0 : nil } }

    private func others(than key: String) -> [(id: String, frame: CGRect)] {
        targets.filter { $0.key != key && $0.value.scope == scope }.map { (id: $0.key, frame: $0.value.frame) }
    }

    func move(_ direction: MoveDirection) {
        if resume() { return }
        guard let key = current, let target = targets[key] else { return selectDefault() }
        if target.handles.contains(direction.axis) { return commands.send((key, .move(direction))) }
        if let next = direction.nearest(from: target.frame, among: others(than: key)) { select(next) }
    }

    /// LT/RT: a carousel jumps; anything else moves the selection about a page.
    func page(_ step: Int) {
        if resume() { return }
        guard let key = current, let target = targets[key] else { return selectDefault() }
        if target.pages { return commands.send((key, .page(step))) }
        let height = window?.bounds.height ?? 800
        let direction: MoveDirection = step > 0 ? .down : .up
        if let next = direction.page(from: target.frame, among: others(than: key), distance: height * 0.6) { select(next) }
    }

    func activate() {
        if resume() { return }
        guard let key = current else { return selectDefault() }
        commands.send((key, .activate))
    }

    /// The View button: the selected game's page.
    func details() {
        if resume() { return }
        guard let key = current else { return selectDefault() }
        commands.send((key, .details))
    }

    func select(_ key: String, reveal shows: Bool = true) {
        selected = key
        remembered[scope] = key
        lastFrame = targets[key]?.frame
        if shows { reveal(key) }
    }

    private var window: UIWindow? {
        UIApplication.shared.connectedScenes.compactMap { ($0 as? UIWindowScene)?.keyWindow }.first
    }

    /// The scroll views holding a point, outermost first.
    private func scrollViews(at point: CGPoint, in window: UIWindow) -> [UIScrollView] {
        var holders: [UIScrollView] = []
        func collect(_ view: UIView) {
            if let scroll = view as? UIScrollView, !scroll.isHidden, scroll.isScrollEnabled,
               scroll.convert(CGRect(origin: .zero, size: scroll.contentSize), to: nil).contains(point) {
                holders.append(scroll)
            }
            view.subviews.forEach(collect)
        }
        collect(window)
        return holders
    }

    /// Scrolls whatever holds the item so it sits in the middle, the innermost scroll view
    /// first (a row of covers, then the page). Centred, the items around it are drawn too:
    /// lazy grids and lists only make what's on screen.
    private func reveal(_ key: String) {
        guard connected, !touched, var frame = targets[key]?.frame, let window else { return }
        let centre = CGPoint(x: frame.midX, y: frame.midY)
        // Well inside the screen, the items around it are drawn already: skip the search
        // for scroll views, which walks the whole window.
        let bounds = window.bounds
        if bounds.insetBy(dx: bounds.width * 0.2, dy: bounds.height * 0.3).contains(centre) { return }
        for scroll in scrollViews(at: centre, in: window).reversed() {
            // Never pull against a finger, or against a scroll still coasting from one.
            guard !scroll.isTracking, !scroll.isDragging, !scroll.isDecelerating else { return }
            let inset = scroll.adjustedContentInset
            let visible = scroll.convert(scroll.bounds.inset(by: inset), to: nil)
            let room = CGSize(width: scroll.contentSize.width + inset.left + inset.right - scroll.bounds.width,
                              height: scroll.contentSize.height + inset.top + inset.bottom - scroll.bounds.height)
            var offset = scroll.contentOffset
            if room.width > 0 { offset.x = min(max(offset.x + frame.midX - visible.midX, -inset.left), room.width - inset.left) }
            if room.height > 0 { offset.y = min(max(offset.y + frame.midY - visible.midY, -inset.top), room.height - inset.top) }
            let moved = CGPoint(x: offset.x - scroll.contentOffset.x, y: offset.y - scroll.contentOffset.y)
            guard moved != .zero else { continue }
            scroll.setContentOffset(offset, animated: !UIAccessibility.isReduceMotionEnabled)
            frame = frame.offsetBy(dx: -moved.x, dy: -moved.y)
        }
    }

    /// The right stick: up and down scroll the page under the selection (or the middle of the
    /// screen) without moving the selection; left and right turn the box on screen. Speed
    /// follows how far it's pushed.
    private func rightStick(x: Float, y: Float) {
        let dead: Float = 0.25
        let sx = abs(x) < dead ? 0 : CGFloat(x * abs(x)), sy = abs(y) < dead ? 0 : CGFloat(-y * abs(y))
        if sx == 0 && sy == 0 {
            stick?.link.invalidate()
            stick = nil
            return
        }
        resume()
        if stick == nil {
            let link = CADisplayLink(target: Ticker { [weak self] link in self?.stickTick(link) }, selector: #selector(Ticker.fire(_:)))
            link.add(to: .main, forMode: .common)
            stick = (link, sx, sy, nil)
        }
        stick?.x = sx
        stick?.y = sy
    }

    private func stickTick(_ link: CADisplayLink) {
        guard let current = stick else { return }
        let time = CGFloat(link.targetTimestamp - link.timestamp)
        if current.x != 0 { spin.send((scope, current.x * 4 * time)) }
        guard current.y != 0 else { return }
        if current.view == nil, let window {
            let point = self.current.flatMap { targets[$0]?.frame }.map { CGPoint(x: $0.midX, y: $0.midY) }
                ?? CGPoint(x: window.bounds.midX, y: window.bounds.midY)
            stick?.view = scrollViews(at: point, in: window).last(where: {
                $0.contentSize.height + $0.adjustedContentInset.top + $0.adjustedContentInset.bottom > $0.bounds.height + 1
            })
        }
        guard let view = stick?.view, !view.isTracking else { return }
        let inset = view.adjustedContentInset
        let top = -inset.top, bottom = max(top, view.contentSize.height + inset.bottom - view.bounds.height)
        view.contentOffset.y = min(max(view.contentOffset.y + current.y * 1600 * time, top), bottom)
    }

    /// The top-most default item on screen, or the top-most item when none is marked.
    func selectDefault() {
        let mine = targets.filter { $0.value.scope == scope && $0.value.frame.maxY > 0 }
        let defaults = mine.filter(\.value.isDefault)
        let pool = defaults.isEmpty ? mine : defaults
        let first = pool.min { a, b in
            let ya = (a.value.frame.minY / 24).rounded(), yb = (b.value.frame.minY / 24).rounded()
            return ya != yb ? ya < yb : a.value.frame.minX < b.value.frame.minX
        }
        if let first { select(first.key) }
    }

    /// The selected item went away (a filter, a layout change, a lazy list dropping it): select
    /// the item nearest where it was, so the selection stays on a game near the same place.
    /// Only items on screen are considered, and nothing scrolls: the page stays where it is.
    func reselect() {
        guard !touched, current == nil, selected != nil || lastFrame != nil else { return }
        let screen = visible
        let mine = targets.filter { $0.value.scope == scope && screen.intersects($0.value.frame) }
        let defaults = mine.filter(\.value.isDefault)
        let pool = defaults.isEmpty ? mine : defaults
        let last = lastFrame.map { CGPoint(x: $0.midX, y: $0.midY) } ?? CGPoint(x: screen.midX, y: screen.midY)
        if let nearest = pool.min(by: { distance($0.value.frame, last) < distance($1.value.frame, last) }) {
            select(nearest.key, reveal: false)
        }
    }

    private func scopeChanged() {
        // A held direction mustn't carry on into the new screen.
        release()
        selected = remembered[scope]
        lastFrame = selected.flatMap { targets[$0]?.frame }
        showSoon()
    }

    /// Shows a selection once the screen's items have laid out.
    private func showSoon() {
        guard connected else { return }
        Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(350))
            guard let self, self.connected, !self.touched, self.current == nil else { return }
            self.selectDefault()
        }
    }

    /// Exactly one view shows the selection: the one that registered its key last.
    private func publishHighlight() {
        let lit = connected && !touched ? selected.flatMap { key in
            targets[key].flatMap { $0.scope == scope ? Lit(key: key, token: $0.token) : nil }
        } : nil
        if highlight.value != lit { highlight.send(lit) }
    }

    func update(_ key: String, _ target: Target) {
        let token = targets[key]?.token
        targets[key] = target
        guard key == selected else { return }
        lastFrame = target.frame
        if token != target.token { publishHighlight() }
    }

    func remove(_ key: String, token: UUID) {
        guard targets[key]?.token == token else { return }
        targets[key] = nil
        guard key == selected else { return }
        publishHighlight()
        // A filter or layout change replaces the items; give the new ones a moment to appear.
        Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(250))
            self?.reselect()
        }
    }
}

/// A display link's target that doesn't keep its owner alive.
private final class Ticker: NSObject {
    let tick: (CADisplayLink) -> Void
    init(_ tick: @escaping (CADisplayLink) -> Void) { self.tick = tick }
    @objc func fire(_ link: CADisplayLink) { tick(link) }
}

private struct FocusScopeKey: EnvironmentKey {
    static let defaultValue = "library"
}

/// Takes the window's game controller input for PadMint (iOS 18 and later). Without it, iPadOS
/// also turns a physical controller's presses into UIKit focus moves and selections, alongside
/// ControllerFocus: its focus can reach the search field, where A opens the keyboard. With it,
/// presses reach only the Game Controller framework, which ControllerFocus reads.
///
/// It also tells ControllerFocus when a finger or pointer touches anywhere, without taking the
/// touch from the views under it.
struct ControllerInputOwner: UIViewRepresentable {
    let touched: () -> Void

    func makeUIView(context: Context) -> Claim { Claim(touched: touched) }
    func updateUIView(_ view: Claim, context: Context) {}

    final class Claim: UIView {
        let touched: () -> Void

        init(touched: @escaping () -> Void) {
            self.touched = touched
            super.init(frame: .zero)
        }

        required init?(coder: NSCoder) { fatalError() }

        override func didMoveToWindow() {
            super.didMoveToWindow()
            isUserInteractionEnabled = false
            guard let window, !(window.gestureRecognizers ?? []).contains(where: { $0 is TouchWatcher }) else { return }
            window.addGestureRecognizer(TouchWatcher(touched))
            guard #available(iOS 18.0, *) else { return }
            let interaction = GCEventInteraction()
            interaction.handledEventTypes = .gamepad
            window.addInteraction(interaction)
        }
    }
}

/// Sees every touch begin and lets it through: it never recognizes, delays or cancels anything.
private final class TouchWatcher: UIGestureRecognizer, UIGestureRecognizerDelegate {
    private let touched: () -> Void

    init(_ touched: @escaping () -> Void) {
        self.touched = touched
        super.init(target: nil, action: nil)
        cancelsTouchesInView = false
        delaysTouchesBegan = false
        delaysTouchesEnded = false
        delegate = self
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent) {
        // Apple's on-screen controller (GCVirtualController) is drawn in the app's window: its
        // buttons are controller input, not a finger taking over.
        if touches.contains(where: { !Self.onController($0.view) }) { touched() }
        state = .failed
    }

    private static func onController(_ view: UIView?) -> Bool {
        var view = view
        while let current = view {
            if String(describing: type(of: current)).hasPrefix("GC") { return true }
            view = current.superview
        }
        return false
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool { true }
}

extension EnvironmentValues {
    /// Which screen a view belongs to, for ControllerFocus.
    var focusScope: String {
        get { self[FocusScopeKey.self] }
        set { self[FocusScopeKey.self] = newValue }
    }
}

private struct ControllerFocusable: ViewModifier {
    @EnvironmentObject private var focus: ControllerFocus
    @Environment(\.focusScope) private var scope
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var token = UUID()
    @State private var frame: CGRect?
    @State private var lit = false
    let id: String
    let handles: Axis.Set
    let isDefault: Bool
    let corner: CGFloat
    let inset: CGFloat
    let lift: CGFloat
    let action: () -> Void
    let move: (MoveDirection) -> Void
    let page: ((Int) -> Void)?
    let details: (() -> Void)?

    private var key: String { "\(scope)/\(id)" }

    func body(content: Content) -> some View {
        content
            .overlay {
                if lit {
                    RoundedRectangle(cornerRadius: corner, style: .continuous)
                        .strokeBorder(Color.padMintLight, lineWidth: 2.5)
                        .padding(-inset)
                        .allowsHitTesting(false)
                        .accessibilityHidden(true)
                        .transition(.opacity)
                }
            }
            // Console-style focus: the selected item lifts a little with a soft glow.
            .scaleEffect(lit && !reduceMotion ? lift : 1)
            .shadow(color: .padMint.opacity(lit ? 0.5 : 0), radius: lit ? 16 : 0)
            .zIndex(lit ? 1 : 0)
            #if DEBUG
            // UI tests read the controller's selection.
            .accessibilityValue(lit ? "controller-selected" : "")
            #endif
            .animation(reduceMotion ? nil : .snappy(duration: 0.18), value: lit)
            .onGeometryChange(for: CGRect.self) { $0.frame(in: .global) } action: { new in
                frame = new
                register()
            }
            .onAppear { register() }
            .onDisappear { focus.remove(key, token: token) }
            .onReceive(focus.highlight.map { [key, token] in $0 == .init(key: key, token: token) }.removeDuplicates()) { lit = $0 }
            .onReceive(focus.commands) { command in
                guard command.key == key else { return }
                switch command.command {
                case .activate: action()
                case .move(let direction): move(direction)
                case .page(let step): page?(step)
                case .details: details?()
                }
            }
    }

    private func register() {
        guard let frame else { return }
        focus.update(key, .init(frame: frame, scope: scope, handles: handles, pages: page != nil,
                                isDefault: isDefault, token: token))
    }
}

extension View {
    /// Lets a game controller select this item and press it with A. `lift` is how much a
    /// selected card grows (1 for full-width rows).
    func controllerFocus(_ id: String, isDefault: Bool = false, corner: CGFloat = 14, inset: CGFloat = 5,
                         lift: CGFloat = 1.05, handles: Axis.Set = [], move: @escaping (MoveDirection) -> Void = { _ in },
                         page: ((Int) -> Void)? = nil, details: (() -> Void)? = nil,
                         action: @escaping () -> Void) -> some View {
        modifier(ControllerFocusable(id: id, handles: handles, isDefault: isDefault, corner: corner, inset: inset,
                                     lift: lift, action: action, move: move, page: page, details: details))
    }
}

extension CaseIterable where Self: Equatable {
    /// The next choice, wrapping around: what A does on a picker.
    var next: Self {
        let all = Array(Self.allCases)
        return all[((all.firstIndex(of: self) ?? 0) + 1) % all.count]
    }
}
