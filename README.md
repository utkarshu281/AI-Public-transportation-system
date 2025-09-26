🚍 PATH FINDER: AI-Driven Public Transportation System

Smart Mobility Solution for Tier-2 Cities (Inspired by SIH 2025 Problem Statement)

💡 Project Overview

Path Finder is an AI-enhanced web application designed to solve the problem of unpredictable public transport and lack of real-time bus information in Tier-2 and small cities.

The system integrates GPS tracking, AI-based ETA predictions, and demand forecasting to deliver accurate information to commuters and actionable insights for transport authorities.

⚠️ Problem Statement

In small cities and Tier-2 towns, public transport suffers from:

No real-time tracking → commuters wait blindly at stops.

Overcrowding due to poor demand prediction.

Unreliable schedules → reduced trust in buses.

This results in wasted time, traffic congestion, and increased pollution as commuters switch to private vehicles.

🎯 Objectives / Expected Outcomes

Real-time bus tracking on a map.

Accurate ETA predictions using AI.

Demand forecasting to avoid overcrowding.

Optimized for low-bandwidth environments.

Separate User and Admin portals.

👨‍💻 Tech Stack
Frontend (User & Admin Web)

Frameworks: React.js / Next.js (SPA with fast routing)

UI: TailwindCSS, Material UI (clean responsive design)

Maps: Leaflet.js / Mapbox / Google Maps API

Backend

Framework: FastAPI (Python) or Node.js (Express)

API Layer: REST / WebSocket for live bus tracking

Database: PostgreSQL / MongoDB (routes, users, analytics)

Cache: Redis (for quick ETA lookups)

AI / ML Models

ETA Prediction: Ridge Regression (trained on synthetic + real data)

Demand Forecasting: Regression / Time-series model

Library Support: scikit-learn, pandas, numpy

DevOps

Hosting: AWS / Azure / GCP

Containerization: Docker + Kubernetes (scalability)

CI/CD: GitHub Actions

👨‍👩‍👦 Stakeholders / Beneficiaries

Commuters → get reliable bus information & save time.

Local Transport Authorities → better management of fleets.

Municipal Corporations → improved urban mobility & reduced pollution.

📌 Features
User (Commuter Web App)

Search routes (start → destination).

Live bus tracking on map.

ETA countdown to destination.

Notifications when bus is near.

Save frequent routes.

Admin (Transport Authority Dashboard)

Real-time bus fleet monitoring.

Route & schedule management.

AI-based demand predictions (peak hours, crowded routes).

Analytics dashboard (delays, ridership trends).

Alerts for missing or delayed buses.

🗂️ Project Structure (Example)
/project-root
│── frontend/           # React.js / Next.js frontend
│   ├── components/     
│   ├── pages/          
│   └── styles/         
│
│── backend/            # FastAPI backend
│   ├── main.py         
│   ├── ai_models.py    # ETA & demand prediction models
│   ├── datasim.py      # Data simulation for testing
│   └── database/       
│
│── docs/               # Documentation, diagrams, research
│── README.md           # Project overview

📊 Supporting Data

Urban Mobility India Report 2024: Highlights inefficiencies in Tier-2 city transport.

NITI Aayog 2023 Report: Push for AI & IoT in urban mobility.

🚀 Future Scope

Mobile app (React Native).

Integration with digital payments.

IoT-based bus sensors for live crowding info.

Multi-city scaling with cloud infrastructure.
