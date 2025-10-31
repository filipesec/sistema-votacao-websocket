const socket = new WebSocket("wss://previsible-dorotha-perturbingly.ngrok-free.dev/ws");

let chart = null;
let jaVotou = false;

// === CONFIGURAÇÃO INICIAL DO GRÁFICO ===
const ctx = document.getElementById('grafico');
let votos = JSON.parse(localStorage.getItem('votos')) || Array(13).fill(0);

// Inicializar gráfico
chart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: [
      'Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro',
      'Axé', 'Samba', 'Eletrônica', 'Forró', 'Rap', 'MPB', 'Pagode', 'Reggae'
    ],
    datasets: [{
      label: 'Votos',
      data: votos,
      backgroundColor: [
        '#d84315', '#ff4081', '#ff9100', '#8bc34a', '#ffb300',
        '#ff6f00', '#795548', '#00bcd4', '#ff7043', '#9c27b0',
        '#4caf50', '#ffca28', '#00acc1'
      ],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 1500,
      easing: 'easeOutBounce'
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          font: { size: 14 },
          color: '#333'
        }
      }
    }
  }
});

// === CONFIGURAÇÃO DOS SONS E DESCRIÇÕES ===
const sons = [
  '/Sons/Rock.mp3',
  '/Sons/Pop.mp3',
  '/Sons/Funk.mp3',
  '/Sons/Sertanejo.mp3',
  '/Sons/Piseiro.mp3',
  '/Sons/Axé.mp3',
  '/Sons/Samba.mp3',
  '/Sons/Eletrônica.mp3',
  '/Sons/Forró.mp3',
  '/Sons/Rap.mp3',
  '/Sons/MPB.mp3',
  '/Sons/Pagode.mp3',
  '/Sons/Reggae.mp3'
];

const descricoes = [
  '🎸 O Rock é marcado por guitarras elétricas e bateria intensa, com bandas lendárias e muita energia.',
  '🎤 O Pop traz melodias cativantes e grande apelo popular, dominando as paradas musicais.',
  '🎶 O Funk é o ritmo dançante das periferias, com batidas fortes e muito swing.',
  '🤠 O Sertanejo fala de amor, saudade e vida no interior, com duplas e vozes marcantes.',
  '💃 O Piseiro é o som das festas nordestinas, alegre e contagiante.',
  '🌞 O Axé é pura energia baiana, perfeito para dançar e celebrar.',
  '🥁 O Samba é o ritmo da alma brasileira, com percussão marcante e letras cheias de emoção.',
  '🎧 A Eletrônica é moderna, com batidas pulsantes e atmosferas digitais vibrantes.',
  '💃 O Forró é a dança típica do Nordeste, com sanfona, zabumba e muito calor humano.',
  '🎤 O Rap traz rimas intensas e mensagens sociais fortes, com batidas urbanas.',
  '🎵 A MPB mistura ritmos nacionais com poesia e melodias sofisticadas.',
  '🎶 O Pagode é o samba mais leve e romântico, ideal para cantar junto.',
  '🌴 O Reggae tem vibrações tranquilas e mensagens de paz e liberdade.'
];

const descricaoDiv = document.getElementById('descricao');
const botoes = document.querySelectorAll('#botoes button');

// === WEBSOCKET EVENTOS ===
socket.onopen = () => {
    console.log("Conectado ao servidor WebSocket");
};

socket.onclose = () => {
    console.log("Conexão encerrada");
};

socket.onerror = (error) => {
    console.error("Erro:", error);
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.tipo === "resultados_atualizados") {
        atualizarResultados(data);
    }
    else if (data.tipo === "voto_registrado") {
        jaVotou = true;
        console.log("Voto registrado com sucesso:", data.opcao);
        // Desabilitar botões após votar
        botoes.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = "0.6";
        });
    }
    else if (data.tipo === "erro") {
        alert(data.mensagem);
    }
};

// === FUNÇÕES ===
function enviarVoto(opcao) {
    if (jaVotou) {
        alert("Você já votou! Aguarde os resultados.");
        return;
    }
    
    if (socket.readyState === WebSocket.OPEN) {
        const mensagem = { acao: "votar", opcao: opcao };
        socket.send(JSON.stringify(mensagem));
        console.log("Voto enviado:", mensagem);
    } else {
        alert("Não conectado ao servidor. Recarregue a página.");
    }
}

function atualizarResultados(data) {
    // Atualizar gráfico com dados do servidor
    const opcoesServidor = ['Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro', 'Axe', 'Samba', 'Eletronica', 'Forro', 'Rap', 'MPB', 'Pagode', 'Reggae'];
    const novosVotos = Array(13).fill(0);
    
    data.opcoes.forEach(item => {
        const index = opcoesServidor.indexOf(item.opcao);
        if (index !== -1) {
            novosVotos[index] = item.votos;
        }
    });
    
    chart.data.datasets[0].data = novosVotos;
    chart.update();
    
    // Atualizar localStorage
    localStorage.setItem('votos', JSON.stringify(novosVotos));
}

// === EVENTOS DOS BOTÕES ===
botoes.forEach((botao, index) => {
    botao.addEventListener('click', () => {
        const opcoes = [
            'Rock', 'Pop', 'Funk', 'Sertanejo', 'Piseiro',
            'Axe', 'Samba', 'Eletronica', 'Forro', 'Rap',
            'MPB', 'Pagode', 'Reggae'
        ];
        
        const opcao = opcoes[index];
        
        // Enviar voto via WebSocket
        enviarVoto(opcao);
        
        // Tocar som - AGORA COM CAMINHO CORRETO
        try {
            const audio = new Audio(sons[index]);
            audio.currentTime = 0;
            audio.play().catch(err => {
                console.warn('Não foi possível reproduzir o som:', err);
            });
        } catch (error) {
            console.error('Erro ao carregar o som:', error);
        }

        // Mostrar descrição
        if (descricaoDiv) {
            descricaoDiv.textContent = descricoes[index];
            descricaoDiv.classList.add('mostrar');
        }

        // Efeito visual
        botao.classList.add('clicado');
        setTimeout(() => botao.classList.remove('clicado'), 200);
    });
});