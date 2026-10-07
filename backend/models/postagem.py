import uuid

from datetime import datetime, timezone

from extensions import db


class Postagem(db.Model):
    __tablename__ = "postagens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    imagem_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "imagens.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    tipo = db.Column(
        db.Enum(
            "STORY",
            name="tipo_postagem"
        ),
        nullable=False,
        default="STORY"
    )

    status = db.Column(
        db.Enum(
            "RASCUNHO",
            "AGENDADO",
            "PROCESSANDO",
            "PUBLICADO",
            "ERRO",
            "CANCELADO",
            name="status_postagem"
        ),
        nullable=False,
        default="RASCUNHO",
        index=True
    )

    agendado_para = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    chave_idempotencia = db.Column(
        db.String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4())
    )

    instagram_container_id = db.Column(
        db.String(100),
        nullable=True
    )

    instagram_media_id = db.Column(
        db.String(100),
        nullable=True
    )

    tentativas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    erro_codigo = db.Column(
        db.String(100),
        nullable=True
    )

    erro_mensagem = db.Column(
        db.Text,
        nullable=True
    )

    ultima_tentativa_em = db.Column(
        db.DateTime,
        nullable=True
    )

    publicado_em = db.Column(
        db.DateTime,
        nullable=True
    )

    cancelado_em = db.Column(
        db.DateTime,
        nullable=True
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    imagem = db.relationship(
        "Imagem",
        backref="postagens"
    )
    
    fase_processamento = db.Column(
        db.String(50),
        nullable=False,
        default="PENDENTE"
    )

    erro_tipo = db.Column(
        db.String(50),
        nullable=True
    )

    erro_recuperavel = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    proxima_tentativa_em = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    processando_desde = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )