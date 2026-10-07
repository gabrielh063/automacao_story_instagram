import {
  useEffect,
  useState,
} from "react";

import api from "../services/api";

import Layout from "../components/Layout";
import FeedbackAlert from "../components/FeedbackAlert";
import StatusBadge from "../components/StatusBadge";
import CancelarAgendamentoModal
  from "../components/CancelarAgendamentoModal";


function formatarData(dataUtc) {
  if (!dataUtc) {
    return "-";
  }

  return new Date(
    dataUtc
  ).toLocaleString(
    "pt-BR",
    {
      timeZone:
        "America/Sao_Paulo",

      dateStyle:
        "short",

      timeStyle:
        "short",
    }
  );
}


function calcularTempoRestante(
  dataUtc
) {
  if (!dataUtc) {
    return "";
  }

  const agora =
    Date.now();

  const agendamento =
    new Date(
      dataUtc
    ).getTime();

  const diferenca =
    agendamento - agora;

  if (diferenca <= 0) {
    return "Aguardando processamento";
  }

  const minutos = Math.floor(
    diferenca / 60000
  );

  if (minutos < 1) {
    return "Menos de 1 minuto";
  }

  if (minutos < 60) {
    return `Em ${minutos} min`;
  }

  const horas =
    Math.floor(
      minutos / 60
    );

  const minutosRestantes =
    minutos % 60;

  if (horas < 24) {
    return (
      `Em ${horas}h ` +
      `${minutosRestantes}min`
    );
  }

  const dias =
    Math.floor(
      horas / 24
    );

  return (
    `Em ${dias} ` +
    `${dias === 1 ? "dia" : "dias"}`
  );
}


export default function Agendamentos() {
  const [
    postagens,
    setPostagens
  ] = useState([]);

  const [
    imagens,
    setImagens
  ] = useState([]);

  const [
    carregando,
    setCarregando
  ] = useState(true);

  const [
    erro,
    setErro
  ] = useState(null);

  const [
    feedback,
    setFeedback
  ] = useState(null);

  const [
    postagemCancelar,
    setPostagemCancelar
  ] = useState(null);

  const [
    cancelando,
    setCancelando
  ] = useState(false);

  const [
    agora,
    setAgora
  ] = useState(
    Date.now()
  );


  async function carregarDados() {
    try {
      setCarregando(true);
      setErro(null);

      const [
        respostaPostagens,
        respostaImagens,
      ] = await Promise.all([
        api.get(
          "/api/postagens?status=AGENDADO&limite=100"
        ),

        api.get(
          "/api/imagens"
        ),
      ]);

      setPostagens(
        respostaPostagens
          .data
          .postagens || []
      );

      setImagens(
        respostaImagens
          .data
          .imagens || []
      );

    } catch (error) {
      setErro(
        error.response
          ?.data
          ?.mensagem ||

        "Não foi possível carregar os agendamentos."
      );

    } finally {
      setCarregando(false);
    }
  }


  useEffect(() => {
    carregarDados();
  }, []);


  useEffect(() => {
    const timer =
      setInterval(
        () => {
          setAgora(
            Date.now()
          );
        },
        30000
      );

    return () =>
      clearInterval(
        timer
      );
  }, []);


  function encontrarImagem(
    imagemId
  ) {
    return imagens.find(
      imagem =>
        imagem.id ===
        imagemId
    );
  }


  async function cancelar() {
    if (
      !postagemCancelar ||
      cancelando
    ) {
      return;
    }

    try {
      setCancelando(true);

      await api.post(
        `/api/postagens/${postagemCancelar.id}/cancelar`
      );

      setPostagens(
        atuais =>
          atuais.filter(
            item =>
              item.id !==
              postagemCancelar.id
          )
      );

      setPostagemCancelar(
        null
      );

      setFeedback({
        tipo: "success",
        titulo:
          "Agendamento cancelado",

        mensagem:
          "O Story não será mais publicado automaticamente.",
      });

    } catch (error) {
      const dados =
        error.response?.data;

      setPostagemCancelar(
        null
      );

      setFeedback({
        tipo: "danger",

        titulo:
          "Não foi possível cancelar",

        mensagem:
          dados?.mensagem ||
          "O agendamento não pôde ser cancelado.",
      });

    } finally {
      setCancelando(false);
    }
  }


  return (
    <Layout>
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h2 className="mb-1">
            Agendamentos
          </h2>

          <p className="text-muted mb-0">
            Acompanhe os Stories que serão
            publicados automaticamente.
          </p>
        </div>

        {!carregando && (
          <span className="badge text-bg-light border fs-6">
            {postagens.length}
            {" "}
            {postagens.length === 1
              ? "agendamento"
              : "agendamentos"}
          </span>
        )}
      </div>


      {feedback && (
        <FeedbackAlert
          tipo={
            feedback.tipo
          }
          titulo={
            feedback.titulo
          }
          mensagem={
            feedback.mensagem
          }
          onClose={() =>
            setFeedback(null)
          }
        />
      )}


      {erro && (
        <div className="alert alert-danger">
          <div className="fw-semibold mb-1">
            Não conseguimos carregar
            seus agendamentos
          </div>

          <div className="mb-3">
            {erro}
          </div>

          <button
            className="btn btn-outline-danger btn-sm"
            onClick={
              carregarDados
            }
          >
            <i className="bi bi-arrow-clockwise me-2"></i>

            Tentar novamente
          </button>
        </div>
      )}


      {carregando ? (
        <div className="text-center py-5">
          <div
            className="spinner-border"
            role="status"
          />

          <div className="mt-3 text-muted">
            Carregando agendamentos...
          </div>
        </div>

      ) : !erro &&
          postagens.length === 0 ? (

        <div className="card border-0 shadow-sm">
          <div className="card-body text-center py-5">

            <i className="bi bi-calendar-check fs-1 text-muted"></i>

            <h5 className="mt-3">
              Nenhum Story agendado
            </h5>

            <p className="text-muted mb-0">
              Quando você agendar uma
              publicação, ela aparecerá aqui.
            </p>

          </div>
        </div>

      ) : (

        <div className="d-flex flex-column gap-3">

          {postagens.map(
            postagem => {

              const imagem =
                encontrarImagem(
                  postagem.imagem_id
                );

              return (
                <div
                  className="card border-0 shadow-sm"
                  key={postagem.id}
                >
                  <div className="card-body">

                    <div className="row align-items-center g-3">

                      <div className="col-auto">

                        {imagem ? (
                          <img
                            src={
                              imagem.url
                            }
                            alt="Story agendado"
                            width="90"
                            height="120"
                            className="rounded border"
                            style={{
                              objectFit:
                                "cover",
                            }}
                          />
                        ) : (
                          <div
                            className="rounded border bg-light d-flex align-items-center justify-content-center"
                            style={{
                              width:
                                "90px",
                              height:
                                "120px",
                            }}
                          >
                            <i className="bi bi-image text-muted fs-3"></i>
                          </div>
                        )}

                      </div>


                      <div className="col">

                        <div className="d-flex align-items-center gap-2 mb-2">

                          <StatusBadge
                            status={
                              postagem.status
                            }
                          />

                          <span className="text-muted small">
                            Story
                          </span>

                        </div>


                        <div className="fw-semibold fs-5">

                          {formatarData(
                            postagem.agendado_para
                          )}

                        </div>


                        <div className="text-primary mt-1">

                          <i className="bi bi-clock me-1"></i>

                          {calcularTempoRestante(
                            postagem.agendado_para,
                            agora
                          )}

                        </div>


                        <small className="text-muted d-block mt-2">

                          Foto #
                          {postagem.imagem_id}

                        </small>

                      </div>


                      <div className="col-md-auto">

                        <button
                          className="btn btn-outline-danger"
                          onClick={() =>
                            setPostagemCancelar(
                              postagem
                            )
                          }
                        >
                          <i className="bi bi-x-circle me-2"></i>

                          Cancelar
                        </button>

                      </div>

                    </div>

                  </div>
                </div>
              );
            }
          )}

        </div>
      )}


      {postagemCancelar && (
        <CancelarAgendamentoModal
          postagem={
            postagemCancelar
          }
          cancelando={
            cancelando
          }
          onCancelar={() => {
            if (!cancelando) {
              setPostagemCancelar(
                null
              );
            }
          }}
          onConfirmar={
            cancelar
          }
        />
      )}

    </Layout>
  );
}