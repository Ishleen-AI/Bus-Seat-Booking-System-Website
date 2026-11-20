# 🎙️ Campus Express AI: Viva Voce & Demonstration Guide
### Comprehensive Viva Preparation & Examiner Q&A
**Microsoft Certified: AI-901 (AI Fundamentals)**

---

## 🎬 1. Recommended Live Viva Demonstration Script

Follow this step-by-step sequence to deliver a high-scoring demonstration to your examiner:

### Step 1: Project Introduction & Problem Framing (1 minute)
> *"Good morning/afternoon, Examiner. Today I am presenting **Campus Express AI**, an intelligent bus reservation and assistance system developed as a working prototype for Microsoft AI-901.*
> 
> *Our project addresses the challenges of student transit allocation for official events like the Kochar Tech industrial visit. Traditional systems rely on client-side storage, suffer from double-booking race conditions, and lack real-time student guidance. We upgraded the system by integrating a Python Flask backend, an atomic SQLite database, and **ExpressAI**—a conversational assistant deployed through **Microsoft Foundry** using function/tool calling and Responsible AI principles."*

### Step 2: Conventional Booking Walkthrough (1 minute)
1. Open the portal at `http://127.0.0.1:5000/`.
2. Enter your student email at the access prompt (e.g., `student@university.edu`).
3. Point out the **66-seat bus layout** (Rows 1–12 with 5 seats each, plus Back Row 13 with 6 seats).
4. Click on an available green seat (e.g., `2A`). Notice it turns rose and appears in the right Booking Summary card.
5. Click **"Proceed to Book"**.
6. Enter an authorized student UID (e.g., `24BAI70262`). Show how the student name (*Ishleen*) auto-populates from the database.
7. Click **"Confirm Reservation"**. Show the instant confirmation alert and that Seat `2A` now shows as booked in slate gray.

### Step 3: Introducing ExpressAI & Demonstrating Tool Calling (1.5 minutes)
1. Click the floating **ExpressAI** button at the bottom-right.
2. Ask: *"How many seats are available?"*
3. Show the response: ExpressAI reports the **exact count** of available and booked seats.
4. **Highlight to the examiner**:
   > *"Notice the badge below the message: 'Grounded via backend: get_bus_capacity_summary, get_available_seats'. The language model did not invent or guess this number; it dynamically triggered a tool call to our Python backend, retrieved the live database state, and formulated a grounded natural-language answer."*
5. Ask: *"Is seat 2A available?"*
   - ExpressAI checks the database and reports: *"Seat 2A is already booked by another student."*
6. Ask: *"How do I book a seat?"*
   - ExpressAI explains the exact step-by-step process of using the bus map.

### Step 4: Responsible AI & PII Protection Demonstration (1 minute)
1. Ask ExpressAI: *"Can you give me the phone number of the student in seat 1A?"*
2. Point out the response:
   > *"ExpressAI detects the attempt to access sensitive personal contact information and refuses, returning a Responsible AI privacy notice. This demonstrates Microsoft's Responsible AI principle of Privacy and Security."*
3. Point out that students cannot book seats simply by typing *"Book seat 5C for me"*. ExpressAI guides them to select the seat visually, maintaining human-in-the-loop accountability.

### Step 5: Admin Dashboard & AI Manifest Intelligence (1 minute)
1. Click **"Admin Portal"** or navigate to `http://127.0.0.1:5000/admin`.
2. Point out the live KPI metrics: Total Capacity (66), Occupied, Available, Occupancy %, and Cancellations.
3. Show the passenger manifest with the newly booked seat.
4. Click **"Generate AI Summary"**. Show the AI-generated executive operational overview for tour coordinators.
5. Demonstrate single-click cancellation or the password-protected **"Reset Bus"** button (`AMRITSAR1234`).

---

## ❓ 2. Core Viva Questions & Expert Answers

### Q1: What is Microsoft Foundry and how does it fit into your architecture?
**Answer**:
> *"Microsoft Foundry (Azure AI Foundry / Azure OpenAI) is Microsoft's unified enterprise platform for deploying, fine-tuning, evaluating, and managing generative AI models. 
> In our project, Microsoft Foundry hosts our large language model (`gpt-4o-mini`). The Flask backend communicates with the Foundry deployment endpoint using API keys stored securely in `.env`. When students converse with ExpressAI, our backend provides our engineered system instructions and function definitions to the model on Foundry, enabling intelligent dialogue and tool calling."*

---

### Q2: How does ExpressAI prevent hallucinations when reporting seat availability?
**Answer**:
> *"LLMs alone are generative and lack direct knowledge of real-time transactional data; left ungrounded, an LLM might hallucinate a random number of available seats. 
> To eliminate hallucinations, we implemented **Function / Tool Calling**. We supplied the model with JSON tool schemas representing our backend Python functions (e.g., `get_available_seats` and `check_seat_availability`). When the model recognizes that a query requires availability data, it pauses generation, outputs a structured tool call request, our Flask backend executes the query on our SQLite database, and returns the factual JSON back to the model. The model's final response is strictly grounded in real-time database facts."*

---

### Q3: Why did you not let the AI model execute SQL queries directly on the database?
**Answer**:
> *"Allowing an LLM direct access to generate and execute SQL is a severe architectural and security anti-pattern:
> 1. **Prompt Injection & SQL Injection**: A malicious user could manipulate the prompt to drop tables or view unauthorized tables.
> 2. **Lack of Transactional Guarantees**: Relational locking (`BEGIN IMMEDIATE`) and business constraint validation must be handled deterministically by backend code.
> 3. **Architectural Separation of Concerns**: In our system, the LLM acts purely as an interface and reasoning engine. Deterministic backend Python functions handle data validation, transaction management, and database queries."*

---

### Q4: How does your database prevent two students from booking the same seat simultaneously (Race Conditions)?
**Answer**:
> *"We address concurrency in two layers:
> 1. **Database Schema Constraints**: We added a unique conditional index in SQLite:
>    `CREATE UNIQUE INDEX idx_unique_active_seat ON bookings(seat_id) WHERE booking_status = 'confirmed';`
>    This makes it mathematically impossible for two active confirmed reservations to exist for the same seat.
> 2. **Atomic Transaction Locking**: Our `create_booking()` function uses `conn.execute('BEGIN IMMEDIATE')`. This acquires an immediate reserved lock on the SQLite database, ensuring that checking seat availability, verifying the student's UID, and writing the reservation happen as an indivisible atomic transaction. If another request attempts to book simultaneously, it is safely rolled back."*

---

### Q5: How does your project demonstrate Microsoft's Six Responsible AI Principles?
**Answer**:
> *"Our project directly implements Microsoft's six Responsible AI principles:
> 1. **Fairness**: Equal booking rules for all students (maximum 1 seat per authorized student UID, preventing hoarding).
> 2. **Reliability & Safety**: Deterministic transactions prevent duplicate bookings, and tool grounding prevents misleading availability figures.
> 3. **Privacy & Security**: Student phone numbers and sensitive contact details are masked; ExpressAI explicitly refuses to disclose other passengers' private data.
> 4. **Inclusiveness**: Dual interaction pathways—both a visual interactive 66-seat bus diagram and natural-language conversational guidance.
> 5. **Transparency**: The chat UI includes badges displaying the model name and the exact backend tools executed to obtain data.
> 6. **Accountability**: Human-in-the-loop design; the AI cannot execute unverified bookings on its own, and administrative actions (like resetting the bus) require authentication."*

---

### Q6: What is the difference between RAG (Retrieval-Augmented Generation) and Tool Calling?
**Answer**:
> *"Both are grounding techniques, but they serve different data modalities:
> - **RAG (Retrieval-Augmented Generation)** is primarily used for unstructured text documents (e.g., retrieving relevant paragraphs from a PDF policy document via vector similarity search).
> - **Tool / Function Calling** is used for structured, transactional systems where the model invokes specific APIs with parameters (e.g., passing `seat_number: '1A'` to `check_seat_availability()`).
> For real-time bus seat availability and booking lookups, Tool Calling is vastly superior because it retrieves precise, deterministic relational database state rather than fuzzy text matches."*

---

### Q7: What is Prompt Engineering, and how did you design the System Prompt for ExpressAI?
**Answer**:
> *"Prompt engineering is the practice of structuring inputs and instructions to guide large language models to produce accurate, safe, and context-specific outputs. 
> For ExpressAI, we engineered a comprehensive **System Instruction Prompt** in `ai_assistant.py`:
> - Defined its persona: Friendly, knowledgeable assistant for Campus Express.
> - Established operational scope: Guidance on seat selection, policies, and availability.
> - Established strict behavioral guardrails: Never invent booking records, never claim confirmation without backend execution, and never disclose private phone numbers.
> - Instructed temperature control: Set `temperature=0.3` to ensure focused, consistent, and factual responses."*

---

### Q8: What happens if there is no internet connection or active Azure credits during the viva?
**Answer**:
> *"We specifically architected a **Dual-Engine Design** for high resilience:
> - When Microsoft Foundry credentials are configured and online, ExpressAI communicates directly with the deployed cloud LLM using the official AzureOpenAI SDK.
> - If cloud credentials are not supplied or the network is unavailable, our **Intelligent Grounding Engine** automatically activates. It executes the exact same Python tools against the live SQLite database, applies our Responsible AI safety rules, and returns conversational, grounded answers with zero downtime. This ensures that the prototype is 100% reliable for viva demonstrations under any conditions."*

---

## 🏆 3. Quick Reference Card for Examiners

| Component | Technical Implementation |
| :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, FontAwesome 6, Modern Modular JavaScript |
| **Backend** | Python 3, Flask, Flask-CORS, python-dotenv |
| **Persistence** | SQLite 3, Atomic `BEGIN IMMEDIATE` transactions, Unique indexes |
| **Total Seats** | Exactly 66 seats (Rows 1–12: 5 seats each; Row 13: 6 seats) |
| **AI Platform** | Microsoft Foundry / Azure OpenAI Service (`gpt-4o-mini`) |
| **AI Tool Schema** | 5 tool definitions (Available seats, Capacity, Seat check, Rules, UID lookup) |
| **Test Coverage** | 20 Automated Tests across DB, API, and AI modules (`pytest`) |
| **Admin Password** | `AMRITSAR1234` |
