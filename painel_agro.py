import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import re, os

# Configuração e Título da Aplicação de Alta Escala
st.set_page_config(page_title="POTÊNCIAL OCULTO AGCO PRIME", layout="wide")
st.title("POTÊNCIAL OCULTO AGCO PRIME")
st.markdown("Mapeamento e inteligência comercial focados em conversão de pastagens e expansão de área útil.")

@st.cache_data(max_entries=5, ttl=86400) # Performance máxima: mantém os dados na memória RAM por 24 horas
def carregar_e_saneamento_car(caminho_shp, nome_estado):
    """Lê o shapefile diretamente do repositório local sem requisições externas à internet."""
    if not os.path.exists(caminho_shp): 
        return None
    try:
        # Leitura rápida ignorando a geometria pesada para focar na inteligência analítica de dados
        gdf = gpd.read_file(caminho_shp, ignore_geometry=True)
        gdf.columns = [c.upper().strip() for c in gdf.columns]
        
        # 1. Filtro de Compliance Cadastral Estrito (Remove Cancelados, Suspensos e o código "CA")
        c_st = next((c for c in gdf.columns if any(p in c for p in ['STATUS', 'STAT', 'SITUA', 'SITUACAO', 'IND_STAT'])), None)
        if c_st:
            excluir = ["DES_CONDIC", "CANCELADO POR DECISAO ADMINISTRATIVA", "CANCELADO POR DUPLICIDADE", "CANCELADO POR DECISAO JUDICIAL", "CA", "CANCELADO", "SUSPENSO"]
            gdf['ST_LIMPAR'] = gdf[c_st].astype(str).str.upper().str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
            gdf = gdf[~gdf['ST_LIMPAR'].isin(excluir)].drop(columns=['ST_LIMPAR'])
        
        # 2. Conversão Inteligente de Métricas de Área (m² para Hectares se necessário)
        c_ha, c_orig = 'AREA_HECTARES_CALCULADA', next((c for c in gdf.columns if any(p in c for p in ['AREA_HA', 'HECTARES', 'NUM_AREA', 'AREA', 'HA'])), None)
        if c_orig and c_orig in gdf.columns:
            gdf[c_orig] = pd.to_numeric(gdf[c_orig], errors='coerce').fillna(0.0)
            gdf[c_ha] = (gdf[c_orig] / 10000.0).round(2) if gdf[c_orig].max() > 1000000 else gdf[c_orig].round(2)
        else:
            gdf[c_ha] = 0.0
            
        gdf['ESTADO_ORIGEM'] = nome_estado
        return gdf
    except Exception as e:
        st.error(f"Erro ao ler os dados internos de {nome_estado}: {e}")
        return None

def obter_coordenadas_municipios():
    """Dicionário geográfico expandido focado nas maiores potências agrícolas regionais."""
    return {
        "BALSAS": (-7.53, -46.03), "BOM JARDIM": (-3.56, -45.99), "ALTO PARNAIBA": (-9.11, -45.93), 
        "SAO BENTO": (-2.69, -44.82), "GRAJAÚ": (-5.75, -46.13), "IMPERATRIZ": (-5.52, -47.47),
        "FORMOSA DO RIO PRETO": (-11.04, -45.19), "SAO DESIDERIO": (-12.36, -44.97), "CORRENTINA": (-13.34, -44.63),
        "BARREIRAS": (-12.15, -45.00), "LUÍS EDUARDO MAGALHÃES": (-12.09, -45.79),
        "CANTO DO BURITI": (-8.11, -42.94), "BAIXA GRANDE DO RIBEIRO": (-7.84, -44.52), 
        "URUÇUÍ": (-7.23, -44.55), "RIBEIRO GONÇALVES": (-7.55, -45.24),
        "SORRISO": (-12.54, -55.71), "SINOP": (-11.86, -55.50), "LUCAS DO RIO VERDE": (-13.05, -55.91),
        "NOVA MUTUM": (-13.83, -56.08), "QUERENCIA": (-12.60, -52.18), "CAMPO NOVO DO PARECIS": (-13.67, -57.89),
        "SAPEZAL": (-13.54, -58.81), "PRIMAVERA DO LESTE": (-15.55, -54.30), "RONDONÓPOLIS": (-16.46, -54.63),
        "MATEIROS": (-10.54, -46.42), "PORTO NACIONAL": (-10.70, -48.41), "DIANÓPOLIS": (-11.62, -46.81),
        "GURUPI": (-11.72, -49.06), "ARAGUAÍNA": (-7.19, -48.20)
    }

# --- CONFIGURAÇÃO DE FILTROS LATERAIS RESTRUTURADOS ---
st.sidebar.header("⚙️ Filtros Inteligentes AGCO")
est_disp = ["Mato Grosso (MT)", "Maranhão (MA)", "Tocantins (TO)", "Piauí (PI)", "Bahia (BA)"]
est_sel = st.sidebar.multiselect("1. Selecione os Estados para Análise:", options=est_disp, default=["Mato Grosso (MT)"])

# Rotas mapeadas para as pastas descompactadas enviadas para o seu repositório do GitHub
caminhos = {
    "Mato Grosso (MT)": os.path.join("MATO GROSSO", "AREA_CONSOLIDADA_1.shp"),
    "Maranhão (MA)": os.path.join("MARANHÃO", "AREA_IMOVEL_1.shp"),
    "Tocantins (TO)": os.path.join("TOCANTINS", "AREA_IMOVEL_1.shp"),
    "Piauí (PI)": os.path.join("PIAUI", "AREA_IMOVEL_1.shp"),
    "Bahia (BA)": os.path.join("BAHIA", "AREA_IMOVEL_1.shp")
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
    "Mato Grosso (MT)": [(-12.54, -55.71), (-13.05, -55.91), (-13.83, -56.08), (-14.22, -57.58), (-12.60, -52.18), (-15.55, -54.30)],
    "Maranhão (MA)": [(-7.53, -46.03), (-9.11, -45.93), (-5.75, -46.13), (-4.93, -43.41), (-3.56, -45.99)],
    "Tocantins (TO)": [(-10.70, -48.41), (-11.62, -46.81), (-7.19, -48.20)],
    "Piauí (PI)": [(-7.84, -44.52), (-7.23, -44.55), (-8.11, -42.94)],
    "Bahia (BA)": [(-11.04, -45.19), (-12.36, -44.97), (-12.09, -45.79)]
}

listas_dfs = []
for e in est_sel:
    if e in caminhos:
        # Se o arquivo não existir localmente, exibe uma mensagem instrutiva amigável na tela
        if not os.path.exists(caminhos[e]):
            st.info(f"📂 A pasta '{e.split()[0].upper()}' com seus arquivos descompactados precisa ser adicionada ao seu repositório do GitHub.")
        else:
            with st.spinner(f"Processando inteligência de {e} em alta velocidade..."):
                df_uf = carregar_e_saneamento_car(caminhos[e], e)
                if df_uf is not None: 
                    listas_dfs.append(df_uf)

if listas_dfs:
    df_bruto = pd.concat(listas_dfs, ignore_index=True)
    
    c_mun = next((c for c in df_bruto.columns if any(p in c for p in ['MUN', 'CID', 'NOME', 'MUNIC', 'NM_'])), None)
    c_cod = next((c for c in df_bruto.columns if any(p in c for p in ['COD_IMOVEL', 'NUM_CERTIF', 'CODIGO', 'COD_CAR', 'COD', 'ID_IMOVEL'])), None)
    c_lat = next((c for c in df_bruto.columns if 'LAT' in c or 'Y' in c), None)
    c_lon = next((c for c in df_bruto.columns if 'LON' in c or 'X' in c), None)
    
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

    # =========================================================================
    # 📊 SEÇÃO SUPERIOR: CARDS DE MÉTRICAS (KPIs DE ÁREAS POTENCIAIS)
    # =========================================================================
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
                nome_rotulo = estado.split("(")[0].strip()
                st.metric(label=f"Área disponível em {nome_rotulo}", value=f"{area_formatada}\nha")
    else:
        st.info("Nenhuma propriedade interceptada para os parâmetros selecionados.")
        
    st.markdown("---") 

    # =========================================================================
    # 🔥 BLOCO GEOGRÁFICO: MAPA DE CALOR ESTÁVEL
    # =========================================================================
    from streamlit_folium import st_folium
    import folium
    from folium.plugins import HeatMap
    import unicodedata

    st.markdown("### 🔥 Mapa de Calor - Concentração de Áreas de Expansão Agrícola")
    
    def limpar_texto(txt):
        raw = str(txt).upper().strip()
        return "".join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn')

    dic_municipios_bruto = obter_coordenadas_municipios()
    geo_municipios_limpo = {limpar_texto(k): v for k, v in dic_municipios_bruto.items()}
    
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
        
        if c_lat and pd.notna(row[c_lat]):
            lat, lon = row[c_lat], row[c_lon]
        elif mun_chave in geo_municipios_limpo:
            lat, lon = geo_municipios_limpo[mun_chave]
        else:
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
        st_folium(mapa, width=1200, height=480, key="mapa_calor_agco_github_v15")

    st.markdown("---")

    # --- ABAS DE EXIBIÇÃO OPERACIONAL ---
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
else:
    st.warning("Selecione os estados desejados e garanta que as pastas de dados estejam no repositório do GitHub.")
