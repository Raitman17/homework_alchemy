"""Модуль для моделей таблиц в базе данных."""

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для таблиц."""

    pass


DEFAULT_IMAGE_CLUB = 'https://cdn.enjore.com/source/img/team/badge/q/1636120TLU33i410VLqAu.png'
DEFAULT_IMAGE_PLAYER = 'https://media.api-sports.io/football/players/330612.png'
DEFAULT_IMAGE_STADIUM = 'https://i.postimg.cc/fbWZrq56/121675725.webp'


class UUIDMixin:
    """Класс миксин для поля: id."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class League(UUIDMixin, Base):
    """Класс для таблицы: лиги."""

    __tablename__ = 'leagues'

    name: Mapped[str]
    country: Mapped[str]
    logo: Mapped[str] = mapped_column(nullable=True, default=DEFAULT_IMAGE_CLUB)
    api_id: Mapped[int] = mapped_column(nullable=True)

    teams: Mapped[list['Team']] = relationship(
        back_populates='league', cascade='all, delete-orphan',
    )

    __table_args__ = (
        UniqueConstraint('name', 'country', name='league_unique_name_country'),
        CheckConstraint('length(name) < 80 and length(country) < 80 and length(logo) < 500'),
    )


class Team(UUIDMixin, Base):
    """Класс для таблицы: команды."""

    __tablename__ = 'teams'

    name: Mapped[str]
    founded: Mapped[int]
    logo: Mapped[str] = mapped_column(nullable=True, default=DEFAULT_IMAGE_CLUB)
    stadium_id: Mapped[UUID] = mapped_column(ForeignKey('stadiums.id'), nullable=True)
    league_id: Mapped[UUID] = mapped_column(ForeignKey('leagues.id'), nullable=True)

    league: Mapped['League'] = relationship(back_populates='teams')
    players: Mapped[list['Player']] = relationship(
        back_populates='team', cascade='all, delete-orphan',
    )
    stadium: Mapped['Stadium'] = relationship(back_populates='teams')

    __table_args__ = (
        UniqueConstraint('name', 'founded', name='team_unique_name_founded'),
        CheckConstraint('length(name) < 80 and length(logo) < 500'),
        CheckConstraint("founded <= (date_part('year', now()))", name='founded_not_future'),
    )


class Stadium(UUIDMixin, Base):
    """Класс для таблицы: стадионы."""

    __tablename__ = 'stadiums'

    name: Mapped[str]
    address: Mapped[str]
    city: Mapped[str]
    capacity: Mapped[int] = mapped_column(nullable=True)
    surface: Mapped[str] = mapped_column(nullable=True)
    image: Mapped[str] = mapped_column(nullable=True, default=DEFAULT_IMAGE_STADIUM)

    teams: Mapped[list['Team']] = relationship(
        back_populates='stadium', cascade='all, delete-orphan',
    )

    __table_args__ = (
        UniqueConstraint('name', 'address', name='stadium_unique_name_address'),
        CheckConstraint('length(name) < 80 and length(image) < 500'),
        CheckConstraint('length(address) < 150 and length(city) < 80'),
        CheckConstraint('capacity > 0', name='capacity_positive'),
    )


class Player(UUIDMixin, Base):
    """Класс для таблицы: игроки."""

    __tablename__ = 'players'

    name: Mapped[str]
    age: Mapped[int] = mapped_column(nullable=True)
    number: Mapped[int] = mapped_column(nullable=True)
    position: Mapped[str] = mapped_column(nullable=True)
    photo: Mapped[str] = mapped_column(nullable=True, default=DEFAULT_IMAGE_PLAYER)
    team_id: Mapped[UUID] = mapped_column(ForeignKey('teams.id'))

    team: Mapped['Team'] = relationship(back_populates='players')

    __table_args__ = (
        UniqueConstraint('name', 'age', 'number', name='player_unique_name_age_number'),
        CheckConstraint(
            'length(name) < 80 and length(position) < 40 and length(photo) < 500',
        ),
        CheckConstraint('number > 0 and age > 0', name='number_age_positive'),
    )
