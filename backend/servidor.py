#IMPORT
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import json
import os
import secrets
from typing import Optional

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
        # Limpa conjunto de clientes que ja votaram por cookie
        self.clientes_votaram = set()

    def _gerar_id_usuario(self) -> str:
        # Gera um ID unico para o usuario
        return secrets.token_hex(16)

    # Registra um voto para uma opcao especifica
    def registrar_voto(self, opcao: str, usuario_id: str) -> bool:
        # Verifica se usuario ja votou
        if usuario_id in self.clientes_votaram:
            return False
        # Verifica se a opcao e valida
        if opcao in self.votos:
            # Incrementa contador de votos da opcao
            self.votos[opcao] += 1
            # Marca usuario como tendo votado
            self.clientes_votaram.add(usuario_id)
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

def obter_usuario_id(websocket: WebSocket) -> Optional[str]:
    # Obtem o cookie de usuario_id do WebSocket
    try:
        cookie_header = websocket.headers.get("cookie", "")
        cookies = {}
        for cookie in cookie_header.split(";"):
            if "=" in cookie:
                key, value = cookie.strip().split("=", 1)
                cookies[key] = value
        return cookies.get("usuario_id")
    except:
        return None

# Endpoint WebSocket para comunicacao em tempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Aceita conexao do cliente
    await websocket.accept()
    
    # Obtem usuario_id do cookie
    usuario_id = obter_usuario_id(websocket)
    
    if not usuario_id:
        # So vota com cookie
        await websocket.send_json({
            'tipo': 'erro',
            'mensagem': 'Cookie de usuário não encontrado. Recarregue a página.'
        })
        await websocket.close()
        return
    
    print(f"Novo cliente conectado: {usuario_id}")
    
    # Adiciona conexao a lista de ativas
    conexoes_ativas.append(websocket)
    
    try:
        # Envia estrutura da enquete atual para o cliente
        await websocket.send_json({
            'tipo': 'enquete_atual',
            'enquete': gerenciador.enquete_atual
        })
        
        # Verifica se este cliente ja votou
        ja_votou = usuario_id in gerenciador.clientes_votaram
        
        # Envia resultados atuais para o cliente
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
                
                # Tenta registrar o voto usando o usuario_id do cookie
                sucesso = gerenciador.registrar_voto(opcao, usuario_id)
                
                if sucesso:
                    print(f"Voto registrado: {opcao} para usuario {usuario_id}")
                    
                    # Confirma voto registrado para o cliente
                    await websocket.send_json({
                        'tipo': 'voto_registrado',
                        'opcao': opcao,
                        'mensagem': f'Voto em {opcao} registrado com sucesso!'
                    })
                    
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
                    # Usuario ja votou envia mensagem de erro
                    print(f"Tentativa de voto duplicado: {usuario_id}")
                    await websocket.send_json({
                        'tipo': 'erro',
                        'mensagem': 'Voce ja votou nesta enquete!'
                    })
                    
    except WebSocketDisconnect:
        # Remove conexao quando cliente desconecta
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)
        print(f"Cliente desconectado: {usuario_id}")

# Endpoint para obter um novo usuario_id via HTTP
@app.get("/obter-usuario-id")
async def obter_novo_usuario_id(response: Response):
    usuario_id = gerenciador._gerar_id_usuario()
    
    # Configura o cookie
    response.set_cookie(
        key="usuario_id",
        value=usuario_id,
        max_age=365*24*60*60,  # 1 ano
        httponly=True,
        samesite="lax"
    )
    
    return {"usuario_id": usuario_id}

# Serve o arquivo HTML principal do frontend
@app.get("/")
async def servir_pagina_principal(request: Request, response: Response):
    # Verifica se ja tem cookie na requisicao
    usuario_id = request.cookies.get("usuario_id")
    
    if not usuario_id:
        # Gera novo ID se nao existe cookie
        usuario_id = gerenciador._gerar_id_usuario()
        response.set_cookie(
            key="usuario_id",
            value=usuario_id,
            max_age=365*24*60*60,
            httponly=True,
            samesite="lax"
        )
        print(f"Novo cookie gerado: {usuario_id}")
    
    # Serve o arquivo HTML
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
    if os.path.exists(arquivo_path):
        return FileResponse(arquivo_path)
    else:
        return {"erro": f"Arquivo de áudio não encontrado: {arquivo}"}, 404

# Serve as capas dos albuns
@app.get("/Capas/{arquivo}")
async def servir_capa(arquivo: str):
    capas_dir = os.path.join(FRONTEND_DIR, "Capas")
    arquivo_path = os.path.join(capas_dir, arquivo)
    if os.path.exists(arquivo_path):
        return FileResponse(arquivo_path)
    else:
        return {"erro": f"Arquivo de capa não encontrado: {arquivo}"}, 404

# Ponto de entrada para execucao direta do servidor
if __name__ == "__main__":
    print("Servidor de votação musical iniciado...")
    print("Sistema de prevenção: APENAS COOKIES")
    print("Servidor rodando na porta 80")
    uvicorn.run(app, host="0.0.0.0", port=80)