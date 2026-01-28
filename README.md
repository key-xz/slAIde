# slAIde
Slide generation with AI-powered styling extraction

## Overview
slAIde allows you to upload a PowerPoint file and extract all styling rules (colors, fonts, layouts, positioning, etc.) that can be used to generate new slides following the same design guidelines.

## Architecture
- **Frontend**: React + TypeScript + Vite (client/)
- **Backend**: Python + Flask + python-pptx (server/)

## Features
- Extract styling rules from PowerPoint templates
- Dynamic layout selection
- Automatic placeholder detection
- Support for text and image placeholders
- Environment-based configuration
- Modular, maintainable codebase
- Production-ready architecture

## Setup

### Backend Setup

1. Navigate to the server directory:
```bash
cd server
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env.development
# Edit .env.development if needed
```

5. Run the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
bun install
# or: npm install
```

3. Configure environment variables:
```bash
cp .env.example .env.development
# Edit .env.development if needed
```

4. Run the development server:
```bash
bun run dev
# or: npm run dev
```

The frontend will run on `http://localhost:5173`

## Configuration

### Client Configuration
Environment variables are managed through `.env` files:
- `.env.development` - Development settings (localhost)
- `.env.production` - Production settings
- `.env.example` - Template with all available options

Key variables:
- `VITE_API_BASE_URL` - Backend API URL

### Server Configuration
Environment variables are managed through `.env` files:
- `.env.development` - Development settings
- `.env.production` - Production settings
- `.env.example` - Template with all available options

Key variables:
- `FLASK_ENV` - Environment (development/production)
- `FLASK_DEBUG` - Debug mode (True/False)
- `PORT` - Server port
- `HOST` - Server host
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `MAX_CONTENT_LENGTH` - Max upload size in bytes

## Deployment

### Production Backend Deployment

1. Set up your production environment:
```bash
cp .env.example .env.production
# Edit .env.production with your production settings
```

2. Update `.env.production`:
```env
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0
CORS_ORIGINS=https://your-frontend-domain.com
```

3. Install production dependencies:
```bash
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

4. Run with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

### Production Frontend Deployment

1. Update `.env.production`:
```env
VITE_API_BASE_URL=https://your-api-domain.com
```

2. Build for production:
```bash
bun run build
# or: npm run build
```

3. Deploy the `dist/` folder to your hosting provider (Vercel, Netlify, etc.)

### Docker Deployment (Optional)

Create `Dockerfile` for backend:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

Create `Dockerfile` for frontend:
```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package.json bun.lock ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Usage

### Step 1: Extract Rules from Template
1. Start both the backend and frontend servers
2. Open the frontend in your browser
3. Upload a `.pptx` file
4. Click "Extract Rules" to analyze the PowerPoint file
5. The system extracts and stores:
   - Slide dimensions
   - Available layouts and their placeholders
   - Shape properties (colors, fonts, positioning)
   - Text formatting
   - Fill and line styles

### Step 2: Select a Layout
1. After extraction, view the list of available layouts
2. Click on a layout to select it
3. Each layout shows the number of placeholders it contains

### Step 3: Fill Placeholders
1. Based on the selected layout, the system dynamically displays input fields
2. For text placeholders (Title, Body, etc.): Enter text in the textarea
3. For image placeholders (Picture, Object): Upload an image file
4. The system detects placeholder types automatically

### Step 4: Generate and Download
1. Click "Generate Slide" to create a new slide with your content
2. The backend applies the template's styling rules to your content
3. Download the generated PowerPoint file
4. The slide maintains all the original styling from the template

## Project Structure

### Client (`client/`)
```
client/
├── src/
│   ├── components/       # Reusable React components
│   ├── config/          # Configuration and constants
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API service layer
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── .env.development     # Development environment config
├── .env.production      # Production environment config
└── .env.example         # Environment config template
```

### Server (`server/`)
```
server/
├── routes/              # API route handlers
├── services/            # Business logic
├── utils/               # Utility functions
├── config.py            # Configuration management
├── app.py               # Application entry point
├── .env.development     # Development environment config
├── .env.production      # Production environment config
└── .env.example         # Environment config template
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/extract-rules` - Extract rules from PowerPoint file
- `GET /api/rules` - Get stored rules
- `POST /api/generate-slide` - Generate new slide

## Development

### Code Quality
The codebase follows best practices:
- Modular architecture with separation of concerns
- Type safety with TypeScript
- Environment-based configuration
- Comprehensive error handling
- Reusable components and utilities

### Adding New Features
1. **Client**: Add components in `client/src/components/`
2. **API**: Add endpoints in `server/routes/api.py`
3. **Business Logic**: Add services in `server/services/`
4. **Utilities**: Add helpers in respective `utils/` folders

## Troubleshooting

### CORS Issues
Update `CORS_ORIGINS` in server `.env` file to include your frontend URL.

### Connection Errors
Ensure both servers are running and the `VITE_API_BASE_URL` matches your backend URL.

### File Upload Errors
Check `MAX_CONTENT_LENGTH` in server configuration if uploading large files.

## License
See LICENSE file for details.
