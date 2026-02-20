"""
API 3S - Sistema de Rastreamento de Veículos
==============================================

Bibliotecas utilizadas:
-----------------------
- os: Manipulação de variáveis de ambiente
- requests: Fazer requisições HTTP (GET, POST)
- json: Manipular dados JSON
- datetime: Trabalhar com datas e horários
- dotenv (python-dotenv): Carregar e salvar variáveis no .env
- time: Controlar delays entre requisições

Instalação:
-----------
pip install requests python-dotenv
"""

import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv, set_key


class API3S:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('3S_USERNAME')
        self.password = os.getenv('3S_PASSWORD')
        self.token = os.getenv('3S_TOKEN')
        self.base_url = 'https://3stecnologia.eti.br/dataexportapi'
        self.env_file = '.env'
        self.max_chamadas_por_minuto = 9  # Limite seguro (API permite 10)
        self.tempo_espera = 62  # segundos de espera após atingir o limite
        self.contador_chamadas = 0
        self.arquivo_posicoes = 'posicoes_veiculos.json'
        self.arquivo_resumo = 'veiculos_resumo.json'

    def validar_login(self):
        """
        Faz login na API e retorna o token de autenticação
        Tenta múltiplos formatos de payload
        Salva automaticamente no .env
        """
        url = f'{self.base_url}/ValidaLogin'
        
        # Lista de formatos de payload para tentar
        payloads = [
            {'username': self.username, 'password': self.password},
            {'Usuario': self.username, 'Senha': self.password},
            {'user': self.username, 'pass': self.password},
        ]
        
        for idx, payload in enumerate(payloads, start=1):
            try:
                print(f'🔐 Tentativa de login {idx}/{len(payloads)}...')
                
                # Tenta com JSON
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    token = (
                        data.get('token')
                        or data.get('Token')
                        or data.get('access_token')
                        or data.get('AccessToken')
                    )
                    
                    if token:
                        set_key(self.env_file, '3S_TOKEN', token)
                        self.token = token
                        print(f'✅ Login realizado com sucesso!\n')
                        return token
                
                # Se não funcionou com JSON, tenta com form-urlencoded
                response = requests.post(url, data=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    token = (
                        data.get('token')
                        or data.get('Token')
                        or data.get('access_token')
                        or data.get('AccessToken')
                    )
                    
                    if token:
                        set_key(self.env_file, '3S_TOKEN', token)
                        self.token = token
                        print(f'✅ Login realizado com sucesso!\n')
                        return token
                
                print(f'⚠️ Tentativa {idx} falhou: {response.status_code}')
                
            except requests.exceptions.RequestException as e:
                print(f'⚠️ Tentativa {idx} com erro: {e}')
                continue
        
        print(f'❌ Todas as tentativas de login falharam')
        return None
    
    def verificar_token_valido(self):
        """
        Verifica se o token atual ainda é válido
        """
        if not self.token or self.token == '':
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(f'{self.base_url}/ListaVeiculos', headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def obter_token(self):
        """
        Obtém um token válido (reutiliza existente ou gera novo)
        """
        if self.verificar_token_valido():
            print('✅ Token válido encontrado!\n')
            return self.token
        
        print('🔄 Token inválido ou expirado. Gerando novo token...')
        
        # Limpa o token antigo do .env
        set_key(self.env_file, '3S_TOKEN', '')
        self.token = ''
        
        # Recarrega as variáveis de ambiente
        load_dotenv(override=True)
        
        # Tenta fazer login
        return self.validar_login()
    
    def controlar_rate_limit(self):
        """
        Controla o rate limit da API (9 chamadas por minuto)
        """
        self.contador_chamadas += 1
        
        if self.contador_chamadas >= self.max_chamadas_por_minuto:
            print(f'\n⏳ Limite de {self.max_chamadas_por_minuto} chamadas atingido.')
            print(f'⏳ Aguardando {self.tempo_espera} segundos...\n')
            time.sleep(self.tempo_espera)
            self.contador_chamadas = 0
    
    def carregar_posicoes_existentes(self):
        """
        Carrega o arquivo JSON existente com as posições
        Se não existir, retorna lista vazia
        """
        if os.path.exists(self.arquivo_posicoes):
            try:
                with open(self.arquivo_posicoes, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    print(f'📂 Arquivo existente carregado: {len(dados)} registros\n')
                    return dados
            except Exception as e:
                print(f'⚠️ Erro ao carregar arquivo existente: {e}')
                return []
        else:
            print(f'📂 Arquivo não existe. Será criado um novo.\n')
            return []
    
    def obter_id_veiculo(self, posicao):
        """
        Tenta extrair o ID do veículo de diferentes campos possíveis
        """
        return (
            posicao.get('idVeiculo')
            or posicao.get('IdVeiculo')
            or posicao.get('id')
            or posicao.get('Id')
            or posicao.get('VeiculoId')
            or posicao.get('veiculoId')
        )
    
    def obter_placa(self, posicao):
        """
        Tenta extrair a Placa do veículo de diferentes campos possíveis
        """
        return (
            posicao.get('Placa')
            or posicao.get('placa')
            or posicao.get('PLACA')
            or 'SEM_PLACA'
        )
    
    def mesclar_posicoes(self, posicoes_antigas, posicoes_novas):
        """
        Mescla as posições antigas com as novas:
        - Se o veículo não existe, adiciona
        - Se as informações mudaram, atualiza
        - Se o veículo não foi localizado na nova busca, mantém o antigo
        """
        # Cria um dicionário com as posições antigas indexadas por idVeiculo
        mapa_antigo = {}
        for posicao in posicoes_antigas:
            id_veiculo = self.obter_id_veiculo(posicao)
            if id_veiculo:
                mapa_antigo[id_veiculo] = posicao
        
        # Estatísticas
        novos = 0
        atualizados = 0
        mantidos = 0
        
        # Atualiza ou adiciona as novas posições
        for posicao_nova in posicoes_novas:
            id_veiculo = self.obter_id_veiculo(posicao_nova)
            
            if not id_veiculo:
                continue
            
            if id_veiculo in mapa_antigo:
                # Verifica se houve mudança
                if mapa_antigo[id_veiculo] != posicao_nova:
                    mapa_antigo[id_veiculo] = posicao_nova
                    atualizados += 1
                else:
                    mantidos += 1
            else:
                # Novo veículo
                mapa_antigo[id_veiculo] = posicao_nova
                novos += 1
        
        # Converte o dicionário de volta para lista
        resultado = list(mapa_antigo.values())
        
        # Exibe estatísticas
        print(f'📊 Estatísticas do merge:')
        print(f'   ➕ Novos veículos: {novos}')
        print(f'   🔄 Atualizados: {atualizados}')
        print(f'   ✅ Mantidos: {mantidos}')
        print(f'   📦 Total no arquivo: {len(resultado)}\n')
        
        return resultado
    
    def gerar_resumo(self, posicoes):
        """
        Gera um arquivo resumo com apenas Placa e idVeiculo
        """
        resumo = []
        
        for posicao in posicoes:
            id_veiculo = self.obter_id_veiculo(posicao)
            placa = self.obter_placa(posicao)
            
            if id_veiculo:
                resumo.append({
                    'Placa': placa,
                    'idVeiculo': id_veiculo
                })
        
        # Ordena por Placa
        resumo.sort(key=lambda x: x['Placa'])
        
        return resumo
    
    def obter_todas_posicoes(self):
        """
        Obtém a última posição de TODOS os veículos de uma vez
        Usando id_veiculo = 0 conforme documentação da API
        """
        token = self.obter_token()
        
        if not token:
            print('❌ Não foi possível obter token válido')
            return None
        
        url = f'{self.base_url}/ListaUltimaPosicaoVeiculos/0'
        headers = {'Authorization': f'Bearer {token}'}
        
        print('📍 Buscando posições de TODOS os veículos...\n')
        
        max_tentativas = 3
        tentativa = 0
        
        while tentativa < max_tentativas:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Incrementa contador de chamadas
                self.controlar_rate_limit()
                
                posicoes = response.json()
                
                # Verifica se retornou erro de rate limit
                if isinstance(posicoes, list) and len(posicoes) > 0:
                    if 'ErroProcessamento' in posicoes[0]:
                        erro = posicoes[0]['ErroProcessamento']
                        
                        if '3S.1040' in erro:  # Excesso de chamadas
                            print(f'⚠️ Rate limit atingido. Aguardando {self.tempo_espera} segundos...')
                            time.sleep(self.tempo_espera)
                            self.contador_chamadas = 0
                            tentativa += 1
                            continue
                        else:
                            print(f'❌ Erro ao buscar posições: {erro}')
                            return None
                
                print(f'✅ {len(posicoes)} posições obtidas com sucesso!\n')
                return posicoes
                
            except requests.exceptions.RequestException as e:
                print(f'❌ Erro ao obter posições: {e}')
                tentativa += 1
                if tentativa < max_tentativas:
                    print(f'🔄 Tentativa {tentativa + 1}/{max_tentativas}...')
                    time.sleep(5)
        
        return None
    
    def processar_todas_posicoes(self):
        """
        Função principal que processa todas as posições dos veículos
        Com merge inteligente e geração de arquivo resumo
        """
        print('🚀 Iniciando processamento...\n')
        print('='*60)
        
        # PASSO 1: Carrega posições existentes
        posicoes_antigas = self.carregar_posicoes_existentes()
        
        # PASSO 2: Busca todas as posições novas da API
        posicoes_novas = self.obter_todas_posicoes()
        
        if not posicoes_novas:
            print('⚠️ Nenhuma posição nova encontrada. Mantendo arquivo existente.')
            
            # Se tem arquivo antigo, mantém ele
            if posicoes_antigas:
                print(f'✅ Arquivo mantido: {self.arquivo_posicoes} ({len(posicoes_antigas)} registros)')
            
            return posicoes_antigas
        
        # PASSO 3: Mescla as posições (antigas + novas)
        posicoes_finais = self.mesclar_posicoes(posicoes_antigas, posicoes_novas)
        
        # PASSO 4: Salva o arquivo completo de posições
        with open(self.arquivo_posicoes, 'w', encoding='utf-8') as f:
            json.dump(posicoes_finais, f, ensure_ascii=False, indent=2)
        
        print(f'✅ Arquivo atualizado: {self.arquivo_posicoes}')
        
        # PASSO 5: Gera e salva o arquivo resumo
        resumo = self.gerar_resumo(posicoes_finais)
        
        with open(self.arquivo_resumo, 'w', encoding='utf-8') as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)
        
        print(f'✅ Arquivo resumo gerado: {self.arquivo_resumo}')
        
        print('='*60)
        print(f'✅ Processamento concluído!')
        print(f'📄 Arquivo completo: {self.arquivo_posicoes} ({len(posicoes_finais)} registros)')
        print(f'📄 Arquivo resumo: {self.arquivo_resumo} ({len(resumo)} registros)')
        print('='*60)
        
        return posicoes_finais


if __name__ == '__main__':
    api = API3S()
    api.processar_todas_posicoes()