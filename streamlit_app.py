import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import paho.mqtt.publish as mqtt_publish

# Konfigurasi MQTT
MQTT_BROKER = "broker.hivemq.com"  # Broker publik (ganti jika perlu)
MQTT_PORT = 1883
MQTT_TOPIC_CONTROL = "smartwater/control"  # Untuk kontrol valve
MQTT_TOPIC_PARAMS = "smartwater/params"   # Untuk parameter

# Fungsi untuk mengirim perintah via MQTT
def send_mqtt_command(topic, payload):
    try:
        mqtt_publish.single(
            topic,
            payload=str(payload),
            hostname=MQTT_BROKER,
            port=MQTT_PORT
        )
        return True
    except Exception as e:
        st.error(f"Gagal mengirim MQTT: {e}")
        return False

# Auto-refresh setiap 10 detik
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

REFRESH_INTERVAL = 10
if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.rerun()

# --- Konfigurasi Awal ---
st.set_page_config(page_title="Dashboard Monitoring", layout="wide")

# --- Fungsi Load Data ---
@st.cache_data(ttl=10)
def load_data(url):
    df = pd.read_csv(url)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S')
    df['Total Biaya'] = df['Flow Sensor'] * df['Biaya']
    df['Bulan'] = df['Date'].dt.to_period('M').astype(str)
    df['Tanggal'] = df['Date'].dt.date
    return df

# --- Data Source ---
gsheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQde6k9bpztDrdIY93vx12iJqtxs_CRH7tGVXeZ-qcUQogmlYRgSr4vRUxGqMJswjLXzNXsYg9dL9TF/pub?output=csv"
df = load_data(gsheet_url)

# --- Sidebar ---
st.sidebar.title("Menu")
menu = st.sidebar.radio("", ["Home", "Monitoring", "About"])

# Input Parameter
client_id = st.sidebar.text_input(
    "Client ID ESP32",
    value=str(df.iloc[-1, 2]) if len(df) > 0 else "esp32-client-1"
)

interval = st.sidebar.number_input(
    "Interval (S)",
    value=int(df.iloc[-1, 3]) if len(df) > 0 else 10000
)

tarif = st.sidebar.number_input(
    "Tarif per m³ (Rp)",
    value=int(df.iloc[-1, 4]) if len(df) > 0 else 10000
)

# Kontrol Valve
valve_status = st.sidebar.toggle("Kontrol Valve", value=False)
if valve_status:
    if send_mqtt_command(MQTT_TOPIC_CONTROL, "ON"):
        st.sidebar.success("Valve: ON")
else:
    if send_mqtt_command(MQTT_TOPIC_CONTROL, "OFF"):
        st.sidebar.success("Valve: OFF")

if st.sidebar.button("Kirim Parameter ke ESP32"):
    params = f"{interval},{tarif}"
    if send_mqtt_command(MQTT_TOPIC_PARAMS, params):
        st.sidebar.success("Parameter terkirim!")
    else:
        st.sidebar.error("Gagal mengirim parameter")

# ... (bagian tampilan dashboard tetap sama seperti sebelumnya) ...