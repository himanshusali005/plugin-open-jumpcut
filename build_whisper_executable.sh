#!/bin/bash
# Build script for creating Whisper-enhanced jumpcut executable

echo "Building Whisper-enhanced jumpcut executable..."

# Install pyinstaller if not present
python3 -m pip install pyinstaller

# Create executable with all dependencies
echo "Creating executable with PyInstaller..."
python3 -m PyInstaller \
    --onefile \
    --name whisper_jumpcut \
    --hidden-import=faster_whisper \
    --hidden-import=numpy \
    --hidden-import=torch \
    --hidden-import=pydub \
    --collect-data faster_whisper \
    --collect-data tiktoken \
    --paths /usr/local/lib/python3.*/site-packages \
    /app/whisper_jumpcut.py

# Copy to dist directory
echo "Copying executable to dist directory..."
mkdir -p /app/dist
cp /app/dist/whisper_jumpcut /app/dist/whisper_jumpcut

# Also copy original jumpcut for fallback
if [ -f "/app/dist/jumpcut" ]; then
    echo "Original jumpcut executable found."
else
    echo "Creating original jumpcut executable as well..."
    python3 -m PyInstaller \
        --onefile \
        --name jumpcut \
        --hidden-import=pydub \
        /app/jumpcut.py
    cp /app/dist/jumpcut /app/dist/jumpcut
fi

echo "Build complete!"
echo "Executables available:"
echo "  - /app/dist/whisper_jumpcut (Whisper-enhanced)"
echo "  - /app/dist/jumpcut (Original loudness-based)"

# Test the executables
echo "Testing executables..."
/app/dist/whisper_jumpcut --help || echo "Whisper executable test failed"
/app/dist/jumpcut --help || echo "Original executable test failed"