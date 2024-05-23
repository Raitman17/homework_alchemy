"""Фласк модуль."""
from os import environ
from uuid import UUID

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

import config
import db

load_dotenv()


app = Flask(__name__)
app.json.ensure_ascii = False
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
engine = db.engine


class AddTeamForm(FlaskForm):
    """Класс формы для добавления команды."""

    name = StringField('Введите название команды: ')
    league = StringField('Введите название лиги: ')
    country = StringField('Введите название страны: ')
    submit = SubmitField('Submit')


@app.route('/')
def homepage():
    """Домашняя страница.

    Returns:
        _type_: _description_
    """
    with db.Session(engine) as session:
        context = {'content': db.get_all_teams(session)}
    return render_template('index.html', **context), config.OK


@app.route('/team/<team_id>')
def team(team_id: UUID):
    """Страница команды.

    Args:
        team_id (UUID): id команды

    Returns:
        _type_: _description_
    """
    with db.Session(engine) as session:
        team_data = db.get_team(team_id, session)
        stadium = db.get_stadium(team_data['stadium_id'], session)
        league = db.get_league(team_data['league_id'], session)
        players = db.get_players_of_team(team_data['id'], session)
    context = {
        'team': team_data,
        'stadium': stadium,
        'league': league,
        'players': players,
    }
    return render_template('team.html', **context), config.OK


@app.route('/add_team', methods=['GET', 'POST'])
def add_team():
    """Страница - добавить команду.

    Returns:
        _type_: _description_
    """
    form = AddTeamForm()
    msg = ''
    flag = False
    team_id = None
    if form.validate_on_submit():
        with db.Session(engine) as session:
            team_id = db.add_team_api(form.name.data, form.league.data, form.country.data, session)
        flag = True
    if team_id:
        return redirect(f'/team/{team_id}')
    if flag:
        msg = 'Команда не найдена, проверьте введенные данные'
    context = {'msg': msg}
    return render_template('add_team.html', **context, form=form), config.OK


@app.post('/<model>/create')
def create_model(model: str):
    """Создание записи модели.

    Args:
        model (str): модель

    Returns:
        _type_: _description_
    """
    body = request.json
    functions = {
        'team': db.create_team,
        'league': db.create_league,
        'stadium': db.create_stadium,
        'player': db.create_player,
    }
    if model in functions.keys():
        with db.Session(engine) as session:
            res = functions[model](body, session)
    else:
        return '', config.NOT_FOUND
    if res:
        return str(res), config.CREATED
    return '', config.BAD_REQUEST


@app.put('/<model>/update')
def update_model(model: str):
    """Обновление записи модели.

    Args:
        model (str): модель

    Returns:
        _type_: _description_
    """
    body = request.json
    functions = {
        'team': db.update_team,
        'league': db.update_league,
        'stadium': db.update_stadium,
        'player': db.update_player,
    }
    if model in functions.keys():
        with db.Session(engine) as session:
            res = functions[model](body, session)
    else:
        return '', config.NOT_FOUND
    if res:
        return str(res), config.OK
    return '', config.BAD_REQUEST


@app.delete('/<model>/delete')
def delete_model(model: str):
    """Удалить запись модели.

    Args:
        model (str): модель

    Returns:
        _type_: _description_
    """
    body = request.json
    functions = {
        'team': db.delete_team,
        'league': db.delete_league,
        'stadium': db.delete_stadium,
        'player': db.delete_player,
    }
    if model in functions.keys():
        with db.Session(engine) as session:
            res = functions[model](body['id'], session)
    else:
        return '', config.NOT_FOUND
    if res:
        return '', config.NO_CONTENT
    return '', config.BAD_REQUEST


@app.get('/<model>')
def get_model_all(model: str):
    """Получить все записи модели.

    Args:
        model (str): модель

    Returns:
        _type_: _description_
    """
    functions = {
        'teams': db.get_all_teams,
        'leagues': db.get_all_league,
        'stadiums': db.get_all_stadium,
        'players': db.get_all_player,
    }
    if model in functions.keys():
        with db.Session(engine) as session:
            res = {f'{model}': functions[model](session)}
    else:
        return '', config.NOT_FOUND
    if res:
        return jsonify(res), config.OK
    return '', config.BAD_REQUEST


if __name__ == '__main__':
    app.run(debug=False)
