import { useEffect, useMemo, useState } from "react";

import api from "../services/api";
import Layout from "../components/Layout";
import FeedbackAlert from "../components/FeedbackAlert";
import ConfirmModal from "../components/ConfirmModal";
import AgendarModal from "../components/AgendarModal";

export default function Fotos() {

  const [modalAgendamento, setModalAgendamento] =
  useState(false);

  const [agendando, setAgendando] =
  useState(false);

  const [imagens, setImagens] = useState([]);

  const [carregando, setCarregando] =
    useState(true);

  const [erro, setErro] = useState(null);

  const [busca, setBusca] = useState("");

  const [selecionada, setSelecionada] =
    useState(null);

  const [confirmando, setConfirmando] =
    useState(false);

  const [publicando, setPublicando] =
    useState(false);

  const [feedback, setFeedback] =
    useState(null);

  async function carregarImagens() {
    try {
      setCarregando(true);
      setErro(null);

      const resposta = await api.get(
        "/api/imagens"
      );

      setImagens(
        resposta.data.imagens || []
      );
    } catch (error) {
      setErro(
        error.response?.data?.mensagem ||
          error.response?.data?.erro ||
          "Não foi possível carregar o banco de fotos."
      );
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregarImagens();
  }, []);

  const imagensFiltradas = useMemo(() => {
    const termo = busca
      .trim()
      .toLowerCase();

    if (!termo) {
      return imagens;
    }

    return imagens.filter((imagem) =>
      imagem.nome
        .toLowerCase()
        .includes(termo)
    );
  }, [imagens, busca]);

  function selecionarImagem(imagem) {
    setSelecionada(imagem);
    setFeedback(null);
  }

  function abrirConfirmacao() {
    if (!selecionada) {
      setFeedback({
        tipo: "warning",
        titulo: "Nenhuma imagem selecionada",
        mensagem:
          "Selecione uma foto antes de publicar.",
      });

      return;
    }

    setConfirmando(true);
  }

  async function publicarAgora() {
    if (!selecionada || publicando) {
      return;
    }

    setPublicando(true);
    setFeedback(null);

    /*
     * Uma chave nova representa uma nova
     * ação de publicação.
     *
     * Se a requisição for repetida pela
     * mesma tentativa, reutilizamos esta
     * chave.
     */
    const idempotencyKey =
      crypto.randomUUID();

    try {
      const resposta = await api.post(
        "/api/postagens/publicar-agora",
        {
            imagem_id: selecionada.id,
        },
        {
            headers: {
            "Idempotency-Key": idempotencyKey,
            },
        }
        );

        setConfirmando(false);

        const dados = resposta.data;

        if (
        dados.enfileirada === true ||
        dados.postagem?.status === "AGENDADO"
        ) {
        setFeedback({
            tipo: "info",
            titulo: "Story adicionado à fila",
            mensagem:
            dados.mensagem ||
            "Outra publicação está sendo processada. Este Story será publicado automaticamente em seguida.",
        });

        return;
        }

        if (
        dados.postagem?.status === "PUBLICADO"
        ) {
        setFeedback({
            tipo: "success",
            titulo: "Story publicado",
            mensagem:
            dados.mensagem ||
            "O Story foi publicado com sucesso no Instagram.",
        });

        return;
        }

        setFeedback({
        tipo: "warning",
        titulo: "Publicação recebida",
        mensagem:
            "A solicitação foi recebida, mas a publicação ainda não foi confirmada pelo Instagram.",
        });
    } catch (error) {
      const dados =
        error.response?.data;

      let mensagem =
        dados?.mensagem ||
        "Não foi possível publicar o Story.";

      if (
        dados?.codigo ===
        "FALHA_PUBLICACAO"
      ) {
        mensagem =
          "A publicação não foi concluída. " +
          "A tentativa foi registrada para diagnóstico.";
      }

      setConfirmando(false);

      setFeedback({
        tipo: "danger",
        titulo:
          "Não foi possível publicar",
        mensagem,
      });
    } finally {
      setPublicando(false);
    }
  }

  async function agendarStory(dataHora) {
  if (!selecionada || agendando) {
    return;
  }

  setAgendando(true);
  setFeedback(null);

  const idempotencyKey =
    crypto.randomUUID();

  try {
    const resposta = await api.post(
      "/api/postagens/agendar",
      {
        imagem_id: selecionada.id,
        agendado_para: `${dataHora}:00`,
      },
      {
        headers: {
          "Idempotency-Key":
            idempotencyKey,
        },
      }
    );

    setModalAgendamento(false);

    const dataFormatada =
      new Date(dataHora).toLocaleString(
        "pt-BR",
        {
          dateStyle: "short",
          timeStyle: "short",
        }
      );

    setFeedback({
      tipo: "success",
      titulo: "Story agendado",
      mensagem:
        `A publicação foi agendada para ${dataFormatada}.`,
    });

  } catch (error) {
    const dados =
      error.response?.data;

    let mensagem =
      dados?.mensagem ||
      "Não foi possível realizar o agendamento.";

    if (
      dados?.codigo ===
      "HORARIO_INVALIDO"
    ) {
      mensagem =
        "Esse horário já passou. Escolha um horário futuro.";
    }

    if (
      dados?.codigo ===
      "IMAGEM_INDISPONIVEL"
    ) {
      mensagem =
        "Esta imagem não está mais disponível. Escolha outra foto.";
    }

    setFeedback({
      tipo: "danger",
      titulo:
        "Não foi possível agendar",
      mensagem,
    });

  } finally {
    setAgendando(false);
  }
}

  return (
    <Layout>
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h2 className="mb-1">
            Banco de Fotos
          </h2>

          <p className="text-muted mb-0">
            Selecione uma imagem para publicar
            ou agendar como Story.
          </p>
        </div>

        {!carregando && (
          <span className="badge text-bg-light border fs-6">
            {imagens.length} imagens
          </span>
        )}
      </div>

      {feedback && (
        <FeedbackAlert
          tipo={feedback.tipo}
          titulo={feedback.titulo}
          mensagem={feedback.mensagem}
          onClose={() =>
            setFeedback(null)
          }
        />
      )}

      {erro && (
        <div className="alert alert-danger">
          <div className="fw-semibold mb-1">
            Não conseguimos carregar suas fotos
          </div>

          <div className="mb-3">
            {erro}
          </div>

          <button
            className="btn btn-outline-danger btn-sm"
            onClick={carregarImagens}
          >
            <i className="bi bi-arrow-clockwise me-2"></i>
            Tentar novamente
          </button>
        </div>
      )}

      {!erro && (
        <>
          <div className="card border-0 shadow-sm mb-4">
            <div className="card-body">
              <div className="input-group">
                <span className="input-group-text bg-white">
                  <i className="bi bi-search"></i>
                </span>

                <input
                  type="search"
                  className="form-control"
                  placeholder="Buscar foto..."
                  value={busca}
                  onChange={(e) =>
                    setBusca(
                      e.target.value
                    )
                  }
                />
              </div>
            </div>
          </div>

          {carregando ? (
            <div className="text-center py-5">
              <div
                className="spinner-border"
                role="status"
              />

              <div className="mt-3 text-muted">
                Carregando banco de fotos...
              </div>
            </div>
          ) : imagensFiltradas.length === 0 ? (
            <div className="text-center py-5">
              <i className="bi bi-images fs-1 text-muted"></i>

              <h5 className="mt-3">
                Nenhuma foto encontrada
              </h5>

              <p className="text-muted">
                Tente alterar sua busca.
              </p>
            </div>
          ) : (
            <div className="row g-3">
              {imagensFiltradas.map(
                (imagem) => {
                  const ativa =
                    selecionada?.id ===
                    imagem.id;

                  return (
                    <div
                      className="col-6 col-md-4 col-lg-3"
                      key={imagem.id}
                    >
                      <button
                        type="button"
                        className={`
                          card w-100 h-100
                          border-2
                          text-start
                          p-0
                          overflow-hidden
                          ${
                            ativa
                              ? "border-primary shadow"
                              : "border-light shadow-sm"
                          }
                        `}
                        onClick={() =>
                          selecionarImagem(
                            imagem
                          )
                        }
                        aria-pressed={
                          ativa
                        }
                      >
                        <div
                          style={{
                            height:
                              "260px",
                            background:
                              "#f5f5f5",
                          }}
                        >
                          <img
                            src={
                              imagem.url
                            }
                            alt="Imagem disponível para Story"
                            className="w-100 h-100"
                            style={{
                              objectFit:
                                "cover",
                            }}
                          />
                        </div>

                        <div className="card-body w-100">
                          <div className="d-flex justify-content-between align-items-center">
                            <small className="text-muted">
                              Foto #
                              {imagem.id}
                            </small>

                            {ativa && (
                              <i className="bi bi-check-circle-fill text-primary fs-5"></i>
                            )}
                          </div>
                        </div>
                      </button>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </>
      )}

      {selecionada &&
        !carregando &&
        !erro && (
          <div
            className="position-sticky bottom-0 mt-4 py-3"
            style={{
              zIndex: 20,
            }}
          >
            <div className="card shadow border-0">
              <div className="card-body d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
                <div>
                  <div className="fw-semibold">
                    Foto selecionada
                  </div>

                  <small className="text-muted">
                    Foto #{selecionada.id}
                  </small>
                </div>

                <div className="d-flex gap-2">
                  <button
                    className="btn btn-outline-primary"
                    onClick={() =>
                        setModalAgendamento(true)
                    }
                    >
                    <i className="bi bi-calendar-event me-2"></i>
                    Agendar
                  </button>

                  <button
                    className="btn btn-primary"
                    onClick={
                      abrirConfirmacao
                    }
                  >
                    <i className="bi bi-send me-2"></i>
                    Publicar agora
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      {confirmando && (
        <ConfirmModal
          imagem={selecionada}
          publicando={publicando}
          onCancelar={() =>
            !publicando &&
            setConfirmando(false)
          }
          onConfirmar={
            publicarAgora
          }
        />
      )}
      {modalAgendamento && (
        <AgendarModal
            imagem={selecionada}
            agendando={agendando}
            onCancelar={() => {
            if (!agendando) {
                setModalAgendamento(false);
            }
            }}
            onConfirmar={agendarStory}
        />
        )}
    </Layout>
  );
}