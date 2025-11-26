from flask import Flask, jsonify, request
from flask_cors import CORS 
import psycopg2
from psycopg2 import DatabaseError
import jwt

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'sisichkipisichki' 

def get_current_user():
    auth_header = request.headers.get('Authorization')
    print("Authorization header:", auth_header)
    if not auth_header:
        return None
    
    try:
        parts = auth_header.split(" ")
        if len(parts) == 2 and parts[0] == "Bearer":
            token = parts[1]
        else:
            token = auth_header 
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        print("Decoded payload:", payload)
        return payload['user_id']
    except Exception as e:
        print("JWT decode error:", e)
        return None
    
def get_db_connection():
    return psycopg2.connect(
        dbname='media_sercher',
        user='admin',
        password='SvT47_!s',
        host='185.237.95.6'
    )

@app.route('/api/register', methods=['POST'])
def register():  
    data = request.get_json()
    email = data['email']
    password = data['password']
    username = data['username']
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'error': 'Пользователь с такой почтой уже существует'}), 409
        
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 409
        
        cur.execute(
            "INSERT INTO users (email, password, username) VALUES (%s, %s, %s)",
            (email, password, username,)
        )
        conn.commit()
        return jsonify({"message": "Регистрация успешна!"}), 201
        
    except DatabaseError as e:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Server error: ' + str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    
    data = request.get_json()  
    email = data['email']
    password = data['password']

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone() 
        print(password , user[1])
        if user and user[1] == password:
            token = jwt.encode({
                'user_id': user[0],
                'email': email,
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return jsonify({
                'message': 'Успешный вход',
                'token': token,
                'user_id': user[0]
            }), 200
        else:
            return jsonify({"error": "Неверный пароль или почта"}), 401
        
    except DatabaseError as e:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Server error: ' + str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug='True',port=5000)

    