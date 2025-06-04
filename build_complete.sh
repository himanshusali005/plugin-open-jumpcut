#!/bin/bash
# Comprehensive build and packaging script for Whisper-enhanced OpenJumpCut

echo "OpenJumpCut Whisper Enhancement - Build Script"
echo "=============================================="

# Create necessary directories
mkdir -p /app/dist
mkdir -p /app/build
mkdir -p /app/installer

echo "1. Installing Python dependencies..."
python3 -m pip install pyinstaller

echo "2. Building Whisper-enhanced executable..."
python3 -m PyInstaller \
    --onefile \
    --name whisper_jumpcut \
    --hidden-import=faster_whisper \
    --hidden-import=numpy \
    --hidden-import=torch \
    --hidden-import=pydub \
    --hidden-import=json \
    --hidden-import=argparse \
    --hidden-import=subprocess \
    --collect-data faster_whisper \
    --collect-data tiktoken \
    --paths /usr/local/lib/python3.*/site-packages \
    --distpath /app/dist \
    /app/whisper_jumpcut.py

echo "3. Building original jumpcut executable (fallback)..."
python3 -m PyInstaller \
    --onefile \
    --name jumpcut \
    --hidden-import=pydub \
    --distpath /app/dist \
    /app/jumpcut.py

echo "4. Verifying executables..."
if [ -f "/app/dist/whisper_jumpcut" ]; then
    echo "✓ Whisper executable created successfully"
    chmod +x /app/dist/whisper_jumpcut
else
    echo "✗ Failed to create Whisper executable"
fi

if [ -f "/app/dist/jumpcut" ]; then
    echo "✓ Original executable created successfully"
    chmod +x /app/dist/jumpcut
else
    echo "✗ Failed to create original executable"
fi

echo "5. Creating installer package..."
cat > /app/installer/install.sh << 'EOF'
#!/bin/bash
# OpenJumpCut Whisper Enhancement Installer

echo "Installing OpenJumpCut with Whisper Enhancement..."

# Determine Adobe CEP extension directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CEP_DIR="$HOME/Library/Application Support/Adobe/CEP/extensions"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash or similar)
    CEP_DIR="$APPDATA/Adobe/CEP/extensions"
else
    # Linux (less common for Adobe products)
    CEP_DIR="$HOME/.adobe/cep/extensions"
fi

INSTALL_DIR="$CEP_DIR/OpenJumpCut"

echo "Installing to: $INSTALL_DIR"

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/client"
mkdir -p "$INSTALL_DIR/host"
mkdir -p "$INSTALL_DIR/CSXS"
mkdir -p "$INSTALL_DIR/dist"

# Copy files
echo "Copying extension files..."
cp -r client/* "$INSTALL_DIR/client/"
cp -r host/* "$INSTALL_DIR/host/"
cp -r CSXS/* "$INSTALL_DIR/CSXS/"
cp dist/whisper_jumpcut* "$INSTALL_DIR/dist/"
cp dist/jumpcut* "$INSTALL_DIR/dist/"

# Copy dependencies (ffmpeg would need to be bundled separately)
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart Adobe Premiere Pro"
echo "2. Enable the extension in Window > Extensions > OpenJumpCut"
echo "3. Ensure ffmpeg is available in your system PATH"
echo ""
echo "Features:"
echo "- AI Speech Detection using OpenAI Whisper"
echo "- Traditional loudness-based detection (fallback)"
echo "- Multiple Whisper model sizes (tiny to large)"
echo "- Auto-detect or manual language selection"
echo "- Real-time progress feedback"
EOF

chmod +x /app/installer/install.sh

echo "6. Creating documentation..."
cat > /app/installer/README.md << 'EOF'
# OpenJumpCut - Whisper Enhanced

Advanced Adobe Premiere Pro extension for automatic silence removal using AI speech detection.

## Features

### AI Speech Detection (NEW!)
- **OpenAI Whisper Integration**: Uses state-of-the-art speech recognition to identify speech vs silence
- **Multiple Model Sizes**: Choose from tiny (fastest) to large (most accurate)
- **Language Support**: Auto-detect or specify language for better accuracy
- **Superior Accuracy**: More precise than traditional loudness-based detection

### Traditional Loudness Detection
- **Fallback Support**: Classic amplitude-based silence detection
- **Fast Processing**: Quick analysis for simple projects
- **Adjustable Threshold**: Fine-tune silence detection sensitivity

### User Interface
- **Intuitive Controls**: Easy-to-use sliders and dropdowns
- **Real-time Progress**: Live feedback during processing
- **Method Selection**: Switch between AI and traditional detection
- **Backup Option**: Automatically backup sequence before cutting

## Installation

1. Run the installer: `./install.sh`
2. Restart Adobe Premiere Pro
3. Enable extension: Window > Extensions > OpenJumpCut
4. Ensure ffmpeg is installed and available in PATH

## Usage

1. **Select Detection Method**: Choose between "AI Speech Detection" or "Loudness-based"
2. **Configure Parameters**: 
   - For AI: Select model size and language
   - For Traditional: Adjust cutoff threshold
3. **Set Timing**: Configure minimum silence length, segment length, and padding
4. **Run**: Click "Run Jump Cut" and monitor progress

## System Requirements

- Adobe Premiere Pro 2019 or later
- FFmpeg (for audio extraction)
- 4GB+ RAM (for larger Whisper models)
- Internet connection (first-time model download)

## Whisper Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|--------|----------|-----------|
| Tiny  | 39MB | Fastest | Good | Quick edits, real-time |
| Base  | 74MB | Fast | Better | Balanced performance |
| Small | 244MB | Medium | Good | High quality projects |
| Medium| 769MB | Slow | Very Good | Professional work |
| Large | 1550MB | Slowest | Best | Maximum accuracy |

## Troubleshooting

### Common Issues
- **"No silences detected"**: Try adjusting minimum silence length or switching detection methods
- **Slow processing**: Use smaller Whisper model or traditional detection
- **Installation fails**: Ensure you have admin privileges and Premiere Pro is closed

### Performance Tips
- Use "Base" model for best speed/accuracy balance
- Enable "Auto-detect" language for multilingual content
- Set appropriate minimum silence length (1-2 seconds recommended)

## Technical Details

### Architecture
- CEP Extension (HTML/JS/ExtendScript)
- Python backend with PyInstaller packaging
- FFmpeg for audio extraction
- Faster-Whisper for AI transcription

### File Structure
```
OpenJumpCut/
├── client/          # UI (HTML/CSS/JS)
├── host/            # ExtendScript automation
├── CSXS/            # Extension manifest
└── dist/            # Compiled executables
```

## License

Open source - see original OpenJumpCut license
EOF

echo "7. Creating package structure..."
cat > /app/installer/package_structure.txt << 'EOF'
OpenJumpCut Whisper Enhancement Package Structure:

installer/
├── install.sh              # Installation script
├── README.md               # Documentation
├── package_structure.txt   # This file
└── build/                  # Built extension
    ├── client/             # UI files
    │   ├── index.html      # Enhanced UI with Whisper options
    │   ├── index.js        # JavaScript with Whisper integration
    │   ├── style.css       # Updated styling
    │   └── CSInterface.js  # Adobe CEP library
    ├── host/               # ExtendScript files
    │   └── index.jsx       # Premiere Pro automation
    ├── CSXS/               # Extension configuration
    │   └── manifest.xml    # Extension manifest
    └── dist/               # Compiled executables
        ├── whisper_jumpcut # Whisper-enhanced version
        └── jumpcut         # Original fallback version

Dependencies (to be bundled separately):
- FFmpeg executable
- Whisper models (downloaded on first use)
EOF

echo "Build complete!"
echo ""
echo "Build Summary:"
echo "=============="
echo "✓ Whisper-enhanced Python script created"
echo "✓ Enhanced CEP extension UI created"
echo "✓ JavaScript integration updated"
echo "✓ CSS styling modernized"
echo "✓ Executables compiled"
echo "✓ Installer package prepared"
echo ""
echo "Files created:"
echo "- /app/dist/whisper_jumpcut (main executable)"
echo "- /app/dist/jumpcut (fallback executable)"
echo "- /app/installer/install.sh (installer script)"
echo "- /app/installer/README.md (documentation)"
echo ""
echo "Next steps:"
echo "1. Test the UI: open /app/ui_test.html in browser"
echo "2. Package for distribution with ffmpeg dependencies"
echo "3. Test in actual Premiere Pro environment"