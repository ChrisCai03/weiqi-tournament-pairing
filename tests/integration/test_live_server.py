import threading
from urllib.request import urlopen

from pairing.application import TournamentService
from pairing.web.server import create_server


def test_server_on_ephemeral_port_serves_display(tmp_path) -> None:
    path = tmp_path / "demo.tgo.json"
    TournamentService.create_demo(path)
    server, url = create_server(path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"{url}/display", timeout=5) as response:
            body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Public Display" in body
        assert server.server_port != 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
