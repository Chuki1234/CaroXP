"""Launch the Python web app inside a native desktop window."""
from threading import Thread

from app import create_server


def main():
    try:
        import webview
    except ImportError:
        raise SystemExit('Hãy cài thư viện: python3 -m pip install -r requirements.txt')
    server = create_server(port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        class DesktopBridge:
            # Frame (x, y, width, height) before grow(); restored by shrink().
            _saved = None

            def minimize(self):
                webview.windows[0].minimize()

            def grow(self, extra):
                """Make the window `extra` px taller (for the detailed rules), within the screen."""
                window, screen = webview.windows[0], webview.screens[0]
                x, y, width, height = window.x, window.y, window.width, window.height
                target = min(height + max(0, int(extra)), int(screen.height) - 50)
                if target <= height:
                    return False
                if DesktopBridge._saved is None:
                    DesktopBridge._saved = (x, y, width, height)
                window.resize(width, target)
                # Keep the bottom edge on screen by moving the window up if needed.
                if y + target > screen.height - 10:
                    window.move(x, max(30, int(screen.height) - target - 10))
                return True

            def shrink(self):
                """Undo grow(), unless the player has resized the window since."""
                saved, DesktopBridge._saved = DesktopBridge._saved, None
                window = webview.windows[0]
                if saved and window.width == saved[2]:
                    window.resize(saved[2], saved[3])
                    window.move(saved[0], saved[1])

        webview.create_window(
            'Caro XP', url, width=700, height=632, min_size=(660, 600),
            background_color='#ece9d8', js_api=DesktopBridge(),
        )
        webview.start()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == '__main__':
    main()
