import boto3

from config import Config


class S3Service:

    def __init__(self):

        session = boto3.Session(
            profile_name=Config.AWS_PROFILE,
            region_name=Config.AWS_REGION
        )

        self.s3 = session.client("s3")

        self.bucket = Config.AWS_S3_BUCKET
        self.prefix = Config.AWS_S3_PREFIX

    def listar_fotos(self):

        resposta = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.prefix
        )

        fotos = []

        for objeto in resposta.get("Contents", []):

            key = objeto["Key"]

            # ignora a própria "pasta"
            if key.endswith("/"):
                continue

            url = self.gerar_url_temporaria(
                key,
                expiracao=1800
            )

            fotos.append({
                "key": key,
                "nome": key.split("/")[-1],
                "tamanho": objeto["Size"],
                "ultima_modificacao": objeto[
                    "LastModified"
                ].isoformat(),
                "url": url
            })

        return fotos

    def gerar_url_temporaria(
        self,
        key,
        expiracao=1800
    ):

        # Segurança:
        # só aceita arquivos do banco-fotos/
        if not key.startswith(self.prefix):
            raise ValueError(
                "Arquivo fora do banco de fotos."
            )

        url = self.s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key
            },
            ExpiresIn=expiracao
        )

        return url