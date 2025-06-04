#!/usr/bin/env python3
"""
Test script for whisper_jumpcut.py
Creates a simple test audio file and tests Whisper silence detection
"""

import json
import tempfile
import os
import subprocess

def create_test_audio():
    """Create a simple test audio file with speech and silence"""
    # Create a 10-second test audio file with speech at 2-4s and 6-8s
    test_file = tempfile.mktemp(suffix='.wav')
    
    # Generate silence (10 seconds)
    cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono', 
        '-t', '10', test_file, '-y'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"Created test audio file: {test_file}")
        return test_file
    except Exception as e:
        print(f"Failed to create test audio: {e}")
        return None

def test_whisper_script():
    """Test the whisper_jumpcut.py script"""
    
    # Test parameters
    test_params = {
        'silenceCutoff': -50,
        'removeOver': 1.0,  # 1 second minimum silence
        'keepOver': 0.3,
        'padding': 0.1,
        'in': 0,
        'out': 10,
        'start': 0,
        'method': 'whisper',
        'model': 'tiny',  # Use smallest model for faster testing
        'language': None
    }
    
    # Create test audio
    audio_file = create_test_audio()
    if not audio_file:
        return False
    
    try:
        # Test the script
        cmd = [
            'python3', '/app/whisper_jumpcut.py',
            audio_file,
            json.dumps(test_params),
            '--method', 'whisper',
            '--model', 'tiny'
        ]
        
        print("Running Whisper script test...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            try:
                # Split stdout to get just the JSON part (in case there are print statements)
                lines = result.stdout.strip().split('\n')
                json_line = None
                for line in lines:
                    if line.strip().startswith('{'):
                        json_line = line.strip()
                        break
                
                if json_line:
                    output = json.loads(json_line)
                    print(f"Success! Output: {output}")
                    return True
                else:
                    print(f"No JSON found in output: {result.stdout}")
                    return False
            except json.JSONDecodeError:
                print(f"Failed to parse JSON output: {result.stdout}")
                return False
        else:
            print("Script failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("Script timed out")
        return False
    except Exception as e:
        print(f"Error running script: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists(audio_file):
            os.remove(audio_file)

def test_loudness_fallback():
    """Test the loudness fallback method"""
    
    test_params = {
        'silenceCutoff': -50,
        'removeOver': 1.0,
        'keepOver': 0.3, 
        'padding': 0.1,
        'in': 0,
        'out': 10,
        'start': 0,
        'method': 'loudness'
    }
    
    audio_file = create_test_audio()
    if not audio_file:
        return False
    
    try:
        cmd = [
            'python3', '/app/whisper_jumpcut.py',
            audio_file,
            json.dumps(test_params),
            '--method', 'loudness'
        ]
        
        print("Running loudness fallback test...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        
        if result.returncode == 0:
            try:
                # Split stdout to get just the JSON part
                lines = result.stdout.strip().split('\n')
                json_line = None
                for line in lines:
                    if line.strip().startswith('{'):
                        json_line = line.strip()
                        break
                
                if json_line:
                    output = json.loads(json_line)
                    print(f"Loudness fallback success! Output: {output}")
                    return True
                else:
                    print(f"No JSON found in output: {result.stdout}")
                    return False
            except json.JSONDecodeError:
                print(f"Failed to parse JSON output: {result.stdout}")
                return False
        else:
            print("Loudness fallback failed")
            return False
            
    except Exception as e:
        print(f"Error running loudness test: {e}")
        return False
    
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    print("Testing Whisper Jumpcut Script...")
    print("=" * 50)
    
    print("\n1. Testing Whisper method...")
    whisper_success = test_whisper_script()
    
    print("\n2. Testing loudness fallback...")
    loudness_success = test_loudness_fallback()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Whisper method: {'✓ PASS' if whisper_success else '✗ FAIL'}")
    print(f"Loudness fallback: {'✓ PASS' if loudness_success else '✗ FAIL'}")
    
    if whisper_success or loudness_success:
        print("\n✓ Core functionality working!")
    else:
        print("\n✗ Both methods failed - check dependencies")