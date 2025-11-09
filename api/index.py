from app import app

# Esto es necesario para que Vercel ejecute la aplicación correctamente
application = app

if __name__ == '__main__':
    app.run(debug=False)