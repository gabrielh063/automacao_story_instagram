import {
  useEffect,
  useMemo,
  useState,
} from "react";

import api from "../services/api";

import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import FeedbackAlert from "../components/FeedbackAlert";
import DetalhesPostagemModal
  from "../components/DetalhesPostagemModal";


function formatarData(data) {
  if (!data) {
    return "-";
  }

  return new Date(data).toLocaleString(
    "pt-BR",
    {
      timeZone: "America/Sao_Paulo",
      dateStyle: "short",
      timeStyle: "short",
    }
  );
}


export default function Historico() {
  const [postagens, setPostagens] =
    useState([]);

  const [imagens, setImagens] =
    useState([]);

  const [carregando, setCarregando] =
    useState(true);

  const [erro, setErro] =
    useState(null);

  const [filtro, setFiltro] =
    useState("TODOS");

  const [detalhes, setDetalhes] =
    useState(null);

  const [
    tentandoNovamente,
    setTentandoNovamente
  ] = useState(false);

  const [feedback, setFeedback] =
    useState(null);


  async function carregarDados(
    mostrarLoading = true
  ) {
    try {
      if (mostrarLoading) {
        setCarregando(true);
      }

      setErro(null);

      const [
        respostaPostagens,
        respostaImagens,
      ] = await Promise.all([
        api.get(
          "/api/postagens?limite=100"
        ),

        api.get(
          "/api/imagens"
        ),
      ]);

      setPostagens(
        respostaPostagens.data.postagens ||
        []
      );

      setImagens(
        respostaImagens.data.imagens ||
        []
      );

    } catch (error) {

      setErro(
        error.response?.data?.mensagem ||
        "Não foi possível carregar o histórico."
      );

    } finally {

      if (mostrarLoading) {
        setCarregando(false);
      }

    }
  }


  useEffect(() => {
    carregarDados();

    const timer = setInterval(
      () => {
        carregarDados(false);
      },
      30000
    );

    return () => clearInterval(timer);
  }, []);


  const historico = useMemo(() => {

    const permitidos = postagens.filter(
      postagem =>
        postagem.status !== "AGENDADO" &&
        postagem.status !== "RASCUNHO"
    );

    if (filtro === "TODOS") {
      return permitidos;
    }

    return permitidos.filter(
      postagem =>
        postagem.status === filtro
    );

  }, [postagens, filtro]);


  function encontrarImagem(imagemId) {
    return imagens.find(
      imagem =>
        imagem.id === imagemId
    );
  }


  async function abrirDetalhes(postagem) {
    try {

      const resposta = await api.get(
        `/api/postagens/${postagem.id}`
      );

      setDetalhes(
        resposta.data.postagem ||
        resposta.data
      );

    } catch (error) {

      setFeedback({
        tipo: "danger",
        titulo:
          "Não foi possível abrir os detalhes",
        mensagem:
          error.response?.data?.mensagem ||
          "Tente novamente.",
      });

    }
  }


  async function tentarNovamente() {
    if (
      !detalhes ||
      tentandoNovamente
    ) {
      return;
    }

    try {

      setTentandoNovamente(true);

      await api.post(
        `/api/postagens/${detalhes.id}/tentar-novamente`
      );

      setDetalhes(null);

      setFeedback({
        tipo: "success",
        titulo:
          "Nova tentativa programada",
        mensagem:
          "O sistema tentará publicar este Story novamente.",
      });

      await carregarDados(false);

    } catch (error) {

      setFeedback({
        tipo: "danger",
        titulo:
          "Não foi possível tentar novamente",
        mensagem:
          error.response?.data?.mensagem ||
          error.response?.data?.erro ||
          "Esta publicação não pode ser reenviada.",
      });

    } finally {

      setTentandoNovamente(false);

    }
  }


  return (
    <Layout>

      <div className="d-flex justify-content-between align-items-start mb-4">

        <div>
          <h2 className="mb-1">
            Histórico
          </h2>

          <p className="text-muted mb-0">
            Veja o resultado das publicações
            e acompanhe possíveis falhas.
          </p>
        </div>

        {!carregando && (
          <span className="badge text-bg-light border fs-6">
            {historico.length} registros
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


      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body">

          <div className="d-flex flex-wrap gap-2">

            {[
              ["TODOS", "Todos"],
              ["PUBLICADO", "Publicados"],
              ["ERRO", "Erros"],
              ["CANCELADO", "Cancelados"],
              ["PROCESSANDO", "Processando"],
            ].map(([valor, texto]) => (

              <button
                key={valor}
                type="button"
                className={
                  filtro === valor
                    ? "btn btn-primary"
                    : "btn btn-outline-secondary"
                }
                onClick={() =>
                  setFiltro(valor)
                }
              >
                {texto}
              </button>

            ))}

          </div>

        </div>
      </div>


      {erro && (
        <div className="alert alert-danger">

          <div className="fw-semibold">
            Não conseguimos carregar
            o histórico.
          </div>

          <div className="mt-1 mb-3">
            {erro}
          </div>

          <button
            className="btn btn-outline-danger btn-sm"
            onClick={() =>
              carregarDados()
            }
          >
            <i className="bi bi-arrow-clockwise me-2" />

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

          <div className="text-muted mt-3">
            Carregando histórico...
          </div>

        </div>

      ) : !erro &&
          historico.length === 0 ? (

        <div className="card border-0 shadow-sm">

          <div className="card-body text-center py-5">

            <i className="bi bi-clock-history fs-1 text-muted" />

            <h5 className="mt-3">
              Nenhuma publicação encontrada
            </h5>

            <p className="text-muted mb-0">
              Não existem registros para
              este filtro.
            </p>

          </div>

        </div>

      ) : (

        <div className="d-flex flex-column gap-3">

          {historico.map(postagem => {

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
                          src={imagem.url}
                          alt="Story"
                          width="75"
                          height="100"
                          className="rounded border"
                          style={{
                            objectFit: "cover",
                          }}
                        />

                      ) : (

                        <div
                          className="rounded border bg-light d-flex align-items-center justify-content-center"
                          style={{
                            width: "75px",
                            height: "100px",
                          }}
                        >
                          <i className="bi bi-image text-muted fs-4" />
                        </div>

                      )}

                    </div>


                    <div className="col">

                      <div className="d-flex gap-2 align-items-center mb-2">

                        <StatusBadge
                          status={
                            postagem.status
                          }
                        />

                        <small className="text-muted">
                          Story
                        </small>

                      </div>


                      <div className="fw-semibold">

                        {postagem.status ===
                          "PUBLICADO"
                          ? formatarData(
                              postagem.publicado_em
                            )
                          : formatarData(
                              postagem.criado_em
                            )}

                      </div>


                      {postagem.status === "ERRO" && (

                        <small className="text-danger d-block mt-1">

                          <i className="bi bi-exclamation-circle me-1" />

                          Publicação não concluída

                        </small>

                      )}


                      <small className="text-muted d-block mt-1">

                        Foto #{postagem.imagem_id}

                        {" · "}

                        {postagem.tentativas || 0}

                        {" "}

                        {postagem.tentativas === 1
                          ? "tentativa"
                          : "tentativas"}

                      </small>

                    </div>


                    <div className="col-md-auto">

                      <button
                        className="btn btn-outline-primary"
                        onClick={() =>
                          abrirDetalhes(
                            postagem
                          )
                        }
                      >

                        <i className="bi bi-eye me-2" />

                        Detalhes

                      </button>

                    </div>

                  </div>

                </div>

              </div>

            );
          })}

        </div>

      )}


      {detalhes && (

        <DetalhesPostagemModal
          postagem={detalhes}
          imagem={
            encontrarImagem(
              detalhes.imagem_id
            )
          }
          tentandoNovamente={
            tentandoNovamente
          }
          onFechar={() => {
            if (
              !tentandoNovamente
            ) {
              setDetalhes(null);
            }
          }}
          onTentarNovamente={
            tentarNovamente
          }
        />

      )}

    </Layout>
  );
}