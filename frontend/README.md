# Health Metrics Frontend

Modern Next.js 14 frontend application for the Health Metrics LLM Prototype.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React 18**

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Configure environment variables:

```bash
cp .env.local.example .env.local
```

Update `.env.local` with your API base URL:

```env
NEXT_PUBLIC_API_BASE_URL=https://health-metrics-api-bhbsebdvhfgxd4gf.centralus-01.azurewebsites.net
```

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
# or
yarn build
```

Start production server:

```bash
npm start
# or
yarn start
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home page
│   ├── metrics/           # Metrics page
│   ├── anomalies/         # Anomalies page
│   ├── explanation/       # Explanation page
│   └── run-pipeline/      # Pipeline runner page
├── components/            # React components (if needed)
├── lib/                   # Utility functions
│   └── api.ts            # API client
├── public/                # Static assets
└── package.json
```

## Features

- **Metrics Dashboard**: View health metrics summary
- **Anomalies Detection**: View detected anomalies
- **AI Explanations**: Get LLM-powered insights
- **Pipeline Runner**: Trigger new pipeline runs

## Design

- Black background theme
- Responsive layout (mobile + desktop)
- Card-based UI with rounded corners and shadows
- Modern, clean interface

