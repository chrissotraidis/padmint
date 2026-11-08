"""A briefly overloaded download server gets a few more tries; other failures stop at once."""
import io
import unittest
import urllib.error
from unittest import mock

from padmint import tools

URL = "https://github.com/example/tool/releases/download/v1/tool.tar.gz"


def http_error(code):
    return urllib.error.HTTPError(URL, code, "Gateway Time-out" if code == 504 else "Not Found", {}, io.BytesIO())


class DownloadRetryTests(unittest.TestCase):
    def setUp(self):
        sleep = mock.patch.object(tools.time, "sleep")
        self.sleep = sleep.start()
        self.addCleanup(sleep.stop)

    def test_a_gateway_timeout_is_tried_again(self):
        answer = object()
        with mock.patch.object(tools.urllib.request, "urlopen", side_effect=[http_error(504), http_error(503), answer]) as opened:
            self.assertIs(tools.open_url(URL), answer)
        self.assertEqual(opened.call_count, 3)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], list(tools.RETRY_WAITS[:2]))

    def test_it_gives_up_after_the_last_wait_and_says_why(self):
        with mock.patch.object(tools.urllib.request, "urlopen", side_effect=http_error(504)) as opened:
            with self.assertRaisesRegex(RuntimeError, "could not reach github.com.*Gateway Time-out"):
                tools.open_url(URL)
        self.assertEqual(opened.call_count, len(tools.RETRY_WAITS) + 1)

    def test_a_missing_file_or_no_connection_fails_at_once(self):
        for error in (http_error(404), urllib.error.URLError("Name or service not known")):
            with self.subTest(error=error), \
                    mock.patch.object(tools.urllib.request, "urlopen", side_effect=error) as opened:
                with self.assertRaises(RuntimeError):
                    tools.open_url(URL)
                self.assertEqual(opened.call_count, 1)
        self.sleep.assert_not_called()
