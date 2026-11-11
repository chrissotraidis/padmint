"""PadMint's own catalog is read and checked once per run. Listing Storage with 21 game
downloads read every catalog file 489 times (1.1 s on an M3 Max, before any folder was
measured); the window's first page read them 116 times."""
import unittest
from unittest import mock

from padmint import manifest


class CatalogReadOnceTests(unittest.TestCase):
    def test_later_calls_do_not_read_the_files_and_each_caller_gets_its_own_copy(self):
        first = manifest.catalog()
        first["kartpad"]["manifest"]["targets"].clear()  # one caller's change stays its own
        with mock.patch.object(manifest, "_read_catalog", side_effect=AssertionError("read again")):
            second = manifest.catalog()
        self.assertEqual(second, manifest._read_catalog())


if __name__ == "__main__":
    unittest.main()
