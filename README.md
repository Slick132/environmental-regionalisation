# Poster Website

Companion website for the Masters thesis poster on a feature-learning approach to environmental regionalisation. The site shows results and process that do not fit on the printed poster, built around an animated illustration of the autoencoder.

## Structure

```
Poster Website/
  index.html            Main page (hero + autoencoder animation, more sections to come)
  css/styles.css        Brand styling (Stellenbosch maroon and gold, paper background)
  js/autoencoder.js     The autoencoder flow animation (HTML canvas, no dependencies)
  figures/              Place exported result images here as sections are added
```

## Viewing it

The site is plain static HTML, CSS and JavaScript with no build step.

- Quickest: open `index.html` in any modern browser.
- For a local server (recommended so relative paths behave exactly as when hosted):
  - Python: run `python -m http.server 8000` inside this folder, then open `http://localhost:8000`.

## The animation

`js/autoencoder.js` draws a trained feed-forward autoencoder on a canvas. Five daily
climate channels flow in on the left, particles travel along the network connections
through a five-neuron bottleneck (the learned code z1 to z5), and a green reconstruction
flows out on the right that mirrors the input. The play and pause control is in the top
right of the canvas.

The input series are illustrative seasonal signals. A real sampled site can be substituted
later for the data section.

## Hosting

The folder can be deployed as-is to any static host (GitHub Pages, Netlify, or a plain
web server). The only external request is the Inter web font, which degrades to a system
font if unavailable.

## Planned sections

- The input data: snippets of the six daily climate channels.
- The pipeline: preprocessing, autoencoder, embedding, clustering, regions.
- Baseline comparison: Koppen-Geiger, PCA on bioclim, direct-feature clustering.
- Validation: elevation recovery, silhouette and stability.
- Case study: site-genotype matching across the learned regions.
