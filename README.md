# THE WORLD TODAY

A deterministic 1024 × 1024 newspaper illustration for a make.fun bounty, dated Friday, 20 November 2026.

The day's news: Trump, Xi and Putin meet in Shenzhen without an arms agreement after New START expired in February; the Gulf war widens and the tanker NAVIG8 MESSI burns in the Strait of Hormuz; GTA VI launches after 13 years, with pre-orders topping 15.9 million copies worth $1.54 billion; Anthropic lists as ANT at $83 in an $81 billion IPO. Briefs cover the Kerch Bridge, Ebola in DR Congo, and Cyclone Akvan. The market strip reproduces the supplied figures, including the separately specified 15.88M pre-order figure.

## Run

Requires Python 3, with no dependencies:

```sh
python3 main.py
```

Writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`, defaulting to `/output`. To write the preview in the current directory:

```sh
MAKEFUN_OUTPUT_DIR=. python3 main.py
```

All rasterization uses Python's standard library: an original 5×7 bitmap font, rectangles, Bresenham lines, filled circles, scanline polygons and stars. The PNG encoder uses `struct` and `zlib`. No network, input files, timestamps or randomness are used. The program validates text bounds, wrapping and text overlap before writing the image.

## Sources

News facts and figures are supplied by the bounty brief, verified there as of 20 November 2026, approximately 00:10 UTC. Source attributions supplied with the brief:

- Reuters
- NY Post
- Bloomberg
- Sensor Tower via Forbes
- Africa CDC/WHO joint statement, 15 November
- Motley Fool market close, 19 November

The renderer preserves the supplied wording and numbers; it does not retrieve or update news at runtime.

## License

MIT; copyright 2026 erikz86. See `LICENSE`.
