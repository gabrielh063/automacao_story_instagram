from flask import (
    Blueprint,
    jsonify,
    request
)

from services.s3_service import S3Service
from services.instagram_service import (
    InstagramService
)


stories_bp = Blueprint(
    "stories",
    __name__,
    url_prefix="/api"
)


@stories_bp.get("/fotos")
def listar_fotos():

    try:

        s3 = S3Service()

        fotos = s3.listar_fotos()

        return jsonify({
            "quantidade": len(fotos),
            "fotos": fotos
        })

    except Exception as erro:

        return jsonify({
            "erro": str(erro)
        }), 500


@stories_bp.post(
    "/stories/publicar"
)
def publicar_story():

    dados = request.get_json(
        silent=True
    ) or {}

    s3_key = dados.get("s3_key")

    if not s3_key:

        return jsonify({
            "erro":
                "Informe o campo s3_key."
        }), 400

    try:

        s3 = S3Service()

        instagram = (
            InstagramService()
        )

        image_url = (
            s3.gerar_url_temporaria(
                s3_key,
                expiracao=1800
            )
        )

        resultado = (
            instagram.publicar_story(
                image_url
            )
        )

        return jsonify({
            "success": True,
            "s3_key": s3_key,
            "container_id":
                resultado[
                    "container_id"
                ],
            "media_id":
                resultado[
                    "media_id"
                ]
        })

    except ValueError as erro:

        return jsonify({
            "erro": str(erro)
        }), 400

    except Exception as erro:

        return jsonify({
            "erro": str(erro)
        }), 500