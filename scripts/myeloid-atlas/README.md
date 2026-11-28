# Myeloid Atlas build scripts

The atlas page at `/myeloid-atlas/` is generated; do not edit `public/myeloid-atlas/` by hand.

1. Run the Colab notebook to produce `atlas_bundle_full.zip`, and unzip it.
2. Convert the bundle to the page's data files:
   `python3 build_site.py <unzipped_bundle_dir> data`
3. Install the page, styles, script and data into the site:
   `python3 build_for_site.py . <path to this repo>`
   (expects `index.html` and `data/` side by side, as in this folder)

`index.html` is the standalone version of the atlas; `build_for_site.py` restyles it with the site's palette and type
and wraps it in the site's header and footer (`src/pages/myeloid-atlas.astro`).

The predictions are AlphaGenome output. Use is subject to the AlphaGenome Output Terms of Use (non-commercial research only, not for clinical use).
