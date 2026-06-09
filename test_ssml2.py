import asyncio, edge_tts

ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
<voice name="vi-VN-HoaiMyNeural">Xin chào Việt Nam!</voice>
</speak>"""

async def test():
    c = edge_tts.Communicate(ssml, "vi-VN-HoaiMyNeural")
    await c.save("test_ssml3.mp3")
    print("OK, size:", __import__("os").path.getsize("test_ssml3.mp3"))

asyncio.run(test())
