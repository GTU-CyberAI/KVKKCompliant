# KVKK Compliant Sensitive Data Masking System

## Project Description

This project detects and masks sensitive personal data in Turkish text, compliant with Türkiye’s KVKK law. It uses:

- **Regex** for TCKN, IBAN, phone, email, card.
- **spaCy (Turkish model)** for names, places.
- **Microsoft Presidio** for orchestrating detection & masking.

Goal: let individuals & SMEs share/store text safely by hiding personal data.

---

## Repository Structure

```
kvkk-mask-system/
├─ src/
│  ├─ backend/ (Flask / FastAPI)
│  └─ frontend/ (React.js)
├─ config/       (Docker, env files)
├─ tests/
├─ docs/         (FILE_OVERVIEW.md)
├─ requirements.txt
├─ package.json
├─ .env.example
└─ README.md
```

---

## Features

| Type     | Details                                                |
| -------- | ------------------------------------------------------ |
| Regex    | Validates TCKN (checksum), IBAN, emails, phones, cards |
| NLP      | Turkish NER with spaCy (`tr_core_news_sm`)             |
| Presidio | Combines regex + NLP, masks output                     |
| API      | `/mask` endpoint returns masked JSON                   |
| Frontend | React UI to paste/upload text/PDF, see masked result   |

---

## Installation & Run

```bash
# clone your fork
$ git clone https://github.com/<your-user>/kvkk-mask-system.git
$ cd kvkk-mask-system

# backend
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env

# frontend
$ cd frontend
$ npm install
```

Run locally:

```bash
$ cd backend && flask run --debug
$ cd frontend && npm run dev
```

Visit [http://localhost:5173](http://localhost:5173).

---

## ▶ Usage Example

Input:

```
T.C. No: 12345678901, Tel: +90 555 123 4567
```

Masked:

```
T.C. No: XXXXXXXXX01, Tel: XXX XXX XXXX
```

---

## Troubleshooting

| Symptom               | Fix                          |
| --------------------- | ---------------------------- |
| `ModuleNotFoundError` | Activate venv & install reqs |
| Blank frontend        | Check `npm run dev` on 5173  |
| Docker conflict       | Change ports in compose file |

---

## Acknowledgements

- Course: Data Privacy / Network Programming
- Instructor: Dr. Salih Sarp
- Collaborators: Osman Sarı, Gülbeyaz Altuntaş
- University: Gebze Technical University

---

## Submission Checklist

- [x] All code & configs included.
- [x] README covers purpose, install, usage.
- [x] `.gitignore` excludes `venv`, `node_modules`.
- [x] Runs locally & via Docker.

---

## Legal Note

Helps follow Türkiye’s **KVKK law** by masking personal data (Articles 4 & 12 on data minimization & security).
