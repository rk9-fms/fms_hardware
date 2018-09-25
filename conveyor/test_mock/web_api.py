from unittest.mock import patch, MagicMock

from conveyor.test_mock.gpio_mock import GPIOMock, ListenerSocketClient

mock_host, mock_port = 'localhost', 42024
mock_based_api_host, mock_based_api_port = '127.0.0.1', 5000

MockRPi = MagicMock()
# fetching simulation-mock
MockRPi.GPIO = GPIOMock(ListenerSocketClient(mock_host, mock_port))
modules = {
    "RPi": MockRPi,
    "RPi.GPIO": MockRPi.GPIO,
}

# patching RPi
with patch.dict("sys.modules", modules):
    # importing module that has RPi-lib imports
    from conveyor.conveyor_web_api import app

app.run(mock_based_api_host, mock_based_api_port)
