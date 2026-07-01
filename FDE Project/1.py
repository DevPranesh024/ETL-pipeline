import requests
import time
import pandas as pd
from datetime import datetime
from pandasql import sqldf
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient



API_KEY = "6a025bc06966b7d0aa0b0f3f16598eec"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

CITIES = [
    "London,uk", "Tokyo,jp", "New York,us", "Sydney,au",
    "Mumbai,in", "Paris,fr", "Cairo,eg", "Berlin,de"
]

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "weather_etl_db"
MONGO_COLLECTION = "city_weather_data"


# EXTRACT

def extract_weather_data(city_name):
    """Fetch weather data for one city."""
    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {city_name}: {e}")
        return None


def extract_all_data(city_list):
    """Extract weather data for all cities."""
    raw_data_list = []
    print("\n--- Starting Extraction (E) ---")
    for city in city_list:
        data = extract_weather_data(city)
        if data:
            raw_data_list.append(data)
            print(f"✅ Extracted data for: {city.split(',')[0]}")
        time.sleep(0.5)
    print("--- Extraction Complete ---")
    return raw_data_list


# --- 3. TRANSFORM (T) STAGE ---

def transform_weather_data(raw_json_list):
    """Flatten and clean the JSON data into a DataFrame."""
    if not raw_json_list:
        print("⚠️ No data to transform.")
        return pd.DataFrame()

    transformed_records = []
    for raw_json in raw_json_list:
        try:
            record = {
                'city': raw_json.get('name'),
                'country': raw_json.get('sys', {}).get('country'),
                'latitude': raw_json.get('coord', {}).get('lat'),
                'longitude': raw_json.get('coord', {}).get('lon'),
                'temp_c': raw_json.get('main', {}).get('temp'),
                'humidity_percent': raw_json.get('main', {}).get('humidity'),
                'pressure_hPa': raw_json.get('main', {}).get('pressure'),
                'wind_speed_m_s': raw_json.get('wind', {}).get('speed'),
                'weather_main': raw_json.get('weather', [{}])[0].get('main'),
                'weather_description': raw_json.get('weather', [{}])[0].get('description'),
                'timestamp': datetime.fromtimestamp(raw_json.get('dt'))
            }
            transformed_records.append(record)
        except Exception as e:
            print(f"⚠️ Error transforming record: {e}")

    df = pd.DataFrame(transformed_records)

    def categorize_temp(temp):
        if temp >= 30:
            return 'Hot'
        elif temp >= 15:
            return 'Mild'
        elif temp >= 0:
            return 'Cool'
        else:
            return 'Freezing'

    df['temp_category'] = df['temp_c'].apply(categorize_temp)

    print("--- Transformation Complete ---")
    return df


# --- 4. ANALYZE + VISUALIZE (IN-MEMORY LOAD) ---

def analyze_data(df):
    """Perform SQL analysis and generate visualizations."""
    if df.empty:
        print("⚠️ No data for analysis.")
        return

    print("\n--- ANALYSIS & VISUALIZATION STAGE ---")

    # --- SQL Query 1: High humidity + low pressure ---
    q_storm_risk = """
    SELECT city, humidity_percent, pressure_hPa, temp_c
    FROM df
    WHERE humidity_percent > (SELECT AVG(humidity_percent) FROM df)
      AND pressure_hPa < (SELECT AVG(pressure_hPa) FROM df)
    ORDER BY humidity_percent DESC;
    """
    storm_risk_results = sqldf(q_storm_risk, locals())
    print("\n[Cities with High Humidity & Low Pressure]")
    print(storm_risk_results.to_markdown(index=False))

    # --- SQL Query 2: Avg wind by temperature category ---
    q_avg_wind = """
    SELECT temp_category, ROUND(AVG(wind_speed_m_s), 2) AS avg_wind_m_s, COUNT(city) AS city_count
    FROM df
    GROUP BY temp_category
    ORDER BY avg_wind_m_s DESC;
    """
    avg_wind_results = sqldf(q_avg_wind, locals())
    print("\n[Average Wind Speed by Temperature Category]")
    print(avg_wind_results.to_markdown(index=False))

    # --- Visualizations ---
    plt.figure(figsize=(15, 12))

    plt.subplot(2, 2, 1)
    sns.histplot(df['pressure_hPa'], kde=True, color='darkred')
    plt.title('Distribution of Atmospheric Pressure (hPa)')
    plt.xlabel('Pressure (hPa)')
    plt.ylabel('Frequency')

    plt.subplot(2, 2, 2)
    sns.regplot(x='temp_c', y='humidity_percent', data=df,
                scatter_kws={'alpha': 0.8}, line_kws={'color': 'red'})
    plt.title('Temperature vs. Humidity Correlation')
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Humidity (%)')

    plt.subplot(2, 2, 3)
    sns.boxplot(x='weather_main', y='wind_speed_m_s', data=df)
    plt.title('Wind Speed by Weather Type')
    plt.xlabel('Weather Condition')
    plt.ylabel('Wind Speed (m/s)')

    plt.subplot(2, 2, 4)
    sns.countplot(x='temp_category', data=df,
                  order=['Hot', 'Mild', 'Cool', 'Freezing'])
    plt.title('Number of Cities by Temperature Category')
    plt.xlabel('Temperature Category')
    plt.ylabel('Count')

    plt.tight_layout(pad=3.0)
    plt.savefig("weather_analysis_charts.png")

    # Show visualization briefly, non-blocking
    plt.show(block=False)
    plt.pause(5)
    plt.close('all')

    print("✅ Visualization displayed briefly and saved as 'weather_analysis_charts.png'")


# --- 5. LOAD TO MONGODB (PERSISTENT STORAGE) ---

def load_data_to_mongodb(df, uri, db_name, collection_name):
    """Load the transformed DataFrame into MongoDB."""
    print("\n--- Starting MongoDB Load (L) ---")
    print(f"Records to load: {len(df)}")

    if df.empty:
        print("⚠️ Skipping MongoDB load: DataFrame is empty.")
        return

    try:
        with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
            client.admin.command('ping')
            print("✅ MongoDB connection successful.")

            db = client[db_name]
            collection = db[collection_name]
            collection.delete_many({})
            collection.insert_many(df.to_dict('records'))

            print(f"✅ Data successfully inserted into '{db_name}.{collection_name}'")

    except Exception as e:
        print(f"❌ MongoDB Load Failure: {e}")
        print("   → Ensure MongoDB server (mongod) is running.")
        print(f"   → URI used: {uri}")


# --- 6. MAIN EXECUTION PIPELINE ---

if __name__ == "__main__":
    print("\n🚀 Starting Full ETL Pipeline...\n")

    # E: Extract
    raw_data = extract_all_data(CITIES)

    # T: Transform
    transformed_df = transform_weather_data(raw_data)
    print(f"\n✅ Transformed DataFrame Shape: {transformed_df.shape}")

    # A: Analyze + Visualize
    analyze_data(transformed_df)

    # L: Load into MongoDB
    print("\n--- Proceeding to MongoDB Load Stage ---")
    load_data_to_mongodb(transformed_df, MONGO_URI, MONGO_DATABASE, MONGO_COLLECTION)

    print("\n✅ ETL Pipeline Completed Successfully!")
    print("📊 Charts saved as 'weather_analysis_charts.png'")
    print("🗄️  Data stored in MongoDB collection 'weather_etl_db.city_weather_data'\n")
