# Kreative Genesis 2026

## Team Code Wave

## AI and Automation

## No Code AI 

# InNovus AI — Conversational No-Code App Builder


---

## Product Overview
**InNovus AI** is a conversational, AI-powered **no-code application builder** that transforms a user's intent into a working web application through an adaptive dialogue engine. The system serves non-technical users (small business owners, NGOs, educators) and technical professionals (engineering students, product managers) alike by understanding requirements before building software.

The key innovation is the **intelligence layer before generation** that behaves like a product consultant understanding the user's needs.

---

## Problem Statement
Many individuals and small organizations have workflows that could easily be solved with simple software tools, but they lack technical skills, find existing no-code tools too complex, or cannot afford expensive developers. Meanwhile, technical professionals waste time on boilerplate code. The gap is not tools, but systems that understand requirements before building software.

---

## Solution
InNovus AI introduces a **conversational intelligence layer before code generation**. The system:
1.  **Asks adaptive questions** and interprets user responses.
2.  **Builds an internal requirements object** across five dimensions (Auth, Data, UI, Logic, Integrations).
3.  **Displays a visual blueprint** and generates a functional web application once requirements are clear.
4.  Provides output in **HTML, CSS, and JavaScript** that can be previewed live, downloaded as a ZIP, or shared via a hosted link.

---

## Project Structure
```text
├── frontend/
│   ├── frontend_app/
│   │   ├── .vscode/
│   │   │   └── launch.json
│   │   ├── public/
│   │   │   └── robots.txt
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── AppPreview.tsx
│   │   │   │   ├── BlueprintPanel.tsx
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── CTASection.tsx
│   │   │   │   ├── FeaturesSection.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── GenerationProgress.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── HeroSection.tsx
│   │   │   │   ├── HowItWorksSection.tsx
│   │   │   │   ├── ModeCard.tsx
│   │   │   │   ├── Particles.css
│   │   │   │   ├── Particles.tsx
│   │   │   │   └── RequirementsSummary.tsx
│   │   │   ├── lib/
│   │   │   │   └── aiEngine.ts
│   │   │   └── pages/
│   │   │       ├── Builder.tsx
│   │   │       ├── Examples.tsx
│   │   │       ├── Home.tsx
│   │   │       ├── HowItWorks.tsx
│   │   │       └── NotFound.tsx
│   │   ├── App.tsx
│   │   ├── eslint.config.js
│   │   ├── index.html
│   │   ├── index.tsx
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── postcss.config.cjs
│   │   ├── styles.css
│   │   ├── tailwind.config.cjs
│   │   ├── tsconfig.app.json
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   ├── vercel.json
│   │   ├── vite-env.d.ts
│   │   └── vite.config.ts
│   ├── .gitignore
│   ├── database.py
│   ├── main.py
│   ├── requirements.txt
├── template/
│   ├── css/
│   │   ├── sb-admin-2.css
│   │   └── sb-admin-2.min.css
│   ├── img/
│   │   ├── undraw_posting_photo.svg
│   │   ├── undraw_profile_1.svg
│   │   ├── undraw_profile_2.svg
│   │   ├── undraw_profile_3.svg
│   │   ├── undraw_profile.svg
│   │   └── undraw_rocket.svg
│   ├── js/
│   │   ├── demo/
│   │   │   ├── chart-area-demo.js
│   │   │   ├── chart-bar-demo.js
│   │   │   ├── chart-pie-demo.js
│   │   │   └── datatables-demo.js
│   │   ├── sb-admin-2.js
│   │   └── sb-admin-2.min.js
│   ├── .browserslistrc
│   ├── 404.html
│   ├── blank.html
│   ├── buttons.html
│   ├── cards.html
│   ├── charts.html
│   ├── forgot-password.html
│   ├── index.html
│   ├── login.html
│   ├── package.json
│   ├── register.html
│   ├── tables.html
│   ├── utilities-animation.html
│   ├── utilities-border.html
│   ├── utilities-color.html
│   └── utilities-other.html
├── .gitignore
├── backend_mode.py
├── database.py
├── generator.py
├── main.py
├── orchestrator.py
├── planner.py
├── project_builder.py
├── requirements.txt
├── simple_mode.py
```

---

## Project Workflow
1.  **Landing Page:** Select between Standard Mode (friendly) or Expert Mode (technical).
2.  **Adaptive Dialogue:** Context-aware Q&A session driven by adaptive LLMs to extract requirements.
3.  **Requirements Confirmation:** Summary of gathered specifications for final approval.
4.  **App Generation:** LLM injects business logic into pre-built templates.
5.  **Preview & Export:** Interaction with the live app, ZIP download, or shareable link generation.

---

## System Architecture
<img width="1600" height="788" alt="image" src="https://github.com/user-attachments/assets/f12a980b-c151-45c4-b3c6-b7f94ef58ed2" />


---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python |
| Frontend | React,Vite, HTML-CSS JS |
| Primary LLM (Q&A) | Groq |
| Secondary LLM (Templates) | Qwen 7B |
| Database | SQLAlchemy |
| App Output Format | HTML / CSS / JS (zipped) |

---


## Getting Started

### Prerequisites
- Python 3.9+
- Groq API key
- Qwen 7B API access (or local model)

### Installation

```bash
# Clone the repository
cd innovus

# Install Python dependencies
pip install -r requirements.txt

Set environment variables


```

Project is hosted using ** Vercel (FrontEnd) ** and ** Render (BackEnd) ** - where
environment variables can be set and frontend server can be accesed via:

https://kreativegenesis-code-wave-wtzy.vercel.app/

### Running the App

```bash
python backend/app.py
```

Then open your browser at `http://localhost:5000`.

---

## Database

InNovus uses **SQLAlchemy** with SQLite by default (easily swappable for PostgreSQL or MySQL). The database stores:
- User sessions and Q&A history
- Confirmed requirements objects
- Generated app files and metadata
- Shareable link tokens

To initialize the database:

```bash
python backend/database.py
```

---

## Key Design Decisions

**Why two LLMs?**
Groq excels at fast, conversational reasoning — ideal for the real-time Q&A loop. Qwen 7B brings strong code understanding for reliably mapping requirements to templates and injecting logic correctly.

**Why templates instead of pure generation?**
Template-based generation produces more consistent, production-ready output than open-ended code generation, especially for common app patterns (forms, dashboards, trackers, etc.).

**Why 5 dimensions?**
Through testing, 5 requirement dimensions (purpose, data model, user actions, UI style, output format) were found to be sufficient to generate a functional first version without overwhelming users with questions.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

