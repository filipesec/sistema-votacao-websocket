from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import json
import os
import hashlib

# Configuracao dos diretorios do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Cria instancia principal do FastAPI
app = FastAPI(title="Sistema de Votacao Musical")

# Configura CORS para permitir requisicoes de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta diretorio de arquivos estaticos do frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Classe responsavel por gerenciar toda a logica de votacao
class GerenciadorVotacao:
    
    def __init__(self):
        self.reiniciar_votacao()
        
    def reiniciar_votacao(self):
        # Define a estrutura da enquete musical
        self.enquete_atual = {
            'id': 'musical',
            'pergunta': 'Qual seu gênero musical favorito?',
            'opcoes': [
                'Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro', 
                'Axe', 'Samba', 'Eletronica', 'Forro', 'Rap', 
                'MPB', 'Pagode', 'Reggae'
            ]
        }
        # Inicializa contador de votos para cada opcao
        self.votos = {opcao: 0 for opcao in self.enquete_atual['opcoes']}
        # Limpa conjunto de clientes que ja votaram
        self.clientes_votaram = set()

    def _gerar_hash_cliente(self, client_info: str) -> str:
        # Gera um hash único baseado nas informações do cliente
        return hashlib.md5(client_info.encode()).hexdigest()

    # Registra um voto para uma opcao especifica
    def registrar_voto(self, opcao: str, client_hash: str) -> bool:
        # Verifica se cliente ja votou
        if client_hash in self.clientes_votaram:
            return False
        # Verifica se a opcao e valida
        if opcao in self.votos:
            # Incrementa contador de votos da opcao
            self.votos[opcao] += 1
            # Marca cliente como tendo votado
            self.clientes_votaram.add(client_hash)
            return True
        return False
    
    # Retorna os resultados atauis da votacao
    def obter_resultados(self) -> dict:
        # Calcula total de votos
        total = sum(self.votos.values())
        resultados = []
        
        # Constroi lista de resultados para cada opcao
        for opcao in self.enquete_atual['opcoes']:
            votos = self.votos[opcao]
            resultados.append({
                'opcao': opcao,
                'votos': votos,
            })
        
        # Retorna estrutura completa dos resultados
        return {
            'enquete_id': self.enquete_atual['id'],
            'pergunta': self.enquete_atual['pergunta'],
            'opcoes': resultados,
            'total_votos': total
        }

gerenciador = GerenciadorVotacao()

# Lista para armazenar todas as conexoes websocket ativas
conexoes_ativas = []

def obter_ip_cliente(websocket: WebSocket) -> str:
    # Obtem o IP do cliente da conexao WebSocket
    try:
        # Tenta obter o IP do cliente
        client_host = websocket.client.host
        return client_host if client_host else "unknown"
    except:
        return "unknown"

# Endpoint WebSocket para comunicacao em tempo real
# Gerencia conexoes votos e broadcast de resultados
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Aceita conexao do cliente
    await websocket.accept()
    
    # Obtem IP do cliente para identificar unicamente
    client_ip = obter_ip_cliente(websocket)
    
    # Gera hash unico baseado no IP e o User-Agent
    client_info = f"{client_ip}"
    client_hash = gerenciador._gerar_hash_cliente(client_info)
    
    print(f"Novo cliente conectado: {client_ip} -> Hash: {client_hash}")
    
    # Adiciona conexao a lista de ativas
    conexoes_ativas.append(websocket)
    
    try:
        # Envia estrutura da enquete atual para o cliente
        await websocket.send_json({
            'tipo': 'enquete_atual',
            'enquete': gerenciador.enquete_atual
        })
        
        # Verifica se este cliente ja votou
        ja_votou = client_hash in gerenciador.clientes_votaram
        
        # Envia resultados atuais para o cliente junto com informacao se ja votou
        resultados = gerenciador.obter_resultados()
        await websocket.send_json({
            'tipo': 'resultados_atualizados',
            **resultados,
            'ja_votou': ja_votou  # Informa ao frontend se ja votou
        })
        
        # Loop principal para receber mensagens do cliente
        while True:
            # Aguarda mensagem do cliente
            dados = await websocket.receive_text()
            # Converte JSON string para dicionario
            dados_json = json.loads(dados)
            
            # Processa acao de votar
            if dados_json.get('acao') == 'votar':
                opcao = dados_json['opcao']
                
                # Tenta registrar o voto usando o hash do cliente
                sucesso = gerenciador.registrar_voto(opcao, client_hash)
                
                if sucesso:
                    print(f"Voto registrado: {opcao} para cliente {client_ip}")
                    
                    # Obtem resultados atualizados
                    resultados_atualizados = gerenciador.obter_resultados()
                    
                    # Envia resultados atualizados para todos os clientes conectados
                    for conexao in conexoes_ativas:
                        try:
                            await conexao.send_json({
                                'tipo': 'resultados_atualizados',
                                **resultados_atualizados
                            })
                        except:
                            # Remove conexoes problematicas da lista
                            if conexao in conexoes_ativas:
                                conexoes_ativas.remove(conexao)
                else:
                    # Cliente ja votou envia mensagem de erro
                    print(f"Tentativa de voto duplicado: {client_ip}")
                    await websocket.send_json({
                        'tipo': 'erro',
                        'mensagem': 'Voce ja votou nesta enquete!'
                    })
                    
    except WebSocketDisconnect:
        # Remove conexao quando cliente desconecta
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)
        print(f"Cliente desconectado: {client_ip}")

# Serve o favicon para evitar erro 404
@app.get("/favicon.ico")
async def servir_favicon():
    favicon_path = os.path.join(FRONTEND_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    # Retorna um icone vazio se nao existir
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/x-icon")

# Serve o arquivo HTML principal do frontend
@app.get("/")
async def servir_pagina_principal():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

# Serve arquivo CSS
@app.get("/style.css")
async def servir_css():
    css_path = os.path.join(FRONTEND_DIR, "style.css")
    return FileResponse(css_path)

# Serve arquivo JavaScript
@app.get("/script.js")
async def servir_js():
    js_path = os.path.join(FRONTEND_DIR, "script.js")
    return FileResponse(js_path)

# Serve os arquivos de audio
@app.get("/Sons/{arquivo}")
async def servir_som(arquivo: str):
    sons_dir = os.path.join(FRONTEND_DIR, "Sons")
    arquivo_path = os.path.join(sons_dir, arquivo)
    # Verifica se arquivo existe antes de servir
    if os.path.exists(arquivo_path):
        return FileResponse(arquivo_path)
    else:
        return {"erro": f"Arquivo de áudio não encontrado: {arquivo}"}, 404

# Serve as capas dos albuns
@app.get("/Capas/{arquivo}")
async def servir_capa(arquivo: str):
    capas_dir = os.path.join(FRONTEND_DIR, "Capas")
    arquivo_path = os.path.join(capas_dir, arquivo)
    # Verifica se arquivo existe antes de servir
    if os.path.exists(arquivo_path):
        return FileResponse(arquivo_path)
    else:
        return {"erro": f"Arquivo de capa não encontrado: {arquivo}"}, 404

# Ponto de entrada para execucao direta do servidor
if __name__ == "__main__":
    # Inicia servidor uvicorn na porta 80
    print("Servidor de votação musical iniciado...")
    print("Servidor rodando na porta 80")
    uvicorn.run(app, host="0.0.0.0", port=80)