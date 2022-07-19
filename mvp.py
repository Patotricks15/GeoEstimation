import streamlit as st
from functions import GeoEstimation, social_dataframe, tendencia_mensal
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.errors import ShapelyDeprecationWarning
import numpy as np
from autoaede_functions import plot_lisa, otimizar_k, weights_matrix, read_geodata, significant_HH


st.set_option('deprecation.showPyplotGlobalUse', False)


st.title('Geo Estimation - MVP')

apps = st.text_input('apps')

app = apps.split(',')
pais = 'BR'
state = st.text_input('Estado (sigla)')

state_sigla = {'SP':'State of São Paulo',
'RJ':'State of Rio de Janeiro',
'MG':'State of Minas Gerais',
'ES':'State of Espírito Santo',
}

dicionario_arquivos = {}

data_inicial = st.text_input('Data inicial: dia-mes-ano')
data_final = st.text_input('Data final: dia-mes-ano')

lista_cores = st.multiselect('Cores dos respectivos apps:', ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds'])


app_color_dict = pd.DataFrame({'app':app, 'cor':lista_cores})
df_potencial = {'app':[],
'n_cidades':[],
'pib_potencial_total':[],
'pib_potencial_medio':[],
'demanda_potencial_total':[],
'demanda_potencial_media':[]}


geo = GeoEstimation(app, pais, start_date=data_inicial, final_date=data_final)
state_df = social_dataframe(app, 'BR', estado=state, start_date=data_inicial, final_date=data_final, dicionario = dicionario_arquivos)
#state_df = []


if st.button('Visualizar tabela (País)'):
    st.table(geo.dataframe(dicionario_arquivos).set_index('abbrev_state').drop(columns='geometry'))
    
if st.button('Exibir mapa (País)'):
    for row, value in app_color_dict.iterrows():
        st.pyplot(GeoEstimation(value['app'], pais, start_date=data_inicial, final_date=data_final).map(cor=value['cor'], dicionario = dicionario_arquivos))



if st.button('Visualizar tabela (Estado)'):
    st.text('visualizar')
    st.table(state_df[['name_muni', 'abbrev_state', 'populacao', 'pib', 'pib_per_capita','app', 'soma', 'max']+app])
if st.button('Exibir mapa (Estado)'):
    for row, value in app_color_dict.iterrows():
        st.pyplot(GeoEstimation(value['app'], 'BR', start_date=data_inicial, final_date=data_final).municip_map(state, cor = value['cor'], dicionario=dicionario_arquivos))
if st.button('Estimativa socioeconômica'):
    df = state_df
    lista_app = app
    df_pib_pot = df[app+['pib_per_capita', 'populacao']]
    for i in lista_app:
      df_pib_pot[f'taxa_{i}'] = (df_pib_pot[i] / df_pib_pot[lista_app].sum(axis=1)) * (df_pib_pot[i] /100)
    df_pib_pot = df_pib_pot.dropna(0)
    for i in lista_app:
      df_pib_pot[f'pib_potencial_{i}'] = df_pib_pot['pib_per_capita'] * df_pib_pot[f'taxa_{i}']
      df_pib_pot[f'demanda_potencial_{i}'] = round(df_pib_pot['populacao'] * df_pib_pot[f'taxa_{i}'], 0)

    for i in lista_app:
      df_potencial['app'].append(i)
      df_potencial['n_cidades'].append(len(df_pib_pot[df_pib_pot[i] > 0]))
      df_potencial['pib_potencial_total'].append(round(df_pib_pot[f'pib_potencial_{i}'].sum(),0))
      df_potencial['pib_potencial_medio'].append(round(df_pib_pot[f'pib_potencial_{i}'].mean(),0))
      df_potencial['demanda_potencial_total'].append(round(df_pib_pot[f'demanda_potencial_{i}'].sum(),0))
      df_potencial['demanda_potencial_media'].append(round(df_pib_pot[f'demanda_potencial_{i}'].mean(),0))
    st.table(df_potencial)

#input_estados_tendencia = st.text_input('Estados para comparar a tendência mensal')
sigla_estado = state_sigla[state]
select_estado = [sigla_estado]

if st.button('tendencia'):
    adapt_cores = [i.lower()[:-1] for i in lista_cores]
    print(adapt_cores)
    app_color_dict['cor'] = adapt_cores
    retorno_df = tendencia_mensal(app, select_estado, adapt_cores)
    estados_lista= [select_estado]
    for select_estado in estados_lista:
      estado = select_estado
      fig, ax =plt.subplots(1,1)
      for row, value in app_color_dict.iterrows():
        retorno_df[retorno_df['app'] == value['app']][[sigla_estado,'app']].plot(ax=ax, label=value['app'], color=value['cor'])
        #df_final4[df_final4['app'] == 'picpay'][[estado,'app']].plot(ax=ax, label='picpay',color='green')
        #df_final4[df_final4['app'] == 'c6 bank'][[estado,'app']].plot(ax=ax, label='c6 bank', color='black')
        #df_final4[df_final4['app'] == 'banco inter'][[estado,'app']].plot(ax=ax, label='banco inter',color='orange')
        ax.legend(app)
        plt.ylim(0,100)
        plt.title(f'Evolução mensal {" X ".join(app)} em {sigla_estado}')
        plt.box(False)
    st.pyplot(fig)


if st.button('Clusters'):
    for j in app:
        dado = read_geodata(dicionario_arquivos[f'{j}_{state}_with_geometry'])
        i_moran = otimizar_k(dado, j, 1, 10, p_value=0.05)
        pesos = weights_matrix(dado, metric = 'knn', k = i_moran)
        st.pyplot(plot_lisa(dado, j, weights= pesos, k_opt=i_moran, estado=state))
        st.text(significant_HH(dado, j, weight= pesos))

#if st.button('Análise de dominância'):
 #   state_df['geometry'] = state_df['geometry'].apply(wkt.loads)
  #  state_df = gpd.GeoDataFrame(state_df, crs='epsg:4326')
   # app_color = pd.DataFrame({'app':app,
    #         'cor':lista_cores})
    #for i in app:
     #   st.pyplot(GeoEstimation(i, 'BR', start_date='01-01-2021', final_date='01-01-2022').dominance(app = app, estado = state, app_color_dict=app_color, state_df=state_df))


