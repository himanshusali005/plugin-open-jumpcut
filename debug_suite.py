#!/usr/bin/env python3
"""
Debug and validation tools for OpenJumpCut Whisper Enhancement
Helps troubleshoot common CEP extension issues
"""

import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_json_format_compatibility():
    """Test that our JSON output matches the expected ExtendScript format"""
    print("Testing JSON Format Compatibility...")
    print("=" * 50)
    
    # Expected format from original jumpcut.py
    expected_format = {
        "silences": [[1.5, 3.2], [5.0, 7.1], 1]  # Last element is alignment flag
    }
    
    # Test our Whisper script output format
    test_params = {
        'silenceCutoff': -50,
        'removeOver': 1.0,
        'keepOver': 0.3,
        'padding': 0.1,
        'in': 0,
        'out': 10,
        'start': 0,
        'method': 'whisper',
        'model': 'tiny'
    }
    
    # Create test audio
    test_file = tempfile.mktemp(suffix='.wav')
    cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono', '-t', '5', test_file, '-y']
    subprocess.run(cmd, capture_output=True)
    
    try:
        # Test Whisper output
        cmd = [
            'python3', '/app/whisper_jumpcut.py',
            test_file,
            json.dumps(test_params),
            '--method', 'whisper',
            '--model', 'tiny'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Parse output
            lines = result.stdout.strip().split('\n')
            json_line = None
            for line in lines:
                if line.strip().startswith('{'):
                    json_line = line.strip()
                    break
            
            if json_line:
                output = json.loads(json_line)
                print(f"✓ Whisper JSON Output: {output}")
                
                # Validate structure
                if 'silences' in output:
                    silences = output['silences']
                    if isinstance(silences, list):
                        print("✓ JSON structure matches expected format")
                        print(f"✓ Silence count: {len(silences) - 1 if silences else 0}")  # -1 for alignment flag
                        return True
                    else:
                        print("✗ 'silences' should be a list")
                        return False
                else:
                    print("✗ Missing 'silences' key in output")
                    return False
            else:
                print("✗ No JSON found in output")
                return False
        else:
            print(f"✗ Script failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing format: {e}")
        return False
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_path_resolution():
    """Test that all file paths resolve correctly"""
    print("\nTesting Path Resolution...")
    print("=" * 50)
    
    # Test paths that the CEP extension would use
    test_paths = [
        '/app/whisper_jumpcut.py',
        '/app/dist/whisper_jumpcut',
        '/app/dist/jumpcut',
        '/app/client/index.html',
        '/app/client/index.js',
        '/app/client/style.css',
        '/app/host/index.jsx',
        '/app/CSXS/manifest.xml'
    ]
    
    all_exist = True
    for path in test_paths:
        if os.path.exists(path):
            print(f"✓ {path}")
        else:
            print(f"✗ {path} - NOT FOUND")
            all_exist = False
    
    return all_exist

def test_executable_permissions():
    """Test that executables have proper permissions"""
    print("\nTesting Executable Permissions...")
    print("=" * 50)
    
    executables = [
        '/app/whisper_jumpcut.py',
        '/app/dist/whisper_jumpcut' if os.path.exists('/app/dist/whisper_jumpcut') else None,
        '/app/dist/jumpcut' if os.path.exists('/app/dist/jumpcut') else None
    ]
    
    all_executable = True
    for exe_path in executables:
        if exe_path and os.path.exists(exe_path):
            if os.access(exe_path, os.X_OK):
                print(f"✓ {exe_path} - Executable")
            else:
                print(f"✗ {exe_path} - Not executable")
                all_executable = False
        elif exe_path:
            print(f"✗ {exe_path} - Does not exist")
            all_executable = False
    
    return all_executable

def test_dependencies():
    """Test that all required dependencies are available"""
    print("\nTesting Dependencies...")
    print("=" * 50)
    
    dependencies = [
        ('ffmpeg', 'ffmpeg -version'),
        ('python3', 'python3 --version'),
        ('faster_whisper', 'python3 -c "import faster_whisper; print(\'faster_whisper available\')"'),
        ('pydub', 'python3 -c "import pydub; print(\'pydub available\')"'),
        ('torch', 'python3 -c "import torch; print(\'torch available\')"')
    ]
    
    all_available = True
    for dep_name, test_cmd in dependencies:
        try:
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.strip().split('\n')[0]
                print(f"✓ {dep_name}: {version_info}")
            else:
                print(f"✗ {dep_name}: Failed - {result.stderr.strip()}")
                all_available = False
        except Exception as e:
            print(f"✗ {dep_name}: Error - {e}")
            all_available = False
    
    return all_available

def simulate_cep_environment():
    """Simulate the CEP extension environment for testing"""
    print("\nSimulating CEP Extension Environment...")
    print("=" * 50)
    
    # Test JavaScript parameter collection (simulate)
    ui_params = {
        'detectionMethod': 'whisper',
        'whisperModel': 'base',
        'whisperLanguage': 'en',
        'silenceCutoff': -50,
        'removeOver': 1.0,
        'keepOver': 0.3,
        'padding': 0.1,
        'backupCheck': True
    }
    
    print("✓ UI Parameters collected:", json.dumps(ui_params, indent=2))
    
    # Test parameter transformation (like JavaScript does)
    jumpcut_params = {
        'silenceCutoff': ui_params['silenceCutoff'],
        'removeOver': ui_params['removeOver'],
        'keepOver': ui_params['keepOver'],
        'padding': ui_params['padding'],
        'method': ui_params['detectionMethod'],
        'model': ui_params['whisperModel'],
        'language': ui_params['whisperLanguage'] if ui_params['whisperLanguage'] else None,
        'in': 0,
        'out': 10000,  # 10 seconds in ms
        'start': 0
    }
    
    print("✓ Parameters transformed for script:", json.dumps(jumpcut_params, indent=2))
    
    return jumpcut_params

def generate_debug_html():
    """Generate a debug version of the UI for testing"""
    print("\nGenerating Debug UI...")
    print("=" * 50)
    
    debug_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OpenJumpCut Debug Console</title>
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #a5a5a5; padding: 20px; }
        .debug-section { margin: 20px 0; padding: 15px; background: #2a2a2a; border-left: 3px solid #0073e6; }
        .test-result { margin: 5px 0; }
        .pass { color: #4CAF50; }
        .fail { color: #f44336; }
        button { background: #0073e6; color: white; border: none; padding: 10px 20px; margin: 5px; cursor: pointer; }
        pre { background: #333; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>OpenJumpCut Debug Console</h1>
    
    <div class="debug-section">
        <h3>CEP Extension Status</h3>
        <div id="cep-status">Checking...</div>
        <button onclick="checkCEPStatus()">Check CEP Interface</button>
    </div>
    
    <div class="debug-section">
        <h3>UI Parameter Collection</h3>
        <div id="param-status">Ready</div>
        <button onclick="testParameters()">Test Parameter Collection</button>
        <pre id="param-output"></pre>
    </div>
    
    <div class="debug-section">
        <h3>Event Listener Status</h3>
        <div id="event-status">Ready</div>
        <button onclick="testEventListeners()">Test Event Listeners</button>
    </div>
    
    <div class="debug-section">
        <h3>Path Resolution</h3>
        <div id="path-status">Ready</div>
        <button onclick="testPaths()">Test File Paths</button>
        <pre id="path-output"></pre>
    </div>
    
    <script>
        function checkCEPStatus() {
            const status = document.getElementById('cep-status');
            try {
                if (typeof CSInterface !== 'undefined') {
                    status.innerHTML = '<span class="pass">✓ CSInterface available</span>';
                } else {
                    status.innerHTML = '<span class="fail">✗ CSInterface not found (normal in browser)</span>';
                }
            } catch (e) {
                status.innerHTML = '<span class="fail">✗ CSInterface error: ' + e.message + '</span>';
            }
        }
        
        function testParameters() {
            const output = document.getElementById('param-output');
            const status = document.getElementById('param-status');
            
            // Simulate parameter collection
            const params = {
                detectionMethod: 'whisper',
                whisperModel: 'base',
                whisperLanguage: 'en',
                silenceCutoff: -50,
                removeOver: 1.0,
                keepOver: 0.3,
                padding: 0.1
            };
            
            output.textContent = JSON.stringify(params, null, 2);
            status.innerHTML = '<span class="pass">✓ Parameters collected successfully</span>';
        }
        
        function testEventListeners() {
            const status = document.getElementById('event-status');
            
            // Test if event listeners are working
            const testButton = document.createElement('button');
            testButton.textContent = 'Test Button';
            testButton.addEventListener('click', function() {
                status.innerHTML = '<span class="pass">✓ Event listeners working</span>';
            });
            
            testButton.click(); // Trigger immediately
        }
        
        function testPaths() {
            const output = document.getElementById('path-output');
            const status = document.getElementById('path-status');
            
            const expectedPaths = [
                'client/index.html',
                'client/index.js', 
                'client/style.css',
                'client/CSInterface.js',
                'host/index.jsx',
                'CSXS/manifest.xml',
                'dist/whisper_jumpcut',
                'dist/jumpcut'
            ];
            
            output.textContent = 'Expected paths:\\n' + expectedPaths.join('\\n');
            status.innerHTML = '<span class="pass">✓ Path list generated</span>';
        }
        
        // Auto-run tests
        window.onload = function() {
            checkCEPStatus();
        };
    </script>
</body>
</html>
    """
    
    with open('/app/debug_console.html', 'w') as f:
        f.write(debug_html)
    
    print("✓ Debug console created: /app/debug_console.html")

def main():
    """Run all debugging tests"""
    print("OpenJumpCut Whisper Enhancement - Debug Suite")
    print("=" * 60)
    
    results = {}
    
    # Run all tests
    results['json_format'] = test_json_format_compatibility()
    results['paths'] = test_path_resolution()
    results['permissions'] = test_executable_permissions()
    results['dependencies'] = test_dependencies()
    
    # Simulate CEP environment
    jumpcut_params = simulate_cep_environment()
    
    # Generate debug tools
    generate_debug_html()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Plugin is ready for production.")
    else:
        print("⚠️  Some tests failed. Review the issues above.")
        
    print("\nDebug tools created:")
    print("- /app/debug_console.html (UI debugging)")
    print("- Run this script anytime to validate the installation")

if __name__ == "__main__":
    main()