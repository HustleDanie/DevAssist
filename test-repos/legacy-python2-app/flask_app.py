# -*- coding: utf-8 -*-
"""
Flask Web Application - For Flask to FastAPI Migration Testing

This module demonstrates Flask patterns that need to be migrated to FastAPI.
"""

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# In-memory data store
users_db = {}
products_db = {}


@app.route('/')
def index():
    """Home endpoint."""
    return jsonify({
        'message': 'Welcome to Legacy API',
        'version': '1.0',
        'endpoints': ['/users', '/products', '/health']
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/users', methods=['GET'])
def get_users():
    """Get all users."""
    users_list = []
    for user_id, user in users_db.iteritems():
        users_list.append({
            'id': user_id,
            'name': user['name'],
            'email': user['email']
        })
    return jsonify({'users': users_list, 'count': len(users_list)})


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID."""
    user_id_str = str(user_id)
    if user_id_str not in users_db.keys():
        return jsonify({'error': 'User not found'}), 404
    
    user = users_db[user_id_str]
    return jsonify({
        'id': user_id,
        'name': user['name'],
        'email': user['email']
    })


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    email = data.get('email')
    
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    
    user_id = str(len(users_db) + 1)
    users_db[user_id] = {
        'name': unicode(name),
        'email': unicode(email)
    }
    
    print "Created user: %s" % name
    
    return jsonify({
        'id': int(user_id),
        'name': name,
        'email': email
    }), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user."""
    user_id_str = str(user_id)
    
    if user_id_str not in users_db.keys():
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        users_db[user_id_str]['name'] = unicode(data['name'])
    if data.get('email'):
        users_db[user_id_str]['email'] = unicode(data['email'])
    
    print "Updated user: %s" % user_id
    
    return jsonify({
        'id': user_id,
        'name': users_db[user_id_str]['name'],
        'email': users_db[user_id_str]['email']
    })


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    user_id_str = str(user_id)
    
    if user_id_str not in users_db.keys():
        return jsonify({'error': 'User not found'}), 404
    
    del users_db[user_id_str]
    print "Deleted user: %s" % user_id
    
    return jsonify({'message': 'User deleted'}), 200


@app.route('/products', methods=['GET'])
def get_products():
    """Get all products."""
    products_list = []
    for prod_id, product in products_db.iteritems():
        products_list.append({
            'id': prod_id,
            'name': product['name'],
            'price': product['price']
        })
    return jsonify({'products': products_list})


@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    data = request.get_json()
    
    name = data.get('name')
    price = data.get('price', 0)
    
    if not name:
        return jsonify({'error': 'Product name is required'}), 400
    
    prod_id = str(len(products_db) + 1)
    products_db[prod_id] = {
        'name': unicode(name),
        'price': float(price)
    }
    
    print "Created product: %s" % name
    
    return jsonify({
        'id': int(prod_id),
        'name': name,
        'price': price
    }), 201


@app.route('/search', methods=['GET'])
def search():
    """Search users and products."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    query = unicode(query).lower()
    
    # Search users
    user_results = []
    for user_id, user in users_db.iteritems():
        if query in user['name'].lower() or query in user['email'].lower():
            user_results.append({'id': user_id, 'name': user['name']})
    
    # Search products
    product_results = []
    for prod_id, product in products_db.iteritems():
        if query in product['name'].lower():
            product_results.append({'id': prod_id, 'name': product['name']})
    
    print "Search for '%s': found %d users, %d products" % (
        query, len(user_results), len(product_results)
    )
    
    return jsonify({
        'query': query,
        'users': user_results,
        'products': product_results
    })


@app.route('/stats')
def get_stats():
    """Get API statistics."""
    return jsonify({
        'users_count': len(users_db),
        'products_count': len(products_db),
        'status': 'running'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    print "Internal error: %s" % str(error)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print "Starting Flask application..."
    app.run(debug=True, host='0.0.0.0', port=5000)
