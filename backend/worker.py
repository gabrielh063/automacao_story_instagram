import time

from datetime import datetime, timezone

from app import create_app
from extensions import db
from models.postagem import Postagem
from services.postagem_service import (
    PostagemService
)


app = create_app()


def utc_now():

    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def tentar_reservar(
    postagem_id
):

    agora = utc_now()

    atualizadas = (
        Postagem.query
        .filter(
            Postagem.id == postagem_id,
            Postagem.status.in_([
                "AGENDADO",
                "ERRO"
            ])
        )
        .update(
            {
                Postagem.status:
                    "PROCESSANDO",

                Postagem.processando_desde:
                    agora,

                Postagem.ultima_tentativa_em:
                    agora,

                Postagem.tentativas:
                    Postagem.tentativas + 1
            },
            synchronize_session=False
        )
    )

    db.session.commit()

    return atualizadas == 1


def processar_agendamentos():

    agora = utc_now()

    candidatos = (
        Postagem.query
        .filter(

            (
                (
                    Postagem.status
                    == "AGENDADO"
                )
                &
                (
                    Postagem.agendado_para
                    <= agora
                )
            )

            |

            (
                (
                    Postagem.status
                    == "ERRO"
                )
                &
                (
                    Postagem.erro_recuperavel
                    == True
                )
                &
                (
                    Postagem.proxima_tentativa_em
                    <= agora
                )
            )
        )
        .order_by(
            Postagem.agendado_para.asc()
        )
        .limit(10)
        .all()
    )

    print(
        f"[WORKER] Agendamentos encontrados: "
        f"{len(candidatos)}",
        flush=True
    )

    for candidato in candidatos:

        if not tentar_reservar(
            candidato.id
        ):

            print(
                f"[WORKER] Postagem "
                f"{candidato.id} já foi "
                f"reservada por outro worker.",
                flush=True
            )

            continue

        print(
            f"[WORKER] Processando "
            f"postagem {candidato.id}",
            flush=True
        )

        service = PostagemService()

        try:

            service._registrar_evento(
                candidato.id,
                "PROCESSANDO",
                "Worker iniciou a publicação."
            )

            db.session.commit()

            service.processar_postagem(
                candidato.id
            )

            print(
                f"[WORKER] Postagem "
                f"{candidato.id} publicada.",
                flush=True
            )

        except Exception as erro:

            print(
                f"[WORKER] Postagem "
                f"{candidato.id} falhou: "
                f"{erro}",
                flush=True
            )


if __name__ == "__main__":

    print(
        "[WORKER] Worker iniciado.",
        flush=True
    )

    while True:

        try:

            with app.app_context():

                print(
                    f"[WORKER] Verificando "
                    f"- UTC: {utc_now()}",
                    flush=True
                )

                processar_agendamentos()

        except Exception as erro:

            print(
                f"[WORKER] Erro no ciclo: "
                f"{erro}",
                flush=True
            )

        time.sleep(30)