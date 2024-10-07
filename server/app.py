#!/usr/bin/env python3

from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Hero, Power, HeroPower
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)


@app.route('/')
def index():
    return '<h1>Code challenge</h1>'


# Define the Resource for /heroes
class HeroesResource(Resource):
    def get(self):
        heroes = Hero.query.all()
        return jsonify([hero.to_dict(only=('id', 'name', 'super_name')) for hero in heroes])


# Define the Resource for /heroes/<int:hero_id>
class HeroResource(Resource):
    def get(self, hero_id):
        hero = Hero.query.get(hero_id)
        if hero:
            return jsonify(hero.to_dict(
                only=('id', 'name', 'super_name', 'hero_powers.id', 'hero_powers.strength', 
                      'hero_powers.hero_id', 'hero_powers.power_id', 
                      'hero_powers.power.id', 'hero_powers.power.name', 
                      'hero_powers.power.description')))
        return jsonify({"error": "Hero not found"}), 404


# Define the Resource for /powers
class PowersResource(Resource):
    def get(self):
        powers = Power.query.all()
        return jsonify([power.to_dict(only=('id', 'name', 'description')) for power in powers])


# Define the Resource for /powers/<int:power_id>
class PowerResource(Resource):
    def get(self, power_id):
        power = Power.query.get(power_id)
        if power:
            return jsonify(power.to_dict(only=('id', 'name', 'description')))
        return jsonify({"error": "Power not found"}), 404

    def patch(self, power_id):
        power = Power.query.get(power_id)
        if not power:
            return jsonify({"error": "Power not found"}), 404

        data = request.get_json()
        description = data.get('description')

        if description:
            try:
                power.description = description
                db.session.commit()
                return jsonify(power.to_dict(only=('id', 'name', 'description')))
            except ValueError as e:
                db.session.rollback()
                return jsonify({"errors": [str(e)]}), 400

        return jsonify({"errors": ["Invalid or missing fields"]}), 400


# Define the Resource for /hero_powers
class HeroPowersResource(Resource):
    def post(self):
        data = request.get_json()
        strength = data.get('strength')
        hero_id = data.get('hero_id')
        power_id = data.get('power_id')

        if not (strength and hero_id and power_id):
            return jsonify({"errors": ["All fields are required"]}), 400

        try:
            hero_power = HeroPower(strength=strength, hero_id=hero_id, power_id=power_id)
            db.session.add(hero_power)
            db.session.commit()

            return jsonify(hero_power.to_dict(
                only=('id', 'hero_id', 'power_id', 'strength',
                      'hero.id', 'hero.name', 'hero.super_name',
                      'power.id', 'power.name', 'power.description')))

        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 400


# Register resources with API
api.add_resource(HeroesResource, '/heroes')
api.add_resource(HeroResource, '/heroes/<int:hero_id>')
api.add_resource(PowersResource, '/powers')
api.add_resource(PowerResource, '/powers/<int:power_id>')
api.add_resource(HeroPowersResource, '/hero_powers')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
