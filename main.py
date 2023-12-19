from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Milk as milkModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 4, 'kalori': 3, 'protein': 4, 'lemak': 6, 'ukuran': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(milkModel.id, milkModel.harga, milkModel.kalori, milkModel.protein, milkModel.lemak,
                    milkModel.ukuran)        
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': Milk.id, 'harga': Milk.harga, 'kalori': Milk.kalori, 'protein': Milk.protein, 'lemak': Milk.lemak, 
                'ukuran': Milk.ukuran} for Milk in result]
    @property
    def normalized_data(self):
        harga_values = [data.get('harga', 0) for data in self.data]
        kalori_values = [data['kalori'] for data in self.data]
        protein_values = [data['protein'] for data in self.data]
        lemak_values = [int(data['lemak']) for data in self.data]  
        ukuran_values = [data['ukuran'] for data in self.data]

        max_harga_value = max(harga_values) if harga_values else 1
        max_kalori_value = max(kalori_values) if kalori_values else 1
        max_protein_value = max(protein_values) if protein_values else 1
        max_lemak_value = max(lemak_values) if lemak_values else 1
        max_ukuran_value = max(ukuran_values) if ukuran_values else 1

        return [
            {
                'id': data['id'],
                'harga': data['harga'] / max_harga_value if max_harga_value != 0 else 0,
                'kalori': data['kalori'] / max_kalori_value,
                'protein': data['protein'] / max_protein_value,
                'lemak': int(data['lemak']) / max_lemak_value,
                'ukuran': data['ukuran'] / max_ukuran_value,
            }
            for data in self.data
            ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'produk': row['harga'] ** self.weight['harga'] *
                    row['kalori'] ** self.weight['kalori'] *
                    row['protein'] ** self.weight['protein'] *
                    row['lemak'] ** self.weight['lemak'] *
                    row['ukuran'] ** self.weight['ukuran']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['id'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'milk': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'id': row['id'],
                'model': row.get('model'),
                'Score': round(row['harga'] * weight['harga'] +
                        row['kalori'] * weight['kalori'] +
                        row['protein'] * weight['protein'] +
                        row['lemak'] * weight['lemak'] +
                        row['ukuran'] * weight['ukuran'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'Milk': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class Mobil(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(milkModel).order_by(milkModel.id)
        result_set = query.all()
        data = [{'id': row.id, 'harga': row.harga, 'kalori': row.kalori, 'protein': row.protein, 'lemak': row.lemak, 
                'ukuran': row.ukuran}
                for row in result_set]
        return self.get_paginated_result('milk/', data, request.args), 200

api.add_resource(Mobil, '/milk')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)