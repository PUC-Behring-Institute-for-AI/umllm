# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import logging
import os

import flask
import typing_extensions as ty

from ..um import UM

#: The Flask application.
app: ty.Final[flask.Flask] = flask.Flask(__name__)

SECRET_KEY: str | None = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_hex()
app.config['SECRET_KEY'] = SECRET_KEY

LOG_STREAM: ty.Final[io.StringIO] = io.StringIO()
_logger: ty.Final[logging.Logger] = logging.getLogger('umllm')
_logger.setLevel(level=logging.INFO)
_logger_handler = logging.StreamHandler(LOG_STREAM)
_logger_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
_logger.addHandler(_logger_handler)


@app.route("/")
def index() -> str:
    return flask.render_template(
        'index.html',
        filename=flask.session.get('filename'),
        um=flask.session.get('um', {}),
        log=LOG_STREAM.getvalue())


@app.route('/', methods=['POST'])
def upload() -> flask.Response:
    file = flask.request.files['file']
    input = flask.request.form['input']
    flask.session['filename'] = file.filename
    flask.session['input'] = input
    try:
        um = UM.load(file.stream.read().decode('utf-8'))
        if input:
            um.work = input
        _save(um)
    except ValueError as err:
        _logger.error(err)
    return flask.redirect(flask.url_for('index'))  # type: ignore


@app.route('/api/clear', methods=['POST'])
def api_clear() -> flask.Response:
    if 'filename' in flask.session:
        del flask.session['filename']
    if 'input' in flask.session:
        del flask.session['input']
    if 'um' in flask.session:
        del flask.session['um']
    LOG_STREAM.seek(0)
    LOG_STREAM.truncate(0)
    return _dump()


@app.route('/api/prev', methods=['POST'])
def api_prev() -> flask.Response:
    try:
        return _save_and_dump(_load().prev())
    except UM.Error:
        return _dump()


@app.route('/api/next', methods=['POST'])
def api_next() -> flask.Response:
    try:
        return _save_and_dump(_load().next())
    except UM.Error:
        return _dump()


@app.route('/api/cycle', methods=['POST'])
def api_cycle() -> flask.Response:
    try:
        return _save_and_dump(_load().cycle())
    except UM.Error:
        return _dump()


@app.route('/api/reset', methods=['POST'])
def api_reset() -> flask.Response:
    try:
        return _save_and_dump(_load().reset())
    except UM.Error:
        return _dump()


def _load() -> UM:
    return UM.of_dict(flask.session['um'])


def _save_and_dump(um: UM) -> flask.Response:
    _save(um)
    return _dump()


def _save(um: UM) -> None:
    t = um.to_dict()
    for k, v in t['_history'][-1].items():
        if k == 'steps':
            t[k] = v
        else:
            t[k] = um._tape2html(v)
    t['formatted_machine'] = _format_machine(um)
    t['formatted_work'] = _format_work(um)
    t['prev_step'] = um.prev_step
    t['next_step'] = um.next_step
    t['cycles'] = um.cycles
    t['halted'] = um.halted()
    flask.session['um'] = t


def _format_machine(um: UM) -> str:
    def it() -> ty.Iterator[str]:
        yield '<table><tbody>'
        f = um._tape2html
        for q0, s0, q1, s1, d in um._parse_machine():  # type: ignore
            yield '<tr>'
            yield f'<td>({f(q0)},&nbsp;{f(s0)})</td>'
            yield '<td>↦</td>'
            yield f'<td>({f(q1)},&nbsp;{f(s1)},&nbsp;{f(d)})</td>'
            yield '</tr>'
        yield '</tbody></table>'
    return '\n'.join(it())


def _format_work(um: UM) -> str:
    f = um._tape2html
    try:
        s, q, t = um._parse_work()
        return f'{f(s)}<strong>{f(q)}</strong>{f(t)}'
    except um.Error:
        return f(um.work)


def _dump() -> flask.Response:
    return flask.jsonify({
        'filename': flask.session.get('filename'),
        'input': flask.session.get('input'),
        'um': flask.session.get('um', {}),
        'log': LOG_STREAM.getvalue()})
