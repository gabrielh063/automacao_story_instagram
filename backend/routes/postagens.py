from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo


from flask import (
    Blueprint,
    jsonify,
    request,
    current_app
)

from services.postagem_service import (
    PostagemService,
    ImagemNaoEncontrada,
    ImagemIndisponivel,
    ConflitoIdempotencia,
    ErroPublicacao,
    HorarioInvalido,
    PostagemJaFinalizada
)


postagens_bp = Blueprint(
    "postagens",
    __name__,
    url_prefix="/api/postagens"
)


def converter_para_utc(data_hora):

    timezone_local = ZoneInfo(
        "America/Sao_Paulo"
    )

    local = datetime.fromisoformat(
        data_hora
    )

    local = local.replace(
        tzinfo=timezone_local
    )

    utc = local.astimezone(
        ZoneInfo("UTC")
    )

    return utc.replace(
        tzinfo=None
    )

def validar_uuid(valor):

    try:
        UUID(valor)
        return True

    except (ValueError, TypeError):
        return False


@postagens_bp.post("/publicar-agora")
def publicar_agora():

    dados = request.get_json(
        silent=True
    ) or {}

    imagem_id = dados.get(
        "imagem_id"
    )

    #
    # Prevenção de erro
    #

    if imagem_id is None:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_OBRIGATORIA",
            "mensagem":
                "Selecione uma imagem antes "
                "de publicar."
        }), 400

    try:
        imagem_id = int(imagem_id)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_INVALIDA",
            "mensagem":
                "A imagem selecionada é inválida."
        }), 400

    chave = request.headers.get(
        "Idempotency-Key"
    )

    if not chave:

        return jsonify({
            "success": False,
            "codigo":
                "IDEMPOTENCY_KEY_OBRIGATORIA",
            "mensagem":
                "Não foi possível identificar "
                "esta tentativa de publicação. "
                "Atualize a página e tente novamente."
        }), 400

    if not validar_uuid(chave):

        return jsonify({
            "success": False,
            "codigo":
                "IDEMPOTENCY_KEY_INVALIDA",
            "mensagem":
                "Identificador da solicitação inválido."
        }), 400

    service = PostagemService()

    try:

        resultado = service.publicar_agora(
            imagem_id=imagem_id,
            chave_idempotencia=chave
        )

        postagem = resultado["postagem"]

        if resultado["nova"]:

            return jsonify({
                "success": True,
                "mensagem":
                    "Story publicado com sucesso.",
                "postagem": postagem
            }), 201

        #
        # Mesma chave foi enviada de novo.
        # NÃO publica novamente.
        #

        return jsonify({
            "success": True,
            "repetida": True,
            "mensagem":
                "Esta solicitação já havia "
                "sido processada.",
            "postagem": postagem
        }), 200

    except ImagemNaoEncontrada as erro:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_NAO_ENCONTRADA",
            "mensagem": str(erro)
        }), 404

    except ImagemIndisponivel as erro:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_INDISPONIVEL",
            "mensagem": str(erro)
        }), 409

    except ConflitoIdempotencia as erro:

        return jsonify({
            "success": False,
            "codigo":
                "CONFLITO_IDEMPOTENCIA",
            "mensagem": str(erro)
        }), 409

    except ErroPublicacao as erro:

        current_app.logger.exception(
            "Falha ao publicar Story %s",
            erro.postagem_id
        )

        return jsonify({
            "success": False,
            "codigo":
                "FALHA_PUBLICACAO",
            "mensagem":
                "Não foi possível publicar o Story. "
                "A tentativa foi registrada e "
                "nenhuma nova publicação será feita "
                "automaticamente.",
            "postagem_id":
                erro.postagem_id
        }), 502


@postagens_bp.get("")
def listar_postagens():

    limite = request.args.get(
        "limite",
        50,
        type=int
    )

    limite = max(
        1,
        min(limite, 100)
    )

    status = request.args.get(
        "status"
    )

    permitidos = {
        "RASCUNHO",
        "AGENDADO",
        "PROCESSANDO",
        "PUBLICADO",
        "ERRO",
        "CANCELADO"
    }

    if status and status not in permitidos:

        return jsonify({
            "success": False,
            "codigo": "STATUS_INVALIDO",
            "mensagem":
                "O status informado é inválido."
        }), 400

    service = PostagemService()

    postagens = service.listar(
        limite=limite,
        status=status
    )

    return jsonify({
        "quantidade": len(postagens),
        "postagens": postagens
    })

@postagens_bp.get("/<int:postagem_id>")
def consultar_postagem(postagem_id):

    service = PostagemService()

    postagem = service.obter(
        postagem_id
    )

    if postagem is None:

        return jsonify({
            "success": False,
            "codigo":
                "POSTAGEM_NAO_ENCONTRADA",
            "mensagem":
                "A postagem informada "
                "não foi encontrada."
        }), 404

    return jsonify({
        "success": True,
        "postagem": postagem
    })
    
@postagens_bp.post("/agendar")
def agendar_postagem():

    dados = request.get_json(
        silent=True
    ) or {}

    imagem_id = dados.get(
        "imagem_id"
    )

    data_hora = dados.get(
        "agendado_para"
    )

    if imagem_id is None:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_OBRIGATORIA",
            "mensagem":
                "Selecione uma imagem."
        }), 400

    if not data_hora:

        return jsonify({
            "success": False,
            "codigo":
                "HORARIO_OBRIGATORIO",
            "mensagem":
                "Informe a data e o horário da publicação."
        }), 400

    try:
        imagem_id = int(imagem_id)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_INVALIDA",
            "mensagem":
                "A imagem informada é inválida."
        }), 400

    chave = request.headers.get(
        "Idempotency-Key"
    )

    if not chave or not validar_uuid(chave):

        return jsonify({
            "success": False,
            "codigo":
                "IDEMPOTENCY_KEY_INVALIDA",
            "mensagem":
                "Não foi possível identificar esta solicitação."
        }), 400

    try:

        agendado_para_utc = (
            converter_para_utc(
                data_hora
            )
        )

    except Exception:

        return jsonify({
            "success": False,
            "codigo":
                "DATA_INVALIDA",
            "mensagem":
                "A data ou horário informado é inválido."
        }), 400

    service = PostagemService()

    try:

        resultado = service.agendar(
            imagem_id=imagem_id,
            agendado_para_utc=
                agendado_para_utc,
            chave_idempotencia=
                chave
        )

        return jsonify({
            "success": True,
            "mensagem":
                "Story agendado com sucesso.",
            "postagem":
                resultado["postagem"]
        }), 201

    except HorarioInvalido as erro:

        return jsonify({
            "success": False,
            "codigo":
                "HORARIO_INVALIDO",
            "mensagem": str(erro)
        }), 400

    except ImagemNaoEncontrada as erro:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_NAO_ENCONTRADA",
            "mensagem": str(erro)
        }), 404

    except ImagemIndisponivel as erro:

        return jsonify({
            "success": False,
            "codigo":
                "IMAGEM_INDISPONIVEL",
            "mensagem": str(erro)
        }), 409
        
@postagens_bp.post(
    "/<int:postagem_id>/cancelar"
)
def cancelar_postagem(postagem_id):

    service = PostagemService()

    try:

        postagem = service.cancelar(
            postagem_id
        )

        if postagem is None:

            return jsonify({
                "success": False,
                "codigo":
                    "POSTAGEM_NAO_ENCONTRADA",
                "mensagem":
                    "A postagem não foi encontrada."
            }), 404

        return jsonify({
            "success": True,
            "mensagem":
                "Agendamento cancelado.",
            "postagem":
                postagem
        })

    except PostagemJaFinalizada as erro:

        return jsonify({
            "success": False,
            "codigo":
                "POSTAGEM_NAO_CANCELAVEL",
            "mensagem": str(erro)
        }), 409
        
@postagens_bp.post(
    "/<int:postagem_id>/tentar-novamente"
)
def tentar_novamente(postagem_id):

    service = PostagemService()

    try:

        postagem = (
            service.preparar_nova_tentativa(
                postagem_id
            )
        )

        if postagem is None:

            return jsonify({
                "success": False,
                "codigo":
                    "POSTAGEM_NAO_ENCONTRADA",
                "mensagem":
                    "Publicação não encontrada."
            }), 404

        return jsonify({
            "success": True,
            "mensagem":
                "Nova tentativa programada.",
            "postagem":
                postagem
        })

    except ValueError as erro:

        return jsonify({
            "success": False,
            "codigo":
                "NOVA_TENTATIVA_NAO_PERMITIDA",
            "mensagem":
                str(erro)
        }), 409