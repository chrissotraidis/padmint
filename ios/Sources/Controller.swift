import Combine
import GameController
import SwiftUI

/// Where the D-pad or left stick points.
enum MoveDirection: CaseIterable {
    case up, down, left, right

    var axis: Axis.Set { self == .left || self == .right ? .horizontal : .vertical }

    /// The direction a stick or D-pad points (y is up), with a dead zone. A held direction
    /// stays held until the stick is nearly back in the middle, so it doesn't flicker.
    static func resolve(x: Float, y: Float, holding: MoveDirection?) -> MoveDirection? {
        let engage: Float = 0.5, release: Float = 0.3
        let size = max(abs(x), abs(y))
        guard size >= release else { return nil }
        let dominant: MoveDirection = abs(x) > abs(y) ? (x > 0 ? .right : .left) : (y > 0 ? .up : .down)
        if size >= engage { return dominant }
        return holding == dominant ? holding : nil
    }

    /// The nearest item that way on screen: the closest edge first, then the one most in
    /// line with `frame`. Nil when nothing lies that way.
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
}

/// Moves a visible selection around the library with a game controller: the D-pad or left
/// stick moves it, A presses the selected item, B goes back, Menu opens Settings. Touch keeps
/// working as before; the selection only shows while a controller is connected.
@MainActor
final class ControllerFocus: ObservableObject {
    enum Command: Equatable { case activate, move(MoveDirection) }

    struct Target {
        var frame: CGRect
        var scope: String
        /// Directions the item handles itself, such as a carousel turning left and right.
        var handles: Axis.Set = []
        /// Where the selection starts on its screen (the top-most such item).
        var isDefault = false
        var token = UUID()
    }

    @Published private(set) var connected = false
    /// The selected item's key (`scope/id`).
    @Published private(set) var selected: String?
    /// The screen in front (the library, a game's page, a sheet); only its items take focus.
    var scope = "library" {
        didSet { if scope != oldValue { scopeChanged() } }
    }
    let commands = PassthroughSubject<(key: String, command: Command), Never>()
    let back = PassthroughSubject<Void, Never>()
    let menu = PassthroughSubject<Void, Never>()

    private(set) var targets: [String: Target] = [:]
    private var remembered: [String: String] = [:]
    /// Where each gamepad's D-pad and stick point, by gamepad and then by source.
    private var pushed: [ObjectIdentifier: [ObjectIdentifier: MoveDirection]] = [:]
    /// The one direction each gamepad holds, and its repeat.
    private var held: [ObjectIdentifier: MoveDirection] = [:]
    private var repeats: [ObjectIdentifier: Task<Void, Never>] = [:]
    /// How long a held direction waits before repeating, then between repeats.
    var repeatDelay = Duration.milliseconds(420)
    var repeatInterval = Duration.milliseconds(130)
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
            configuration.elements = [GCInputDirectionPad, GCInputButtonA, GCInputButtonB]
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
            pad.buttonA.pressedChangedHandler = { [weak self] _, _, pressed in
                if pressed { MainActor.assumeIsolated { self?.activate() } }
            }
            pad.buttonB.pressedChangedHandler = { [weak self] _, _, pressed in
                if pressed { MainActor.assumeIsolated { self?.back.send() } }
            }
            pad.buttonMenu.pressedChangedHandler = { [weak self] _, _, pressed in
                if pressed { MainActor.assumeIsolated { self?.menu.send() } }
            }
        }
        let was = connected
        connected = !pads.isEmpty
        if connected && !was { showSoon() }
    }

    private func release() {
        repeats.values.forEach { $0.cancel() }
        repeats = [:]
        held = [:]
        pushed = [:]
    }

    /// A held direction moves once, then repeats after a short pause. A gamepad holds one
    /// direction: its D-pad and stick pushed the same way are one push with one repeat.
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
        let (delay, interval) = (repeatDelay, repeatInterval)
        repeats[pad] = Task { [weak self] in
            try? await Task.sleep(for: delay)
            while !Task.isCancelled {
                self?.move(now)
                try? await Task.sleep(for: interval)
            }
        }
    }

    /// The selection, if it's on the screen in front.
    private var current: String? { selected.flatMap { targets[$0]?.scope == scope ? $0 : nil } }

    func move(_ direction: MoveDirection) {
        guard let key = current, let target = targets[key] else { return selectDefault() }
        if target.handles.contains(direction.axis) { return commands.send((key, .move(direction))) }
        let others = targets.filter { $0.key != key && $0.value.scope == scope }.map { (id: $0.key, frame: $0.value.frame) }
        if let next = direction.nearest(from: target.frame, among: others) { select(next) }
    }

    func activate() {
        guard let key = current else { return selectDefault() }
        commands.send((key, .activate))
    }

    func select(_ key: String) {
        selected = key
        remembered[scope] = key
        reveal(key)
    }

    /// Scrolls whatever holds the item so it sits in the middle, the innermost scroll view
    /// first (a row of covers, then the page). Centred, the items around it are drawn too:
    /// lazy grids and lists only make what's on screen.
    private func reveal(_ key: String) {
        guard connected, var frame = targets[key]?.frame,
              let window = UIApplication.shared.connectedScenes.compactMap({ ($0 as? UIWindowScene)?.keyWindow }).first
        else { return }
        let centre = CGPoint(x: frame.midX, y: frame.midY)
        var holders: [UIScrollView] = []
        func collect(_ view: UIView) {
            if let scroll = view as? UIScrollView, !scroll.isHidden, scroll.isScrollEnabled,
               scroll.convert(CGRect(origin: .zero, size: scroll.contentSize), to: nil).contains(centre) {
                holders.append(scroll)
            }
            view.subviews.forEach(collect)
        }
        collect(window)
        for scroll in holders.reversed() {
            let inset = scroll.adjustedContentInset
            let visible = scroll.convert(scroll.bounds.inset(by: inset), to: nil)
            let room = CGSize(width: scroll.contentSize.width + inset.left + inset.right - scroll.bounds.width,
                              height: scroll.contentSize.height + inset.top + inset.bottom - scroll.bounds.height)
            var offset = scroll.contentOffset
            if room.width > 0 { offset.x = min(max(offset.x + frame.midX - visible.midX, -inset.left), room.width - inset.left) }
            if room.height > 0 { offset.y = min(max(offset.y + frame.midY - visible.midY, -inset.top), room.height - inset.top) }
            let moved = CGPoint(x: offset.x - scroll.contentOffset.x, y: offset.y - scroll.contentOffset.y)
            guard moved != .zero else { continue }
            scroll.setContentOffset(offset, animated: true)
            frame = frame.offsetBy(dx: -moved.x, dy: -moved.y)
        }
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

    private func scopeChanged() {
        selected = remembered[scope]
        showSoon()
    }

    /// Shows a selection once the screen's items have laid out.
    private func showSoon() {
        guard connected else { return }
        Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(350))
            guard let self, self.connected, self.current == nil else { return }
            self.selectDefault()
        }
    }

    func update(_ key: String, _ target: Target) { targets[key] = target }

    func remove(_ key: String, token: UUID) {
        if targets[key]?.token == token { targets[key] = nil }
    }
}

private struct FocusScopeKey: EnvironmentKey {
    static let defaultValue = "library"
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
    @State private var token = UUID()
    @State private var frame: CGRect?
    let id: String
    let handles: Axis.Set
    let isDefault: Bool
    let corner: CGFloat
    let inset: CGFloat
    let action: () -> Void
    let move: (MoveDirection) -> Void

    private var key: String { "\(scope)/\(id)" }

    func body(content: Content) -> some View {
        content
            .overlay {
                if focus.connected && focus.selected == key {
                    RoundedRectangle(cornerRadius: corner, style: .continuous)
                        .strokeBorder(Color.padMintLight, lineWidth: 3)
                        .shadow(color: .padMint.opacity(0.6), radius: 6)
                        .padding(-inset)
                        .allowsHitTesting(false)
                        .accessibilityHidden(true)
                }
            }
            .onGeometryChange(for: CGRect.self) { $0.frame(in: .global) } action: { new in
                frame = new
                register()
            }
            .onAppear { register() }
            .onDisappear { focus.remove(key, token: token) }
            .onReceive(focus.commands) { command in
                guard command.key == key else { return }
                switch command.command {
                case .activate: action()
                case .move(let direction): move(direction)
                }
            }
    }

    private func register() {
        guard let frame else { return }
        focus.update(key, .init(frame: frame, scope: scope, handles: handles, isDefault: isDefault, token: token))
    }
}

extension View {
    /// Lets a game controller select this item and press it with A.
    func controllerFocus(_ id: String, isDefault: Bool = false, corner: CGFloat = 14, inset: CGFloat = 5,
                         handles: Axis.Set = [], move: @escaping (MoveDirection) -> Void = { _ in },
                         action: @escaping () -> Void) -> some View {
        modifier(ControllerFocusable(id: id, handles: handles, isDefault: isDefault, corner: corner, inset: inset,
                                     action: action, move: move))
    }
}

extension CaseIterable where Self: Equatable {
    /// The next choice, wrapping around: what A does on a picker.
    var next: Self {
        let all = Array(Self.allCases)
        return all[((all.firstIndex(of: self) ?? 0) + 1) % all.count]
    }
}
