import asyncio, edge_tts

ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
<prosody rate="+0%" pitch="+0Hz" volume="+0%">Xin chào Việt Nam!</prosody>
</speak>"""

async def test():
    c = edge_tts.Communicate(ssml, "vi-VN-HoaiMyNeural")
    await c.save("test_ssml2.mp3")
    print("OK, size:", __import__("os").path.getsize("test_ssml2.mp3"))

asyncio.run(test())
