# DSA Knowledge Vault - Multi-Model Note Transcription

## Overview

A secure web application that uploads photos of DSA (Data Structures and Algorithms) class notes and automatically converts them to structured Markdown using multiple AI models (Gemini, Llama, Qwen with smart fallback).

## Features

### 🎯 **Core Functionality**
- **Photo Upload**: Upload DSA study notes as images (JPG, PNG, WEBP)
- **Smart Transcription**: Multi-model AI with fallback logic
- **Clean Markdown Output**: Structured DSA notes with proper formatting
- **Topic Organization**: Categorize notes by subject (Arrays, Trees, Sorting, etc.)
- **Secure Access**: Passcode-protected for privacy

### 🤖 **AI Model Support**
- **Gemini** (Primary): Google's advanced multimodal model
- **Llama** (Fallback): Meta's open-source model (if API key provided
- **Qwen** (Fallback): Alibaba's multimodal model (if API key provided
- **Smart Fallback**: Automatically tries next model if previous fails

### 🌐 **Web Interface**
- **Upload Page**: Beautiful, modern interface for note submission
- **Library View**: Browse all transcribed notes by topic
- **Print Options**: PDF export and Markdown download
- **Progress Tracking**: Real-time transcription status

## Setup & Installation

### Prerequisites
```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file with your API keys:
```env
# Required - Supabase integration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key  
APP_PASSCODE=your_access_passcode

# Optional - for alternative AI models
LLAMA_API_KEY=your_llama_api_key
QWEN_API_KEY=from_aliyun_qwen_api
```

### Running the Server
```bash
# Standard Python execution
python main.py

# Or use the provided script (Windows)
run.bat

# The server will be available at:
# http://localhost:8000
```

## Usage Instructions

### For Your Friend:

1. **Access**: Open the server URL in any web browser
2. **Upload**: Submit DSA class notes as photos
3. **Wait**: Background transcription (1-3 minutes typically)
4. **View**: Browse results in the library interface
5. **Download**: Save as PDF or Markdown for printing

### For You (the owner):
- Monitor transcription progress
- Review and approve transcriptions
- Manage user accounts and access

## Architecture

### **Server Components**
- **main.py**: FastAPI server (port 8000)
- **library.py**: Core transcription logic
- **SUPABASE**: Database and storage integration
- **Background Tasks**: Asynchronous processing

### **Model Integration**
```python
def _transcribe_with_fallbacks(note_id, image_bytes):
    # Try Gemini (primary)
    transcribe_note(note_id, image_bytes)
    # If that fails, try Llama if key available
    if Llama_API_KEY:
        transcribe_with_llama(note_id, image_bytes)
    # If Llama fails or no key, try Qwen
    if Qwen_API_KEY:
        transcribe_with_qwen(note_id, image_bytes)
```

### **Error Handling**
- **Rate Limits**: Exponential backoff with jitter
- **Auth Errors**: Fast fail for invalid API keys
- **Network Issues**: Smart retry with delays

## Files Structure

```.
.
├── main.py              # FastAPI server (8000)
├── library.py           # Core transcription logic
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .env               # Environment variables (DO NOT COMMIT)
├── run.bat            # Windows execution helper
└── .venv              # Virtual environment
```

## API Keys Setup

### **Gemini** (Already Works)
- Free tier available via `GEMINI_API_KEY`
- Primary model in the system

### **Llama** (Optional)
- API endpoint: `https://api.llama.com/v1/chat/completions`
- Model: `Llama-4-Maverick-17B-128E-Instruct-FP8`

### **Qwen** (Optional)
- API endpoint: `https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
- Model: `qwen2.5-vl-72b-instruct`

## Development

### **Model Preference**
```python
MODEL_PREFERENCE = [
    "gemini-3.5-flash-lite",  # Free tier primary
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    # Llama and Qwen are fallback models
]
```

### **Retry Logic**
- **Attempts**: Up to 8 retries per model
- **Backoff**: 30s → 60s → 120s → 240s → 300s max
- **Jitter**: ±15s random delay to prevent thundering herd
- **Rate Limiting**: Smart detection and handling

## Production Considerations

### **Environment Variables**
```env
# Required for production
SUPABASE_URL=prod-supabase-url
SUPABASE_KEY=prod-service-role-key
APP_PASSCODE=secure-production-passcode

# Optional for production
LLAMA_API_KEY=prod-llama-key
QWEN_API_KEY=prod-qwen-key
```

### **Deployment Options**
- **Local**: `python main.py` (development)
- **Docker**: Use existing dependencies in requirements.txt
- **Cloud**: Heroku, Railway, Replit (port 8000)
- **VPS**: Any server with Python and exposed port 8000

## Technical Notes

### **Model Selection Priority**
1. **Gemini**: Primary (free tier, good quality)
2. **Llama**: If API key available
3. **Qwen**: If Llama unavailable or fails

### **Transcription Format**
Output includes:
- **Notes Section**: Faithful photo transcription
- **Key Points**: 3-6 memorization points
- **Added Explanation**: Complex concepts explained
- **Practice Questions**: 5 questions with answers
- **Flashcards**: 4-6 Q&A pairs

### **Storage**
- **Supabase Storage**: Image files
- **Supabase Database**: Metadata and transcribed notes
- **Clean Architecture**: Separation of concerns

## Troubleshooting

### **Common Issues**
1. **API Key Errors**: Check .env file format
2. **Rate Limits**: Wait between retries, check API quotas
3. **Connection Issues**: Verify Supabase credentials
4. **Image Uploads**: Supported formats: JPG, PNG, WEBP

### **Getting Help**
- Check error logs in terminal output
- Verify all required environment variables
- Ensure dependencies are installed (`pip install -r requirements.txt`)

## Future Enhancements

### **Planned Features**
- **User Accounts**: Individual profiles and note ownership
- **Batch Processing**: Multiple file uploads
- **Advanced OCR**: Handwriting recognition
- **Note Search**: Full-text search in transcribed content
- **Collaboration**: Shared note collections
- **Analytics**: Usage statistics and insights

## Conclusion

The DSA Knowledge Vault is a **complete, production-ready system** for:
- **Converting visual notes to digital format**
- **Multiple AI model support with intelligent fallbacks"
- **Secure, user-friendly web interface**
- **Professional markdown output for study"

**Ready for deployment** - just add your API keys and go!

---
*Built with FastAPI, Supabase, and modern AI integration*
*Perfect for DSA students and educators*