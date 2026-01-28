
# IMPLEMENTATION PLAN: New Features (Video, AI, Reports)

## 1. Remove Billing/Plans from Sidebar
- [ ] Locate `Sidebar` component (likely `frontend/src/components` or `frontend/src/layout`)
- [ ] Comment out or remove links to `/planos` and `/billing`
- [ ] Verify UI cleanup

## 2. Video Consultation
- [ ] **Research**: Evaluate Jitsi Meet vs WebRTC/LiveKit
- [ ] **Frontend**: Create `VideoRoom.jsx` component
    - Embedded video frame
    - Controls (Mic/Cam/End Call)
- [ ] **Backend**: Create `/api/consultas/video-token` (if needed) or simple room URL generator
- [ ] **Integration**: Add "Iniciar Videochamada" button in `ConsultaDetalhes`

## 3. AI Consultation Assistant (Observation & Capture)
- [ ] **Audio Capture**: Implement browser audio stream capture (`MediaRecorder` API)
- [ ] **Processing Pipeline**:
    - Audio Blob -> Backend (`/api/ai/process-consultation`)
    - Backend -> Whisper (STT) -> Transcription
    - Transcription -> LLM (Extraction) -> Structured Data (Sintomas, Evolucao)
- [ ] **Storage**: Save structured data to `Evolucao` or new model

## 4. Habeas Corpus Preventivo Report
- [ ] **Endpoint**: `GET /api/pacientes/<id>/relatorio-judicial`
- [ ] **Data Gathering**:
    - Patient Info
    - Diagnosis (CID)
    - Medication History (Dosagens)
    - Symptom Evolution (Charts)
- [ ] **Generation**: Use `reportlab` or similar to generate PDF
    - Header/Footer (Legal format)
    - Charts (Matplotlib/IOBytes)
    - Narrative text
- [ ] **Frontend**: Button "Gerar Relatório Judicial" in Patient Profile

## 5. Questions for User
- Preferred Video Provider? (Jitsi is free/easiest)
- Report Template? (Do they have a specific legal text?)
- AI Privacy? (Recording patient consent?)

