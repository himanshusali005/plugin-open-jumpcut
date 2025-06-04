#!/usr/bin/env python3
"""
Whisper-based Jumpcut Script for Premiere Pro Extension
Replaces loudness-based silence detection with AI speech detection using faster-whisper
"""

import argparse
import os
import json
import sys
import logging
import tempfile
from pathlib import Path

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s (Line: %(lineno)d)'
logging.basicConfig(filename='whisper_jumpcut.log', format=log_format)
logging.getLogger().setLevel(logging.DEBUG)

def detect_silences_with_whisper(audio_path, model_size="base", language=None, detection_method="whisper", **kwargs):
    """
    Detect silences using Whisper speech detection or fallback to loudness-based detection
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (None for auto-detection)
        detection_method: "whisper" or "loudness"
        **kwargs: Additional parameters (cutoff, padding, etc.)
    
    Returns:
        List of silence segments [[start, end], [start, end], ...]
    """
    
    if detection_method == "loudness":
        return detect_silences_loudness(audio_path, **kwargs)
    
    try:
        # Import faster-whisper
        from faster_whisper import WhisperModel
        
        # Initialize Whisper model
        print("Loading Whisper model...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        # Transcribe audio
        print("Transcribing audio...")
        segments, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True  # Voice Activity Detection
        )
        
        # Convert segments to list for processing
        segments = list(segments)
        
        if not segments:
            logging.warning("No speech detected in audio file")
            return []
        
        # Extract silence gaps between speech segments
        silences = []
        
        # Parameters
        min_silence_length = kwargs.get('removeOver', 1000) / 1000.0  # Convert ms to seconds
        padding = kwargs.get('padding', 500) / 1000.0
        
        # Get audio duration (needed for end silence detection)
        import subprocess
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
            ], capture_output=True, text=True, check=True)
            audio_duration = float(result.stdout.strip())
        except Exception as e:
            logging.error(f"Could not get audio duration: {e}")
            audio_duration = segments[-1].end + 10  # Fallback estimate
        
        # Find silence gaps between speech segments
        for i in range(len(segments)):
            current_segment = segments[i]
            
            if i == 0:
                # Check for silence at the beginning
                if current_segment.start > min_silence_length:
                    silence_start = 0
                    silence_end = current_segment.start
                    if silence_end - silence_start >= min_silence_length:
                        silences.append([silence_start, silence_end])
            
            if i < len(segments) - 1:
                # Check for silence between segments
                next_segment = segments[i + 1]
                gap_start = current_segment.end
                gap_end = next_segment.start
                gap_duration = gap_end - gap_start
                
                if gap_duration >= min_silence_length:
                    silences.append([gap_start, gap_end])
            else:
                # Check for silence at the end
                if audio_duration - current_segment.end > min_silence_length:
                    silence_start = current_segment.end
                    silence_end = audio_duration
                    if silence_end - silence_start >= min_silence_length:
                        silences.append([silence_start, silence_end])
        
        # Apply padding (same logic as original)
        audio_length_ms = audio_duration * 1000
        to_remove = []
        
        for i in range(len(silences)):
            # Convert to ms for padding calculation
            start_ms = silences[i][0] * 1000
            end_ms = silences[i][1] * 1000
            
            # Check that this silence is not at the beginning of the file
            if start_ms > 0:
                start_ms = start_ms + (padding * 1000)
            
            # Check that this silence is not at the end of the file
            if end_ms < audio_length_ms:
                end_ms = end_ms - (padding * 1000)
            
            if end_ms <= start_ms:
                to_remove.append(i)
            else:
                # Convert back to seconds
                silences[i] = [start_ms / 1000.0, end_ms / 1000.0]
        
        # Remove silences that were padded out of existence
        silences = [s for idx, s in enumerate(silences) if idx not in to_remove]
        
        print(f"Detected {len(silences)} silence segments using Whisper")
        return silences
        
    except ImportError:
        logging.error("faster-whisper not available, falling back to loudness detection")
        return detect_silences_loudness(audio_path, **kwargs)
    except Exception as e:
        logging.error(f"Whisper detection failed: {e}")
        return detect_silences_loudness(audio_path, **kwargs)

def detect_silences_loudness(audio_path, **kwargs):
    """
    Fallback loudness-based silence detection (original method)
    """
    try:
        from pydub import AudioSegment, silence
        
        # Parameters
        threshold = int(kwargs.get('silenceCutoff', -50))
        min_silence_length = int(kwargs.get('removeOver', 1000))
        keep_over = int(kwargs.get('keepOver', 300))
        padding = int(kwargs.get('padding', 500))
        
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        
        # Detect silences using amplitude
        silences = silence.detect_silence(
            audio, 
            min_silence_len=min_silence_length, 
            silence_thresh=threshold
        )
        
        # Convert to seconds and apply same processing as original
        silences = [[s[0]/1000.0, s[1]/1000.0] for s in silences]
        
        print(f"Detected {len(silences)} silence segments using loudness")
        return silences
        
    except ImportError as e:
        logging.error(f"Pydub not available: {e}")
        return []
    except Exception as e:
        logging.error(f"Loudness detection failed: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Whisper-based jumpcut silence detection')
    parser.add_argument("path", help="Path to audio/video file")
    parser.add_argument("jumpcutparams", help="JSON string with jumpcut parameters")
    parser.add_argument("--method", default="whisper", choices=["whisper", "loudness"], 
                       help="Detection method")
    parser.add_argument("--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size")
    parser.add_argument("--language", default=None, help="Language code (auto-detect if None)")
    
    args = parser.parse_args()
    
    # Default parameters (same as original)
    jumpcut_params = {
        'silenceCutoff': -80,
        'removeOver': 1000,
        'keepOver': 300,
        'padding': 500,
        'in': None,
        'out': None,
        'start': None,
        'method': 'whisper',
        'model': 'base',
        'language': None
    }
    
    try:
        # Parse input parameters
        if args.jumpcutparams:
            input_params = json.loads(args.jumpcutparams)
            jumpcut_params.update(input_params)
            
            # Convert to ms (except for dB and method/model/language)
            for key, value in jumpcut_params.items():
                if key not in ['silenceCutoff', 'method', 'model', 'language'] and value is not None:
                    jumpcut_params[key] = float(value) * 1000
            
            # Keep dB as-is
            if 'silenceCutoff' in jumpcut_params:
                jumpcut_params['silenceCutoff'] = int(jumpcut_params['silenceCutoff'])
    
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON parameters: {e}")
        print(json.dumps({"error": "Invalid parameters"}))
        return
    
    # Extract clip timing parameters
    in_point = int(jumpcut_params.get('in', 0))
    out_point = int(jumpcut_params.get('out', 0))
    start_point = int(jumpcut_params.get('start', 0))
    
    # Get detection method and Whisper parameters
    detection_method = jumpcut_params.get('method', args.method)
    model_size = jumpcut_params.get('model', args.model)
    language = jumpcut_params.get('language', args.language)
    
    # For Whisper, we need to extract audio if video file
    file_path = args.path
    temp_audio_path = None
    
    try:
        # Check if we need to extract audio
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            # Extract audio using ffmpeg
            temp_audio_path = tempfile.mktemp(suffix='.wav')
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', str(in_point / 1000.0),  # Start time
                '-t', str((out_point - in_point) / 1000.0),  # Duration
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # WAV format
                '-ar', '16000',  # 16kHz sample rate (good for Whisper)
                '-ac', '1',  # Mono
                temp_audio_path,
                '-y'  # Overwrite
            ]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            audio_file = temp_audio_path
        else:
            audio_file = file_path
        
        # Detect silences
        # Filter out parameters that we're passing explicitly
        filtered_params = {k: v for k, v in jumpcut_params.items() 
                          if k not in ['method', 'model', 'language']}
        
        silences = detect_silences_with_whisper(
            audio_file,
            model_size=model_size,
            language=language,
            detection_method=detection_method,
            **filtered_params
        )
        
        # Apply start offset (same as original)
        silences = [[s[0] + start_point/1000.0, s[1] + start_point/1000.0] for s in silences]
        
        # Add flag for clip start alignment (same as original logic)
        if silences and len(silences) > 0:
            if silences[0][0] == start_point/1000.0:
                silences.append(1)
            else:
                silences.append(0)
        else:
            silences.append(0)
        
        # Output in same format as original
        result = {"silences": silences}
        print(json.dumps(result))
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        print(json.dumps({"error": str(e)}))
    
    finally:
        # Clean up temporary audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass

if __name__ == "__main__":
    main()