import { useEffect, useState } from "react";

function gerarMinimo() {
  const agora = new Date();

  // margem de 1 minuto
  agora.setMinutes(agora.getMinutes() + 1);

  const ano = agora.getFullYear();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  const hora = String(agora.getHours()).padStart(2, "0");
  const minuto = String(agora.getMinutes()).padStart(2, "0");

  return `${ano}-${mes}-${dia}T${hora}:${minuto}`;
}

export default function AgendarModal({
  imagem,
  agendando,
  onCancelar,
  onConfirmar,
}) {
  const [dataHora, setDataHora] = useState("");
  const [erro, setErro] = useState("");

  useEffect(() => {
    setDataHora("");
    setErro("");
  }, [imagem]);

  if (!imagem) {
    return null;
  }

  function confirmar() {
    setErro("");

    if (!dataHora) {
      setErro("Escolha a data e o horário da publicação.");
      return;
    }

    const selecionada = new Date(dataHora);
    const agora = new Date();

    if (selecionada <= agora) {
      setErro("Escolha um horário futuro.");
      return;
    }

    onConfirmar(dataHora);
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
                Agendar Story
              </h5>

              {!agendando && (
                <button
                  type="button"
                  className="btn-close"
                  onClick={onCancelar}
                  aria-label="Fechar"
                />
              )}
            </div>

            <div className="modal-body">
              <div className="text-center mb-4">
                <img
                  src={imagem.url}
                  alt="Prévia da imagem selecionada"
                  className="img-fluid rounded"
                  style={{
                    maxHeight: "320px",
                    objectFit: "contain",
                  }}
                />
              </div>

              {!agendando ? (
                <>
                  <label
                    htmlFor="agendadoPara"
                    className="form-label fw-semibold"
                  >
                    Quando publicar?
                  </label>

                  <input
                    id="agendadoPara"
                    type="datetime-local"
                    className={`form-control ${
                      erro ? "is-invalid" : ""
                    }`}
                    min={gerarMinimo()}
                    value={dataHora}
                    onChange={(e) => {
                      setDataHora(e.target.value);
                      setErro("");
                    }}
                  />

                  {erro && (
                    <div className="invalid-feedback">
                      {erro}
                    </div>
                  )}

                  <div className="form-text mt-2">
                    O horário será considerado no horário de Brasília.
                  </div>

                  {dataHora && !erro && (
                    <div className="alert alert-light border mt-3 mb-0">
                      <i className="bi bi-calendar-check me-2"></i>

                      Publicação programada para{" "}
                      <strong>
                        {new Date(dataHora).toLocaleString(
                          "pt-BR",
                          {
                            dateStyle: "short",
                            timeStyle: "short",
                          }
                        )}
                      </strong>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-4">
                  <div
                    className="spinner-border mb-3"
                    role="status"
                  />

                  <div className="fw-semibold">
                    Salvando agendamento...
                  </div>

                  <small className="text-muted">
                    Aguarde enquanto registramos a publicação.
                  </small>
                </div>
              )}
            </div>

            {!agendando && (
              <div className="modal-footer">
                <button
                  className="btn btn-outline-secondary"
                  onClick={onCancelar}
                >
                  Cancelar
                </button>

                <button
                  className="btn btn-primary"
                  onClick={confirmar}
                  disabled={!dataHora}
                >
                  <i className="bi bi-calendar-check me-2"></i>
                  Confirmar agendamento
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