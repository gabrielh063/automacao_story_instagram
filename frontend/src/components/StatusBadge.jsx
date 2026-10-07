const configuracoes = {
  AGENDADO: {
    classe: "text-bg-primary",
    icone: "bi-clock",
    texto: "Agendado",
  },

  PROCESSANDO: {
    classe: "text-bg-info",
    icone: "bi-arrow-repeat",
    texto: "Publicando",
  },

  PUBLICADO: {
    classe: "text-bg-success",
    icone: "bi-check-circle",
    texto: "Publicado",
  },

  ERRO: {
    classe: "text-bg-danger",
    icone: "bi-exclamation-triangle",
    texto: "Erro",
  },

  CANCELADO: {
    classe: "text-bg-secondary",
    icone: "bi-x-circle",
    texto: "Cancelado",
  },
};

export default function StatusBadge({
  status,
}) {
  const config =
    configuracoes[status] || {
      classe: "text-bg-secondary",
      icone: "bi-question-circle",
      texto: status,
    };

  return (
    <span
      className={`badge ${config.classe}`}
    >
      <i
        className={`bi ${config.icone} me-1`}
      />

      {config.texto}
    </span>
  );
}