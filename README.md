# 🎤 Sampark AI - Voice-First Government Scheme Assistant

> **"सरकारी योजना की जानकारी आपकी भाषा में"**  
> Empowering illiterate and semi-literate Indian citizens to access government schemes through voice

![Sampark AI](https://img.shields.io/badge/AI%20for%20Bharat-Hackathon-orange)
![AWS](https://img.shields.io/badge/AWS-Powered-yellow)
![Hindi](https://img.shields.io/badge/Language-Hindi%2FHinglish-blue)

---

## 🎯 Problem Statement

Over 300 million Indians cannot read or write. They are excluded from accessing government schemes due to:
- Complex websites requiring reading and typing
- Forms in English or formal Hindi
- Multi-step navigation processes
- No voice-based alternatives

## 💡 Solution: Sampark AI

A **voice-first AI assistant** that:
- Uses voice as the primary interface (tap and speak)
- Explains schemes in simple Hinglish
- Provides audio guidance at every step
- Works on basic smartphones
- Requires zero typing or reading

---

## 📱 App Screenshots

### Screen 1: Voice Input
- Big 🎤 button
- Auto-plays: "Namaste! Mic dabaiye aur boliye"
- Tap to speak your query

### Screen 2: Category Selection  
- 👨‍🌾 Kisan (Farmer)
- 🎓 Student (Vidyarthi)
- 👩 Mahila (Woman)

### Screen 3: Scheme Result
- Scheme name with 🔊 Play button
- Eligibility, Benefits, Documents, Steps
- "Nearest Help Center" button

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React App     │────▶│   API Gateway    │────▶│     Lambda      │
│   (S3 Hosted)   │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                    ┌─────────────────────────────────────┼─────────────────────────────────────┐
                    │                                     │                                     │
              ┌─────▼─────┐                        ┌──────▼──────┐                       ┌──────▼──────┐
              │ Transcribe │                        │   Bedrock   │                       │    Polly    │
              │ (Hindi STT)│                        │  (Claude)   │                       │ (Hindi TTS) │
              └───────────┘                        └─────────────┘                       └─────────────┘
                                                          │
                                                   ┌──────▼──────┐
                                                   │  DynamoDB   │
                                                   │  (Schemes)  │
                                                   └─────────────┘
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| **Amazon S3** | Frontend hosting + Audio storage |
| **Amazon API Gateway** | REST API endpoints |
| **AWS Lambda** | Backend logic |
| **Amazon DynamoDB** | Scheme data storage |
| **Amazon Transcribe** | Hindi voice to text |
| **Amazon Polly** | Hindi text to speech |
| **Amazon Bedrock** | AI explanations (Claude) |

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- AWS CLI configured
- AWS SAM CLI
- AWS Account with Bedrock access

### Local Development

```bash
# 1. Clone and enter project
cd Sampark

# 2. Install frontend dependencies
cd frontend
npm install

# 3. Start development server
npm run dev
```

Open http://localhost:3000 in your browser.

> **Note**: The app works in demo mode without AWS backend. Voice recognition uses browser's Web Speech API.

### AWS Deployment

```bash
# 1. Install SAM CLI
# macOS: brew install aws-sam-cli
# Others: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# 2. Configure AWS CLI
aws configure
# Enter your AWS Access Key, Secret Key, and Region (ap-south-1)

# 3. Deploy infrastructure
cd infrastructure
chmod +x deploy.sh
./deploy.sh
```

---

## 📁 Project Structure

```
Sampark/
├── frontend/                    # React Vite Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── StartScreen.jsx      # Voice input screen
│   │   │   ├── CategoryScreen.jsx   # Category selection
│   │   │   └── ResultScreen.jsx     # Scheme details
│   │   ├── services/
│   │   │   └── api.js               # API client
│   │   ├── App.jsx                  # Main app component
│   │   ├── main.jsx                 # Entry point
│   │   └── index.css                # Styles
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── lambda/
│   │   ├── index.js                 # Main Lambda handler
│   │   └── package.json
│   └── dynamodb/
│       ├── seed-data.json           # Initial scheme data
│       └── create-table.sh          # Table creation script
│
├── infrastructure/
│   ├── template.yaml                # SAM/CloudFormation template
│   └── deploy.sh                    # Deployment script
│
└── README.md
```

---

## 🗃️ DynamoDB Schema

**Table: SamparkSchemes**

```json
{
  "scheme_id": "PM_KISAN",
  "category": "farmer",
  "name": "PM Kisan Samman Nidhi",
  "eligibility": "Chhote aur seemant kisan",
  "benefit": "₹6000 har saal",
  "documents": ["Aadhaar", "Bank Account", "Land Record"],
  "steps": [
    "PM Kisan website par jao",
    "Registration karo",
    "Documents upload karo"
  ],
  "helpline": "155261"
}
```

### Available Schemes

| Category | Scheme | Benefit |
|----------|--------|---------|
| 👨‍🌾 Farmer | PM Kisan | ₹6000/year |
| 👨‍🌾 Farmer | Kisan Credit Card | 3L loan @ 4% |
| 🎓 Student | PM Vidyalakshmi | Education Loan |
| 🎓 Student | National Scholarship | ₹5K-20K |
| 👩 Woman | PM Ujjwala | Free LPG |
| 👩 Woman | Sukanya Samriddhi | 8% savings |

---

## 🤖 Bedrock AI Prompt

```
Tum Sampark AI ho.

Rules:
- Hinglish me jawab do
- Bahut simple shabd use karo
- Gaon ke aadmi jaise samjhao
- Legal ya sarkari bhaasha mat use karo
- Steps hamesha numbered me likho
- Short sentences

Goal:
User ko scheme, eligibility, documents aur steps samjhao.
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Process voice transcript |
| GET | `/scheme/{category}` | Get scheme by category |
| POST | `/transcribe` | Transcribe audio |
| GET | `/audio/{schemeId}` | Get audio URL |
| GET | `/health` | Health check |

### Example Request

```bash
curl -X POST https://your-api.execute-api.ap-south-1.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"transcript": "kisan yojana ke baare mein batao"}'
```

### Example Response

```json
{
  "category": "farmer",
  "scheme": {
    "scheme_id": "PM_KISAN",
    "name": "PM Kisan Samman Nidhi",
    "benefit": "₹6000 har saal",
    "eligibility": "Chhote aur seemant kisan",
    "documents": ["Aadhaar Card", "Bank Account"],
    "steps": ["Website par jao", "Register karo", "Submit karo"]
  },
  "audioUrl": "https://s3.../audio/PM_KISAN_123.mp3"
}
```

---

## 🧪 Testing

### Test Voice Recognition (Browser)
1. Open app in Chrome/Safari
2. Click mic button
3. Say "Kisan yojana batao"
4. Should navigate to farmer scheme

### Test API (Terminal)
```bash
# Health check
curl https://your-api-url/prod/health

# Query endpoint
curl -X POST https://your-api-url/prod/query \
  -H "Content-Type: application/json" \
  -d '{"transcript": "mahila ke liye kya yojana hai"}'
```

---

## 🛠️ Environment Variables

### Frontend (.env)
```
VITE_API_URL=https://your-api.execute-api.ap-south-1.amazonaws.com/prod
```

### Lambda
```
SCHEMES_TABLE=SamparkSchemes
AUDIO_BUCKET=sampark-audio-bucket
```

---

## 📊 Cost Estimation (AWS)

For hackathon/demo usage (low traffic):

| Service | Free Tier | Estimated Cost |
|---------|-----------|----------------|
| Lambda | 1M requests/month | Free |
| API Gateway | 1M calls/month | Free |
| DynamoDB | 25 GB storage | Free |
| S3 | 5 GB storage | ~$0.12/month |
| Polly | 5M characters/month | Free for 12 months |
| Transcribe | 60 min/month | Free for 12 months |
| Bedrock | Pay per token | ~$0.50 for demo |

**Total: ~$1-2/month for demo**

---

## 🔒 Security

- API Gateway with CORS configured
- S3 buckets with appropriate policies
- Lambda with minimal IAM permissions
- No user data stored (stateless)
- Audio files with expiring URLs

---

## 📈 Future Enhancements

1. **More Schemes**: Add 50+ central and state schemes
2. **Regional Languages**: Tamil, Telugu, Bengali, etc.
3. **WhatsApp Bot**: Integration via Twilio
4. **Offline Mode**: PWA with cached responses
5. **CSC Integration**: Direct application submission
6. **Analytics**: Track most searched schemes

---

## 👥 Team

**Sampark AI** - AI for Bharat Hackathon 2026

---

## 📜 License

MIT License - Free for educational and non-commercial use.

---

## 🙏 Acknowledgments

- AI for Bharat initiative
- AWS for cloud infrastructure
- Government of India for open scheme data

---

**Made with ❤️ for Bharat**
