"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
from uuid import uuid4

import pytest
from store_manager import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status': 'ok'}
    

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    product_data = {'name': 'Some Item', 'sku': '12345', 'price': 99.90}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0 
    product_id = data['product_id']


    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    stock_data = {'product_id': product_id, 'quantity': 5}
    stock_response = client.post('/stocks',
        data=json.dumps(stock_data),
        content_type='application/json',
    )
    assert stock_response.status_code == 201
    stock_update_result = stock_response.get_json()
    assert 'rows' in stock_update_result['result']

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    initial_stock_response = client.get(f'/stocks/{product_id}')
    assert initial_stock_response.status_code == 201
    initial_stock = initial_stock_response.get_json()
    assert initial_stock['quantity'] == 5

    # 4. Faites une commande de l'article que vous avez créé, 2 unités (`POST /orders`)
    #Utiliser ID manuel 1 pour creer la commande sur l'utilisateur 1.
    user_id=1
    user_response = client.get(f'/users/{user_id}')
    assert user_response.status_code == 201
    assert user_response.get_json()['name'] == 'Ada Lovelace'
    assert user_response.get_json()['email'] == 'alovelace@example.com'

    order_payload = {
        'user_id': user_id,
        'items': [{'product_id': product_id, 'quantity': 2}],
    }
    order_response = client.post(
        '/orders',
        data=json.dumps(order_payload),
        content_type='application/json',
    )
    assert order_response.status_code == 201
    order_id = order_response.get_json()['order_id']

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    stock_after_order_response = client.get(f'/stocks/{product_id}')
    assert stock_after_order_response.status_code == 201
    stock_after_order = stock_after_order_response.get_json()
    assert stock_after_order['quantity']  == 3

    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    delete_response = client.delete(f'/orders/{order_id}')
    assert delete_response.status_code == 200
    assert delete_response.get_json()['deleted'] is True

    stock_after_delete_response = client.get(f'/stocks/{product_id}')
    assert stock_after_delete_response.status_code == 201
    assert stock_after_delete_response.get_json()['quantity'] == 5
