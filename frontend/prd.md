# Product Requirements Document
## AppForge AI — Conversational No-Code App Builder

**Version:** 1.0  
**Scope:** Hackathon Build (24-Hour Sprint)

---

# 1. Product Overview

**AppForge AI** is a conversational, AI-powered **no-code application builder** that transforms a user's intent into a working web application through an adaptive dialogue engine.

The platform targets two distinct user personas:

1. **Non-technical users** (small business owners, NGOs, educators)
2. **Technical users** (developers, engineering students, product managers)

Both are served through a dual-mode interface:

- **Simple Mode**
- **Expert Mode**

The system:

1. Asks adaptive questions through a conversational interface  
2. Builds an internal **requirements object** from the dialogue  
3. Displays a **live visual blueprint** of the app being described  
4. Generates a **functional web application**  
5. Allows the user to **preview, download, or share** the generated app  

The key innovation is **not code generation**, but the **intelligence layer before generation** that behaves like a **product consultant** understanding the user's needs.

---

# 2. Problem Statement

Many individuals and small organizations have workflows that could easily be solved with simple software tools.

However:

- They **lack technical skills**
- Hiring developers is **expensive**
- Existing no-code tools like **Bubble** or **Webflow** are often **too complex**

Meanwhile, **technical professionals** waste time repeatedly creating boilerplate code for internal tools and prototypes.

The gap is not tools.  
The gap is **systems that understand requirements before building software**.

---

# 3. Solution Statement

AppForge AI introduces a **conversational intelligence layer before code generation**.

The system:

1. Asks adaptive questions  
2. Interprets user responses  
3. Builds an internal understanding of the required system  
4. Displays a **visual blueprint**  
5. Generates a working application once requirements are clear  

The output is a **functional web application** built using:

- HTML
- CSS
- JavaScript

The app can be:

- Previewed live
- Downloaded as a ZIP
- Shared via a hosted link

---

# 4. Target Users

## User Type 1 — Simple Mode User

Examples:

- Small business owner  
- School administrator  
- NGO field worker  
- Clinic receptionist  

Characteristics:

- No programming experience
- Cannot describe needs technically
- Needs fast results

**Success metric:**  
A working tool within **15 minutes**.

---

## User Type 2 — Expert Mode User

Examples:

- Developer  
- Technical founder  
- Product manager  
- Engineering student  

Characteristics:

- Comfortable with system descriptions
- Wants speed and precision
- May modify generated code

**Success metric:**  
Working prototype within **10 minutes**.

---

# 5. Key Features

## Feature 1 — Mode Selection Screen

The landing page presents two entry points.

**Simple Mode**

- Friendly interface
- Conversational language
- Large UI elements

**Expert Mode**

- Minimal interface
- Technical phrasing
- Faster interactions

Users may **switch modes anytime**.

---

## Feature 2 — Adaptive Conversational Question Engine

This is the **core intelligence layer**.

Responsibilities:

- Maintain conversation context
- Infer unstated requirements
- Ask **one relevant question per response**
- Avoid redundant questions

Example:

If a user says:

> “I run a bakery and want to track orders.”

The system may infer:

- Customer list
- Order form
- Order status tracker
- Notification logic

### Session Length

Typically **5–9 questions**.

The AI updates a **requirements object** across five dimensions:

1. Authentication and Users
2. Data and Storage
3. User Interface Complexity
4. Business Logic and Workflows
5. External Integrations

When confidence passes a threshold, generation begins.

---

## Feature 3 — Requirements Summary and Confirmation

Before generation, the system presents a **summary card**.

**Simple Mode**

Plain-English description.

**Expert Mode**

Technical spec including:

- Entities
- Routes
- Roles
- Data structures

The user may **confirm or edit**.

---

## Feature 4 — App Generation Engine

The generation layer produces a working web application.

Powered by **Mistral (via Hugging Face)**.

Approach:

**Template + AI logic injection**

Instead of generating everything from scratch:

1. Pre-built templates are selected
2. Mistral fills:
   - business logic
   - UI copy
   - workflow behavior
   - data handling

Advantages:

- Reduced hallucination
- Faster generation
- Higher reliability

Data storage uses **localStorage** for hackathon scope.

---

## Feature 5 — Live Preview and Download

The generated application appears instantly in an **iframe preview panel**.

Users can:

- Interact with the app
- Test functionality
- Download a **ZIP package**
- Generate a **shareable hosted link**

---

# 6. User Workflow

1. User opens the landing page  
2. Selects **Simple Mode** or **Expert Mode**  
3. Chat interface begins conversation  
4. AI asks adaptive questions  
5. Blueprint updates live  
6. Requirements summary appears  
7. User confirms  
8. App generation begins  
9. Generated app appears in preview  
10. User downloads or shares the application  

---

# 7. Technical Architecture

## Frontend Stack

- React
- Vite
- Tailwind CSS
- Framer Motion

Responsibilities:

- Chat interface
- Mode toggle
- Blueprint visualizer
- Requirements summary
- Preview iframe
- Download/share UI

Communication via **REST APIs**.

---

## Backend Stack

Options:

- Node.js  
- Python (FastAPI)

Responsibilities:

- LLM API calls
- Session management
- Prompt chain execution
- App generation
- File packaging

---

# 8. AI Architecture

## Model Usage

Two models are used:

Used for:

- Adaptive questioning
- Requirements extraction
- Context reasoning
- Requirements updates

### Mistral (Hugging Face)

Used for:

- Code generation
- HTML/CSS/JS output
- Business logic creation

### Fallback Strategy

If the dual-model pipeline fails:

System switches to **single-model generation using Mistral**.

---

# 9. Session Management

Sessions are handled using:

- **UUID stored in the browser**

Backend stores:

- conversation history
- requirements object

Storage method:

- in-memory **Map** (Node)
- in-memory **dictionary** (Python)

No authentication required.

---

# 10. Deployment

Frontend deployed on **Vercel**.

Backend deployed on **Render**.

Deployment target:

**Hour 20 of the hackathon**

Remaining time used for:

- testing
- demo preparation

---

# 11. Prompt Chains

## Requirements Extraction Chain

Responsibilities:

- Ask adaptive questions
- Update requirements object
- Calculate confidence score

Output format:

```json
{
 "next_question": "...",
 "requirements_object": {...},
 "confidence_score": xx.xx
}
