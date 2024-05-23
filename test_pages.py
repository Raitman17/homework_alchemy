"""Модуль тестов на страницы."""

import json

import pytest
import requests

import config

league_data = {
    'name': 'abc',
    'country': 'abc',
}

stadium_data = {
    'name': 'abc',
    'address': 'abc',
    'city': 'abc',
    'capacity': 123,
    'surface': 'abc',
}

team_data = {
    'name': 'abc',
    'founded': 2000,
}

player_data = {
    'name': 'abc',
    'age': 18,
    'number': 18,
    'position': 'abc',
}

CREATE = 'create'
UPDATE = 'update'
DELETE = 'delete'
HEADERS = {'Content-Type': 'application/json'}
URL = 'http://127.0.0.1:5000/'
GET_DATA = (URL, f'{URL}add_team')
POST_DATA = (
    ('team', team_data),
    ('league', league_data),
    ('player', player_data),
    ('stadium', stadium_data),
)


@pytest.mark.parametrize('url', GET_DATA)
def test_get(url: str):
    """Тест страниц.

    Args:
        url (str): ссылка
    """
    response = requests.get(url, timeout=10)
    assert response.status_code == config.OK


@pytest.mark.parametrize('model, model_data', POST_DATA)
def test_post_delete(model: str, model_data: dict):
    """Тест методов создания, обновления и удаления.

    Args:
        model (str): модель
        model_data (dict): словарь данных о модели
    """
    if model == 'player':
        team_id = requests.post(
            f'{URL}team/{CREATE}',
            headers=HEADERS,
            data=json.dumps(team_data),
            timeout=10,
        )
        model_data['team_id'] = team_id.content.decode()

    create_ok = requests.post(
        f'{URL}{model}/{CREATE}',
        headers=HEADERS,
        data=json.dumps(model_data),
        timeout=10,
    )
    assert create_ok.status_code == config.CREATED

    create_bad_req = requests.post(
        f'{URL}{model}/{CREATE}',
        headers=HEADERS,
        data=json.dumps(model_data),
        timeout=10,
    )
    assert create_bad_req.status_code == config.BAD_REQUEST

    model_data['id'] = create_ok.content.decode()
    update_ok = requests.post(
        f'{URL}{model}/{UPDATE}',
        headers=HEADERS,
        data=json.dumps(model_data),
        timeout=10,
    )
    assert update_ok.status_code == config.OK

    delete_no_cont = requests.delete(
        f'{URL}{model}/{DELETE}',
        headers=HEADERS,
        data=json.dumps({'id': model_data['id']}),
        timeout=10,
    )
    assert delete_no_cont.status_code == config.NO_CONTENT

    if model == 'player':
        requests.delete(
            f'{URL}team/{DELETE}',
            headers=HEADERS,
            data=json.dumps({'id': team_id.content.decode()}),
            timeout=10,
        )

    update_bad_req = requests.post(
        f'{URL}{model}/{UPDATE}',
        headers=HEADERS,
        data=json.dumps(model_data),
        timeout=10,
    )
    assert update_bad_req.status_code == config.BAD_REQUEST

    delete_bad_req = requests.delete(
        f'{URL}{model}/{DELETE}',
        headers=HEADERS,
        data=json.dumps({'id': model_data['id']}),
        timeout=10,
    )
    assert delete_bad_req.status_code == config.BAD_REQUEST
