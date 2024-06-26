# Notion OpenStreatMap Integration

## Overview
This project integrates Notion API with OpenStreetMap to visualize data points on a map. It fetches data from a Notion database and displays locations on a map based on the status of each entry.

## Features
- Fetch data from Notion database.
- Filter data based on predefined statuses.
- Cache results to optimize performance.

## Prerequisites
- Python 3.10+
- Poetry for dependency management

## Installation
1. Clone the repository:
2. Navigate to the project directory:
   ```
   cd notion-openstreatmap-integration
   ```
3. Install dependencies using Poetry:
   ```
   poetry install
   ```

## Configuration
Create a `.env` file in the root directory with the following content, replacing `SECRET_KEY` and `DATABASE_ID` with your actual Notion API key and database ID:
    ```
    NOTION_API_KEY=YOUR_NOTION_API_KEY
    NOTION_DATABASE_ID=YOUR_NOTION_DATABASE_ID
    ```


## Embedding the Map using JavaScript

To embed the map using JavaScript, follow these steps:

1. Include the OpenStreetMap library in your HTML file:
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
```

2. Create a div element in your HTML file where the map will be displayed:
```html
<div id="map" style="height: 500px;"></div>
```

3. Initialize the map in your JavaScript file:
```javascript
const center = [24.7136, 46.6753];
const zoom = 10;
const map = L.map('map').setView(center, zoom);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
```

4. Fetch data from your app and add markers to the map:
```javascript
fetch('http://localhost:8000/api/locations')
    .then(response => response.json())
    .then(data => {
        data.forEach(location => {
            L.marker([location.latitude, location.longitude])
                .addTo(map)
                .bindPopup(`<b>Name: ${location.name}</b><br>Status: ${location.status}`);
        });
    })
    .catch(error => console.error('Error fetching data:', error));
```

## Pointing the Fetch to This App

To point the fetch request to your app, ensure that your app is running and accessible. The example above assumes your app is running locally on port 8000 and has an endpoint `/api/locations` that returns location data in JSON format.

Make sure your app's API endpoint returns data in the following format:
```json
[
    {
        "name": "Location Name",
        "latitude": 24.7136,
        "longitude": 46.6753,
        "status": "Signed"
    },
    ...
]
```

Adjust the fetch URL and data processing logic as needed to match your app's actual API structure and data format.




