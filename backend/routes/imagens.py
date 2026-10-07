from flask import Blueprint, jsonify

from services.imagem_service import ImagemService


imagens_bp = Blueprint(
    "imagens",
    __name__,
    url_prefix="/api/imagens"
)


@imagens_bp.post("/sincronizar")
def sincronizar():

    try:

        service = ImagemService()

        resultado = service.sincronizar_s3()

        return jsonify({
            "success": True,
            "mensagem": "Banco de imagens sincronizado com sucesso.",
            **resultado
        })

    except Exception as erro:

        return jsonify({
            "success": False,
            "erro": "Não foi possível sincronizar o banco de imagens.",
            "detalhes": str(erro)
        }), 500


@imagens_bp.get("")
def listar():

    try:

        service = ImagemService()

        imagens = service.listar_ativas()

        return jsonify({
            "quantidade": len(imagens),
            "imagens": imagens
        })

    except Exception as erro:

        return jsonify({
            "success": False,
            "erro": "Não foi possível carregar as imagens.",
            "detalhes": str(erro)
        }), 500