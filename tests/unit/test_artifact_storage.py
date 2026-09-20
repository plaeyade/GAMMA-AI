import tempfile
import unittest
from pathlib import Path

from gamma_core.errors import ConflictError
from gamma_storage import LocalImmutableObjectStore, content_addressed_key, sha256_digest


class ArtifactStorageTests(unittest.TestCase):
    def test_content_addressed_store_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = LocalImmutableObjectStore(Path(root))
            data = b"synthetic artifact"
            checksum = sha256_digest(data)
            key = content_addressed_key(checksum)
            uri = store.put_immutable(key, data, "text/plain")
            self.assertTrue(uri.startswith("file://"))
            self.assertEqual(store.put_immutable(key, data, "text/plain"), uri)
            with self.assertRaises(ConflictError):
                store.put_immutable(key, b"different bytes", "text/plain")


if __name__ == "__main__":
    unittest.main()
