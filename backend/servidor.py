from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
import os

# Obter o diretório atual do script (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Frontend está no mesmo nível que backend: ../frontend
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI(title="Sistema de Votacao Musical")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos do frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

class GerenciadorVotacao:
    def __init__(self):
        self.enquete_atual = {
            'id': 'musical',
            'pergunta': 'Qual seu estilo musical favorito?',
            'opcoes': ['Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro', 'Axe', 'Samba', 'Eletronica']
        }
        self.votos = {opcao: 0 for opcao in self.enquete_atual['opcoes']}
        self.clientes_votaram = set()

    def registrar_voto(self, opcao: str, client_id: str) -> bool:
        if client_id in self.clientes_votaram:
            return False
        if opcao in self.votos:
            self.votos[opcao] += 1
            self.clientes_votaram.add(client_id)
            return True
        return False

    def obter_resultados(self) -> dict:
        total = sum(self.votos.values())
        resultados = []
        
        for opcao in self.enquete_atual['opcoes']:
            votos = self.votos[opcao]
            porcentagem = (votos / total * 100) if total > 0 else 0
            resultados.append({
                'opcao': opcao,
                'votos': votos,
                'porcentagem': round(porcentagem, 1)
            })
        
        return {
            'enquete_id': self.enquete_atual['id'],
            'pergunta': self.enquete_atual['pergunta'],
            'opcoes': resultados,
            'total_votos': total
        }

gerenciador = GerenciadorVotacao()
conexoes_ativas = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(id(websocket))
    conexoes_ativas.append(websocket)
    
    try:
        await websocket.send_json({
            'tipo': 'enquete_atual',
            'enquete': gerenciador.enquete_atual
        })
        
        resultados = gerenciador.obter_resultados()
        await websocket.send_json({
            'tipo': 'resultados_atualizados',
            **resultados
        })
        
        while True:
            dados = await websocket.receive_text()
            dados_json = json.loads(dados)
            
            if dados_json.get('acao') == 'votar':
                opcao = dados_json['opcao']
                
                sucesso = gerenciador.registrar_voto(opcao, client_id)
                
                if sucesso:
                    await websocket.send_json({
                        'tipo': 'voto_registrado',
                        'opcao': opcao,
                        'mensagem': f'Voto em {opcao} registrado com sucesso!'
                    })
                    
                    resultados_atualizados = gerenciador.obter_resultados()
                    
                    for conexao in conexoes_ativas:
                        try:
                            await conexao.send_json({
                                'tipo': 'resultados_atualizados',
                                **resultados_atualizados
                            })
                        except:
                            if conexao in conexoes_ativas:
                                conexoes_ativas.remove(conexao)
                else:
                    await websocket.send_json({
                        'tipo': 'erro',
                        'mensagem': 'Voce ja votou nesta enquete!'
                    })
                    
    except WebSocketDisconnect:
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)

# Servir a página HTML principal
@app.get("/")
async def servir_pagina_principal():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

# Servir arquivos CSS e JS individualmente
@app.get("/style.css")
async def servir_css():
    css_path = os.path.join(FRONTEND_DIR, "style.css")
    return FileResponse(css_path)

@app.get("/script.js")
async def servir_js():
    js_path = os.path.join(FRONTEND_DIR, "script.js")
    return FileResponse(js_path)

@app.get("/enquete")
async def obter_enquete():
    return gerenciador.enquete_atual

@app.get("/resultados")
async def obter_resultados():
    return gerenciador.obter_resultados()

@app.get("/estatisticas")
async def obter_estatisticas():
    resultados = gerenciador.obter_resultados()
    return {
        "total_votos": resultados["total_votos"],
        "estilos_disponiveis": len(gerenciador.enquete_atual["opcoes"])
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Servidor de Votacao Musical Iniciando...")
    print(f"Diretorio frontend: {FRONTEND_DIR}")
    print("WebSocket: ws://localhost:8000/ws")
    print("URL: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)