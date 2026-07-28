import AppKit
import Foundation
import PDFKit

guard CommandLine.arguments.count == 3 else {
    fputs("usage: render_coregraphics.swift INPUT_DIR OUTPUT_DIR\n", stderr)
    exit(2)
}

let fileManager = FileManager.default
let input = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
try fileManager.createDirectory(at: output, withIntermediateDirectories: true)

let files = try fileManager.contentsOfDirectory(
    at: input,
    includingPropertiesForKeys: nil
).filter { $0.pathExtension.lowercased() == "pdf" }.sorted {
    $0.lastPathComponent < $1.lastPathComponent
}

guard files.count == 6 else {
    fatalError("Expected 6 PDFs, found \(files.count)")
}

for file in files {
    guard let document = PDFDocument(url: file), document.pageCount > 0 else {
        fatalError("Cannot open \(file.path)")
    }
    for index in 0..<document.pageCount {
        guard let page = document.page(at: index) else {
            fatalError("Cannot read page \(index + 1) of \(file.path)")
        }
        let image = page.thumbnail(
            of: NSSize(width: 1191, height: 1684),
            for: .mediaBox
        )
        guard
            let data = image.tiffRepresentation,
            let bitmap = NSBitmapImageRep(data: data),
            let png = bitmap.representation(using: .png, properties: [:])
        else {
            fatalError("Cannot render page \(index + 1) of \(file.path)")
        }
        let name = "\(file.deletingPathExtension().lastPathComponent)-\(index + 1).png"
        try png.write(to: output.appendingPathComponent(name))
    }
}

print("CoreGraphics rendered \(files.count) PDFs.")

