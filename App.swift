import Cocoa

final class DropView: NSView {
    var accept: ((URL) -> Void)?
    override init(frame: NSRect) {
        super.init(frame: frame)
        registerForDraggedTypes([.fileURL])
    }
    required init?(coder: NSCoder) { fatalError() }
    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation { .copy }
    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        guard let urls = sender.draggingPasteboard.readObjects(forClasses: [NSURL.self]) as? [URL],
              urls.count == 1 else { return false }
        accept?(urls[0]); return true
    }
}

final class App: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var status: NSTextField!
    var button: NSButton!
    var busy = false
    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 620, height: 410),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Welcome Email Splitter"
        let root = DropView(frame: window.contentView!.bounds)
        root.accept = { [weak self] url in self?.run(url) }
        window.contentView = root
        let title = NSTextField(labelWithString: "Drop your welcome email workbook here")
        title.font = .systemFont(ofSize: 22, weight: .semibold)
        title.frame = NSRect(x: 32, y: 335, width: 565, height: 32)
        root.addSubview(title)
        let subtitle = NSTextField(wrappingLabelWithString: "The original excel workbook will be split into two workbooks: \nSTUDENTS ONLY and NON-STUDENTS. The original is replaced.")
        subtitle.frame = NSRect(x: 32, y: 245, width: 555, height: 75)
        root.addSubview(subtitle)
        button = NSButton(title: "Choose Excel File…", target: self, action: #selector(choose))
        button.bezelStyle = .rounded
        button.frame = NSRect(x: 30, y: 195, width: 180, height: 36)
        root.addSubview(button)
        status = NSTextField(wrappingLabelWithString: "Ready for one .xlsx file.")
        status.frame = NSRect(x: 32, y: 25, width: 555, height: 155)
        status.font = .systemFont(ofSize: 13)
        root.addSubview(status)
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    @objc func choose() {
        let panel = NSOpenPanel()
        panel.allowedFileTypes = ["xlsx"]
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url { run(url) }
    }
    func run(_ url: URL) {
        guard !busy else { return }
        busy = true; button.isEnabled = false
        status.stringValue = "Splitting \(url.lastPathComponent)…"
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            let script = Bundle.main.resourceURL!.appendingPathComponent("split_emails.py").path
            process.arguments = ["python3", script, url.path]
            let pipe = Pipe()
            process.standardOutput = pipe; process.standardError = pipe
            var message: String
            do {
                try process.run()
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                message = String(data: data, encoding: .utf8) ?? "Unable to read result."
                if process.terminationStatus != 0 { message = "Could not split the workbook.\n\n" + message }
            } catch { message = "Unable to start Python 3: \(error.localizedDescription)" }
            DispatchQueue.main.async {
                self.status.stringValue = message
                self.busy = false; self.button.isEnabled = true
            }
        }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}
let app = NSApplication.shared
let delegate = App()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
