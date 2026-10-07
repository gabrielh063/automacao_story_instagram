import mimetypes

from extensions import db
from models.imagem import Imagem
from services.s3_service import S3Service


class ImagemService:

    def __init__(self):
        self.s3 = S3Service()

    def sincronizar_s3(self):

        resposta = self.s3.s3.list_objects_v2(
            Bucket=self.s3.bucket,
            Prefix=self.s3.prefix
        )

        objetos = resposta.get("Contents", [])

        chaves_encontradas = set()

        criadas = 0
        atualizadas = 0
        desativadas = 0

        for objeto in objetos:

            key = objeto["Key"]

            if key.endswith("/"):
                continue

            chaves_encontradas.add(key)

            nome = key.split("/")[-1]

            mime_type, _ = mimetypes.guess_type(nome)

            imagem = Imagem.query.filter_by(
                s3_key=key
            ).first()

            if imagem is None:

                imagem = Imagem(
                    s3_key=key,
                    nome_original=nome,
                    mime_type=mime_type,
                    tamanho_bytes=objeto["Size"],
                    ativa=True
                )

                db.session.add(imagem)

                criadas += 1

            else:

                alterada = False

                if imagem.nome_original != nome:
                    imagem.nome_original = nome
                    alterada = True

                if imagem.mime_type != mime_type:
                    imagem.mime_type = mime_type
                    alterada = True

                if imagem.tamanho_bytes != objeto["Size"]:
                    imagem.tamanho_bytes = objeto["Size"]
                    alterada = True

                if not imagem.ativa:
                    imagem.ativa = True
                    alterada = True

                if alterada:
                    atualizadas += 1

        imagens_ativas = Imagem.query.filter_by(
            ativa=True
        ).all()

        for imagem in imagens_ativas:

            if imagem.s3_key not in chaves_encontradas:
                imagem.ativa = False
                desativadas += 1

        db.session.commit()

        return {
            "encontradas_s3": len(chaves_encontradas),
            "criadas": criadas,
            "atualizadas": atualizadas,
            "desativadas": desativadas
        }

    def listar_ativas(self):

        imagens = (
            Imagem.query
            .filter_by(ativa=True)
            .order_by(Imagem.nome_original.asc())
            .all()
        )

        resultado = []

        for imagem in imagens:

            url = self.s3.gerar_url_temporaria(
                imagem.s3_key,
                expiracao=1800
            )

            resultado.append({
                "id": imagem.id,
                "nome": imagem.nome_original,
                "s3_key": imagem.s3_key,
                "mime_type": imagem.mime_type,
                "tamanho_bytes": imagem.tamanho_bytes,
                "url": url
            })

        return resultado