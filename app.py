"""Фласк модуль."""
from os import environ
from uuid import UUID

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request
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
        context = {'content': [team.__dict__ for team in db.get_all_teams(session)]}
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


@app.post('/<model>/<method>')
def post_methods(model: str, method: str):
    """Пост методы: создание/обновление записи модели.

    Args:
        model (str): модель
        method (str): метод

    Returns:
        _type_: _description_
    """
    body = request.json
    functions = {
        'team': {'create': db.create_team, 'update': db.update_team},
        'league': {'create': db.create_league, 'update': db.update_league},
        'stadium': {'create': db.create_stadium, 'update': db.update_stadium},
        'player': {'create': db.create_player, 'update': db.update_player},
    }
    if model in functions.keys() and method in functions[model].keys():
        with db.Session(engine) as session:
            res = functions[model][method](body, session)
    else:
        return '', config.NOT_FOUND
    if res:
        status_code = config.CREATED if method == 'create' else config.OK
        return str(res), status_code
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


if __name__ == '__main__':
    app.run(debug=False)
