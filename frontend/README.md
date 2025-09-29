# TradingAgents Frontend

React + TypeScript frontend for the TradingAgents stock analysis platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run test:watch` - Run tests in watch mode

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Ant Design** - UI components
- **Zustand** - State management
- **Axios** - HTTP client
- **ECharts** - Data visualization
- **React Router** - Routing

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── stores/         # State management
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions
│   ├── hooks/          # Custom hooks
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── package.json        # Dependencies
├── tsconfig.json       # TypeScript config
└── vite.config.ts      # Vite config
```

## Development

The frontend runs on http://localhost:3000 and proxies API requests to the backend at http://localhost:8000.