from datetime import date
from typing import NotRequired, TypedDict

from sqlalchemy import Engine, ForeignKey, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[str] = mapped_column(primary_key=True)
    semana: Mapped[str] = mapped_column(index=True)
    post_date: Mapped[date]
    post_type: Mapped[str]
    post_text: Mapped[str | None]
    reach: Mapped[int]
    impressions: Mapped[int]
    likes_and_reactions: Mapped[int]
    comments: Mapped[int]
    shares: Mapped[int]
    saves: Mapped[int]
    link_clicks: Mapped[int | None]
    plays: Mapped[int | None]
    watch_time: Mapped[float | None]
    retention: Mapped[float | None]
    taxa_engajamento: Mapped[float]


class ResumoSemanal(Base):
    __tablename__ = "resumos_semanais"

    semana: Mapped[str] = mapped_column(primary_key=True)
    reach_total: Mapped[int]
    engajamento_total: Mapped[int]
    taxa_engajamento_semanal: Mapped[float]
    quantidade_posts: Mapped[int]
    melhor_post_id: Mapped[str] = mapped_column(ForeignKey("posts.post_id"))
    pior_post_id: Mapped[str] = mapped_column(ForeignKey("posts.post_id"))


class DadosPost(TypedDict):
    post_id: str
    post_date: date
    post_type: str
    post_text: NotRequired[str | None]
    reach: int
    impressions: int
    likes_and_reactions: int
    comments: int
    shares: int
    saves: int
    link_clicks: NotRequired[int | None]
    plays: NotRequired[int | None]
    watch_time: NotRequired[float | None]
    retention: NotRequired[float | None]
    taxa_engajamento: float


def criar_engine(caminho_banco: str = "banco/historico.db") -> Engine:
    engine = create_engine(f"sqlite:///{caminho_banco}")

    @event.listens_for(engine, "connect")
    def _ativar_chaves_estrangeiras(conexao_dbapi, _):
        conexao_dbapi.execute("PRAGMA foreign_keys=ON")

    return engine


def criar_tabelas(engine: Engine) -> None:
    Base.metadata.create_all(engine)
