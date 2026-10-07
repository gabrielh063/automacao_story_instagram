import requests

from config import Config


class InstagramApiError(Exception):

    def __init__(
        self,
        mensagem,
        codigo=None,
        subcodigo=None,
        transitorio=False,
        http_status=None
    ):
        super().__init__(mensagem)

        self.codigo = codigo
        self.subcodigo = subcodigo
        self.transitorio = transitorio
        self.http_status = http_status


class InstagramNetworkError(Exception):

    def __init__(
        self,
        mensagem,
        publicacao_ambigua=False
    ):
        super().__init__(mensagem)

        self.publicacao_ambigua = publicacao_ambigua


class InstagramService:

    def __init__(self):

        self.user_id = Config.INSTAGRAM_USER_ID
        self.token = Config.INSTAGRAM_ACCESS_TOKEN
        self.base_url = Config.INSTAGRAM_GRAPH_URL

        if not self.user_id:
            raise RuntimeError(
                "INSTAGRAM_USER_ID não configurado."
            )

        if not self.token:
            raise RuntimeError(
                "INSTAGRAM_ACCESS_TOKEN não configurado."
            )

    def _headers(self):

        return {
            "Authorization":
                f"Bearer {self.token}"
        }

    def _validar_resposta(self, resposta):

        try:
            dados = resposta.json()

        except ValueError:
            dados = {}

        if resposta.ok:
            return dados

        erro = dados.get("error", {})

        mensagem = erro.get(
            "message",
            "Erro desconhecido retornado pelo Instagram."
        )

        raise InstagramApiError(
            mensagem=mensagem,
            codigo=erro.get("code"),
            subcodigo=erro.get("error_subcode"),
            transitorio=erro.get(
                "is_transient",
                False
            ),
            http_status=resposta.status_code
        )

    def criar_story(self, image_url):

        url = (
            f"{self.base_url}/"
            f"{self.user_id}/media"
        )

        try:

            resposta = requests.post(
                url,
                headers=self._headers(),
                data={
                    "media_type": "STORIES",
                    "image_url": image_url
                },
                timeout=30
            )

        except (
            requests.Timeout,
            requests.ConnectionError
        ) as erro:

            raise InstagramNetworkError(
                "Não foi possível conectar ao Instagram."
            ) from erro

        dados = self._validar_resposta(
            resposta
        )

        return dados["id"]

    def consultar_status(
        self,
        container_id
    ):

        url = (
            f"{self.base_url}/"
            f"{container_id}"
        )

        try:

            resposta = requests.get(
                url,
                headers=self._headers(),
                params={
                    "fields":
                        "status_code,status"
                },
                timeout=30
            )

        except (
            requests.Timeout,
            requests.ConnectionError
        ) as erro:

            raise InstagramNetworkError(
                "Não foi possível consultar "
                "o processamento da mídia."
            ) from erro

        return self._validar_resposta(
            resposta
        )

    def aguardar_processamento(
        self,
        container_id,
        tentativas=30,
        intervalo=2
    ):

        import time

        for _ in range(tentativas):

            dados = self.consultar_status(
                container_id
            )

            status = dados.get(
                "status_code"
            )

            if status == "FINISHED":
                return dados

            if status in (
                "ERROR",
                "EXPIRED"
            ):
                raise InstagramApiError(
                    mensagem=(
                        f"Instagram retornou "
                        f"status {status}."
                    ),
                    transitorio=False
                )

            time.sleep(intervalo)

        raise InstagramNetworkError(
            "O Instagram demorou demais "
            "para processar a imagem."
        )

    def publicar_container(
        self,
        container_id
    ):

        url = (
            f"{self.base_url}/"
            f"{self.user_id}/media_publish"
        )

        try:

            resposta = requests.post(
                url,
                headers=self._headers(),
                data={
                    "creation_id":
                        container_id
                },
                timeout=30
            )

        except (
            requests.Timeout,
            requests.ConnectionError
        ) as erro:

            #
            # CUIDADO:
            #
            # A requisição pode ter chegado
            # à Meta antes da conexão cair.
            #
            # Repetir automaticamente poderia
            # gerar duplicidade.
            #

            raise InstagramNetworkError(
                "A conexão caiu durante a "
                "publicação. Não é possível "
                "confirmar automaticamente se "
                "o Story foi publicado.",
                publicacao_ambigua=True
            ) from erro

        return self._validar_resposta(
            resposta
        )