import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Configurar la app para pantalla ancha
st.set_page_config(page_title="Inventario Autopartes", layout="wide")

# 🔐 Cargar credenciales desde secrets.toml
creds_dict = {
    "type": st.secrets["gcp_service_account"]["type"],
    "project_id": st.secrets["gcp_service_account"]["project_id"],
    "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
    "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
    "client_email": st.secrets["gcp_service_account"]["client_email"],
    "client_id": st.secrets["gcp_service_account"]["client_id"],
    "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri": st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
}

# Autorización
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

try:
    # 📄 Leer datos desde Google Sheets
    spreadsheet = client.open("INVENTARIO FINAL AUTOPARTES Phyton")
    sheet = spreadsheet.worksheet("Escaneo c precios de venta")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 🧼 Limpiar columnas y datos
    df.columns = df.columns.str.strip()
    columnas_deseadas = ["Código", "Descripción", "Precio Outlet", "Marca", "Modelo", "Categoria"]
    df = df[columnas_deseadas]

    df["Código"] = df["Código"].fillna("").astype(str).str.strip()
    df["Descripción"] = df["Descripción"].fillna("").astype(str).str.strip()
    df["Categoria"] = df["Categoria"].fillna("").astype(str).str.strip()

    df["Precio Outlet"] = (
        df["Precio Outlet"]
        .astype(str)
        .str.replace(r"[^\d.]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )

    # 🧠 Título y filtros
    st.title("🔧 Inventario Autopartes")
    st.caption("Filtra por código, descripción, precio o categoría")

    col1, col2 = st.columns(2)

    with col1:
        codigo = st.text_input("🔍 Filtrar por Código")
        descripcion = st.text_input("📝 Buscar en Descripción")
        categoria = st.selectbox("📦 Filtrar por Categoría", options=["Todos"] + sorted(df["Categoria"].unique().tolist()))

    with col2:
        precio_min, precio_max = st.slider(
            "💰 Rango de Precio Outlet",
            min_value=float(df["Precio Outlet"].min()),
            max_value=float(df["Precio Outlet"].max()),
            value=(float(df["Precio Outlet"].min()), float(df["Precio Outlet"].max()))
        )

    # ✅ Aplicar filtros
    if codigo:
        df = df[df["Código"].str.contains(codigo, case=False, na=False)]

    if descripcion:
        df = df[df["Descripción"].str.contains(descripcion, case=False, na=False)]

    if categoria != "Todos":
        df = df[df["Categoria"] == categoria]

    df = df[
        (df["Precio Outlet"] >= precio_min) &
        (df["Precio Outlet"] <= precio_max)
    ]

    # 📊 Mostrar resultados
    st.markdown(f"**🔎 Resultados encontrados: {len(df)}**")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

except Exception as e:
    st.error(f"❌ Error al cargar los datos de Google Sheets:\n\n{e}")
