export default function CancelarAgendamentoModal({
  postagem,
  cancelando,
  onCancelar,
  onConfirmar,
}) {
  if (!postagem) {
    return null;
  }

  return (
    <>
      <div
        className="modal d-block"
        tabIndex="-1"
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content shadow">
            <div className="modal-header">
              <h5 className="modal-title">
                Cancelar agendamento
              </h5>

              {!cancelando && (
                <button
                  type="button"
                  className="btn-close"
                  onClick={onCancelar}
                />
              )}
            </div>

            <div className="modal-body">
              {!cancelando ? (
                <>
                  <div className="alert alert-warning">
                    <i className="bi bi-exclamation-triangle me-2"></i>

                    Este Story não será mais
                    publicado automaticamente.
                  </div>

                  <p className="mb-0">
                    Deseja realmente cancelar
                    este agendamento?
                  </p>
                </>
              ) : (
                <div className="text-center py-4">
                  <div
                    className="spinner-border mb-3"
                    role="status"
                  />

                  <div className="fw-semibold">
                    Cancelando agendamento...
                  </div>
                </div>
              )}
            </div>

            {!cancelando && (
              <div className="modal-footer">
                <button
                  className="btn btn-outline-secondary"
                  onClick={onCancelar}
                >
                  Manter agendamento
                </button>

                <button
                  className="btn btn-danger"
                  onClick={onConfirmar}
                >
                  <i className="bi bi-x-circle me-2"></i>
                  Cancelar Story
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