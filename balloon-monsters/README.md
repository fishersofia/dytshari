# Balloon monsters — local installation

Run `python3 server.py` from this folder and open http://127.0.0.1:4173/. On macOS, you can also double-click `start.command`. Python 3 is required; no additional packages or Node.js installation are needed.

This export starts with an empty participant gallery. Existing portraits, maker names, and assignment history from the original installation are deliberately excluded.

- 52 distinct 3D models with individual face profiles and seeded surface textures; fixed bright palettes, no title and no hands.
- Bright green UI accents. Finished monsters can zoom with +/−, the mouse wheel or two-finger pinch, and perform seven switchable dances, including Twerk, with individual default styles and tempos.
- Tap the round mystery balloon once: pieces form one by one in about 2–4 seconds total. Enter/Space starts it too. Extra taps speed it up.
- The local server assigns a different design to each new maker, without repeats within a 52-design cycle. Assignments and participant portraits persist in `.local/`.
- Gallery includes all 52 designs and the portraits made by participants on this installation.
- After completion: a real latex pop, a flame burst and a brief screen shake. No music or third-party player.
- Name & save photo writes a 1200×1200 PNG to the computer's Desktop and adds it to the local participant gallery. A Download PNG fallback is available.
- UI: English, Helvetica Bold with system fallbacks.

The server binds to loopback only. This is a local installation, not a shared online service. Static hosting alone cannot write to Desktop or share participant records.

Audio source and licenses: `dist/audio/CREDITS.txt`. No song files or third-party music player are included.
