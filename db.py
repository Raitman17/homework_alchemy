"""Модуль для работы с базой данных."""

import os
from typing import Callable
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session, exc

from football_api import get_data_league, get_data_team, get_team_roster
from models import League, Player, Stadium, Team


def get_db_url() -> str:
    """Получить данные для подключение к базе данных.

    Returns:
        str: данные для подключения к базе данных
    """
    load_dotenv()
    pg_vars = 'PG_USER', 'PG_PASSWORD', 'PG_HOST', 'PG_PORT', 'PG_DBNAME'
    credentials = [os.environ.get(pg_var) for pg_var in pg_vars]
    return 'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(*credentials)


engine = create_engine(get_db_url(), echo=False)


def add_league_api(name: str, country: str, session: Session) -> League | None:
    """Добавить лигу с использованием внешнего апи.

    Args:
        name (str): название лиги
        country (str): страна
        session (Session): сессия

    Returns:
        League | None: объект класса Лига или ничего, если не получилось добавить.
    """
    league = session.scalar(select(League).where(League.name == name, League.country == country))
    if league:
        return league
    data_league = get_data_league(name, country)
    if data_league:
        league = League(name=name, country=country, logo=data_league[1], api_id=data_league[0])
        session.add(league)
        session.commit()
        return league
    return None


def add_stadium_api(venue: dict, session: Session) -> UUID:
    """Добавить стадион с использованием внешнего апи.

    Args:
        venue (dict): словарь с данными о стадионе
        session (Session): сессия

    Returns:
        UUID: id стадиона
    """
    stadium = session.scalar(select(Stadium).where(
        Stadium.name == venue['name'], Stadium.address == venue['address'],
    ))
    if stadium:
        return stadium.id
    stadium = Stadium(
        name=venue['name'],
        address=venue['address'],
        city=venue['city'],
        capacity=venue['capacity'],
        surface=venue['surface'],
        image=venue['image'],
    )
    session.add(stadium)
    session.commit()
    return stadium.id


def add_players_api(team_id: Team, api_id: int, session: Session):
    """Добавить игроков с использованием внешнего апи.

    Args:
        team_id (Team): id команды
        api_id (int): api id команды
        session (Session): сессия
    """
    roster = get_team_roster(api_id)
    players = [Player(**player, team_id=team_id) for player in roster]
    session.add_all(players)
    session.commit()


def add_team_api(name: str, league: str, country: str, session: Session) -> UUID | None:
    """Добавить команду с использованием внешнего апи.

    Args:
        name (str): название команды
        league (str): название лиги
        country (str): страна
        session (Session): сессия

    Returns:
        UUID | None: id команды или ничего, если не получилось добавить
    """
    league = add_league_api(league, country, session)
    if not league:
        return None
    team = session.scalar(select(Team).where(Team.name == name, Team.league == league))
    if team:
        return team.id
    team_json = get_data_team(name, league.api_id)
    if team_json:
        stadium_id = add_stadium_api(team_json['venue'], session)
        team = Team(
            name=team_json['team']['name'], founded=team_json['team']['founded'],
            logo=team_json['team']['logo'], league_id=league.id, stadium_id=stadium_id,
        )
        session.add(team)
        session.commit()
        add_players_api(team.id, team_json['team']['id'], session)
        return team.id
    return None


def delete_empty_relations(model_id: str, model_class, session: Session):
    """Удалить пустые связи.

    Args:
        model_id (str): id модели
        model_class (_type_): класс модели
        session (Session): сессия
    """
    if not model_id:
        return
    if model_class == Stadium:
        teams = session.scalars(select(Team).where(Team.stadium_id == model_id)).all()
    else:
        teams = session.scalars(select(Team).where(Team.league_id == model_id)).all()
    if not teams:
        session.delete(session.scalar(select(model_class).where(model_class.id == model_id)))
        session.commit()


def create_delete(model_class) -> Callable:
    """Создать метод для удаления записи.

    Args:
        model_class (_type_): класс модели

    Returns:
        Callable: функция для удаления записи
    """
    def delete_obj(obj_id: UUID, session: Session) -> int | None:
        """Удалить объект.

        Args:
            obj_id (UUID): id записи
            session (Session): сессия

        Returns:
            int | None: 1 или ничего, если запись не найдена или ошибка
        """
        try:
            data_obj = session.scalar(select(model_class).where(model_class.id == obj_id))
            if not data_obj:
                return None
            session.delete(data_obj)
            session.commit()
            if model_class == Team:
                delete_empty_relations(data_obj.stadium_id, Stadium, session)
                delete_empty_relations(data_obj.league_id, League, session)
            return 1
        except DataError:
            return None
    return delete_obj


delete_league = create_delete(League)
delete_stadium = create_delete(Stadium)
delete_player = create_delete(Player)
delete_team = create_delete(Team)


def create_add(model_class) -> Callable:
    """Создать метод для добавления записи.

    Args:
        model_class (_type_): класс модели

    Returns:
        Callable: функция для добавления записи
    """
    def create_obj(data_obj: dict, session: Session) -> UUID | None:
        """Создать объект.

        Args:
            data_obj (dict): словарь, с данными о объекте
            session (Session): сессия

        Returns:
            UUID | None: id или ничего, если не получилось создать объект
        """
        try:
            rec = model_class(**data_obj)
            session.add(rec)
            session.commit()
            return rec.id
        except IntegrityError:
            return None
        except ProgrammingError:
            return None
        except DataError:
            return None
    return create_obj


create_league = create_add(League)
create_stadium = create_add(Stadium)
create_player = create_add(Player)
create_team = create_add(Team)


def create_update(model_class) -> Callable:
    """Создать метод для обновления записи.

    Args:
        model_class (_type_): класс модели

    Returns:
        Callable: функция для обновления записи
    """
    def update_obj(data_obj: dict, session: Session):
        """Обновить объект.

        Args:
            data_obj (dict): словарь, с данными для обновления
            session (Session): сессия

        Returns:
            UUID | None: id или ничего, если не получилось обновить объект
        """
        if 'stadium_id' in data_obj.keys():
            data_obj['stadium_id'] = data_obj['stadium_id'] if data_obj['stadium_id'] else None
        if 'league_id' in data_obj.keys():
            data_obj['league_id'] = data_obj['league_id'] if data_obj['league_id'] else None
        try:
            session.bulk_update_mappings(model_class, [{'id': data_obj['id'], **data_obj}])
            session.commit()
            return data_obj['id']
        except DataError:
            return None
        except exc.StaleDataError:
            return None
        except IntegrityError:
            return None
    return update_obj


update_league = create_update(League)
update_stadium = create_update(Stadium)
update_player = create_update(Player)
update_team = create_update(Team)


def create_get(model_class) -> Callable:
    """Создать метод для получения данных о записи.

    Args:
        model_class (_type_): класс модели

    Returns:
        Callable: функция для получения данных о записи
    """
    def get_obj(obj_id: dict, session: Session) -> dict | None:
        """Получить объект.

        Args:
            obj_id (dict): id записи
            session (Session): сессия

        Returns:
            dict | None: словарь с данными о объекте или ничего, если запись не найдена или ошибка
        """
        data_obj = session.scalar(select(model_class).where(model_class.id == obj_id))
        if not data_obj:
            return None
        return data_obj.__dict__
    return get_obj


get_league = create_get(League)
get_stadium = create_get(Stadium)
get_player = create_get(Player)
get_team = create_get(Team)


def create_get_all(model_class) -> Callable:
    """Создать метод для получения всех записей модели.

    Args:
        model_class (_type_): класс модели

    Returns:
        Callable: функция для получения данных о записи
    """
    def get_all_obj(session: Session) -> list:
        """Получить все записи модели.

        Args:
            session (Session): сессия

        Returns:
            list: список объектов класса команда
        """
        model_values = [mod_val.__dict__ for mod_val in session.scalars(select(model_class))]
        for mod_val in model_values:
            mod_val.pop('_sa_instance_state', None)
            for keys, value_field in mod_val.items():
                if isinstance(value_field, UUID):
                    mod_val[keys] = str(value_field)
        return model_values
    return get_all_obj


get_all_teams = create_get_all(Team)
get_all_stadium = create_get_all(Stadium)
get_all_league = create_get_all(League)
get_all_player = create_get_all(Player)


def get_players_of_team(team_id, session: Session) -> list[dict]:
    """получить игроков команды.

    Args:
        team_id (_type_): id команды
        session (Session): сессия

    Returns:
        list[dict]: список словарей с данными об игроках или ничего,
        если у команды нет игроко или ошибка
    """
    try:
        players = session.scalars(select(Player).where(Player.team_id == team_id))
    except DataError:
        return None
    if players:
        return [player.__dict__ for player in players]
    return None
