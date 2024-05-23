"""Модуль для работы с внешним api."""
from os import environ

import requests
from dotenv import load_dotenv

import config

load_dotenv()


class ForeignApiError(Exception):
    """Класс ошибки внешнего api."""

    def __init__(self, status_code: int) -> None:
        """Инициализация ошибки.

        Args:
            status_code (int): статус код
        """
        super().__init__(f'Ошибка запроса внешнего апи, код ошибки: {status_code}')


def get_data(path: str, options: dict) -> dict:
    """Получить данные.

    Args:
        path (str): путь
        options (dict): параметры

    Raises:
        ForeignApiError: ошибка внешнего api

    Returns:
        dict: словарь с данными
    """
    url = f'{config.FOOTBALL_URL}{path}'
    headers = {config.FOOTBALL_HEADER: environ.get('FOOTBAll_KEY')}
    response = requests.get(url, headers=headers, params=options, timeout=10)
    if response.status_code != config.OK:
        raise ForeignApiError(response.status_code)
    return response.json()


def get_data_league(name: str, country: str) -> tuple[str] | None:
    """Получить данные лиги.

    Args:
        name (str): название
        country (str): страна

    Returns:
        tuple[str] | None: кортеж с данными или ничего, если совпадений не найдено
    """
    league_data = get_data('/leagues', {'season': config.SEASON})['response']
    for league in league_data:
        if league['league']['name'] == name and league['country']['name'] == country:
            return league['league']['id'], league['league']['logo']
    return None


def get_data_team(name: str, league_api_id: int) -> dict | None:
    """Получить данные команды.

    Args:
        name (str): название
        league_api_id (int): api id лиги

    Returns:
        dict | None: словарь с данными или ничего, если совпадений не найдено
    """
    team_data = get_data('/teams', {'league': league_api_id, 'season': config.SEASON})['response']
    for team in team_data:
        name_team = team['team']['name']
        if name_team == name:
            return team
    return None


def get_team_roster(team_api_id: int) -> list[dict]:
    """Получить состав команды.

    Args:
        team_api_id (int): api id команды

    Returns:
        list[dict]: список словарей с данными об игроках
    """
    roster_data = get_data('/players/squads', {'team': team_api_id})
    list_of_players = roster_data['response'][0]['players']
    res = []
    for player in list_of_players:
        player_data = {}
        for key, val_player in player.items():
            if key == 'id':
                continue
            player_data[key] = val_player
        res.append(player_data)
    return res
