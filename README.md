# AI Chrome Chat Manager - Universal AI Edition

A sophisticated AI orchestration system that enables multiple AI models to collaborate through role-based conversations. Built with UniversalAIAdapter architecture supporting multiple AI providers.

## 🌟 Features

- **🤖 Multi-AI Support**: Seamlessly integrate with Gemini, OpenAI, and future AI providers
- **🔐 Secure Configuration**: Encrypted API key storage with military-grade security
- **🎭 Role-Based AI System**: Project Manager, Lead Developer, and Boss roles
- **📊 Analytics Dashboard**: Real-time cost tracking, token usage, and performance metrics
- **🧠 Memory Bank Integration**: Persistent knowledge management with MCP
- **🐳 Docker Ready**: Production-ready containerization
- **🌐 Web Interface**: Modern, responsive control panel

## 🏗️ Architecture

```
ai-chrome-chat-manager/
├── src/
│   ├── ai_adapters/          # Universal AI adapter system
│   │   ├── base_adapter.py   # Abstract base class
│   │   ├── gemini_adapter.py # Google Gemini integration
│   │   ├── openai_adapter.py # OpenAI GPT integration
│   │   ├── universal_adapter.py # Central AI manager
│   │   └── secure_config.py  # Encrypted configuration
│   ├── main_universal.py     # Main application entry
│   ├── memory_bank_integration.py # Knowledge persistence
│   ├── message_broker.py     # Inter-AI communication
│   ├── web_ui.py            # Web interface
│   └── roles/               # AI role definitions
├── templates/               # Web UI templates
├── static/                 # CSS/JS assets
├── memory-bank/           # Project knowledge base
├── Dockerfile            # Container definition
├── docker-compose.yml   # Orchestration config
└── requirements.txt    # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- API keys for Gemini and/or OpenAI

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-chrome-chat-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys:
```bash
cp env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
python src/main_universal.py
```

### Docker Deployment

```bash
docker-compose up --build
```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
# Gemini Configuration
GEMINI_PM_API_KEY=your-gemini-api-key
GEMINI_PM_MODEL=gemini-2.0-flash

# OpenAI Configuration (Optional)
OPENAI_LD_API_KEY=your-openai-api-key
OPENAI_LD_MODEL=gpt-4o-mini

# Security
CONFIG_PASSWORD=your-secure-password
```

## 💬 Usage

1. **Start a conversation bridge**:
   - Choose option 1 from the menu
   - Enter your initial prompt
   - Watch AI roles collaborate

2. **Monitor analytics**:
   - Access the web interface at http://localhost:5000
   - View real-time metrics and costs

3. **Manage roles**:
   - Dynamically assign AI models to roles
   - Switch between providers on the fly

## 🎯 AI Roles

- **👔 Project Manager**: Strategic planning and task coordination
- **👨‍💻 Lead Developer**: Technical implementation and code review
- **🎩 Boss**: Executive oversight and decision making

## 📊 Analytics Dashboard

Track your AI usage with:
- Total cost in USD
- Token usage breakdown
- Request counts per AI
- Success rates and response times
- Live activity feed

## 🛡️ Security

- API keys are encrypted using Fernet (AES-256)
- Secure key derivation with PBKDF2
- Environment-based configuration
- Docker secrets support

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with ❤️ using modern Python async architecture
- Powered by Google Gemini and OpenAI
- Memory Bank MCP for knowledge persistence
- Flask & SocketIO for real-time web interface