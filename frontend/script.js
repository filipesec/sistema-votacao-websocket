const socket = new WebSocket("wss://previsible-dorotha-perturbingly.ngrok-free.dev/ws");

  socket.onopen = () => console.log("Conectado ao servidor WebSocket");
  socket.onclose = () => console.log("Conexão encerrada");
  socket.onerror = (error) => console.error("Erro:", error);

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.tipo === "resultados_atualizados") {
      updateResults(data.dados); //Função da parte da Juliana
    }
  };

  function enviarVoto(opcao) {
    const mensagem = { acao: "votar", opcao: opcao };
    socket.send(JSON.stringify(mensagem));
    console.log("Voto enviado:", mensagem);
  }

  function updateResults(resultados) {
    // Funcao temporaria (será criada pela Juliana)
    document.getElementById("resultados").innerHTML =
      Object.entries(resultados)
        .map(([opcao, votos]) => '${opcao}: ${votos}')
        .join("<br>");
  }

// === PEGAR O CANVAS DO GRÁFICO ===
const ctx = document.getElementById('grafico');

// === RECUPERAR OS VOTOS ANTERIORES (SE EXISTIREM) ===
let votos = JSON.parse(localStorage.getItem('votos')) || Array(13).fill(0);

// === CRIAR O GRÁFICO ===
const grafico = new Chart(ctx, {
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
        '#d84315', // Rock
        '#ff4081', // Pop
        '#ff9100', // Funk
        '#8bc34a', // Sertanejo
        '#ffb300', // Piseiro
        '#ff6f00', // Axé
        '#795548', // Samba
        '#00bcd4', // Eletrônica
        '#ff7043', // Forró
        '#9c27b0', // Rap
        '#4caf50', // MPB
        '#ffca28', // Pagode
        '#00acc1'  // Reggae
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

// === PEGAR OS BOTÕES ===
const botoes = document.querySelectorAll('#botoes button');

// === CAMINHOS DOS ARQUIVOS DE SOM ===
const sons = [
  'Sons/Rock.mp3',
  'Sons/Pop.mp3',
  'Sons/Funk.mp3',
  'Sons/Sertanejo.mp3',
  'Sons/Piseiro.mp3',
  'Sons/Axé.mp3',
  'Sons/Samba.mp3',
  'Sons/Eletrônica.mp3',
  'Sons/Forró.mp3',
  'Sons/Rap.mp3',
  'Sons/MPB.mp3',
  'Sons/Pagode.mp3',
  'Sons/Reggae.mp3'
];

// === DESCRIÇÕES DAS MÚSICAS ===
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

// === ELEMENTO ONDE A DESCRIÇÃO SERÁ EXIBIDA ===
const descricaoDiv = document.getElementById('descricao');

// === ADICIONAR EVENTO DE CLIQUE EM CADA BOTÃO ===
botoes.forEach((botao, index) => {
  botao.addEventListener('click', () => {

    // Atualiza os votos
    votos[index] += 1;
    grafico.data.datasets[0].data = votos;
    grafico.update();

    // Salva no localStorage
    localStorage.setItem('votos', JSON.stringify(votos));

    // === TOCAR SOM USANDO new Audio() ===
    try {
      const audio = new Audio(sons[index]);
      audio.currentTime = 0;
      audio.play().catch(err => {
        console.warn('Erro ao reproduzir o som:', err);
      });
    } catch (error) {
      console.error('Erro ao carregar o som:', error);
    }

    // === MOSTRAR DESCRIÇÃO ===
    if (descricaoDiv) {
      descricaoDiv.textContent = descricoes[index];
    }

    // Efeito visual do clique
    botao.classList.add('clicado');
    setTimeout(() => botao.classList.remove('clicado'), 200);
  });
});