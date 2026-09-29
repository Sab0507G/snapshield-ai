# 🛡️ SnapShield AI

### Real-Time On-Device Privacy Protection

SnapShield AI is a privacy-first desktop application that continuously analyzes visible screen content for sensitive information and potential unauthorized viewers.

It combines **screen capture, OCR, sensitive-data detection, viewer detection, risk assessment, and automatic visual protection** into a local-first privacy pipeline.

The goal is to prevent sensitive information such as passwords, API keys, phone numbers, email addresses, and payment-card numbers from remaining exposed on the screen.

---

## 🚀 Key Features

### 🔐 Sensitive Information Detection

SnapShield currently detects:

- ✉️ Email addresses
- 📱 Phone numbers
- 💳 Credit/debit card numbers
- 🔑 API keys and tokens
- 🔒 Passwords

The detector uses pattern matching, contextual filtering, confidence scores, card-number validation, and duplicate detection to reduce false positives.

---

### 👀 Viewer Detection

SnapShield analyzes the camera feed to identify the number of visible viewers.

The system distinguishes between:

- `NO VIEWER`
- `SINGLE VIEWER`
- `POTENTIAL UNAUTHORIZED VIEWER`

When multiple viewers are detected, the privacy risk is increased.

---

### 📊 Privacy Risk Assessment

The privacy engine combines:

- Sensitive-data detections
- Detection severity
- Number of visible viewers

to calculate a privacy risk score.

Example states:

```text
SAFE
WARNING
HIGH RISK