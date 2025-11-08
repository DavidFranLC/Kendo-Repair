from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from supabase import create_client, Client
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuración de Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = JSONEncoder

# Modelos de datos
class User:
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

class RepairRequest:
    def __init__(self, id, user_id, equipment_type, description, status, created_at):
        self.id = id
        self.user_id = user_id
        self.equipment_type = equipment_type
        self.description = description
        self.status = status
        self.created_at = created_at

# Rutas principales
@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Autenticación con Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Obtener información adicional del usuario
                user_data = supabase.table('users').select('*').eq('id', auth_response.user.id).execute()
                
                if user_data.data:
                    user = user_data.data[0]
                    session['user_id'] = user['id']
                    session['user_email'] = user['email']
                    session['user_role'] = user['role']
                    
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            flash('Error en el login: ' + str(e), 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        try:
            # Registrar usuario en Auth de Supabase
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Crear registro en tabla users
                user_data = {
                    'id': auth_response.user.id,
                    'email': email,
                    'role': 'client'
                }
                
                supabase.table('users').insert(user_data).execute()
                flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('login'))
                
        except Exception as e:
            flash('Error en el registro: ' + str(e), 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session or session['user_role'] != 'client':
        return redirect(url_for('login'))
    
    # Obtener solicitudes del usuario
    requests = supabase.table('repair_requests').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).execute()
    
    return render_template('dashboard.html', requests=requests.data)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    
    # Obtener todas las solicitudes
    requests = supabase.table('repair_requests').select('*, users(email)').order('created_at', desc=True).execute()
    users = supabase.table('users').select('*').eq('role', 'client').execute()
    
    return render_template('admin.html', 
                         requests=requests.data, 
                         users=users.data,
                         status_options=['pendiente', 'en_proceso', 'completado', 'cancelado'])

@app.route('/create_request', methods=['GET', 'POST'])
def create_request():
    if 'user_id' not in session or session['user_role'] != 'client':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        equipment_type = request.form['equipment_type']
        description = request.form['description']
        
        request_data = {
            'user_id': session['user_id'],
            'equipment_type': equipment_type,
            'description': description,
            'status': 'pendiente',
            'created_at': datetime.now().isoformat()
        }
        
        try:
            supabase.table('repair_requests').insert(request_data).execute()
            flash('Solicitud creada exitosamente', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash('Error al crear la solicitud: ' + str(e), 'error')
    
    return render_template('create_request.html')

@app.route('/update_status/<request_id>', methods=['POST'])
def update_status(request_id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    new_status = request.json.get('status')
    
    try:
        supabase.table('repair_requests').update({'status': new_status}).eq('id', request_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)