import SwiftUI

@main
struct PadMintLibraryApp: App {
    @StateObject private var library = LibraryModel()
    @StateObject private var covers = CoverStore()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            root
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

    @ViewBuilder private var root: some View {
        #if DEBUG
        if UserDefaults.standard.object(forKey: "boxGallery") != nil {
            let yaw = UserDefaults.standard.double(forKey: "boxGallery")
            let console = UserDefaults.standard.string(forKey: "galleryConsole") ?? ""
            BoxGallery(games: library.sorted(library.games, by: .console, official: true)
                .filter { console.isEmpty || $0.platform == console },
                       image: { covers.image(for: $0) }, yaw: yaw)
                .background(Color(white: 0.25)).ignoresSafeArea()
        } else {
            LibraryView()
        }
        #else
        LibraryView()
        #endif
    }
}

