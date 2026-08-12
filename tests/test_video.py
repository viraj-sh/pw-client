"""Unit tests for core.video pure logic (no network required)."""

import base64
import unittest

from core.video import (
    _iso8601_seconds,
    _otp_decrypt,
    _otp_encrypt,
    _plain_mp4_url,
    _split_mpd,
    extract_kid,
    parse_mpd,
)

TOKEN = "tok1234567890abcdef"
KID = "9b3e22955c8e4e8cbc2d3f0a6c1d4e5f"

TIMELINE_MPD = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT30S" type="static">
  <Period>
    <AdaptationSet contentType="video" mimeType="video/mp4" segmentAlignment="true">
      <ContentProtection cenc:default_KID="9B3E2295-5C8E-4E8C-BC2D-3F0A6C1D4E5F" xmlns:cenc="urn:mpeg:cenc:2013"/>
      <Representation id="v0" mimeType="video/mp4" width="1280" height="720" bandwidth="2000000">
        <SegmentTemplate timescale="90000" initialization="init-v0.mp4" media="seg-$Number$.m4s" startNumber="1">
          <SegmentTimeline><S t="0" d="90000" r="9"/></SegmentTimeline>
        </SegmentTemplate>
      </Representation>
    </AdaptationSet>
    <AdaptationSet contentType="audio" mimeType="audio/mp4">
      <Representation id="a0" mimeType="audio/mp4" bandwidth="128000">
        <SegmentTemplate timescale="48000" initialization="init-a0.mp4" media="a-$Number$.m4s" startNumber="1">
          <SegmentTimeline><S t="0" d="48000" r="9"/></SegmentTimeline>
        </SegmentTemplate>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""


class OtpTest(unittest.TestCase):
    def test_encrypt_shape(self):
        encoded = _otp_encrypt(TOKEN, KID)
        self.assertTrue(encoded.startswith("00"))
        self.assertTrue(all(c in "0123456789abcdef" for c in encoded[2:]))

    def test_xor_roundtrip(self):
        encoded = _otp_encrypt(TOKEN, KID)
        b64 = bytes.fromhex(encoded[2:]).decode()
        self.assertEqual(_otp_decrypt(TOKEN, b64), KID)


class KidTest(unittest.TestCase):
    def test_extract(self):
        mpd = '<ContentProtection cenc:default_KID="9B3E2295-5C8E-4E8C-BC2D-3F0A6C1D4E5F"/>'
        self.assertEqual(extract_kid(mpd), KID)

    def test_none(self):
        self.assertIsNone(extract_kid(None))
        self.assertIsNone(extract_kid("<MPD/>"))


class IsoTest(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(_iso8601_seconds("PT2H3M4.5S"), 2 * 3600 + 3 * 60 + 4.5)
        self.assertEqual(_iso8601_seconds("PT1H"), 3600)
        self.assertEqual(_iso8601_seconds("PT90.5S"), 90.5)
        self.assertIsNone(_iso8601_seconds("garbage"))


class MpdTest(unittest.TestCase):
    def test_timeline(self):
        base, sig = _split_mpd("https://cdn.example.com/batch/master.mpd?Policy=abc&Signature=xyz")
        self.assertEqual(base, "https://cdn.example.com/batch/")
        plan = parse_mpd(TIMELINE_MPD, base, sig)
        self.assertTrue(plan["drm"])
        self.assertEqual(plan["kid"], KID)
        self.assertEqual(plan["duration"], 30.0)
        self.assertEqual(len(plan["video"]["segments"]), 10)
        self.assertEqual(len(plan["audio"]["segments"]), 10)
        self.assertTrue(plan["video"]["init"].endswith("init-v0.mp4?Policy=abc&Signature=xyz"))
        self.assertTrue(plan["video"]["segments"][0].endswith("seg-1.m4s?Policy=abc&Signature=xyz"))
        self.assertTrue(plan["video"]["segments"][-1].endswith("seg-10.m4s?Policy=abc&Signature=xyz"))

    def test_no_timeline_falls_back_to_duration(self):
        mpd = """<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT10S" type="static">
  <Period>
    <AdaptationSet contentType="video">
      <Representation id="v" mimeType="video/mp4" height="1080">
        <SegmentTemplate timescale="1000" duration="1000" initialization="init.mp4" media="s$Number$.m4s" startNumber="1"/>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""
        plan = parse_mpd(mpd, "https://x.example.com/d/", None)
        self.assertEqual(len(plan["video"]["segments"]), 10)

    def test_segment_list(self):
        mpd = """<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static">
  <Period>
    <AdaptationSet contentType="audio">
      <Representation id="a" mimeType="audio/mp4">
        <SegmentList timescale="44100" duration="88200">
          <Initialization sourceURL="init.mp4"/>
          <SegmentURL media="a1.m4s"/><SegmentURL media="a2.m4s"/>
        </SegmentList>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""
        plan = parse_mpd(mpd, "https://x.example.com/d/", "k=v")
        self.assertTrue(plan["audio"]["init"].endswith("init.mp4?k=v"))
        self.assertEqual(len(plan["audio"]["segments"]), 2)

    def test_zero_padded_media_template(self):
        mpd = """<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT4S" type="static">
  <Period>
    <AdaptationSet contentType="video">
      <Representation id="v" mimeType="video/mp4">
        <SegmentTemplate timescale="1000" duration="1000" initialization="init.mp4" media="s$Number%04d$.m4s" startNumber="1"/>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""
        plan = parse_mpd(mpd, "https://x.example.com/d/", None)
        segments = plan["video"]["segments"]
        self.assertEqual(len(segments), 4)
        self.assertTrue(segments[0].endswith("s0001.m4s"))
        self.assertTrue(segments[-1].endswith("s0004.m4s"))

    def test_childless_elements_are_still_found(self):
        plan = parse_mpd(TIMELINE_MPD, "https://cdn.example.com/batch/", None)
        self.assertIsNotNone(plan["video"])
        self.assertIsNotNone(plan["audio"])


class UrlTest(unittest.TestCase):
    def test_plain_mp4(self):
        self.assertIsNone(_plain_mp4_url({}))
        self.assertEqual(
            _plain_mp4_url({"videoUrl": "https://cdn.x.com/a.mp4"}),
            "https://cdn.x.com/a.mp4",
        )
        self.assertIsNone(_plain_mp4_url({"videoUrl": "https://cdn.x.com/master.mpd"}))


if __name__ == "__main__":
    unittest.main()
