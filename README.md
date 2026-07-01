Weather ETL Pipeline with Python, SQL & MongoDB

Overview

This project implements a complete ETL (Extract, Transform, Load) pipeline using Python. It collects real-time weather data from the OpenWeatherMap API, cleans and transforms the data, performs SQL-based analysis, generates visualizations, and stores the processed data in MongoDB.


Features

- Fetches live weather data from multiple cities
- Cleans and transforms JSON data into structured format
- Categorizes cities based on temperature
- Performs SQL analysis using PandasSQL
- Generates insightful visualizations
- Stores processed data in MongoDB
- Modular ETL architecture

Tools Used

- Python
- Pandas
- Requests
- PandasSQL
- Matplotlib
- Seaborn
- MongoDB
- PyMongo
- OpenWeatherMap API



Workflow

Extract

- Connects to the OpenWeatherMap API
- Fetches live weather information for multiple cities
- Handles API errors gracefully

Transform

Converts nested JSON into a clean DataFrame containing:

- City
- Country
- Coordinates
- Temperature
- Humidity
- Pressure
- Wind Speed
- Weather Condition
- Timestamp

Additional transformation:

- Temperature Categorization
  - Hot
  - Mild
  - Cool
  - Freezing

Analyze

SQL Queries:

- Cities with High Humidity & Low Pressure
- Average Wind Speed by Temperature Category

Visualizations:

- Pressure Distribution
- Temperature vs Humidity Correlation
- Wind Speed by Weather Type
- Cities by Temperature Category

Load

Stores the transformed dataset into MongoDB.

Database:

```
weather_etl_db
```

Collection:

```
city_weather_data
```

---

Sample Output

The project generates:

- SQL query results
- Statistical analysis
- Weather charts
- MongoDB collection containing transformed records

Charts are automatically saved as:

```
weather_analysis_charts.png
```

---

## 📁 Project Structure

```
Weather-ETL-Pipeline/
│
├── main.py
├── weather_analysis_charts.png
├── README.md
└── requirements.txt
```

---






 Author

Dev Pranesh

B.Tech Computer Science Student

Interested in:
- Data Engineering
- Data Analytics
- Data Science
- Machine Learning
- Artificial Intelligence
