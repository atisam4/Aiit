from app import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    if os.environ.get("RENDER") or os.environ.get("VERCEL"):
        try:
            import gunicorn
            os.system(f"gunicorn app:app --bind 0.0.0.0:{port}")
        except ImportError:
            from waitress import serve
            serve(app, port=port)
    else:
        app.run(host="0.0.0.0", port=port)
