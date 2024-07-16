#!/usr/bin/env python3

from flask import request, session, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):

        request_json = request.get_json()

        username = request_json.get('username')
        password = request_json.get('password')
        bio = request_json.get('bio')
        image_url = request_json.get('image_url')
        
        if not username or not password:
            return {'error': 'Missing username or password'}, 422

        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 422

        user = User(username=username, bio=bio, image_url=image_url)
        user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Failed to create user'}, 500

class CheckSession(Resource):
    def get(self):
        user_id = session['user_id']
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return make_response(user.to_dict(), 200)
        return {'error': 'No active session'}, 401

class Login(Resource):
    def post(self):
        request_json = request.get_json()

        username = request_json.get('username')
        password = request_json.get('password')

        if not username or not password:
            return {'error': 'Missing username or password'}, 422

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password'}, 401
    pass

class Logout(Resource):
    def delete(self):
        if session['user_id']:
            session['user_id'] = None
            return {}, 204
        else:
            return {'error': 'No active session'}, 401
    pass

class RecipeIndex(Resource):
    def get(self):
        if session['user_id']:
            user = User.query.filter(User.id == session['user_id']).first()
            return [recipe.to_dict() for recipe in user.recipes], 200
        else:
            return {'error': 'No active session'}, 401
    
    def post(self):
        if session['user_id']:
            request_json = request.get_json()

            title = request_json.get('title')
            instructions = request_json.get('instructions')
            minutes_to_complete = request_json.get('minutes_to_complete')

            if not title or not instructions or not minutes_to_complete or len(instructions) < 50:
                return {'error': 'Missing required fields'}, 422

            recipe = Recipe(title=title, instructions=instructions, minutes_to_complete=minutes_to_complete)
            recipe.user_id = session['user_id']

            try:
                db.session.add(recipe)
                db.session.commit()
                return recipe.to_dict(), 201
            except IntegrityError:
                db.session.rollback()
                return {'error': 'Failed to create recipe'}, 500
        else:
            return {'error': 'No active session'}, 401
    pass

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)