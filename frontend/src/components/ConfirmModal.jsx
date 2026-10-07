export default function ConfirmModal({
  imagem,
  publicando,
  onCancelar,
  onConfirmar,
}) {
  if (!imagem) {
    return null;
  }

  return (
    <>
      <div className="modal d-block" tabIndex="-1">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content shadow">
            <div className="modal-header">
              <h5 className="modal-title">
                Publicar Story
              </h5>

              {!publicando && (
                <button
                  type="button"
                  className="btn-close"
                  onClick={onCancelar}
                />
              )}
            </div>

            <div className="modal-body">
              <div className="text-center mb-3">
                <img
                  src={imagem.url}
                  alt="Prévia do Story"
                  className="img-fluid rounded"
                  style={{
                    maxHeight: "420px",
                    objectFit: "contain",
                  }}
                />
              </div>

              {!publicando ? (
                <p className="mb-0">
                  Esta imagem será publicada como Story
                  no Instagram. Deseja continuar?
                </p>
              ) : (
                <div className="text-center py-3">
                  <div
                    className="spinner-border mb-3"
                    role="status"
                  />

                  <div className="fw-semibold">
                    Publicando Story...
                  </div>

                  <small className="text-muted">
                    Aguarde enquanto o Instagram processa
                    a imagem.
                  </small>
                </div>
              )}
            </div>

            {!publicando && (
              <div className="modal-footer">
                <button
                  className="btn btn-outline-secondary"
                  onClick={onCancelar}
                >
                  Cancelar
                </button>

                <button
                  className="btn btn-primary"
                  onClick={onConfirmar}
                >
                  <i className="bi bi-send me-2"></i>
                  Publicar agora
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="modal-backdrop fade show" />
    </>
  );
}