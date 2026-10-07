from datetime import datetime, timezone

from extensions import db


class PostagemEvento(db.Model):
    __tablename__ = "postagem_eventos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    postagem_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "postagens.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    evento = db.Column(
        db.String(100),
        nullable=False
    )

    mensagem = db.Column(
        db.Text,
        nullable=True
    )

    detalhes = db.Column(
        db.JSON,
        nullable=True
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    postagem = db.relationship(
        "Postagem",
        backref="eventos"
    )