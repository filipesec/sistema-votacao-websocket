import asyncio
import websockets
import json
from gerenciador import GerenciadorVotacao

class ServidorVotacao:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.gerenciador = GerenciadorVotacao()
        self.conexoes_ativas = set()
    
    async def handler(self, websocket):
        client_id = f"client_{id(websocket)}"
        self.conexoes_ativas.add(websocket)
        
        try:
            await self.enviar_enquete_atual(websocket)
            
            async for message in websocket:
                dados = json.loads(message)
                acao = dados.get('acao')
                
                if acao == 'votar':
                    await self.processar_voto(websocket, dados, client_id)
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.conexoes_ativas.discard(websocket)
    
    async def enviar_enquete_atual(self, websocket):
        enquete = self.gerenciador.obter_enquete_atual()
        mensagem = {
            'tipo': 'enquete_atual',
            'enquete': enquete
        }
        await websocket.send(json.dumps(mensagem))
        
        resultados = self.gerenciador.obter_resultados()
        mensagem_resultados = {
            'tipo': 'resultados_atualizados',
            **resultados
        }
        await websocket.send(json.dumps(mensagem_resultados))
    
    async def processar_voto(self, websocket, dados, client_id):
        opcao = dados['opcao']
        
        sucesso = self.gerenciador.registrar_voto(opcao, client_id)
        
        if sucesso:
            confirmacao = {
                'tipo': 'voto_registrado',
                'opcao': opcao
            }
            await websocket.send(json.dumps(confirmacao))
            await self.broadcast_resultados()
        else:
            erro = {'tipo': 'erro', 'mensagem': 'Voce ja votou!'}
            await websocket.send(json.dumps(erro))
    
    async def broadcast_resultados(self):
        resultados = self.gerenciador.obter_resultados()
        mensagem = {
            'tipo': 'resultados_atualizados',
            **resultados
        }
        await self.broadcast(mensagem)
    
    async def broadcast(self, mensagem):
        msg_json = json.dumps(mensagem)
        for conexao in self.conexoes_ativas.copy():
            try:
                await conexao.send(msg_json)
            except Exception:
                self.conexoes_ativas.discard(conexao)

async def main():
    servidor = ServidorVotacao()
    async with websockets.serve(servidor.handler, "localhost", 8765):
        print("Servidor de Votacao Musical rodando na porta 8765")
        print("Enquete fixa: 'Qual seu estilo musical favorito?'")
        print(f"Total de estilos disponíveis: {len(servidor.gerenciador.enquete_atual['opcoes'])}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())