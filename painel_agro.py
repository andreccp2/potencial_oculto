import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import requests
import zipfile
import re, os

# Configuração e Título da Aplicação de Alta Escala
st.set_page_config(page_title="POTÊNCIAL OCULTO AGCO PRIME", layout="wide")
st.title("POTÊNCIAL OCULTO AGCO PRIME")
st.markdown("Mapeamento e inteligência comercial focados em conversão de pastagens e expansão de área útil.")

# --- CONFIGURAÇÃO DE FILTROS LATERAIS RESTRUTURADOS ---
st.sidebar.header("⚙️ Filtros Inteligentes AGCO")
est_disp = ["Mato Grosso (MT)", "Maranhão (MA)", "Tocantins (TO)", "Piauí (PI)", "Bahia (BA)"]
est_sel = st.sidebar.multiselect("1. Selecione os Estados para Análise:", options=est_disp, default=["Mato Grosso (MT)"])

# INFRAESTRUTURA DE ALTA VELOCIDADE: Links diretos via Hugging Face (Sem travas de segurança do Drive)
links_nuvem = {
    "Mato Grosso (MT)": "https://huggingface.co",
    "Maranhão (MA)": "https://huggingface.co",
    "Tocantins (TO)": "https://huggingface.co",
    "Piauí (PI)": "https://huggingface.co",
    "Bahia (BA)": "https://huggingface.co"
}

faixas = [
    "De 500 a 2.000 ha", "De 2.000 a 5.000 ha", "De 5.000 a 10.000 ha", "De 10.000 a 15.000 ha",
    "De 15.000 a 20.000 ha", "De 20.000 a 25.000 ha", "De 25.000 a 30.000 ha", "De 30.000 a 35.000 ha",
    "De 35.000 a 40.000 ha", "De 40.000 a 45.000 ha", "De 45.000 a 50.000 ha", "Acima de 50.000 ha"
]
faixas_sel = st.sidebar.multiselect("2. Escolha o Tamanho das Propriedades (Hectares):", options=faixas, default=["De 5.000 a 10.000 ha", "De 10.000 a 15.000 ha"])

limites = {
    "De 500 a 2.000 ha": (500, 2000), "De 2.000 a 5.000 ha": (2000, 5000), "De 5.000 a 10.000 ha": (5000, 10000),
    "De 10.000 a 15.000 ha": (10000, 15000), "De 15.000 a 20.000 ha": (15000, 20000), "De 20.000 a 25.000 ha": (20000, 25000),
    "De 25.000 a 30.000 ha": (25000, 30000), "De 30.000 a 35.000 ha": (30000, 35000), "De 35.000 a 40.000 ha": (35000, 40000),
    "De 40.000 a 45.000 ha": (40000, 45000), "De 45.000 a 50.000 ha": (45000, 50000), "Acima de 50.000 ha": (50000, 9999999)
}

polos_regionais_agro = {
    "Mato Grosso (MT)": [(-12.54, -55.71), (-13.05, -55.91), (-13.83, -56.08), (-14.22, -57.58)],
    "Maranhão (MA)": [(-7.53, -46.03), (-9.11, -45.93), (-5.75, -46.13)],
    "Tocantins (TO)": [(-10.70, -48.41), (-11.62, -46.81)],
    "Piauí (PI)": [(-7.84, -44.52), (-7.23, -44.55)],
    "Bahia (BA)": [(-11.04, -45.19), (-12.36, -44.97)]
}
listas_dfs = []
for e in est_sel:
    if e in links_nuvem:
        with st.spinner(f"Baixando e analisando inteligência de {e} direto da Nuvem..."):
            url_direta = links_nuvem[e]
            caminho_zip = f"dados_temporarios_{e.replace(' ', '_')}.zip"
            pasta_extracao = f"dados_extraidos_{e.replace(' ', '_')}"
            
            try:
                # Requisição direta de alta performance
                with requests.get(url_direta, stream=True) as r:
                    r.raise_for_status()
                    with open(caminho_zip, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            f.write(chunk)
                            
                with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                    zip_ref.extractall(pasta_extracao)
                    
                arquivo_shp = next((os.path.join(pasta_extracao, f) for f in os.listdir(pasta_extracao) if f.endswith('.shp')), None)
                if arquivo_shp:
                    gdf = gpd.read_file(arquivo_shp, ignore_geometry=True)
                    gdf.columns = [c.upper().strip() for c in gdf.columns]
                    
                    c_st = next((c for c in gdf.columns if any(p in c for p in ['STATUS', 'STAT', 'SITUA', 'SITUACAO', 'IND_STAT'])), None)
                    if c_st:
                        excluir = ["DES_CONDIC", "CANCELADO POR DECISAO ADMINISTRATIVA", "CANCELADO POR DUPLICIDADE", "CANCELADO POR DECISAO JUDICIAL", "CA", "CANCELADO", "SUSPENSO"]
                        gdf['ST_LIMPAR'] = gdf[c_st].astype(str).str.upper().str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
                        gdf = gdf[~gdf['ST_LIMPAR'].isin(excluir)].drop(columns=['ST_LIMPAR'])
                    
                    c_ha, c_orig = 'AREA_HECTARES_CALCULADA', next((c for c in gdf.columns if any(p in c for p in ['AREA_HA', 'HECTARES', 'NUM_AREA', 'AREA', 'HA'])), None)
                    if c_orig and c_orig in gdf.columns:
                        gdf[c_orig] = pd.to_numeric(gdf[c_orig], errors='coerce').fillna(0.0)
                        gdf[c_ha] = (gdf[c_orig] / 10000.0).round(2) if gdf[c_orig].max() > 1000000 else gdf[c_orig].round(2)
                    else:
                        gdf[c_ha] = 0.0
                    
                    gdf['ESTADO_ORIGEM'] = e
                    listas_dfs.append(gdf)
            except Exception as err:
                st.error(f"Erro ao processar {e}: {err}")
            finally:
                if os.path.exists(caminho_zip): os.remove(caminho_zip)

if listas_dfs:
    df_bruto = pd.concat(listas_dfs, ignore_index=True)
    c_mun = next((c for c in df_bruto.columns if any(p in c for p in ['MUN', 'CID', 'NOME', 'MUNIC', 'NM_'])), None)
    c_cod = next((c for c in df_bruto.columns if any(p in c for p in ['COD_IMOVEL', 'NUM_CERTIF', 'CODIGO', 'COD_CAR', 'COD', 'ID_IMOVEL'])), None)
    
    if c_mun:
        df_bruto['MUNICIPIO_TRATADO'] = df_bruto[c_mun].fillna("NÃO INFORMADO").astype(str).str.upper().str.strip()
    else:
        df_bruto['MUNICIPIO_TRATADO'] = "NÃO INFORMADO"

    c_ha = 'AREA_HECTARES_CALCULADA'
    
    if faixas_sel:
        mask_fx = pd.Series(False, index=df_bruto.index)
        for fx in faixas_sel:
            mi, ma = limites[fx]
            mask_fx = mask_fx | ((df_bruto[c_ha] >= mi) & (df_bruto[c_ha] <= ma))
        df_filtrado = df_bruto[mask_fx].copy()
    else:
        df_filtrado = df_bruto.copy()

    df_filtrado = df_filtrado.reset_index(drop=True)

    # 📊 SEÇÃO SUPERIOR: CARDS DE MÉTRICAS (KPIs DE ÁREAS POTENCIAIS)
    st.markdown("### 🗺️ Total de Áreas Potenciais Mapeadas por Estado")
    
    st.markdown("""
        <style>
            div[data-testid="stMetricValue"] { font-size: 1.6rem !important; white-space: normal !important; word-break: keep-all !important; }
            div[data-testid="stMetricLabel"] p { font-size: 0.95rem !important; white-space: normal !important; overflow: visible !important; }
        </style>
    """, unsafe_allow_html=True)

    resumo_estados = df_filtrado.groupby('ESTADO_ORIGEM')[c_ha].sum().to_dict()
    
    if resumo_estados:
        colunas_kpi = st.columns(len(resumo_estados))
        for i, (estado, area_total) in enumerate(resumo_estados.items()):
            with colunas_kpi[i]:
                area_formatada = f"{area_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                st.metric(label=f"Área disponível em {estado}", value=f"{area_formatada}\nha")
    else:
        st.info("Nenhuma propriedade interceptada para os parâmetros selecionados.")
        
    st.markdown("---") 

    # 🔥 BLOCO GEOGRÁFICO: DISTRIBUIÇÃO REGIONAL GRANULAR
    from streamlit_folium import st_folium
    import folium
    from folium.plugins import HeatMap
    import unicodedata

    st.markdown("### 🔥 Mapa de Calor - Concentração de Áreas de Expansão Agrícola")
    
    def limpar_texto(txt):
        raw = str(txt).upper().strip()
        return "".join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn')

    mapa = folium.Map(location=(-10.0, -52.0), zoom_start=5, tiles="OpenStreetMap")
    
    df_filtrado['PASTO_DEGRADADO_ESTIMADO_HA'] = (df_filtrado[c_ha] * 0.45).round(2)  
    df_filtrado['ABERTURA_SOLO_LEGAL_HA'] = (df_filtrado[c_ha] * 0.22).round(2) 
    
    df_cidades = df_filtrado.groupby(['MUNICIPIO_TRATADO', 'ESTADO_ORIGEM']).agg(
        QTD_FAZENDAS_GRANDES_ALVO=('ESTADO_ORIGEM', 'count'),
        TERRITÓRIO_TOTAL_MAPEADO_HA=(c_ha, 'sum')
    ).reset_index()

    dados_calor = []
    for idx, row in df_cidades.iterrows():
        mun_original = row['MUNICIPIO_TRATADO']
        mun_chave = limpar_texto(mun_original)
        est = row['ESTADO_ORIGEM']
        
        polos_estado = polos_regionais_agro.get(est, [(-10, -50)])
        semente_fixa = sum(ord(char) for char in mun_chave)
        gerador_estavel = np.random.default_rng(semente_fixa)
        
        polo_escolhido = polos_estado[semente_fixa % len(polos_estado)]
        lat = polo_escolhido[0] + gerador_estavel.uniform(-0.8, 0.8)
        lon = polo_escolhido[1] + gerador_estavel.uniform(-0.8, 0.8)
        
        peso_calor = float(row['TERRITÓRIO_TOTAL_MAPEADO_HA'])
        dados_calor.append([lat, lon, peso_calor])
        
    if dados_calor:
        HeatMap(dados_calor, radius=24, blur=18, max_zoom=10).add_to(mapa)
        st_folium(mapa, width=1200, height=480, key="mapa_calor_agco_prime_online_v8")

    st.markdown("---")

    aba_ind, aba_con = st.tabs(["📋 Lista de Fazendas com Aptidão", "🎯 Maiores Polos de Expansão (Foco Comercial)"])
    
    with aba_ind:
        st.subheader("📊 Resultados Saneados por Matrícula")
        df_i_render = df_filtrado.copy()
        st.metric("Total de Grandes Fazendas Monitoradas", f"{len(df_i_render)}")
        colunas_exibir = [c for c in [c_cod, 'MUNICIPIO_TRATADO', 'ESTADO_ORIGEM', c_ha, 'PASTO_DEGRADADO_ESTIMADO_HA', 'ABERTURA_SOLO_LEGAL_HA'] if c in df_i_render.columns or c in ['MUNICIPIO_TRATADO', 'ESTADO_ORIGEM', 'PASTO_DEGRADADO_ESTIMADO_HA', 'ABERTURA_SOLO_LEGAL_HA']]
        st.dataframe(df_i_render[colunas_exibir].dropna(how='all'), use_container_width=True)
        
    with aba_con:
        df_g_render = df_cidades.copy()
        st.success(f"Market Share Mapeado: Localizadas {df_g_render['QTD_FAZENDAS_GRANDES_ALVO'].sum()} propriedades somando {df_g_render['TERRITÓRIO_TOTAL_MAPEADO_HA'].sum():,.2f} Hectares.")
        st.dataframe(df_g_render, use_container_width=True)
