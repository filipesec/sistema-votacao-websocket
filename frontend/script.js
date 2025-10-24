const socket = new WebSocket("ws://localhost:8765");

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
