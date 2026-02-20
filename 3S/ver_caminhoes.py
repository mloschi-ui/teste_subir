import folium
from branca.element import Template, MacroElement
import json
import os
import sys

# Configurar encoding UTF-8 para evitar erros de caracteres no Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def gerar_mapa():
    # 1. Configurações de arquivos
    arquivo_json = 'posicoes_veiculos.json'
    arquivo_saida = 'mapa_logistica.html'

    # 2. Verifica se o arquivo de dados existe
    if not os.path.exists(arquivo_json):
        print(f"[ERRO] O arquivo {arquivo_json} não foi encontrado!")
        return

    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            veiculos = json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler o JSON: {e}")
        return

    # 3. Criar o objeto do Mapa (Estilo moderno e limpo)
    mapa = folium.Map(location=[-15.78, -47.92], zoom_start=4, tiles='CartoDB positron')

    coordenadas_validas = []

    # 4. Percorrer a lista de veículos
    for v in veiculos:
        # Extração de dados (ajuste os nomes entre aspas se a API mudar)
        lat_raw = v.get('Latitude')
        lon_raw = v.get('Longitude')
        placa = v.get('Placa', 'S/P')
        motorista = v.get('Motorista', 'Não informado')
        trajeto = v.get('DescricaoViagem') or v.get('Trajeto') or 'Sem trajeto definido'
        velocidade = v.get('Velocidade', 0)
        data_pos = v.get('DataHoraPosicao', '---')

        if lat_raw and lon_raw:
            try:
                # Tratamento de coordenadas (Troca vírgula por ponto)
                lat = float(str(lat_raw).replace(',', '.'))
                lon = float(str(lon_raw).replace(',', '.'))
                coordenadas_validas.append([lat, lon])

                # Lógica de cor baseada na velocidade
                cor_pino = "green" if velocidade > 0 else "red"
                status = "Em Movimento" if velocidade > 0 else "Parado"

                # Construção do Tooltip HTML (O que aparece ao passar o mouse)
                conteudo_tooltip = f"""
                    <div style="font-family: Arial; font-size: 12px; width: 200px; padding: 5px;">
                        <b style="color: #2c3e50; font-size: 14px;">🚚 Placa: {placa}</b><br>
                        <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
                        <b>👤 Motorista:</b> {motorista}<br>
                        <b>🛣️ Trajeto:</b> {trajeto}<br>
                        <b>🚀 Velocidade:</b> {velocidade} km/h<br>
                        <small style="color: #7f8c8d;">🕒 Atualizado: {data_pos}</small>
                    </div>
                """

                # Adicionar o marcador
                folium.Marker(
                    location=[lat, lon],
                    tooltip=folium.Tooltip(conteudo_tooltip, sticky=True),
                    popup=f"Veículo: {placa}",
                    icon=folium.Icon(color=cor_pino, icon="truck", prefix="fa")
                ).add_to(mapa)

            except ValueError:
                continue

    # 5. Adicionar Legenda Fixa no Mapa (HTML/CSS)
    template_legenda = """
    {% macro html(this, kwargs) %}
    <div id='maplegend' class='maplegend' 
        style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.9);
        border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px; font-family: Arial; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);'>
        
        <div class='legend-title'><b>Monitoramento 3S</b></div>
        <div class='legend-scale'>
          <ul class='legend-labels' style="list-style: none; padding: 0; margin: 0; margin-top: 5px;">
            <li><span style='background:green; width:12px; height:12px; display:inline-block; margin-right:5px; border-radius:50%;'></span>Em Movimento</li>
            <li><span style='background:red; width:12px; height:12px; display:inline-block; margin-right:5px; border-radius:50%;'></span>Veículo Parado</li>
          </ul>
        </div>
    </div>
    {% endmacro %}
    """
    
    macro = MacroElement()
    macro._template = Template(template_legenda)
    mapa.get_root().add_child(macro)

    # 6. Ajustar o zoom automaticamente para as carretas
    if coordenadas_validas:
        mapa.fit_bounds(coordenadas_validas)

    # 7. Salvar e finalizar
    mapa.save(arquivo_saida)
    print("---")
    print(f"✅ SUCESSO! Mapa gerado em: {arquivo_saida}")
    print("👉 Passe o mouse sobre os caminhões para ver Motorista e Trajeto.")
    print("---")

if __name__ == "__main__":
    gerar_mapa()