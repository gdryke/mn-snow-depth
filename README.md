# Minnesota Snow Depth Maps

This repository tracks and archives weekly snow depth maps for Minnesota, published by the [Minnesota DNR State Climatology Office](https://www.dnr.state.mn.us/climate/snowmap/index.html).

## About the Maps

Each Thursday during the cold season, the MN DNR State Climatology Office produces maps depicting:

1. **Snow Depth Maps** - Current snow depth measurements across Minnesota
2. **Ranking Maps** - Historical percentile rankings showing how current snow depths compare to historical records for that date

The data is provided by volunteers working with DNR Forestry, the National Weather Service, the University of Minnesota, Soil and Water Conservation Districts, and CoCoRaHS.

## Data Collection

Maps are automatically downloaded weekly using the `download_maps.py` script:

- **Schedule**: Updates run every Saturday at 00:00 UTC (Friday evening in US timezones)
- **Storage**: Maps are stored in the `data/` directory with date-based naming:
  - Format: `YYYY-MM-DD_depth.[jpg|gif]` for depth maps
  - Format: `YYYY-MM-DD_ranking.[gif]` for ranking maps (when available)
- **Update Mode**: The script only downloads maps that are missing from the local data folder

### Running Manually

To download maps manually:

```bash
python3 download_maps.py
```

The script will:
1. Fetch the list of all available maps from the MN DNR website
2. Check which maps are already downloaded
3. Download only the missing maps
4. Display a summary of downloaded, skipped, and failed downloads

## Repository Structure

```
.
├── download_maps.py          # Script to download maps from MN DNR
├── data/                     # Downloaded map images (committed to repo)
│   ├── 2026-03-05_depth.jpg
│   ├── 2025-04-17_depth.gif
│   ├── 2025-04-17_ranking.gif
│   └── ...
└── .github/
    └── workflows/
        └── update-maps.yml   # GitHub Actions workflow for weekly updates
```

## Data Source

- **Source**: [Minnesota DNR Climate Office - Snow Depth Maps](https://www.dnr.state.mn.us/climate/snowmap/index.html)
- **Update Frequency**: Weekly (Thursdays)
- **Historical Data**: Maps available back to 2015-2016 season

## Future Plans

- Create a GitHub Pages site to display the maps
- Add visualization and comparison tools
- Provide historical trend analysis

## License

The snow depth data and maps are provided by the Minnesota Department of Natural Resources. This repository is for archival and display purposes.
