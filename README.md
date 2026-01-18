# RoonPipe Albert Plugin

A simple [Albert launcher](https://albertlauncher.github.io/) plugin for controlling [Roon](https://roon.app/) via [RoonPipe](https://github.com/BlueManCZ/roonpipe).

## Features

- Search your Roon library directly from Albert
- Play tracks with a single keystroke
- Displays album artwork in search results

## Requirements

- [Albert launcher](https://albertlauncher.github.io/)
- [RoonPipe](https://github.com/BlueManCZ/roonpipe) running in the background

## Installation

Clone this repository into your Albert Python plugins directory:

```bash
git clone https://github.com/BlueManCZ/albert-plugin-python-roonpipe ~/.local/share/albert/python/plugins/roonpipe
```

Then enable the plugin in Albert settings.

## Usage

1. Make sure RoonPipe daemon is running (`roonpipe` in terminal)
2. Open Albert and type `roon ` followed by your search query
3. Select a track and press Enter to play

## License

MIT
