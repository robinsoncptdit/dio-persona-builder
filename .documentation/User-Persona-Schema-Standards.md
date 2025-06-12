# User Persona Schema Standards

| **Element** | **Description** |
|:-:|:-:|
| **Name & Photo** | A memorable identity |
| **Job / Role & Background** | Position, environment, demographics |
| **Technical Fluency** | Skill level, tools used |
| **Goals (Short & Long)** | What they aim to achieve |
| **Motivations & Expectations** | Emotional/cognitive drivers |
| **Needs & Pain Points** | What they require vs what’s holding them back |
| **Behaviors & Usage Context** | How & where they engage with your system |
| **Journeys / Scenarios** | Key use cases or typical tasks |
| **Preferred Style** | Tone, communication, accessibility considerations |
| **Key Quote** | A representative statement in their voice |
Here are the **industry-standard elements** included in user persona profiles (beyond just goals), as recommended by leading UX authorities like Nielsen Norman Group, Interaction Design Foundation, and ISO human-centered design standards:

---

### **👤 1.**

### **Background & Demographics**

* Includes age, job title, education, experience, and environment (remote/in-office) – essential for empathy and context .

---

### **📌 2.**

### **Behaviors & Context of Use**

* How they interact with your product/system: technical fluency, frequency, preferred devices, work patterns .

---

### **🛠️ 3.**

### **Needs & Pain Points**

* Their core functional requirements and the frustrations they experience with current solutions .

---

### **🎯 4.**

### **Goals & Objectives**

* Both short- and long-term — what success looks like for them (personal, professional, task-oriented) .

---

### **💭 5.**

### **Motivations & Expectations**

* What drives them, emotionally or socially: recognition, efficiency, reliability, safety. Shapes tone and UX direction .

---

### **🧠 6.**

### **Mental Models & Attitudes**

* Their expectations, assumptions, and design preferences. Aligns product with “what they expect to see” .

---

### **🧩 7.**

### **Preferred Communication & Traits**

* Tone, pace, and mode they appreciate (formal vs casual, visual vs text-heavy), including accessibility/inclusivity needs .

---

### **✏️ 8.**

### **Scenarios or User Journey Highlights**

* Representative scenarios, tasks, or “day‐in‐the‐life” moments to contextualize their experience and drive empathy .

---

### **🔬 9.**

### **Technical Proficiency & Tool Familiarity**

* Systems they know (e.g., CRM, IDEs, mobile vs desktop), and how confident they are using them .

---

### **🔄 10.**

### **Frustrations with Current Tools**

* Specific pain points in current workflows or competitors’ products, providing direct insight for UX and product improvements .

---

## **🧭 How This Ties to Standards**

* **ISO 9241‑210** (Human‑Centered Design) emphasizes understanding users’ **context, needs, behaviors**, and iterative validation .

* **Interaction Design Foundation** highlights **needs, goals, behaviors, expectations** as core elements .

* **NN/g** underscores that well-grounded personas—**fictional but data-backed**—support empathy, usability, and better design decisions .

---

### **✅ Persona Template Checklist**

|  **Element**  |  **Description**  | 
|---|---|
|  **Name & Photo**  |  A memorable identity  | 
|  **Job / Role & Background**  |  Position, environment, demographics  | 
|  **Technical Fluency**  |  Skill level, tools used  | 
|  **Goals (Short & Long)**  |  What they aim to achieve  | 
|  **Motivations & Expectations**  |  Emotional/cognitive drivers  | 
|  **Needs & Pain Points**  |  What they require vs what’s holding them back  | 
|  **Behaviors & Usage Context**  |  How & where they engage with your system  | 
|  **Journeys / Scenarios**  |  Key use cases or typical tasks  | 
|  **Preferred Style**  |  Tone, communication, accessibility considerations  | 
|  **Key Quote**  |  A representative statement in their voice  | 
---

## Example
**Persona Name**: e.g., “Anna the Analyst”  
**Photo**: [Insert image]

**Background & Demographics**  
- Role: e.g., Financial Analyst  
- Age: e.g., 32  
- Education: e.g., Bachelor’s in Finance  
- Experience: e.g., 8 years working remotely/in-office  

**Behaviors & Context of Use**  
- Devices: Desktop (60%), Mobile (40%)  
- Frequency: Daily use during business hours  
- Technical Fluency: Advanced with spreadsheets & BI tools  

**Needs & Pain Points**  
- Needs: Quick access to real-time financial data  
- Pain Points: Slow reports, manual data entry  

**Goals & Objectives**  
- Short-term: Generate weekly finance reports faster  
- Long-term: Automate recurring analytics tasks  

**Motivations & Expectations**  
- Motivated by efficiency and accuracy  
- Expects intuitive dashboard design and reliable outputs  

**Mental Models & Attitudes**  
- Expects spreadsheet-like drill-down capability  
- Prefers predictable, stable interfaces  

**Preferred Communication & Traits**  
- Prefers concise, visual data, light text  
- Tone: Professional but friendly; accessible layout  

**Technical Proficiency & Tool Familiarity**  
- Uses Excel, Tableau, SQL regularly  
- Comfortable learning new analytics interfaces  

**Scenarios / User Journey Highlights**  
- Scenario: Logging in Monday morning → refresh project dashboard → share insights with team  

**Frustrations with Current Tools**  
- “Reports often time out and need manual refreshing”—leading to delays  

**Key Quote**  
> “I need dashboards that just *work*, without the constant toggling.”

## Example JSON
```
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserPersona",
  "type": "object",
  "required": ["name", "background", "behaviors", "needs", "goals"],
  "properties": {
    "name": { "type": "string", "description": "Persona name/title" },
    "photo": { "type": "string", "format": "uri", "description": "Image URL" },
    "background": {
      "type": "object",
      "properties": {
        "role": { "type": "string" },
        "age": { "type": "integer" },
        "education": { "type": "string" },
        "experience": { "type": "string" }
      }
    },
    "behaviors": {
      "type": "object",
      "properties": {
        "devices": { "type": "string" },
        "frequency": { "type": "string" },
        "technicalFluency": { "type": "string" }
      }
    },
    "needs": { "type": "array", "items": { "type": "string" } },
    "painPoints": { "type": "array", "items": { "type": "string" } },
    "goals": {
      "type": "object",
      "properties": {
        "shortTerm": { "type": "string" },
        "longTerm": { "type": "string" }
      }
    },
    "motivations": { "type": "string" },
    "expectations": { "type": "string" },
    "mentalModels": { "type": "string" },
    "preferredCommunication": { "type": "string" },
    "technicalProficiency": { "type": "string" },
    "toolsUsed": { "type": "array", "items": { "type": "string" } },
    "scenarios": { "type": "array", "items": { "type": "string" } },
    "frustrations": { "type": "array", "items": { "type": "string" } },
    "keyQuote": { "type": "string" }
  }
}
```


#DEV