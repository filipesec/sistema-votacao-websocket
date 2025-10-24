from collections import defaultdict

class GerenciadorVotacao:
    def __init__(self):
        # ENQUETE FIXA
        self.enquete_atual = {
            'pergunta': 'Qual seu estilo musical favorito?',
            'opcoes': [
                'Rock', 'Pop', 'Sertanejo', 'Funk', 'MPB', 'Eletrônica',
                'Hip Hop/Rap', 'Samba', 'Pagode', 'Forró', 'Axé', 
                'Jazz', 'Reggae', 'Metal', 'Gospel', 'Sertanejo Universitário',
                'Funk Carioca', 'Brega', 'Arrocha'
            ]
        }
        self.votos = defaultdict(int)
        self.clientes_votaram = set()
    
    def registrar_voto(self, opcao, client_id):
        if opcao not in self.enquete_atual['opcoes']:
            return False
        
        if client_id in self.clientes_votaram:
            return False
        
        self.votos[opcao] += 1
        self.clientes_votaram.add(client_id)
        return True
    
    def obter_resultados(self):
        return {
            'pergunta': self.enquete_atual['pergunta'],
            'dados': dict(self.votos)
        }
    
    def obter_enquete_atual(self):
        return self.enquete_atual