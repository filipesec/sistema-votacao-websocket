from collections import defaultdict

class GerenciadorVotacao:
    def __init__(self):
        self.enquete_atual = None
        self.votos = defaultdict(int)
        self.clientes_votaram = set()
    
    def definir_enquete(self, pergunta, opcoes):
        self.enquete_atual = {
            'pergunta': pergunta,
            'opcoes': opcoes
        }
        self.votos.clear()
        self.clientes_votaram.clear()
        return True
    
    def registrar_voto(self, opcao, client_id):
        if not self.enquete_atual:
            return False
        
        if opcao not in self.enquete_atual['opcoes']:
            return False
        
        if client_id in self.clientes_votaram:
            return False
        
        self.votos[opcao] += 1
        self.clientes_votaram.add(client_id)
        return True
    
    def obter_resultados(self):
        if not self.enquete_atual:
            return {}
        
        total = sum(self.votos.values())
        
        resultados = {
            'pergunta': self.enquete_atual['pergunta'],
            'opcoes': []
        }
        
        for opcao in self.enquete_atual['opcoes']:
            qtd_votos = self.votos[opcao]
            porcentagem = (qtd_votos / total * 100) if total > 0 else 0
            resultados['opcoes'].append({
                'opcao': opcao,
                'votos': qtd_votos,
                'porcentagem': round(porcentagem, 1)
            })
        
        return resultados
    
    def obter_enquete_atual(self):
        return self.enquete_atual