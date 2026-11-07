import SwiftUI

@main
struct PadMintLibraryApp: App {
    @StateObject private var library = LibraryModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            LibraryView()
                .environmentObject(library)
                .task { await library.refresh() }
                // A game installed or deleted while PadMint was in the background.
                .onChange(of: scenePhase) { _, phase in
                    if phase == .active { library.checkInstalled() }
                }
        }
    }
}
