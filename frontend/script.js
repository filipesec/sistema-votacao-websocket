const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = new WebSocket(`${protocol}//${window.location.host}/ws`);

let chart = null;
let jaVotou = false;

const ctx = document.getElementById('grafico');
let votos = JSON.parse(localStorage.getItem('votos')) || Array(13).fill(0);

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
        '#d84315', '#ff4081', '#ff9100', '#8bc34a', '#ffb300',
        '#ff6f00', '#795548', '#00bcd4', '#ff7043', '#9c27b0',
        '#4caf50', '#ffca28', '#00acc1'
      ],
      borderColor: '#fff',
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#f1f5f9', font: { size: 14 } } }
    }
  }
});

const botoes = document.querySelectorAll('#botoes button');
const modal = document.getElementById('modal');
const capaAlbum = document.getElementById('capaAlbum');
const nomeMusica = document.getElementById('nomeMusica');
const artista = document.getElementById('artista');
const album = document.getElementById('album');
const audioGenero = document.getElementById('audioGenero');
const descricao = document.getElementById('descricao');
const confirmar = document.getElementById('confirmar');
const cancelar = document.getElementById('cancelar');

const audios = [
  'Sons/Rock.mp3', 'Sons/Pop.mp3', 'Sons/Funk.mp3', 'Sons/Sertanejo.mp3',
  'Sons/Piseiro.mp3', 'Sons/Axé.mp3', 'Sons/Samba.mp3', 'Sons/Eletrônica.mp3',
  'Sons/Forró.mp3', 'Sons/Rap.mp3', 'Sons/MPB.mp3', 'Sons/Pagode.mp3', 'Sons/Reggae.mp3'
];

const capas = [
  'Capas/Rock.jpeg', 'Capas/Pop.jpeg', 'Capas/Funk.jpeg', 'Capas/Sertanejo.jpeg',
  'Capas/Piseiro.jpeg', 'Capas/Axé.jpeg', 'Capas/Samba.jpeg', 'Capas/Eletrônica.jpg',
  'Capas/Forró.jpeg', 'Capas/Rap.jpeg', 'Capas/MPB.jpeg', 'Capas/Pagode.jpeg', 'Capas/Reggae.jpg'
];

const musicasInfo = [
  { nome: 'Sweet Child O’ Mine', artista: 'Guns N’ Roses', album: 'Appetite For Destruction' },
  { nome: 'Thriller', artista: 'Michael Jackson', album: 'Thriller' },
  { nome: 'Vou Desafiar Você', artista: 'MC Sapao, DJ Detonna', album: 'Vou Desafiar Você' },
  { nome: 'Evidências', artista: 'Chitãozinho & Xororó', album: 'Cowboy do Asfalto' },
  { nome: 'Letícia', artista: 'Zé Vaqueiro', album: 'O Original' },
  { nome: '100% Você - Ao Vivo', artista: 'Bell Marques', album: 'Só as Antigas (Ao Vivo)' },
  { nome: 'Cheia de Manias', artista: 'Raça Negra', album: 'Cheia de Manias' },
  { nome: 'Titanium (feat. Sia)', artista: 'David Guetta, Sia', album: 'Nothing but the Beat (Ultimate Edition)' },
  { nome: 'Planeta de Cores', artista: 'Forrozao Tropykalia', album: 'Planeta de Cores, Vol. 7' },
  { nome: 'Negro Drama', artista: 'Racionais MC’s', album: 'Nada Como um Dia Após o Outro Dia, Vol. 1 & 2' },
  { nome: 'Garoto de Aluguel (Taxi Boy) [Ao Vivo]', artista: 'Zé Ramalho', album: 'Zé Ramalho Ao Vivo 2005 (Deluxe)' },
  { nome: 'Deixa Acontecer - Ao Vivo', artista: 'Grupo Revelação', album: 'Ao Vivo - Na Palma da Mão' },
  { nome: 'Is This Love', artista: 'Bob Marley & The Wailers', album: 'Kaya' }
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
  '🎼 O Forró é a dança típica do Nordeste, com sanfona, zabumba e muito calor humano.',
  '🎙️ O Rap traz rimas intensas e mensagens sociais fortes, com batidas urbanas.',
  '🎵 A MPB mistura ritmos nacionais com poesia e melodias sofisticadas.',
  '🪕 O Pagode é o samba mais leve e romântico, ideal para cantar junto.',
  '🌴 O Reggae tem vibrações tranquilas e mensagens de paz e liberdade.'
];

let generoSelecionado = null;

botoes.forEach((botao, index) => {
  botao.addEventListener('click', () => {
    generoSelecionado = index;

    capaAlbum.src = capas[index];
    nomeMusica.textContent = musicasInfo[index].nome;
    artista.textContent = `🎤 Artista: ${musicasInfo[index].artista}`;
    album.textContent = `💿 Álbum: ${musicasInfo[index].album}`;
    descricao.textContent = descricoes[index];
    audioGenero.src = audios[index];

    modal.style.display = 'flex';
  });
});

cancelar.addEventListener('click', () => {
  modal.style.display = 'none';
  audioGenero.pause();
});

confirmar.addEventListener('click', () => {
  if (generoSelecionado !== null) {
    votos[generoSelecionado]++;
    grafico.data.datasets[0].data = votos;
    grafico.update();
    localStorage.setItem('votos', JSON.stringify(votos));
    modal.style.display = 'none';
    audioGenero.pause();

    // rolar até o gráfico
    document.getElementById('grafico-container').scrollIntoView({ behavior: 'smooth' });
  }
});