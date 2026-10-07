from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from extensions import db
from models.imagem import Imagem
from models.postagem import Postagem
from models.postagem_evento import PostagemEvento
from services.instagram_service import (
    InstagramApiError,
    InstagramNetworkError,
    InstagramService,
)
from services.s3_service import S3Service


def utc_now():
    """Retorna o horário atual em UTC sem tzinfo para DATETIME do MariaDB."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalizar_utc_naive(data):
    """Normaliza um datetime para UTC sem tzinfo, compatível com o MariaDB."""
    if data is None:
        return None

    if data.tzinfo is not None:
        data = data.astimezone(timezone.utc).replace(tzinfo=None)

    return data.replace(microsecond=0)


def iso_utc(data):
    """Serializa um DATETIME armazenado em UTC usando o sufixo Z."""
    if data is None:
        return None

    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    else:
        data = data.astimezone(timezone.utc)

    return data.isoformat().replace("+00:00", "Z")


class HorarioInvalido(Exception):
    pass


class PostagemJaFinalizada(Exception):
    pass


class ImagemNaoEncontrada(Exception):
    pass


class ImagemIndisponivel(Exception):
    pass


class ConflitoIdempotencia(Exception):
    pass


class InstagramOcupado(Exception):
    pass


class ErroPublicacao(Exception):
    def __init__(self, postagem_id, mensagem):
        self.postagem_id = postagem_id
        self.mensagem = mensagem
        super().__init__(mensagem)


class PostagemService:
    def __init__(self):
        self.s3 = S3Service()
        self.instagram = InstagramService()

    def _registrar_evento(
        self,
        postagem_id,
        evento,
        mensagem=None,
        detalhes=None,
    ):
        registro = PostagemEvento(
            postagem_id=postagem_id,
            evento=evento,
            mensagem=mensagem,
            detalhes=detalhes,
        )
        db.session.add(registro)

    def _tem_evento(self, postagem_id, evento):
        """Retorna True quando a postagem já possui determinado evento."""
        return (
            PostagemEvento.query
            .filter_by(
                postagem_id=postagem_id,
                evento=evento,
            )
            .first()
            is not None
        )

    def _serializar(self, postagem, incluir_eventos=False):
        dados = {
            "id": postagem.id,
            "imagem_id": postagem.imagem_id,
            "imagem_nome": (
                postagem.imagem.nome_original
                if postagem.imagem
                else None
            ),
            "tipo": postagem.tipo,
            "status": postagem.status,
            "fase_processamento": getattr(
                postagem, "fase_processamento", None
            ),
            "agendado_para": iso_utc(postagem.agendado_para),
            "tentativas": postagem.tentativas,
            "ultima_tentativa_em": iso_utc(
                getattr(postagem, "ultima_tentativa_em", None)
            ),
            "processando_desde": iso_utc(
                getattr(postagem, "processando_desde", None)
            ),
            "proxima_tentativa_em": iso_utc(
                getattr(postagem, "proxima_tentativa_em", None)
            ),
            "instagram_container_id": postagem.instagram_container_id,
            "instagram_media_id": postagem.instagram_media_id,
            "erro_codigo": postagem.erro_codigo,
            "erro_tipo": getattr(postagem, "erro_tipo", None),
            "erro_recuperavel": bool(
                getattr(postagem, "erro_recuperavel", False)
            ),
            "erro_mensagem": postagem.erro_mensagem,
            "publicado_em": iso_utc(postagem.publicado_em),
            "cancelado_em": iso_utc(
                getattr(postagem, "cancelado_em", None)
            ),
            "criado_em": iso_utc(postagem.criado_em),
            "atualizado_em": iso_utc(
                getattr(postagem, "atualizado_em", None)
            ),
        }

        if incluir_eventos:
            eventos = (
                PostagemEvento.query
                .filter_by(postagem_id=postagem.id)
                .order_by(PostagemEvento.id.asc())
                .all()
            )

            dados["eventos"] = [
                {
                    "id": evento.id,
                    "evento": evento.evento,
                    "mensagem": evento.mensagem,
                    "detalhes": evento.detalhes,
                    "criado_em": iso_utc(evento.criado_em),
                }
                for evento in eventos
            ]

        return dados

    def obter(self, postagem_id):
        postagem = db.session.get(Postagem, postagem_id)

        if postagem is None:
            return None

        return self._serializar(
            postagem,
            incluir_eventos=True,
        )

    def listar(self, limite=50, status=None):
        consulta = Postagem.query

        if status:
            consulta = consulta.filter(Postagem.status == status)

        # Na tela de agendamentos, o próximo Story vem primeiro.
        # No histórico, o registro mais recente vem primeiro.
        if status == "AGENDADO":
            consulta = consulta.order_by(
                Postagem.agendado_para.asc(),
                Postagem.id.asc(),
            )
        else:
            consulta = consulta.order_by(Postagem.id.desc())

        postagens = consulta.limit(limite).all()

        return [
            self._serializar(postagem)
            for postagem in postagens
        ]

    def publicar_agora(
        self,
        imagem_id,
        chave_idempotencia,
    ):
        # 1. Idempotência: a mesma solicitação não pode criar outra postagem.
        existente = (
            Postagem.query
            .filter_by(chave_idempotencia=chave_idempotencia)
            .first()
        )

        if existente:
            if existente.imagem_id != imagem_id:
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada para outra imagem."
                )

            # Uma publicação imediata pode ganhar agendado_para caso precise
            # entrar na fila. Por isso, não usamos mais agendado_para como único
            # critério para diferenciar publicação imediata de agendamento.
            if not self._tem_evento(
                existente.id,
                "PUBLICACAO_SOLICITADA",
            ):
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada em um agendamento."
                )

            enfileirada = (
                existente.status == "AGENDADO"
                and getattr(
                    existente,
                    "fase_processamento",
                    None,
                ) == "AGUARDANDO_FILA"
            )

            return {
                "nova": False,
                "enfileirada": enfileirada,
                "postagem": self._serializar(existente),
            }

        # 2. Valida a imagem antes de criar a postagem.
        imagem = db.session.get(Imagem, imagem_id)

        if imagem is None:
            raise ImagemNaoEncontrada(
                "A imagem selecionada não existe."
            )

        if not imagem.ativa:
            raise ImagemIndisponivel(
                "A imagem selecionada não está mais disponível para publicação."
            )

        agora = utc_now()

        # 3. Registra a solicitação antes de chamar serviços externos.
        postagem = Postagem(
            imagem_id=imagem.id,
            tipo="STORY",
            status="PROCESSANDO",
            chave_idempotencia=chave_idempotencia,
            tentativas=1,
            ultima_tentativa_em=agora,
        )

        if hasattr(postagem, "fase_processamento"):
            postagem.fase_processamento = "PENDENTE"

        if hasattr(postagem, "processando_desde"):
            postagem.processando_desde = agora

        db.session.add(postagem)
        db.session.flush()

        self._registrar_evento(
            postagem.id,
            "PUBLICACAO_SOLICITADA",
            "Publicação imediata solicitada.",
            {"imagem_id": imagem.id},
        )

        self._registrar_evento(
            postagem.id,
            "PROCESSANDO",
            "Preparando a imagem para publicação.",
        )

        db.session.commit()
        postagem_id = postagem.id

        # A publicação imediata usa exatamente a mesma rotina do worker.
        # Se outra publicação já estiver usando o Instagram, processar_postagem
        # devolve a postagem como AGENDADO / AGUARDANDO_FILA.
        try:
            postagem = self.processar_postagem(postagem_id)

            enfileirada = (
                postagem.status == "AGENDADO"
                and getattr(
                    postagem,
                    "fase_processamento",
                    None,
                ) == "AGUARDANDO_FILA"
            )

            return {
                "nova": True,
                "enfileirada": enfileirada,
                "postagem": self._serializar(postagem),
            }

        except Exception as erro:
            # processar_postagem já registrou/classificou a falha.
            raise ErroPublicacao(
                postagem_id,
                "Não foi possível publicar o Story.",
            ) from erro

    def agendar(
        self,
        imagem_id,
        agendado_para_utc,
        chave_idempotencia,
    ):
        agendado_para_utc = normalizar_utc_naive(
            agendado_para_utc
        )

        existente = (
            Postagem.query
            .filter_by(chave_idempotencia=chave_idempotencia)
            .first()
        )

        if existente:
            if existente.imagem_id != imagem_id:
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada para outra imagem."
                )

            # Se existe PUBLICACAO_SOLICITADA, a chave pertence a uma
            # publicação imediata, mesmo que ela tenha sido colocada na fila.
            if self._tem_evento(
                existente.id,
                "PUBLICACAO_SOLICITADA",
            ):
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada em uma publicação imediata."
                )

            if existente.agendado_para is None:
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada em outra operação."
                )

            agendamento_existente = normalizar_utc_naive(
                existente.agendado_para
            )

            if agendamento_existente != agendado_para_utc:
                raise ConflitoIdempotencia(
                    "Esta chave de solicitação já foi utilizada para outro horário."
                )

            return {
                "nova": False,
                "postagem": self._serializar(existente),
            }

        imagem = db.session.get(Imagem, imagem_id)

        if imagem is None:
            raise ImagemNaoEncontrada(
                "A imagem selecionada não existe."
            )

        if not imagem.ativa:
            raise ImagemIndisponivel(
                "A imagem selecionada não está disponível."
            )

        agora = utc_now().replace(microsecond=0)

        if agendado_para_utc <= agora:
            raise HorarioInvalido(
                "Escolha um horário futuro para a publicação."
            )

        postagem = Postagem(
            imagem_id=imagem.id,
            tipo="STORY",
            status="AGENDADO",
            agendado_para=agendado_para_utc,
            chave_idempotencia=chave_idempotencia,
            tentativas=0,
        )

        if hasattr(postagem, "fase_processamento"):
            postagem.fase_processamento = "PENDENTE"

        db.session.add(postagem)
        db.session.flush()

        self._registrar_evento(
            postagem.id,
            "AGENDADO",
            "Story agendado para publicação.",
            {
                "imagem_id": imagem.id,
                "agendado_para_utc": iso_utc(agendado_para_utc),
            },
        )

        db.session.commit()

        return {
            "nova": True,
            "postagem": self._serializar(postagem),
        }

    def cancelar(self, postagem_id):
        postagem = db.session.get(Postagem, postagem_id)

        if postagem is None:
            return None

        if postagem.status == "PUBLICADO":
            raise PostagemJaFinalizada(
                "Uma publicação já realizada não pode ser cancelada."
            )

        if postagem.status == "PROCESSANDO":
            raise PostagemJaFinalizada(
                "A publicação já está sendo processada."
            )

        if postagem.status == "CANCELADO":
            return self._serializar(postagem)

        postagem.status = "CANCELADO"
        postagem.cancelado_em = utc_now()

        if hasattr(postagem, "fase_processamento"):
            postagem.fase_processamento = "CANCELADA"

        if hasattr(postagem, "proxima_tentativa_em"):
            postagem.proxima_tentativa_em = None

        self._registrar_evento(
            postagem.id,
            "CANCELADO",
            "Agendamento cancelado pelo usuário.",
        )

        db.session.commit()

        return self._serializar(postagem)

    def _classificar_erro(self, erro):
        # Erros de imagem não melhoram sozinhos e exigem intervenção.
        if isinstance(
            erro,
            (ImagemNaoEncontrada, ImagemIndisponivel),
        ):
            return {
                "tipo": "IMAGEM",
                "recuperavel": False,
            }

        # Problema de rede.
        if isinstance(erro, InstagramNetworkError):
            if erro.publicacao_ambigua:
                return {
                    "tipo": "PUBLICACAO_AMBIGUA",
                    "recuperavel": False,
                }

            return {
                "tipo": "TEMPORARIO",
                "recuperavel": True,
            }

        # Erro retornado pela Meta.
        if isinstance(erro, InstagramApiError):
            if erro.codigo == 190:
                return {
                    "tipo": "TOKEN",
                    "recuperavel": False,
                }

            if erro.transitorio:
                return {
                    "tipo": "TEMPORARIO",
                    "recuperavel": True,
                }

            return {
                "tipo": "META",
                "recuperavel": False,
            }

        return {
            "tipo": "DESCONHECIDO",
            "recuperavel": False,
        }

    def _calcular_proxima_tentativa(self, tentativas):
        atrasos = {
            1: 60,
            2: 300,
        }

        segundos = atrasos.get(tentativas)

        if segundos is None:
            return None

        return utc_now() + timedelta(seconds=segundos)

    @contextmanager
    def _lock_instagram(self, timeout=0):
        """
        Garante que apenas uma publicação por conta do Instagram seja
        processada por vez, mesmo com Flask e worker em processos diferentes.
        """
        instagram_user_id = getattr(
            self.instagram,
            "user_id",
            None,
        )

        # Fallback para uma chave estável caso a implementação do serviço
        # não exponha user_id como atributo público.
        if instagram_user_id:
            chave = f"instagram_publish_{instagram_user_id}"
        else:
            chave = "instagram_publish_default"

        conexao = db.engine.connect()
        adquirido = False

        try:
            resultado = conexao.execute(
                text("SELECT GET_LOCK(:chave, :timeout)"),
                {
                    "chave": chave,
                    "timeout": timeout,
                },
            ).scalar()

            adquirido = resultado == 1

            if not adquirido:
                raise InstagramOcupado(
                    "Outra publicação está sendo processada nesta conta."
                )

            yield

        finally:
            if adquirido:
                try:
                    conexao.execute(
                        text("SELECT RELEASE_LOCK(:chave)"),
                        {"chave": chave},
                    )
                finally:
                    conexao.close()
            else:
                conexao.close()

    def _recolocar_na_fila(self, postagem_id):
        """Reagenda sem tratar disputa de lock como falha de publicação."""
        db.session.rollback()

        postagem = db.session.get(
            Postagem,
            postagem_id,
        )

        if postagem is None:
            raise ValueError(
                "Postagem não encontrada ao recolocar na fila."
            )

        postagem.status = "AGENDADO"

        if hasattr(postagem, "fase_processamento"):
            postagem.fase_processamento = "AGUARDANDO_FILA"

        if hasattr(postagem, "processando_desde"):
            postagem.processando_desde = None

        # A disputa por lock não é uma tentativa real de publicação.
        # O worker normalmente incrementa tentativas ao reservar um item;
        # por isso devolvemos esse incremento quando nem chegamos à Meta.
        if postagem.tentativas and postagem.tentativas > 0:
            postagem.tentativas -= 1

        postagem.agendado_para = (
            utc_now() + timedelta(seconds=15)
        )

        postagem.erro_codigo = None
        postagem.erro_mensagem = None

        if hasattr(postagem, "erro_tipo"):
            postagem.erro_tipo = None

        if hasattr(postagem, "erro_recuperavel"):
            postagem.erro_recuperavel = False

        if hasattr(postagem, "proxima_tentativa_em"):
            postagem.proxima_tentativa_em = None

        self._registrar_evento(
            postagem.id,
            "AGUARDANDO_FILA",
            (
                "Outra publicação está sendo processada. "
                "Esta postagem será executada em seguida."
            ),
            {
                "nova_tentativa_em": iso_utc(
                    postagem.agendado_para
                )
            },
        )

        db.session.commit()
        return postagem

    def processar_postagem(self, postagem_id):
        postagem = db.session.get(
            Postagem,
            postagem_id,
        )

        if postagem is None:
            raise ValueError(
                "Postagem não encontrada."
            )

        # Estados terminais não podem ser publicados novamente.
        if postagem.status == "PUBLICADO":
            return postagem

        if postagem.status == "CANCELADO":
            raise PostagemJaFinalizada(
                "Esta publicação foi cancelada."
            )

        try:
            imagem = postagem.imagem

            if not imagem:
                raise ImagemNaoEncontrada(
                    "Imagem não encontrada."
                )

            if not imagem.ativa:
                raise ImagemIndisponivel(
                    "A imagem não está mais disponível."
                )

            postagem.status = "PROCESSANDO"

            if hasattr(postagem, "fase_processamento"):
                postagem.fase_processamento = "PREPARANDO_IMAGEM"

            if hasattr(postagem, "processando_desde"):
                postagem.processando_desde = (
                    postagem.processando_desde or utc_now()
                )

            db.session.commit()

            # Gerar URL do S3 não precisa ocupar o lock do Instagram.
            image_url = self.s3.gerar_url_temporaria(
                imagem.s3_key,
                expiracao=1800,
            )

            # A partir daqui, somente uma postagem por conta pode conversar
            # com a API de publicação do Instagram por vez.
            with self._lock_instagram(timeout=0):
                container_id = postagem.instagram_container_id

                if not container_id:
                    container_id = self.instagram.criar_story(
                        image_url
                    )

                    postagem.instagram_container_id = container_id

                    if hasattr(postagem, "fase_processamento"):
                        postagem.fase_processamento = "CONTAINER_CRIADO"

                    self._registrar_evento(
                        postagem.id,
                        "CONTAINER_CRIADO",
                        "Instagram recebeu a imagem.",
                        {"container_id": container_id},
                    )

                    db.session.commit()

                self.instagram.aguardar_processamento(
                    container_id
                )

                if hasattr(postagem, "fase_processamento"):
                    postagem.fase_processamento = "MIDIA_PROCESSADA"

                self._registrar_evento(
                    postagem.id,
                    "MIDIA_PROCESSADA",
                    "Instagram processou a imagem.",
                )

                db.session.commit()

                # Daqui em diante uma falha de rede pode deixar o resultado
                # ambíguo: a Meta pode publicar sem nossa aplicação receber
                # a resposta.
                if hasattr(postagem, "fase_processamento"):
                    postagem.fase_processamento = "PUBLICANDO"

                db.session.commit()

                resultado = self.instagram.publicar_container(
                    container_id
                )

                postagem.instagram_media_id = resultado["id"]
                postagem.status = "PUBLICADO"

                if hasattr(postagem, "fase_processamento"):
                    postagem.fase_processamento = "CONCLUIDA"

                postagem.publicado_em = utc_now()

                if hasattr(postagem, "processando_desde"):
                    postagem.processando_desde = None

                postagem.erro_codigo = None
                postagem.erro_mensagem = None

                if hasattr(postagem, "erro_tipo"):
                    postagem.erro_tipo = None

                if hasattr(postagem, "erro_recuperavel"):
                    postagem.erro_recuperavel = False

                if hasattr(postagem, "proxima_tentativa_em"):
                    postagem.proxima_tentativa_em = None

                self._registrar_evento(
                    postagem.id,
                    "PUBLICADO",
                    "Story publicado com sucesso.",
                    {"media_id": resultado["id"]},
                )

                db.session.commit()

            return postagem

        except InstagramOcupado:
            # Não é erro da Meta e não deve consumir tentativa.
            return self._recolocar_na_fila(postagem_id)

        except Exception as erro:
            db.session.rollback()

            postagem = db.session.get(
                Postagem,
                postagem_id,
            )

            if postagem is None:
                raise

            classificacao = self._classificar_erro(
                erro
            )

            postagem.status = "ERRO"

            if hasattr(postagem, "erro_tipo"):
                postagem.erro_tipo = classificacao["tipo"]

            if hasattr(postagem, "erro_recuperavel"):
                postagem.erro_recuperavel = classificacao[
                    "recuperavel"
                ]

            postagem.erro_codigo = type(erro).__name__
            postagem.erro_mensagem = str(erro)[:2000]

            if hasattr(postagem, "processando_desde"):
                postagem.processando_desde = None

            if hasattr(postagem, "fase_processamento"):
                postagem.fase_processamento = "ERRO"

            if hasattr(postagem, "proxima_tentativa_em"):
                if (
                    classificacao["recuperavel"]
                    and postagem.tentativas < 3
                ):
                    postagem.proxima_tentativa_em = (
                        self._calcular_proxima_tentativa(
                            postagem.tentativas
                        )
                    )
                else:
                    postagem.proxima_tentativa_em = None

            self._registrar_evento(
                postagem.id,
                "ERRO",
                "A publicação não foi concluída.",
                {
                    "tipo": classificacao["tipo"],
                    "recuperavel": classificacao[
                        "recuperavel"
                    ],
                    "erro_codigo": type(erro).__name__,
                },
            )

            db.session.commit()
            raise

    def preparar_nova_tentativa(self, postagem_id):
        postagem = db.session.get(Postagem, postagem_id)

        if postagem is None:
            return None

        if postagem.status != "ERRO":
            raise ValueError(
                "Somente publicações com erro podem ser reenviadas."
            )

        if getattr(
            postagem,
            "erro_tipo",
            None,
        ) == "PUBLICACAO_AMBIGUA":
            raise ValueError(
                "Não é seguro tentar novamente automaticamente porque "
                "o Instagram pode já ter publicado este Story."
            )

        if postagem.tentativas >= 3:
            raise ValueError(
                "O limite de tentativas desta publicação foi atingido."
            )

        if hasattr(postagem, "erro_recuperavel"):
            postagem.erro_recuperavel = True

        if hasattr(postagem, "proxima_tentativa_em"):
            postagem.proxima_tentativa_em = utc_now()

        self._registrar_evento(
            postagem.id,
            "NOVA_TENTATIVA_SOLICITADA",
            "Usuário solicitou uma nova tentativa.",
        )

        db.session.commit()

        return self._serializar(postagem)
