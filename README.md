# GURU SERVER

A powerful message sending server with user tracking and multi-token support.

## Deployment on Render

1. Fork or clone this repository
2. Go to [render.com](https://render.com)
3. Create a new Web Service
4. Connect your repository
5. Select the Python environment
6. The following settings will be automatically picked up:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn app:app`

## Features

- Multi-token support
- Real-time user tracking
- Message sending with customizable delay
- File upload support
- Active user monitoring
- Uptime tracking
- Beautiful UI with animations

## Environment Variables

- `PORT`: Port number (default: 8000)
- `PYTHON_VERSION`: Python version (set to 3.9.18)

## File Structure

```
MP/
├── app.py              # Main application file
├── database.py         # Database handling
├── requirements.txt    # Python dependencies
├── Procfile           # Process file for deployment
├── runtime.txt        # Python version specification
├── render.yaml        # Render configuration
├── build.sh           # Build script
├── README.md          # This file
└── templates/         # HTML templates
    └── index.html     # Main interface
```

## Support

For support, contact GURU KIING.
