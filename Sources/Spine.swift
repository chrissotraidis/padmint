import UIKit

/// The sides of a game box, drawn like the real ones: the title running down the spine,
/// the console's name in plain type (no logos), and the case's own colours.
@MainActor
enum Spine {
    enum Kind { case blackCase, whiteCase, jewelCase, xboxCase, bigBox }

    static func kind(_ platform: String) -> Kind {
        switch platform {
        case "GameCube", "PlayStation 2": .blackCase
        case "Wii": .whiteCase
        case "Xbox": .xboxCase
        case "PlayStation": .jewelCase
        default: .bigBox  // Nintendo 64 and PC: printed card
        }
    }

    private static var cache: [String: UIImage] = [:]

    /// The left face: the spine you read on a shelf, title running top to bottom.
    static func image(game: Game, cover: UIColor, length: CGFloat, depth: CGFloat) -> UIImage {
        let key = "\(game.id)-\(length)-\(depth)-\(cover.hashValue)"
        if let cached = cache[key] { return cached }
        let kind = kind(game.platform)
        // The face is depth wide and length tall in the scene; draw it at 1024 px tall.
        let size = CGSize(width: max(80, 1024 * depth / length), height: 1024)
        let base: UIColor
        let ink: UIColor
        switch kind {
        case .blackCase, .xboxCase: (base, ink) = (UIColor(white: 0.07, alpha: 1), .white)
        case .whiteCase: (base, ink) = (UIColor(white: 0.95, alpha: 1), UIColor(white: 0.12, alpha: 1))
        case .jewelCase: (base, ink) = (UIColor(white: 0.1, alpha: 1), .white)
        case .bigBox:
            base = cover.adjusted(brightness: 0.8).adjusted(saturation: 1.15)
            ink = cover.luminance > 0.55 ? UIColor(white: 0.08, alpha: 1) : .white
        }
        let image = UIGraphicsImageRenderer(size: size).image { context in
            let cg = context.cgContext
            base.setFill()
            cg.fill(CGRect(origin: .zero, size: size))
            // A soft sheen across the spine, like light on card or plastic.
            let sheen = CGGradient(colorsSpace: nil, colors: [UIColor(white: 1, alpha: 0.10).cgColor,
                                                             UIColor(white: 1, alpha: 0).cgColor,
                                                             UIColor(white: 0, alpha: 0.18).cgColor] as CFArray,
                                   locations: [0, 0.45, 1])!
            cg.drawLinearGradient(sheen, start: .zero, end: CGPoint(x: size.width, y: 0), options: [])
            var top: CGFloat = 0
            if kind == .xboxCase {
                UIColor(red: 0.30, green: 0.66, blue: 0.13, alpha: 1).setFill()
                cg.fill(CGRect(x: 0, y: 0, width: size.width, height: 150))
                top = 150
            }
            if kind == .bigBox {
                // Coloured bands at both ends, as printed spines have.
                cover.adjusted(brightness: 0.45).setFill()
                cg.fill(CGRect(x: 0, y: 0, width: size.width, height: 110))
                cg.fill(CGRect(x: 0, y: size.height - 70, width: size.width, height: 70))
                top = 110
            }
            if kind == .whiteCase {
                UIColor(white: 0.82, alpha: 1).setFill()
                cg.fill(CGRect(x: size.width - 6, y: 0, width: 6, height: size.height))
            }
            // Console name, small, across the top band.
            let label = NSAttributedString(string: game.platform.uppercased(), attributes: [
                .font: UIFont.systemFont(ofSize: min(26, size.width * 0.16), weight: .heavy),
                .foregroundColor: kind == .xboxCase ? UIColor.white : ink.withAlphaComponent(0.75),
                .kern: 1.5,
            ])
            drawVertical(label, in: CGRect(x: 0, y: 14, width: size.width, height: max(top - 20, 120)), context: cg)
            // The title, running down the rest of the spine.
            let available = size.height - top - 140
            var fontSize = min(size.width * 0.5, 64)
            var title = NSAttributedString(string: game.title, attributes: titleAttributes(fontSize, ink))
            while title.size().width > available, fontSize > 14 {
                fontSize -= 2
                title = NSAttributedString(string: game.title, attributes: titleAttributes(fontSize, ink))
            }
            drawVertical(title, in: CGRect(x: 0, y: top + 40, width: size.width, height: available), context: cg)
        }
        cache[key] = image
        return image
    }

    private static func titleAttributes(_ size: CGFloat, _ ink: UIColor) -> [NSAttributedString.Key: Any] {
        [.font: UIFont.systemFont(ofSize: size, weight: .bold), .foregroundColor: ink]
    }

    /// Draws text rotated to run top to bottom, centred in the rect.
    private static func drawVertical(_ text: NSAttributedString, in rect: CGRect, context: CGContext) {
        let textSize = text.size()
        context.saveGState()
        context.translateBy(x: rect.midX, y: rect.minY)
        context.rotate(by: .pi / 2)
        text.draw(at: CGPoint(x: 0, y: -textSize.height / 2))
        context.restoreGState()
    }

    /// The right face: a big box's printed side, or a case's hinge.
    static func side(platform: String, cover: UIColor) -> UIColor {
        switch kind(platform) {
        case .bigBox: cover.adjusted(brightness: 0.6)
        case .whiteCase: UIColor(white: 0.88, alpha: 1)
        default: UIColor(white: 0.09, alpha: 1)
        }
    }

    static func back(platform: String, cover: UIColor) -> UIColor {
        switch kind(platform) {
        case .bigBox: cover.adjusted(brightness: 0.4)
        case .whiteCase: UIColor(white: 0.9, alpha: 1)
        default: UIColor(white: 0.08, alpha: 1)
        }
    }

    static func lid(platform: String, cover: UIColor) -> UIColor {
        switch kind(platform) {
        case .bigBox: cover.adjusted(brightness: 0.5)
        case .whiteCase: UIColor(white: 0.86, alpha: 1)
        default: UIColor(white: 0.11, alpha: 1)
        }
    }
}

extension UIColor {
    func adjusted(saturation factor: CGFloat) -> UIColor {
        var hue: CGFloat = 0, saturation: CGFloat = 0, brightness: CGFloat = 0, alpha: CGFloat = 0
        getHue(&hue, saturation: &saturation, brightness: &brightness, alpha: &alpha)
        return UIColor(hue: hue, saturation: min(1, saturation * factor), brightness: brightness, alpha: alpha)
    }

    var luminance: CGFloat {
        var red: CGFloat = 0, green: CGFloat = 0, blue: CGFloat = 0, alpha: CGFloat = 0
        getRed(&red, green: &green, blue: &blue, alpha: &alpha)
        return 0.299 * red + 0.587 * green + 0.114 * blue
    }
}

