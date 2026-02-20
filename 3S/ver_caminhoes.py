import folium
import json
import os

def gerar_mapa():
    # 1. Nome do arquivo JSON que a sua API gera
    arquivo_json = 'posicoes_veiculos.json'

    # 2. Tenta abrir e ler os dados do arquivo
    if not os.path.exists(arquivo_json):
        print(f"❌ Erro: O arquivo {arquivo_json} não foi encontrado!")
        return

    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            veiculos = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo JSON: {e}")
        return

    # 3. Criar o mapa
    # Começamos no centro do Brasil, mas o mapa vai se ajustar depois
    mapa = folium.Map(location=[-15.78, -47.92], zoom_start=4)

    # Lista para guardar as coordenadas válidas e centralizar o mapa depois
    coordenadas_validas = []

    # 4. Percorrer a lista de veículos (O "FOR")
    for v in veiculos:
        # Pega os dados da API
        lat_raw = v.get('Latitude')
        lon_raw = v.get('Longitude')
        placa = v.get('Placa', 'S/P')
        velocidade = v.get('Velocidade', 0)
        data_pos = v.get('DataHoraPosicao', 'Não informada')

        if lat_raw and lon_raw:
            try:
                # TRATAMENTO DA VÍRGULA:
                # Transformamos em string, trocamos vírgula por ponto e viramos float
                lat = float(str(lat_raw).replace(',', '.'))
                lon = float(str(lon_raw).replace(',', '.'))
                
                coordenadas_validas.append([lat, lon])

                # Define a cor do ícone: Verde se estiver andando, Vermelho se parado
                cor_pino = "green" if velocidade > 0 else "red"

                # Adiciona o marcador no mapa
                folium.Marker(
                    location=[lat, lon],
                    popup=(
                        f"<b>Caminhão:</b> {placa}<br>"
                        f"<b>Velocidade:</b> {velocidade} km/h<br>"
                        f"<b>Última Atualização:</b> {data_pos}"
                    ),
                    tooltip=f"Placa: {placa}",
                    icon=folium.Icon(color=cor_pino, icon="truck", prefix="fa")
                ).add_to(mapa)

            except ValueError:
                print(f"⚠️ Pulei o veículo {placa} por erro nas coordenadas: {lat_raw}")

    # 5. Ajustar o zoom do mapa automaticamente para ver todos os caminhões
    if coordenadas_validas:
        mapa.fit_bounds(coordenadas_validas)

    # 6. Salvar o arquivo final que você vai abrir no Live Preview
    mapa.save("mapa_logistica.html")
    print("---")
    print("✅ SUCESSO! O arquivo 'mapa_logistica.html' foi criado.")
    print("👉 Agora clique no arquivo 'mapa_logistica.html' na esquerda e abra o Live Preview.")
    print("---")

if __name__ == "__main__":
    gerar_mapa()