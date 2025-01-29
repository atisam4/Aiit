from app import app

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Render,
    # Render will use the gunicorn command specified in Procfile
    app.run(host='0.0.0.0', port=5000)
