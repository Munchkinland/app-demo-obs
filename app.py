from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

app = Flask(__name__)

# Configuración de logging para observabilidad
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conexión a SQLite (en memoria)
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    entries = conn.execute('SELECT * FROM entries').fetchall()
    conn.close()
    return render_template('index.html', entries=entries)

@app.route('/create', methods=['POST'])
def create_entry():
    title = request.json['title']
    content = request.json['content']
    conn = get_db_connection()
    conn.execute('INSERT INTO entries (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()
    logger.info(f"Entry created: {title}")
    return jsonify({"message": "Entry created"}), 201

@app.route('/update/<int:id>', methods=['PUT'])
def update_entry(id):
    title = request.json['title']
    content = request.json['content']
    conn = get_db_connection()
    conn.execute('UPDATE entries SET title = ?, content = ? WHERE id = ?', (title, content, id))
    conn.commit()
    conn.close()
    logger.info(f"Entry updated: {title}")
    return jsonify({"message": "Entry updated"}), 200

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_entry(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM entries WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    logger.info(f"Entry deleted: {id}")
    return jsonify({"message": "Entry deleted"}), 200

# Inicialización de la base de datos
if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=8080)
