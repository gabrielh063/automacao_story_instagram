from datetime import datetime, timezone

from extensions import db


class Imagem(db.Model):
    __tablename__ = "imagens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    s3_key = db.Column(
        db.String(500),
        nullable=False,
        unique=True,
        index=True
    )

    nome_original = db.Column(
        db.String(255),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    tamanho_bytes = db.Column(
        db.BigInteger,
        nullable=True
    )

    ativa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
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