export default function FeedbackAlert({
  tipo = "info",
  titulo,
  mensagem,
  onClose,
}) {
  return (
    <div
      className={`alert alert-${tipo} d-flex align-items-start`}
      role="alert"
    >
      <i
        className={`bi ${
          tipo === "success"
            ? "bi-check-circle-fill"
            : tipo === "danger"
            ? "bi-exclamation-triangle-fill"
            : "bi-info-circle-fill"
        } me-3 fs-5`}
      />

      <div className="flex-grow-1">
        {titulo && (
          <div className="fw-semibold mb-1">
            {titulo}
          </div>
        )}

        <div>{mensagem}</div>
      </div>

      {onClose && (
        <button
          className="btn-close"
          onClick={onClose}
          aria-label="Fechar"
        />
      )}
    </div>
  );
}