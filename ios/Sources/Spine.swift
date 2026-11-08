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
            // One look for every big box: black spine and white title, coloured by an accent
            // band below. The cover's average colour made each spine a different muddy shade.
            (base, ink) = (UIColor(white: 0.07, alpha: 1), .white)
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
            // Every spine has a top section holding the console's name, then the title below
            // it; the two never share space. Sizes are measured, not guessed.
            let labelColor: UIColor
            switch kind {
            case .xboxCase: labelColor = .white
            case .bigBox: labelColor = cover.luminance > 0.6 ? UIColor(white: 0.08, alpha: 1) : .white
            default: labelColor = ink.withAlphaComponent(0.7)
            }
            var labelSize = min(24, size.width * 0.3)
            var label = consoleLabel(game.platform, labelSize, labelColor)
            while label.size().width > 170, labelSize > 9 {  // keep the section short
                labelSize -= 1
                label = consoleLabel(game.platform, labelSize, labelColor)
            }
            let top = label.size().width + 56
            switch kind {
            case .xboxCase:
                UIColor(red: 0.30, green: 0.66, blue: 0.13, alpha: 1).setFill()
                cg.fill(CGRect(x: 0, y: 0, width: size.width, height: top))
            case .bigBox:
                // An accent band in the cover's most vivid colour, as printed spines have.
                cover.setFill()
                cg.fill(CGRect(x: 0, y: 0, width: size.width, height: top))
                cg.fill(CGRect(x: 0, y: size.height - 24, width: size.width, height: 24))
            default:
                ink.withAlphaComponent(0.35).setFill()
                cg.fill(CGRect(x: size.width * 0.18, y: top - 2, width: size.width * 0.64, height: 2))
            }
            if kind == .whiteCase {
                UIColor(white: 0.82, alpha: 1).setFill()
                cg.fill(CGRect(x: size.width - 6, y: 0, width: 6, height: size.height))
            }
            drawVertical(label, in: CGRect(x: 0, y: 28, width: size.width, height: top - 56), context: cg)
            // The title, below the top section, shrunk until it fits with margin at both ends.
            let start = top + 36
            let available = size.height - start - 60
            var fontSize = min(size.width * 0.56, 70)
            var title = NSAttributedString(string: game.title, attributes: titleAttributes(fontSize, ink))
            while (title.size().width > available || title.size().height > size.width * 0.86), fontSize > 12 {
                fontSize -= 1
                title = NSAttributedString(string: game.title, attributes: titleAttributes(fontSize, ink))
            }
            drawVertical(title, in: CGRect(x: 0, y: start, width: size.width, height: available), context: cg)
        }
        cache[key] = image
        return image
    }

    private static func consoleLabel(_ platform: String, _ size: CGFloat, _ color: UIColor) -> NSAttributedString {
        NSAttributedString(string: platform.uppercased(), attributes: [
            .font: UIFont.systemFont(ofSize: size, weight: .heavy), .foregroundColor: color, .kern: 1.2,
        ])
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

    static func back(platform: String, cover: UIColor) -> UIColor {
        switch kind(platform) {
        case .whiteCase: UIColor(white: 0.9, alpha: 1)
        default: UIColor(white: 0.08, alpha: 1)
        }
    }

    static func lid(platform: String, cover: UIColor) -> UIColor {
        switch kind(platform) {
        case .whiteCase: UIColor(white: 0.86, alpha: 1)
        default: UIColor(white: 0.11, alpha: 1)
        }
    }
}

extension UIImage {
    /// The cover's strongest colour (saturated and bright), for a spine's accent band.
    var vividColor: UIColor? {
        let side = 12
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let small = UIGraphicsImageRenderer(size: CGSize(width: side, height: side), format: format)
            .image { _ in draw(in: CGRect(x: 0, y: 0, width: side, height: side)) }
        guard let cg = small.cgImage, let data = cg.dataProvider?.data, let bytes = CFDataGetBytePtr(data) else { return nil }
        var best: (score: CGFloat, color: UIColor)?
        for y in 0..<cg.height {
            for x in 0..<cg.width {
                let offset = y * cg.bytesPerRow + x * (cg.bitsPerPixel / 8)
                let color = UIColor(red: CGFloat(bytes[offset]) / 255, green: CGFloat(bytes[offset + 1]) / 255,
                                    blue: CGFloat(bytes[offset + 2]) / 255, alpha: 1)
                var hue: CGFloat = 0, saturation: CGFloat = 0, brightness: CGFloat = 0, alpha: CGFloat = 0
                color.getHue(&hue, saturation: &saturation, brightness: &brightness, alpha: &alpha)
                let score = saturation * brightness
                if score > (best?.score ?? -1) { best = (score, color) }
            }
        }
        guard let best, best.score > 0.25 else { return nil }
        return best.color
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

