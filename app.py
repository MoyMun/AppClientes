import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import io
import xlsxwriter
import os

st.set_page_config(page_title="Inventario Autopartes", layout="wide")

col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("logo.png", width=120)
with col_title:
    st.markdown("<h1 style='padding-top: 20px;'>🔧 Inventario Autopartes</h1>", unsafe_allow_html=True)

# Botón de WhatsApp flotante
st.markdown(
    """
    <style>
    .whatsapp-button {
        position: fixed;
        bottom: 20px;
        right: 25px;
        z-index: 100;
    }
    </style>
    <div class="whatsapp-button">
        <a href="https://wa.me/5214772479133" target="_blank">
            <img src="https://img.icons8.com/color/48/000000/whatsapp--v1.png"/>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# Cargar credenciales desde secrets.toml
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

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

try:
    spreadsheet = client.open("INVENTARIO FINAL AUTOPARTES Phyton")
    sheet = spreadsheet.worksheet("Escaneo c precios de venta")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

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

    st.caption("Filtra por código, descripción, precio o categoría")
    col1, col2 = st.columns(2)

    with col1:
        codigo = st.text_input("🔍 Filtrar por Código")
        descripcion = st.text_input("📝 Buscar en Descripción")
        categoria = st.selectbox("📦 Filtrar por Categoría", options=["Todos"] + sorted(df["Categoria"].unique()))

    with col2:
        precio_min, precio_max = st.slider(
            "💰 Rango de Precio Outlet",
            min_value=float(df["Precio Outlet"].min()),
            max_value=float(df["Precio Outlet"].max()),
            value=(float(df["Precio Outlet"].min()), float(df["Precio Outlet"].max()))
        )

    if codigo:
        df = df[df["Código"].str.contains(codigo, case=False, na=False)]

    if descripcion:
        df = df[df["Descripción"].str.contains(descripcion, case=False, na=False)]

    if categoria != "Todos":
        df = df[df["Categoria"] == categoria]

    df = df[(df["Precio Outlet"] >= precio_min) & (df["Precio Outlet"] <= precio_max)]

    # Formatear columna para mostrar el signo $
    df_formateado = df.copy()
    df_formateado["Precio Outlet"] = df_formateado["Precio Outlet"].map("${:,.2f}".format)

    st.markdown(f"**🔎 Resultados encontrados: {len(df)}**")
    st.dataframe(df_formateado.reset_index(drop=True), use_container_width=True)

    st.subheader("📦 Descargar resultados filtrados")

    df_to_export = df.copy()
    df_to_export["Precio Outlet"] = df_to_export["Precio Outlet"].map("${:,.2f}".format)

    csv = df_to_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📄 Descargar como CSV",
        data=csv,
        file_name="inventario_filtrado.csv",
        mime="text/csv"
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_to_export.to_excel(writer, index=False, sheet_name="Inventario")

    st.download_button(
        label="📊 Descargar como Excel",
        data=output.getvalue(),
        file_name="inventario_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"❌ Error al cargar los datos de Google Sheets:\n\n{e}")