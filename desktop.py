"""Launch the Python web app inside a native desktop window."""
import time
from threading import Lock, Thread

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
            # Frame (x, y) before grow(); shrink() moves the window back there.
            _saved = None
            # Window size at launch: shrink() never goes below this height.
            BASE = (700, 632)
            _lock = Lock()

            def minimize(self):
                webview.windows[0].minimize()

            @staticmethod
            def _resize(window, width, height):
                """Resize and wait until the new size is applied (resize() is asynchronous on macOS)."""
                window.resize(width, height)
                for _ in range(25):
                    if abs(window.height - height) < 1:
                        break
                    time.sleep(0.02)

            def grow(self, extra):
                """Make the window `extra` px taller (for the detailed rules), within the screen."""
                with DesktopBridge._lock:
                    window, screen = webview.windows[0], webview.screens[0]
                    x, y, width, height = window.x, window.y, window.width, window.height
                    target = min(height + max(0, int(extra)), int(screen.height) - 50)
                    if target <= height:
                        return False
                    if DesktopBridge._saved is None:
                        DesktopBridge._saved = (x, y)
                    self._resize(window, width, target)
                    # Keep the bottom edge on screen by moving the window up if needed.
                    if y + target > screen.height - 10:
                        window.move(x, max(30, int(screen.height) - target - 10))
                    return True

            def shrink(self, extra=0):
                """Fit the window to the menu again after the rules close.

                `extra` is how many px the page is too tall (negative when there is
                spare room). The result is never smaller than the launch height, so
                the whole menu stays visible even if the saved size was wrong.
                """
                with DesktopBridge._lock:
                    saved, DesktopBridge._saved = DesktopBridge._saved, None
                    window = webview.windows[0]
                    target = max(DesktopBridge.BASE[1], int(window.height + int(extra)))
                    if abs(window.height - target) >= 1:
                        self._resize(window, window.width, target)
                    if saved:
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
