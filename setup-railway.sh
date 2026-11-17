#!/bin/bash
# DSA Vault Multi-Model Transcription Setup Script
# One-command deployment for Railway hosting

# Exit on any error
set -e

echo "🚀 Setting up DSA Vault Multi-Model Transcription System..."

# Check for required files
echo "📁 Checking project files..."
if [ ! -f "main.py" ] || [ ! -f "library.py" ]; then
    echo "❌ Error: main.py or library.py not found!"
    echo "Please run this script from the project directory"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

python3 --version

# Check pip availability
echo "📦 Checking pip availability..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 not found. Please install pip"
    exit 1
fi

# Install dependencies
echo "🔧 Installing Python dependencies..."
pip3 install --no-cache-dir -r requirements.txt

# Create .env file example
echo "📝 Creating .env file example..."
cat > .env.example << 'EOF'
# DSA Vault Environment Variables
# Copy this to .env and replace with your actual values

# Required - Supabase integration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_service_role_key_here
APP_PASSCODE=your_secure_passcode_here

# Optional - for alternative AI models
LLAMA_API_KEY=your_llama_api_key_here_if_available
QWEN_API_KEY=your_qwen_api_key_here_if_available

# Optional - model selection
GEMINI_MODEL=gemini-3.5-flash-lite  # or leave empty for auto-selection
EOF

# Create .gitignore
echo "🚫 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.env
.venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Cache
*.cache
dist/
*.log

# Poetry
.pytest_cache/
test_reports/
*.coverage
*.pyc
EOF

# Check for Railway CLI
echo "🚊 Checking Railway CLI..."
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI found"
else
    echo "⚠️  Railway CLI not found"
    echo "📋 Install it with: curl -s https://railway.com/install.sh | bash"
    echo "   OR visit: https://railway.com/docs/getting-started/cli"
fi

echo ""
echo "🎉 Setup complete! Next steps:"
echo "1. Configure your environment variables (.env file)"
echo "2. Deploy to Railway:"
echo "   - Go to railway.com → New Project → Deploy from GitHub"
echo "   - Select your repository"
echo "   - Add environment variables from .env.example"
echo "   - Click 'Deploy'"
echo ""
echo "3. Your application will be available at:"
echo "   https://your-project-railway.app"
echo ""
echo "📖 For detailed instructions, see README.md"
echo "🐛 For troubleshooting, check Railway dashboard"
echo ""
echo "🚀 Happy coding with your multi-model DSA transcription system!"

# Make this script executable
chmod +x "$0"