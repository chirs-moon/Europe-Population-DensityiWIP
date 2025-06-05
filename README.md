# EU Population Density Dashboard

This is a Dash-powered interactive dashboard that visualizes population density trends across EU member states. It uses data from Eurostat via their official API and offers:

- A choropleth map showing % change in population density between two selected years
- A line chart to analyze a selected country's density over time
- A modern UI with Roboto font, styled dropdowns, and a clean light background (not fully :])

---

## 📦 Requirements

Install the required Python libraries:

```bash
pip install dash pandas requests pyjstat plotly
```

---

## 🚀 How to Run

Simply run the Python script:

```bash
python app.py
```

Then open your browser and go to [http://127.0.0.1:8050](http://127.0.0.1:8050)

---

## 📊 Features

- **Choropleth Map**: Select a start and end year to view how population density has changed across EU countries.
- **Time Series Plot**: Pick a country and see its density trend over the years.
- **Live Eurostat Data**: Data is fetched via the Eurostat JSON API and cached locally in `population_density.csv`.

---

## 🗂 File Structure

```
project/
│
├── app.py                  # Main Dash app
├── population_density.csv  # Cached data file (auto-created)
└── assets/
    └── (optional) style.css  # For custom CSS styling
```

> Note: Font and background styles are applied via inline and external Google Fonts (`Roboto`).

---

## 🌐 Data Source

This app uses Eurostat’s REST API:

**Population density by NUTS 3 region**  
[https://ec.europa.eu/eurostat/api](https://ec.europa.eu/eurostat/api)

---

## 📄 License

MIT License — feel free to use, modify, and share!
