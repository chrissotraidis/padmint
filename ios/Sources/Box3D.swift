import SceneKit
import SwiftUI
import UIKit

/// The printed faces of a game box. A missing back or spine is drawn by the app.
struct BoxFaces {
    var front: UIImage?
    var back: UIImage? = nil
    var spine: UIImage? = nil

    /// Changes when any face's picture changes, so a box is redressed only then.
    var identity: [ObjectIdentifier?] { [front, back, spine].map { $0.map(ObjectIdentifier.init) } }
}

/// Game cases in 3D: the cover on the front, spines cut from the cover's edges, and a
/// depth that matches the console (deep N64 and PC big boxes, slim disc cases).
@MainActor
enum GameBox {
    static func depth(for platform: String) -> CGFloat {
        switch platform {
        case "Nintendo 64", "PC": 0.22
        case "PlayStation": 0.09
        default: 0.075
        }
    }

    /// Width and height in scene units: tall cases are 1 high, wide boxes 1.25 wide.
    static func size(for image: UIImage?) -> (width: CGFloat, height: CGFloat) {
        let aspect = image.map { $0.size.width / max($0.size.height, 1) } ?? 0.71
        return aspect >= 1 ? (1.25, 1.25 / aspect) : (aspect, 1)
    }

    /// A holder node (placed by the caller) with the box as its child, standing on y = 0.
    static func make(faces: BoxFaces, game: Game) -> SCNNode {
        let holder = SCNNode()
        let box = SCNNode()
        box.name = "box"
        holder.addChildNode(box)
        dress(holder, faces: faces, game: game)
        return holder
    }

    static func dress(_ holder: SCNNode, faces: BoxFaces, game: Game) {
        guard let box = holder.childNode(withName: "box", recursively: false) else { return }
        let image = faces.front
        let platform = game.platform
        let (width, height) = size(for: image)
        let depth = depth(for: platform) * max(height, 0.8)
        let geometry = SCNBox(width: width, height: height, length: depth, chamferRadius: min(depth, width) * 0.08)
        let average = image?.averageColor ?? UIColor(red: 0.13, green: 0.74, blue: 0.48, alpha: 1)
        let accent = image?.vividColor ?? average
        let spine: UIImage = faces.spine ?? Spine.image(game: game, cover: accent, length: height, depth: depth)
        let lid = Spine.lid(platform: platform, cover: average)
        geometry.materials = [
            material(image ?? average, gloss: true),                         // front
            material(spine),                                                 // right: spine too, so boxes on either side show it
            material(faces.back ?? Spine.back(platform: platform, cover: average), gloss: faces.back != nil),  // back
            material(spine),                                                 // left: the printed spine
            material(lid),                                                   // top
            material(lid),                                                   // bottom
        ]
        box.geometry = geometry
        box.position = SCNVector3(0, Float(height / 2), 0)
        // A faint mirror image under the box stands in for a reflective floor; as a child
        // of the box it turns and spins with it.
        box.childNode(withName: "reflection", recursively: false)?.removeFromParentNode()
        if UserDefaults.standard.flag("reflections") {
            let reflection = SCNNode(geometry: geometry)
            reflection.name = "reflection"
            reflection.scale = SCNVector3(1, -1, 1)
            reflection.position = SCNVector3(0, Float(-height) - 0.004, 0)
            reflection.opacity = 0.22
            box.addChildNode(reflection)
        }
    }

    private static func material(_ contents: Any, gloss: Bool = false) -> SCNMaterial {
        let material = SCNMaterial()
        material.diffuse.contents = contents
        material.lightingModel = .blinn
        material.specular.contents = UIColor(white: gloss ? 0.45 : 0.15, alpha: 1)
        material.shininess = gloss ? 0.7 : 0.2
        material.locksAmbientWithDiffuse = true
        material.isDoubleSided = true  // the mirrored reflection shows its inner faces
        return material
    }

    /// A stage with soft lights; the background stays clear so the blurred cover behind
    /// the view shows through.
    static func stage() -> (scene: SCNScene, camera: SCNNode) {
        let scene = SCNScene()
        let ambient = SCNNode()
        ambient.light = SCNLight()
        ambient.light?.type = .ambient
        ambient.light?.intensity = 650
        scene.rootNode.addChildNode(ambient)
        let key = SCNNode()
        key.light = SCNLight()
        key.light?.type = .directional
        key.light?.intensity = 650
        key.eulerAngles = SCNVector3(-0.5, 0.45, 0)
        scene.rootNode.addChildNode(key)
        let camera = SCNNode()
        camera.camera = SCNCamera()
        camera.camera?.fieldOfView = 30
        camera.camera?.wantsHDR = false
        scene.rootNode.addChildNode(camera)
        return (scene, camera)
    }

    static func view(scene: SCNScene, camera: SCNNode) -> StageView {
        let view = StageView(frame: .zero, options: nil)
        view.scene = scene
        view.pointOfView = camera
        view.backgroundColor = .clear
        view.antialiasingMode = .multisampling4X
        view.preferredFramesPerSecond = 60
        return view
    }

    /// Whether boxes may sway at rest: the player's setting, and never with Reduce Motion.
    static var motion: Bool {
        (UserDefaults.standard.flag("boxMotion")) && !UIAccessibility.isReduceMotionEnabled
    }

    /// A resting box sways for three slow cycles, then settles: after that nothing moves,
    /// so nothing is drawn and the stage costs no power.
    static let swayTime: TimeInterval = 3 * 4.8 + 1.2

    @discardableResult
    static func sway(_ holder: SCNNode, on: Bool) -> Bool {
        guard let box = holder.childNode(withName: "box", recursively: false) else { return false }
        if on && motion {
            guard box.action(forKey: "sway") == nil else { return false }
            let left = SCNAction.rotateTo(x: 0, y: 0.16, z: 0, duration: 2.4, usesShortestUnitArc: true)
            let right = SCNAction.rotateTo(x: 0, y: -0.16, z: 0, duration: 2.4, usesShortestUnitArc: true)
            let settle = SCNAction.rotateTo(x: 0, y: 0, z: 0, duration: 1.2, usesShortestUnitArc: true)
            left.timingMode = .easeInEaseOut
            right.timingMode = .easeInEaseOut
            settle.timingMode = .easeInEaseOut
            box.runAction(.sequence([.repeat(.sequence([left, right]), count: 3), settle]), forKey: "sway")
            return true
        } else {
            box.removeAction(forKey: "sway")
            box.runAction(.rotateTo(x: 0, y: 0, z: 0, duration: 0.3, usesShortestUnitArc: true))
            return false
        }
    }
}

/// An SCNView that reports its size, so the camera can frame the boxes for it.
final class StageView: SCNView {
    var onResize: ((CGSize) -> Void)?
    private var lastSize: CGSize = .zero
    private var active = true
    private var holding = false
    private var busyUntil = Date.distantPast

    override init(frame: CGRect, options: [String: Any]? = nil) {
        super.init(frame: frame, options: options)
        let center = NotificationCenter.default
        center.addObserver(self, selector: #selector(stagePause), name: UIApplication.didEnterBackgroundNotification, object: nil)
        center.addObserver(self, selector: #selector(stageResume), name: UIApplication.willEnterForegroundNotification, object: nil)
    }

    required init?(coder: NSCoder) { super.init(coder: coder) }

    /// Plays (and draws) only while on screen with the app in front: a hidden carousel or
    /// a page you've left costs nothing.
    override func didMoveToWindow() {
        super.didMoveToWindow()
        update()
    }

    @objc private func stagePause() { active = false; update() }
    @objc private func stageResume() { active = true; update() }

    /// Keep drawing for a while: a box is sliding, spinning or swaying.
    func play(for seconds: TimeInterval) {
        busyUntil = max(busyUntil, Date().addingTimeInterval(seconds))
        update()
        DispatchQueue.main.asyncAfter(deadline: .now() + seconds + 0.05) { [weak self] in self?.update() }
    }

    /// Keep drawing while a finger is on the stage.
    func hold(_ on: Bool) {
        holding = on
        update()
    }

    private func update() {
        let wanted = window != nil && active && (holding || Date() < busyUntil)
        if isPlaying != wanted { isPlaying = wanted }
        if !wanted { setNeedsDisplay() }  // draw the final resting frame
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        if bounds.size != lastSize, bounds.width > 0 {
            lastSize = bounds.size
            onResize?(bounds.size)
        }
    }
}

/// Cover flow with real boxes: swipe to move, tap a side box to bring it forward, tap the
/// front box to open its page, double-tap it to spin it.
struct CoverFlow3D: UIViewRepresentable {
    let games: [Game]
    @Binding var focused: Int
    let faces: (Game) -> BoxFaces
    let open: (Game) -> Void

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    func makeUIView(context: Context) -> StageView {
        let coordinator = context.coordinator
        let view = GameBox.view(scene: coordinator.scene, camera: coordinator.camera)
        view.onResize = { [weak coordinator] size in coordinator?.fit(size) }
        view.addGestureRecognizer(UIPanGestureRecognizer(target: coordinator, action: #selector(Coordinator.pan)))
        let double = UITapGestureRecognizer(target: coordinator, action: #selector(Coordinator.spin))
        double.numberOfTapsRequired = 2
        view.addGestureRecognizer(double)
        let tap = UITapGestureRecognizer(target: coordinator, action: #selector(Coordinator.tap))
        tap.require(toFail: double)
        view.addGestureRecognizer(tap)
        coordinator.view = view
        coordinator.sync(animated: false)
        return view
    }

    func updateUIView(_ view: StageView, context: Context) {
        context.coordinator.parent = self
        context.coordinator.sync(animated: true)
    }

    @MainActor
    final class Coordinator: NSObject {
        var parent: CoverFlow3D
        let scene: SCNScene
        let camera: SCNNode
        weak var view: StageView?
        private var nodes: [String: SCNNode] = [:]
        private var dressedWith: [String: [ObjectIdentifier?]] = [:]
        private var order: [String] = []
        private var offset: CGFloat = 0
        private var panStart: CGFloat = 0
        private var panning = false
        private var swaying: String?
        /// Half the visible width at the boxes, to skip drawing boxes off screen.
        private var halfWidth: CGFloat = 3
        private let haptics = UISelectionFeedbackGenerator()

        init(parent: CoverFlow3D) {
            self.parent = parent
            (scene, camera) = GameBox.stage()
            super.init()
            fit(CGSize(width: 1000, height: 800))
        }

        /// Frames the front box large: three quarters of the stage height for a tall case,
        /// and a wide N64 box within 80% of the width. Side boxes fill the rest.
        func fit(_ size: CGSize) {
            let aspect = size.width / max(size.height, 1)
            let viewHeightPerUnit = 2 * tan(CGFloat(15) * .pi / 180)  // field of view 30°
            let distance = max(1.0 / (0.66 * viewHeightPerUnit), 1.25 / (0.6 * viewHeightPerUnit * aspect))
            camera.position = SCNVector3(0, 0.62, Float(distance))
            camera.look(at: SCNVector3(0, 0.4, 0))
            let halfWidth = viewHeightPerUnit * distance * aspect / 2
            self.halfWidth = halfWidth
            layout()
        }

        func sync(animated: Bool) {
            let games = parent.games
            let ids = games.map(\.id)
            for (id, node) in nodes where !ids.contains(id) {
                node.removeFromParentNode()
                nodes[id] = nil
                dressedWith[id] = nil
            }
            for game in games {
                let faces = parent.faces(game)
                let identity = faces.identity
                if let node = nodes[game.id] {
                    if dressedWith[game.id] != identity {
                        GameBox.dress(node, faces: faces, game: game)
                        view?.play(for: 0.2)  // a cover arrived while resting
                    }
                } else {
                    let node = GameBox.make(faces: faces, game: game)
                    scene.rootNode.addChildNode(node)
                    nodes[game.id] = node
                }
                dressedWith[game.id] = identity
            }
            order = ids
            guard !panning else { return }
            let target = CGFloat(min(max(parent.focused, 0), max(ids.count - 1, 0)))
            if animated && target != offset { move(to: target) } else { offset = target; layout() }
        }

        private func size(_ id: String) -> (width: CGFloat, depth: CGFloat) {
            guard let box = nodes[id]?.childNode(withName: "box", recursively: false)?.geometry as? SCNBox
            else { return (0.71, 0.1) }
            return (box.width, box.length)
        }

        /// Where every box stands while `focus` is in front: the front box faces you, and the
        /// others stand like books on a shelf, spine out, each spaced by its own thickness so
        /// no box covers another.
        private func slots(focus: Int) -> [(x: CGFloat, z: CGFloat, yaw: CGFloat)] {
            var result = Array(repeating: (x: CGFloat(0), z: CGFloat(0), yaw: CGFloat(0)), count: order.count)
            guard order.indices.contains(focus) else { return result }
            // Spines all sit on one plane (z = shelf); a box's centre is half its width
            // behind it, so a wide N64 box can't stick out and cover its neighbours.
            let gap: CGFloat = 0.16, between: CGFloat = 0.012, shelf: CGFloat = -0.05
            let half = size(order[focus]).width / 2
            var edge = half + gap
            for index in stride(from: focus + 1, to: order.count, by: 1) {
                let box = size(order[index])
                result[index] = (edge + box.depth / 2, shelf - box.width / 2, -.pi / 2)  // a spine toward you
                edge += box.depth + between
            }
            edge = half + gap
            for index in stride(from: focus - 1, through: 0, by: -1) {
                let box = size(order[index])
                result[index] = (-(edge + box.depth / 2), shelf - box.width / 2, .pi / 2)
                edge += box.depth + between
            }
            return result
        }

        /// Places the boxes for the current (possibly fractional) offset, moving smoothly
        /// between the shelf layouts of the two nearest games.
        private func layout() {
            guard !order.isEmpty else { return }
            let clamped = max(0, min(CGFloat(order.count - 1), offset))
            let low = Int(clamped.rounded(.down)), high = min(low + 1, order.count - 1)
            let t = clamped - CGFloat(low)
            let from = slots(focus: low), to = slots(focus: high)
            for (index, id) in order.enumerated() {
                guard let node = nodes[id] else { continue }
                let a = from[index], b = to[index]
                let x = a.x + (b.x - a.x) * t
                node.position = SCNVector3(Float(x), 0, Float(a.z + (b.z - a.z) * t))
                node.eulerAngles = SCNVector3(0, Float(a.yaw + (b.yaw - a.yaw) * t), 0)
                node.isHidden = abs(x) > halfWidth + 1
            }
            // Only the front box sways, and only while it rests.
            let front = panning || order.isEmpty ? nil : order[max(0, min(order.count - 1, Int(offset.rounded())))]
            if front != swaying {
                if let old = swaying, let node = nodes[old] { GameBox.sway(node, on: false) }
                if let front, let node = nodes[front], GameBox.sway(node, on: true) { view?.play(for: GameBox.swayTime) }
                swaying = front
            }
        }

        private func move(to target: CGFloat) {
            SCNTransaction.begin()
            SCNTransaction.animationDuration = 0.5
            view?.play(for: 0.6)
            SCNTransaction.animationTimingFunction = CAMediaTimingFunction(controlPoints: 0.2, 0.9, 0.25, 1)
            offset = target
            layout()
            SCNTransaction.commit()
        }

        private func focus(_ index: Int) {
            move(to: CGFloat(index))
            if parent.focused != index { parent.focused = index }
        }

        @objc func pan(_ gesture: UIPanGestureRecognizer) {
            guard let view = gesture.view, !order.isEmpty else { return }
            let unit = view.bounds.width * 0.2
            switch gesture.state {
            case .began:
                panStart = offset
                panning = true
                (view as? StageView)?.hold(true)
            case .changed:
                SCNTransaction.begin()
                SCNTransaction.disableActions = true
                let before = Int(offset.rounded())
                offset = max(-0.45, min(CGFloat(order.count) - 0.55, panStart - gesture.translation(in: view).x / unit))
                layout()
                SCNTransaction.commit()
                if Int(offset.rounded()) != before, UserDefaults.standard.flag("haptics") {
                    haptics.selectionChanged()
                }
            default:
                panning = false
                (view as? StageView)?.hold(false)
                let flick = gesture.velocity(in: view).x / unit * 0.22
                focus(Int(max(0, min(CGFloat(order.count - 1), (offset - flick).rounded()))))
            }
        }

        @objc func tap(_ gesture: UITapGestureRecognizer) {
            guard let index = index(at: gesture) else { return }
            if index == parent.focused, parent.games.indices.contains(index) { parent.open(parent.games[index]) }
            else { focus(index) }
        }

        @objc func spin(_ gesture: UITapGestureRecognizer) {
            guard let index = index(at: gesture), index == parent.focused,
                  let box = nodes[order[index]]?.childNode(withName: "box", recursively: false) else { return }
            view?.play(for: 1)
            // The sway turns the box to fixed angles, which cancelled the spin while it ran.
            box.removeAction(forKey: "sway")
            box.runAction(.sequence([
                .rotateTo(x: 0, y: .pi * 2, z: 0, duration: 0.9, usesShortestUnitArc: false),
                .run { node in node.eulerAngles.y = 0 },
            ]))
        }

        private func index(at gesture: UIGestureRecognizer) -> Int? {
            guard let view else { return nil }
            let hit = view.hitTest(gesture.location(in: view), options: [.searchMode: SCNHitTestSearchMode.closest.rawValue]).first
            guard let holder = hit?.node.parent, let id = nodes.first(where: { $0.value == holder })?.key else { return nil }
            return order.firstIndex(of: id)
        }
    }
}

/// One game's box that you turn with your finger; it settles back and keeps swaying.
struct SpinningBox: UIViewRepresentable {
    let game: Game
    let faces: BoxFaces

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> StageView {
        let coordinator = context.coordinator
        let view = GameBox.view(scene: coordinator.scene, camera: coordinator.camera)
        coordinator.view = view
        view.addGestureRecognizer(UIPanGestureRecognizer(target: coordinator, action: #selector(Coordinator.pan)))
        coordinator.show(faces: faces, game: game)
        return view
    }

    func updateUIView(_ view: StageView, context: Context) {
        context.coordinator.show(faces: faces, game: game)
    }

    @MainActor
    final class Coordinator: NSObject {
        let scene: SCNScene
        let camera: SCNNode
        weak var view: StageView?
        private var holder: SCNNode?
        private var shown: [ObjectIdentifier?]?
        private var start: Float = 0

        override init() {
            (scene, camera) = GameBox.stage()
            super.init()
        }

        func show(faces: BoxFaces, game: Game) {
            let identity = faces.identity
            guard shown != identity else { return }
            shown = identity
            if holder == nil {
                let node = GameBox.make(faces: faces, game: game)
                scene.rootNode.addChildNode(node)
                holder = node
            } else if let holder {
                GameBox.dress(holder, faces: faces, game: game)
            }
            let (width, height) = GameBox.size(for: faces.front)
            // Frame the whole box, wide or tall.
            let distance = max(Float(height) * 2.3, Float(width) * 1.9) + 0.4
            camera.position = SCNVector3(0, Float(height) * 0.62, distance)
            camera.look(at: SCNVector3(0, Float(height) * 0.5, 0))
            view?.play(for: 0.5)
            if let holder, GameBox.sway(holder, on: true) { view?.play(for: GameBox.swayTime) }
        }

        @objc func pan(_ gesture: UIPanGestureRecognizer) {
            guard let holder, let view = gesture.view else { return }
            switch gesture.state {
            case .began:
                GameBox.sway(holder, on: false)
                self.view?.hold(true)
                holder.removeAllActions()
                start = holder.eulerAngles.y
            case .changed:
                holder.eulerAngles.y = start + Float(gesture.translation(in: view).x / view.bounds.width) * .pi * 1.6
            default:
                // Coast with the flick, then settle facing front.
                self.view?.hold(false)
                self.view?.play(for: 0.8)
                let coast = holder.eulerAngles.y + Float(gesture.velocity(in: view).x / view.bounds.width) * 0.6
                let turns = (coast / (.pi * 2)).rounded() * .pi * 2
                holder.runAction(.sequence([
                    .rotateTo(x: 0, y: CGFloat(turns), z: 0, duration: 0.7, usesShortestUnitArc: false),
                    .run { node in node.eulerAngles.y = 0 },
                ])) { [weak self] in
                    Task { @MainActor in
                        if let self, let holder = self.holder, GameBox.sway(holder, on: true) { self.view?.play(for: GameBox.swayTime) }
                    }
                }
            }
        }
    }
}

extension UIImage {
    /// The cover's average colour, for the back and edges of its box.
    var averageColor: UIColor? {
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: 1, height: 1), format: {
            let format = UIGraphicsImageRendererFormat()
            format.scale = 1
            return format
        }())
        let pixel = renderer.image { _ in draw(in: CGRect(x: 0, y: 0, width: 1, height: 1)) }
        guard let data = pixel.cgImage?.dataProvider?.data, let bytes = CFDataGetBytePtr(data) else { return nil }
        return UIColor(red: CGFloat(bytes[0]) / 255, green: CGFloat(bytes[1]) / 255, blue: CGFloat(bytes[2]) / 255, alpha: 1)
    }

    /// A thin strip from the cover's left or right edge, stretched over the spine.
    func edgeStrip(left: Bool) -> UIImage? {
        guard let cgImage else { return nil }
        let width = max(2, Int(Double(cgImage.width) * 0.035))
        let rect = CGRect(x: left ? 0 : cgImage.width - width, y: 0, width: width, height: cgImage.height)
        return cgImage.cropping(to: rect).map { UIImage(cgImage: $0) }
    }
}

extension UIColor {
    func adjusted(brightness factor: CGFloat) -> UIColor {
        var hue: CGFloat = 0, saturation: CGFloat = 0, brightness: CGFloat = 0, alpha: CGFloat = 0
        getHue(&hue, saturation: &saturation, brightness: &brightness, alpha: &alpha)
        return UIColor(hue: hue, saturation: saturation, brightness: brightness * factor, alpha: alpha)
    }
}

