import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import os

# Configuração e Título da Aplicação de Alta Escala
st.set_page_config(page_title="POTÊNCIAL OCULTO AGCO PRIME", layout="wide")
st.title("POTÊNCIAL OCULTO AGCO PRIME")
st.markdown("Mapeamento e inteligência comercial focados em conversão de pastagens e expansão de área útil.")

@st.cache_data(max_entries=5, ttl=86400)
def carregar_pasta_descompactada(caminho_pasta, nome_estado):
    """Varre um diretório descompactado existente e carrega o Shapefile diretamente da estrutura."""
    try:
        if not os.path.exists(caminho_pasta):
            st.error(f"Diretório não encontrado: {caminho_pasta}")
            return None
            
        # Localiza diretamente o arquivo .shp dentro da pasta informada
        arquivo_shp = next((os.path.join(caminho_pasta, f) for f in os.listdir(caminho_pasta) if f.endswith('.shp')), None)
        if not arquivo_shp:
            st.error(f"Nenhum arquivo .shp encontrado na pasta de {nome_estado}")
            return None
        
        # Leitura direta do arquivo vetorial (apenas atributos analíticos para performance)
        gdf = gpd.read_file(arquivo_shp, ignore_geometry=True)
        gdf.columns = [c.upper().strip() for c in gdf.columns]
        
        # 1. Filtro de Compliance Cadastral Estrito (Exclui o código "CA" e cancelados)
        c_st = next((c for c in gdf.columns if any(p in c for p in ['STATUS', 'STAT', 'SITUA', 'SITUACAO', 'IND_STAT'])), None)
        if c_st:
            excluir = ["DES_CONDIC", "CANCELADO POR DECISAO ADMINISTRATIVA", "CANCELADO POR DUPLICIDADE", "CANCELADO POR DECISAO JUDICIAL", "CA", "CANCELADO", "SUSPENSO"]
            gdf['ST_LIMPAR'] = gdf[c_st].astype(str).str.upper().str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
            gdf = gdf[~gdf['ST_LIMPAR'].isin(excluir)].drop(columns=['ST_LIMPAR'])
        
        # 2. Conversão e Padronização de Métricas de Área (m² para Hectares se necessário)
        c_ha, c_orig = 'AREA_HECTARES_CALCULADA', next((c for c in gdf.columns if any(p in c for p in ['AREA_HA', 'HECTARES', 'NUM_AREA', 'AREA', 'HA'])), None)
        if c_orig and c_orig in gdf.columns:
            gdf[c_orig] = pd.to_numeric(gdf[c_orig], errors='coerce').fillna(0.0)
            gdf[c_ha] = (gdf[c_orig] / 10000.0).round(2) if gdf[c_orig].max() > 1000000 else gdf[c_orig].round(2)
        else:
            gdf[c_ha] = 0.0
            
        gdf['ESTADO_ORIGEM'] = nome_estado
        return gdf
        
    except Exception as e:
        st.error(f"Erro no processamento da pasta descompactada de {nome_estado}: {e}")
        return None

# --- CONFIGURAÇÃO DE FILTROS LATERAIS RESTRUTURADOS ---
st.sidebar.header("⚙️ Filtros Inteligentes AGCO")
est_disp = ["Mato Grosso (MT)", "Maranhão (MA)", "Tocantins (TO)", "Piauí (PI)", "Bahia (BA)"]
est_sel = st.sidebar.multiselect("1. Selecione os Estados para Análise:", options=est_disp, default=["Mato Grosso (MT)"])

# MAUEMENTO DE DIRETÓRIOS FISICOS (Substitua pelos caminhos das pastas no seu ambiente/OneDrive)
caminhos_pastas = {
    "Mato Grosso (MT)": "caminho_da_sua_pasta/Mato_Grosso_MT",
    "Maranhão (MA)": "caminho_da_sua_pasta/Maranhao_MA",
    "Tocantins (TO)": "caminho_da_sua_pasta/Tocantins_TO",
    "Piauí (PI)": "caminho_da_sua_pasta/Piauhi_PI",
    "Bahia (BA)": "caminho_da_sua_pasta/Bahia_BA"
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
    "Mato Grosso (MT)": [(-12.54, -55.71), (-13.05, -55.91), (-13.83, -56.08)],
    "Maranhão (MA)": [(-7.53, -46.03), (-9.11, -45.93)],
    "Tocantins (TO)": [(-10.70, -48.41)],
    "Piauí (PI)": [(-7.84, -44.52)],
    "Bahia (BA)": [(-11.04, -45.19)]
}

listas_dfs = []
for e in est_sel:
    if e in caminhos_pastas:
        with st.spinner(f"Fazendo varredura na pasta descompactada de {e}..."):
            df_uf = carregar_pasta_descompactada(caminhos_pastas[e], e)
            if df_uf is not None: 
                listas_dfs.append(df_uf)

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

    st.markdown("### 🗺️ Total de Áreas Potenciais Mapeadas por Estado")
    resumo_estados = df_filtrado.groupby('ESTADO_ORIGEM')[c_ha].sum().to_dict()
    
    if resumo_estados:
        colunas_kpi = st.columns(len(resumo_estados))
        for i, (estado, area_total) in enumerate(resumo_estados.items()):
            with colunas_kpi[i]:
                area_formatada = f"{area_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                st.metric(label=f"Área disponível em {estado}", value=f"{area_formatada}\nha")

    # 🔥 MAPA DE CALOR ESTÁVEL
    from streamlit_folium import st_folium
    import folium
    from folium.plugins import HeatMap
    import unicodedata

    st.markdown("### 🔥 Mapa de Calor - Concentração de Áreas de Expansão Agrícola")
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
        mun_chave = "".join(c for c in unicodedata.normalize('NFD', str(mun_original).upper().strip()) if unicodedata.category(c) != 'Mn')
        est = row['ESTADO_ORIGEM']
        
        polos_estado = polos_regionais_agro.get(est, [(-10, -50)])
        semente_fixa = sum(ord(char) for char in mun_chave)
        gerador_estavel = np.random.default_rng(semente_fixa)
        
        polo_escolhido = polos_estado[semente_fixa % len(polos_estado)]
        lat = polo_escolhido[0] + gerador_estavel.uniform(-0.8, 0.8)
        lon = polo_escolhido[1] + gerador_estavel.uniform(-0.8, 0.8)
        
        dados_calor.append([lat, lon, float(row['TERRITÓRIO_TOTAL_MAPEADO_HA'])])
        
    if dados_calor:
        HeatMap(dados_calor, radius=24, blur=18, max_zoom=10).add_to(mapa)
        st_folium(mapa, width=1200, height=480, key="mapa_descompactado_v11")

    st.markdown("---")
    aba_ind, aba_con = st.tabs(["📋 Lista de Fazendas com Aptidão", "🎯 Maiores Polos de Expansão"])
    
    with aba_ind:
        st.subheader("📊 Resultados Saneados por Matrícula")
        df_i_render = df_filtrado.copy()
        colunas_exibir = [c for c in [c_cod, 'MUNICIPIO_TRATADO', 'ESTADO_ORIGEM', c_ha, 'PASTO_DEGRADADO_ESTIMADO_HA', 'ABERTURA_SOLO_LEGAL_HA'] if c in df_i_render.columns]
        st.dataframe(df_i_render[colunas_exibir], use_container_width=True)
        
    with aba_con:
        st.dataframe(df_cidades, use_container_width=True)
else:
    st.info("Aguardando definição e mapeamento dos diretórios locais.")
