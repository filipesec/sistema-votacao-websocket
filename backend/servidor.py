from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

#Configuracao dos diretorios do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

#Cria instancia principal do FastAPI
app = FastAPI(title="Sistema de Votacao Musical")

#Configura CORS para permitir requisicoes de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Monta diretorio de arquivos estaticos do frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

#Classe responsavel por gerenciar toda a logica de votacao
class GerenciadorVotacao:
    
    def __init__(self):
        #Define a estrutura da enquete musical
        self.enquete_atual = {
            'id': 'musical',
            'pergunta': 'Qual seu gênero musical favorito?',
            'opcoes': [
                'Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro', 
                'Axe', 'Samba', 'Eletronica', 'Forro', 'Rap', 
                'MPB', 'Pagode', 'Reggae'
            ]
        }
        #Inicializa contador de votos para cada opcao
        self.votos = {opcao: 0 for opcao in self.enquete_atual['opcoes']}
        #Conjunto para armazenar ids dos clientes que já votaram
        self.clientes_votaram = set()

        #Registra um voto para uma opcao especifica
    def registrar_voto(self, opcao: str, client_id: str) -> bool:
        #Verifica se cliente ja votou
        if client_id in self.clientes_votaram:
            return False
        #Verifica se a opcao e valida
        if opcao in self.votos:
            #Incrementa contador de votos da opcao
            self.votos[opcao] += 1
            #Marca cliente como tendo votado
            self.clientes_votaram.add(client_id)
            return True
        return False
    
    #Retorna os resultados atauis da votacao
    def obter_resultados(self) -> dict:
        #Calcula total de votos
        total = sum(self.votos.values())
        resultados = []
        
        #Constroi lista de resultados para cada opcao
        for opcao in self.enquete_atual['opcoes']:
            votos = self.votos[opcao]
            resultados.append({
                'opcao': opcao,
                'votos': votos,
            })
        
        #Retorna estrutura completa dos resultados
        return {
            'enquete_id': self.enquete_atual['id'],
            'pergunta': self.enquete_atual['pergunta'],
            'opcoes': resultados,
            'total_votos': total
        }

#Instancia global do gerenciador de votacao
gerenciador = GerenciadorVotacao()

#Lista para armazenar todas as conexoes websocket ativas
conexoes_ativas = []

#Endpoint WebSocket para comunicacao em tempo real
#Gerencia conexoes votos e broadcast de resultados
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    #Aceita conexao do cliente
    await websocket.accept()
    #Gera id unico baseado no objeto WebSocket
    client_id = str(id(websocket))
    #Adiciona conexao a lista de ativas
    conexoes_ativas.append(websocket)
    
    try:
        #Envia estrutura da enquete atual para o cliente
        await websocket.send_json({
            'tipo': 'enquete_atual',
            'enquete': gerenciador.enquete_atual
        })
        
        #Envia resultados atuais para o cliente
        resultados = gerenciador.obter_resultados()
        await websocket.send_json({
            'tipo': 'resultados_atualizados',
            **resultados
        })
        
        #Loop principal para receber mensagens do cliente
        while True:
            # Aguarda mensagem do cliente
            dados = await websocket.receive_text()
            #Converte JSON string para dicionario
            dados_json = json.loads(dados)
            
            #Processa acao de votar
            if dados_json.get('acao') == 'votar':
                opcao = dados_json['opcao']
                
                #Tenta registrar o voto
                sucesso = gerenciador.registrar_voto(opcao, client_id)
                
                if sucesso:
                    #Confirma voto registrado para o cliente
                    await websocket.send_json({
                        'tipo': 'voto_registrado',
                        'opcao': opcao,
                        'mensagem': f'Voto em {opcao} registrado com sucesso!'
                    })
                    
                    #Obtem resultados atualizados
                    resultados_atualizados = gerenciador.obter_resultados()
                    
                    #Envia resultados atualizados para todos os clientes conectados
                    for conexao in conexoes_ativas:
                        try:
                            await conexao.send_json({
                                'tipo': 'resultados_atualizados',
                                **resultados_atualizados
                            })
                        except:
                            #Remove conexões problematicas da lista
                            if conexao in conexoes_ativas:
                                conexoes_ativas.remove(conexao)
                else:
                    #Cliente ja votou envia mensagem de erro
                    await websocket.send_json({
                        'tipo': 'erro',
                        'mensagem': 'Voce ja votou nesta enquete!'
                    })
                    
    except WebSocketDisconnect:
        #Remove conexão quando cliente desconecta
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)

#Serve o arquivo HTML principal do frontend
@app.get("/")
async def servir_pagina_principal():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)
#Serve os arquivos de audio
@app.get("/Sons/{arquivo}")
async def servir_som(arquivo: str):
    sons_dir = os.path.join(FRONTEND_DIR, "Sons")
    arquivo_path = os.path.join(sons_dir, arquivo)
    # Verifica se arquivo existe antes de servir
    if os.path.exists(arquivo_path):
        return FileResponse(arquivo_path)
    else:
        return {"erro": f"Arquivo de áudio não encontrado: {arquivo}"}, 404

#Ponto de entrada para execucao direta do servidor
if __name__ == "__main__":

    import uvicorn
    # Inicia servidor UVicorn na porta 80
    print("Servidor de votação musical inciado...")
    print("Servidor rodando na porta 80")
    uvicorn.run(app, host="0.0.0.0", port=80)