#if DEBUG
import SceneKit
import SwiftUI

/// Debug only: every game's box in one scene, turned to show a spine, to check them all
/// at once. Launch with -boxGallery 40 (right spines) or -boxGallery -40 (left spines).
struct BoxGallery: UIViewRepresentable {
    let games: [Game]
    let faces: (Game) -> BoxFaces
    let yaw: Double

    func makeUIView(context: Context) -> StageView {
        let (scene, camera) = GameBox.stage()
        let columns = 4
        for (index, game) in games.enumerated() {
            let node = GameBox.make(faces: faces(game), game: game)
            node.position = SCNVector3(Float(index % columns) * 1.6, Float(-(index / columns)) * 1.5, 0)
            node.eulerAngles.y = Float(yaw * .pi / 180)
            scene.rootNode.addChildNode(node)
        }
        let rows = (games.count + columns - 1) / columns
        camera.position = SCNVector3(Float(columns - 1) * 0.8, Float(-(rows - 1)) * 0.75 + 0.5, 4.2 + Float(rows) * 1.3)
        camera.camera?.fieldOfView = 50
        return GameBox.view(scene: scene, camera: camera)
    }

    func updateUIView(_ view: StageView, context: Context) {}
}
#endif

