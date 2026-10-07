import StatusBadge from "./StatusBadge";


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


function mensagemErro(postagem) {
  switch (postagem.erro_tipo) {
    case "TOKEN":
      return (
        "A conexão com o Instagram expirou " +
        "ou precisa ser renovada."
      );

    case "TEMPORARIO":
      return (
        "Houve uma falha temporária de comunicação. " +
        "A publicação pode ser tentada novamente."
      );

    case "IMAGEM":
      return (
        "A imagem usada nesta publicação não está " +
        "mais disponível."
      );

    case "META":
      return (
        "O Instagram recusou esta publicação."
      );

    case "PUBLICACAO_AMBIGUA":
      return (
        "Não foi possível confirmar se o Instagram " +
        "publicou o Story. Uma nova tentativa automática " +
        "poderia gerar uma publicação duplicada."
      );

    default:
      return (
        postagem.erro_mensagem ||
        "A publicação não foi concluída."
      );
  }
}


export default function DetalhesPostagemModal({
  postagem,
  imagem,
  tentandoNovamente,
  onFechar,
  onTentarNovamente,
}) {
  if (!postagem) {
    return null;
  }

  const podeTentarNovamente =
    postagem.status === "ERRO" &&
    postagem.erro_tipo !== "PUBLICACAO_AMBIGUA" &&
    postagem.tentativas < 3;

  return (
    <>
      <div
        className="modal d-block"
        tabIndex="-1"
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-dialog modal-lg modal-dialog-centered">
          <div className="modal-content shadow">

            <div className="modal-header">
              <div>
                <h5 className="modal-title mb-1">
                  Detalhes da publicação
                </h5>

                <StatusBadge
                  status={postagem.status}
                />
              </div>

              {!tentandoNovamente && (
                <button
                  type="button"
                  className="btn-close"
                  onClick={onFechar}
                />
              )}
            </div>

            <div className="modal-body">

              <div className="row g-4">

                <div className="col-md-4">
                  {imagem ? (
                    <img
                      src={imagem.url}
                      alt="Imagem da publicação"
                      className="img-fluid rounded border"
                      style={{
                        maxHeight: "420px",
                        width: "100%",
                        objectFit: "contain",
                      }}
                    />
                  ) : (
                    <div
                      className="bg-light border rounded d-flex align-items-center justify-content-center"
                      style={{
                        height: "300px",
                      }}
                    >
                      <i className="bi bi-image fs-1 text-muted" />
                    </div>
                  )}
                </div>


                <div className="col-md-8">

                  <div className="mb-3">
                    <small className="text-muted">
                      Solicitado em
                    </small>

                    <div className="fw-semibold">
                      {formatarData(
                        postagem.criado_em
                      )}
                    </div>
                  </div>


                  {postagem.publicado_em && (
                    <div className="mb-3">
                      <small className="text-muted">
                        Publicado em
                      </small>

                      <div className="fw-semibold">
                        {formatarData(
                          postagem.publicado_em
                        )}
                      </div>
                    </div>
                  )}


                  {postagem.cancelado_em && (
                    <div className="mb-3">
                      <small className="text-muted">
                        Cancelado em
                      </small>

                      <div className="fw-semibold">
                        {formatarData(
                          postagem.cancelado_em
                        )}
                      </div>
                    </div>
                  )}


                  <div className="mb-3">
                    <small className="text-muted">
                      Tentativas
                    </small>

                    <div className="fw-semibold">
                      {postagem.tentativas || 0}
                    </div>
                  </div>


                  {postagem.status === "ERRO" && (
                    <div className="alert alert-danger">
                      <div className="fw-semibold mb-2">
                        <i className="bi bi-exclamation-triangle me-2" />
                        A publicação não foi concluída
                      </div>

                      <div>
                        {mensagemErro(postagem)}
                      </div>
                    </div>
                  )}


                  {postagem.erro_tipo ===
                    "PUBLICACAO_AMBIGUA" && (
                    <div className="alert alert-warning">
                      Por segurança, o sistema não fará
                      uma nova tentativa automaticamente.
                      Confira o Instagram antes de publicar
                      novamente.
                    </div>
                  )}


                  {postagem.eventos?.length > 0 && (
                    <>
                      <hr />

                      <h6 className="mb-3">
                        Histórico da operação
                      </h6>

                      <div className="d-flex flex-column gap-3">
                        {postagem.eventos.map(
                          evento => (
                            <div
                              key={evento.id}
                              className="border-start ps-3"
                            >
                              <div className="fw-semibold">
                                {evento.mensagem ||
                                  evento.evento}
                              </div>

                              <small className="text-muted">
                                {formatarData(
                                  evento.criado_em
                                )}
                              </small>
                            </div>
                          )
                        )}
                      </div>
                    </>
                  )}

                </div>

              </div>

            </div>


            <div className="modal-footer">

              <button
                className="btn btn-outline-secondary"
                onClick={onFechar}
                disabled={tentandoNovamente}
              >
                Fechar
              </button>


              {podeTentarNovamente && (
                <button
                  className="btn btn-primary"
                  onClick={onTentarNovamente}
                  disabled={tentandoNovamente}
                >
                  {tentandoNovamente ? (
                    <>
                      <span
                        className="spinner-border spinner-border-sm me-2"
                      />

                      Solicitando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-arrow-clockwise me-2" />
                      Tentar novamente
                    </>
                  )}
                </button>
              )}

            </div>

          </div>
        </div>
      </div>

      <div className="modal-backdrop fade show" />
    </>
  );
}