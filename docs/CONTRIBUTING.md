# Contributing to FinAgent Sentinel

Thank you for your interest in contributing to FinAgent Sentinel! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating a new issue
3. **Include details:**
   - OS and version
   - Python and Node.js versions
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Relevant logs

### Suggesting Features

1. **Check existing feature requests** first
2. **Describe the use case** clearly
3. **Explain the benefits** to users
4. **Consider implementation complexity**

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
   ```bash
   git commit -m "feat: Add voice language selection"
   ```
6. **Push to your fork**
7. **Create a Pull Request**

## 📝 Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
```bash
feat: Add Tamil language support to TTS
fix: Prevent duplicate high-risk actions
docs: Update README with voice features
refactor: Simplify validator logic
```

## 🧪 Testing Guidelines

### Before Submitting PR

- [ ] Code runs without errors
- [ ] All existing tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No console errors in browser
- [ ] Voice features tested (if applicable)
- [ ] TTS tested on macOS (if applicable)

### Manual Testing

```bash
# Backend
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Test voice input
# Test task execution
# Test approval flow
# Test error handling
```

## 🏗️ Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- macOS (for TTS features)
- Google Cloud account

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/sentinel-ai.git
cd sentinel-ai

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
playwright install chromium

# Frontend setup
cd ../frontend
npm install

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

## 📂 Project Structure

```
finagent-sentinel/
├── backend/
│   ├── app/
│   │   ├── main.py          # WebSocket server
│   │   ├── agent.py         # LangGraph agent
│   │   ├── brain.py         # Gemini Vision
│   │   ├── voice.py         # Whisper STT
│   │   ├── tts.py           # macOS TTS
│   │   ├── validator.py     # Financial validation
│   │   ├── models.py        # Data models
│   │   └── utils.py         # Utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   └── components/
│   │       └── VoiceRecorder.jsx
│   └── package.json
└── docs/                     # Documentation
```

## 🎯 Areas for Contribution

### High Priority

- [ ] Unit tests for backend modules
- [ ] Integration tests for agent workflow
- [ ] Frontend component tests
- [ ] Support for more TTS voices
- [ ] Improved error messages
- [ ] Performance optimizations

### Medium Priority

- [ ] Additional language support
- [ ] Custom risk policies
- [ ] Session replay feature
- [ ] Advanced analytics
- [ ] Mobile-responsive UI

### Documentation

- [ ] Video tutorials
- [ ] Architecture diagrams
- [ ] Code examples
- [ ] Troubleshooting guides
- [ ] Best practices

## 🔍 Code Review Process

1. **Automated checks** run on PR
2. **Maintainer review** within 48 hours
3. **Feedback addressed** by contributor
4. **Approval and merge** by maintainer

## 🐛 Debugging Tips

### Backend Issues

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 -m uvicorn app.main:app --reload --port 8000

# Check Whisper model
python3 -c "import whisper; print(whisper.load_model('small'))"

# Test TTS
say "Test message"
```

### Frontend Issues

```bash
# Check console for errors
# Open browser DevTools (F12)

# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Clear cache
rm -rf node_modules package-lock.json
npm install
```

## 📜 Code Style

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Document functions with docstrings
- Keep functions focused and small

```python
async def transcribe_audio(audio: UploadFile) -> dict:
    """
    Transcribe audio to text in original language script.
    
    Args:
        audio: Uploaded audio file
        
    Returns:
        dict with text, language, and segments
    """
    # Implementation
```

### JavaScript/React

- Use functional components
- Follow React hooks best practices
- Use meaningful variable names
- Add JSDoc comments for complex functions

```javascript
/**
 * Voice recorder component with multilingual support
 * @param {Function} onTranscript - Callback with transcribed text
 */
export default function VoiceRecorder({ onTranscript }) {
    // Implementation
}
```

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## 📧 Questions?

- Open a [GitHub Discussion](https://github.com/Avinashdevray/sentinel-ai/discussions)
- Join our community chat
- Email: [your-email@example.com]

---

**Thank you for contributing to FinAgent Sentinel!** 🎉
