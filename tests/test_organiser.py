"""Run: python tests/test_organiser.py"""
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "root", "usr", "local", "bin", "fmd2-organiser")
loader = importlib.machinery.SourceFileLoader("organiser", SCRIPT)
spec = importlib.util.spec_from_loader("organiser", loader)
org = importlib.util.module_from_spec(spec)
loader.exec_module(org)


def make_cbz(path, extra=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("001.jpg", b"x")
        z.writestr("002.jpg", b"y")
        for name, data in (extra or {}).items():
            z.writestr(name, data)


class ParseTests(unittest.TestCase):
    def test_chapter_names(self):
        cases = {
            "Vol.03 Ch.021 - The Storm": ("03", "021", "The Storm"),
            "Chapter 21: 100 Days": (None, "21", "100 Days"),
            "Ch.21.5": (None, "21.5", ""),
            "Volume 3": ("3", None, ""),
            "Vol. 12 Chapter 104.5 Extra": ("12", "104.5", "Extra"),
            "21": (None, "21", ""),
            "Capítulo 7": (None, "7", ""),
            "Tomo 2 Cap. 9": ("2", "9", ""),
            "Episode 15 - Arc 2 begins": (None, "15", "Arc 2 begins"),
            "Oneshot": (None, None, "Oneshot"),
            "v05 c033": ("05", "033", ""),
        }
        for name, want in cases.items():
            self.assertEqual(org.parse_chapter(name), want, name)

    def test_filenames(self):
        f = org.target_filename
        self.assertEqual(f("One Piece", "3", "21", "", ".cbz"), "One Piece v03 c021.cbz")
        self.assertEqual(f("One Piece", None, "21.5", "", ".cbz"), "One Piece c021.5.cbz")
        self.assertEqual(f("One Piece", "12", None, "", ".cbz"), "One Piece v12.cbz")
        self.assertEqual(f("One Piece", None, "1050", "", ".cbz"), "One Piece c1050.cbz")
        self.assertEqual(f("One Piece", None, None, "Oneshot", ".cbz"), "One Piece - Oneshot.cbz")

    def test_folder(self):
        m = org.parse_folder("Berserk ~~ Miura Kentarou ~~  ~~ MangaDex")
        self.assertEqual((m["series"], m["author"], m["artist"], m["website"]),
                         ("Berserk", "Miura Kentarou", "", "MangaDex"))
        self.assertEqual(org.parse_folder("Plain Name")["series"], "Plain Name")


class FilingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        org.STAGING = os.path.join(self.tmp.name, "staging")
        org.LIBRARY = os.path.join(self.tmp.name, "library")
        org.SETTLE = -1
        os.makedirs(org.LIBRARY)

    def tearDown(self):
        self.tmp.cleanup()

    def test_files_into_existing_series_folder_with_metadata(self):
        os.makedirs(os.path.join(org.LIBRARY, "Pokémon Adventures!"))
        src = os.path.join(org.STAGING, "pokemon adventures ~~ Kusaka ~~ Mato ~~ Site", "Vol.2 Ch.15 - Go.cbz")
        make_cbz(src)
        org.scan_once(set())
        dest = os.path.join(org.LIBRARY, "Pokémon Adventures!", "Pokémon Adventures! v02 c015.cbz")
        self.assertTrue(os.path.isfile(dest))
        self.assertFalse(os.path.exists(src))
        self.assertEqual(sorted(os.listdir(org.LIBRARY)), ["Pokémon Adventures!"])
        with zipfile.ZipFile(dest) as z:
            xml = z.read("ComicInfo.xml").decode("utf-8")
        for bit in ("<Series>Pokémon Adventures!</Series>", "<Number>15</Number>", "<Volume>2</Volume>",
                    "<Title>Go</Title>", "<Writer>Kusaka</Writer>", "<Penciller>Mato</Penciller>",
                    "<PageCount>2</PageCount>"):
            self.assertIn(bit, xml)

    def test_never_overwrites_and_keeps_existing_comicinfo(self):
        existing = os.path.join(org.LIBRARY, "Berserk", "Berserk c001.cbz")
        make_cbz(existing)
        before = os.path.getsize(existing)
        clash = os.path.join(org.STAGING, "Berserk", "Chapter 1.cbz")
        own = os.path.join(org.STAGING, "Berserk", "Chapter 2.cbz")
        make_cbz(clash)
        make_cbz(own, {"ComicInfo.xml": "<ComicInfo><Series>Original</Series></ComicInfo>"})
        org.scan_once(set())
        self.assertEqual(os.path.getsize(existing), before)
        self.assertTrue(os.path.isfile(clash))
        with zipfile.ZipFile(os.path.join(org.LIBRARY, "Berserk", "Berserk c002.cbz")) as z:
            self.assertIn("Original", z.read("ComicInfo.xml").decode())
            self.assertEqual(sum(n == "ComicInfo.xml" for n in z.namelist()), 1)

    def test_unfinished_downloads_are_left_alone(self):
        folder = os.path.join(org.STAGING, "Series")
        make_cbz(os.path.join(folder, "Chapter 3.cbz"))
        os.makedirs(os.path.join(folder, "Chapter 3"))           # FMD2 still compressing
        with open(os.path.join(folder, "Chapter 4.cbz"), "wb") as fh:
            fh.write(b"PK\x03\x04 truncated")                    # half-written zip
        org.scan_once(set())
        self.assertFalse(os.path.exists(os.path.join(org.LIBRARY, "Series")))


if __name__ == "__main__":
    unittest.main(verbosity=1)
