# ADS-B Decoder Tool 

A real-time aircraft message decoder using `pyModeS`, dump1090, and OpenSky API. It parses and decodes raw ADS-B messages from various Downlink Formats (DF), extracting data like altitude, callsign, velocity, and position.

## Features

- Connects to `dump1090` on port `30002` (raw TCP)
- Decodes multiple ADS-B message types (DF17, DF11, DF4, DF5, DF24, etc.)
- Uses OpenSky Network API as a fallback data source
- Lightweight, terminal-based output

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
