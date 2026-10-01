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
            def resize(self, width, height):
                webview.windows[0].resize(int(width), int(height))

            def minimize(self):
                webview.windows[0].minimize()

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
