import SwiftUI

@main
struct PadMintLibraryApp: App {
    @StateObject private var library = LibraryModel()
    @StateObject private var covers = CoverStore()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            LibraryView()
                .environmentObject(library)
                .environmentObject(covers)
                .task {
                    await covers.fetch(library.games)
                    await library.refresh()
                    await covers.fetch(library.games)
                }
                // A game installed or deleted while PadMint was in the background.
                .onChange(of: scenePhase) { _, phase in
                    if phase == .active { library.checkInstalled() }
                }
        }
    }
}

