# DevAssist Frontend

Next.js frontend for the DevAssist code migration tool.

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### Environment Variables

- `NEXT_PUBLIC_API_URL` - URL of the DevAssist API (default: `http://localhost:8000`)

## Features

- **Drag & Drop Upload** - Easy file upload with drag and drop support
- **Migration Type Selection** - Choose between Python 2→3 and Flask→FastAPI
- **Real-time Progress** - Track migration progress with live updates
- **Download Results** - Download migrated codebase as a ZIP file

## Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

## Docker

Build and run with Docker:

```bash
docker build -t devassist-frontend .
docker run -p 3000:3000 devassist-frontend
```

Or use docker-compose from the project root:

```bash
docker-compose up frontend
```
