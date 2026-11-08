// Render Icon/AppIcon.svg into the app icon: swift scripts/render-icon.swift
// Same approach as PadMint's macos/icon.swift. iOS wants an opaque 1024 px icon; the
// SVG fills every pixel, so flatten afterwards: magick AppIcon.png -alpha off AppIcon.png
import AppKit

let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
guard let image = NSImage(contentsOf: root.appendingPathComponent("Icon/AppIcon.svg")) else { exit(2) }
let size = 1024
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8,
                           samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
                           bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
image.draw(in: NSRect(x: 0, y: 0, width: size, height: size))
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!
    .write(to: root.appendingPathComponent("Assets.xcassets/AppIcon.appiconset/AppIcon.png"))
