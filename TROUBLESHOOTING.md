# OpenJumpCut Whisper Enhancement - Troubleshooting Guide

## 🔧 Common Issues & Solutions

### 1. UI Button Not Responding

#### **Symptoms:**
- Click "Run Jump Cut" but nothing happens
- No progress indicators appear
- No error messages

#### **Diagnosis Steps:**
```javascript
// Open browser console (F12) and check for errors
console.log("Testing button click");

// Test if CSInterface is available
if (typeof CSInterface !== 'undefined') {
    console.log("✓ CSInterface loaded");
} else {
    console.log("✗ CSInterface missing");
}
```

#### **Solutions:**
1. **Check Event Listeners:**
   ```javascript
   // In index.js, ensure button has onclick handler
   document.getElementById('jumpcutbutton').addEventListener('click', runJumpCut);
   ```

2. **Verify CSInterface Loading:**
   ```html
   <!-- In index.html, ensure CSInterface.js loads first -->
   <script type="text/javascript" src="CSInterface.js"></script>
   <script type="text/javascript" src="index.js"></script>
   ```

3. **Debug with Console:**
   - Use our debug console: `/app/debug_console.html`
   - Check browser console for JavaScript errors
   - Enable CEP debugging: `--enable-blink-debug`

### 2. Whisper Not Executing Automatically

#### **Symptoms:**
- Plugin runs but falls back to loudness detection
- "faster-whisper not available" errors
- Manual terminal execution required

#### **Diagnosis Steps:**
```bash
# Test Whisper availability
python3 -c "import faster_whisper; print('Whisper available')"

# Test executable path resolution
ls -la /app/dist/whisper_jumpcut

# Test execution permissions
/app/dist/whisper_jumpcut --help
```

#### **Solutions:**
1. **Check Dependencies:**
   ```bash
   # Install missing dependencies
   pip install faster-whisper torch numpy
   
   # Verify ffmpeg is available
   ffmpeg -version
   ```

2. **Fix Path Resolution:**
   ```javascript
   // In index.js, use absolute paths
   var WHISPER_EXE_PATH = path.join(
       path.normalize(csInterface.getSystemPath(SystemPath.EXTENSION)), 
       "/dist/whisper_jumpcut"
   );
   ```

3. **Ensure Executable Permissions:**
   ```bash
   chmod +x /app/dist/whisper_jumpcut
   chmod +x /app/whisper_jumpcut.py
   ```

### 3. Cuts Not Being Applied After Detection

#### **Symptoms:**
- Silence detection works (shows results)
- Timeline remains unchanged
- "Success" message but no cuts visible

#### **Diagnosis Steps:**
```javascript
// Check if silences are detected correctly
console.log("Detected silences:", silences);

// Verify ExtendScript communication
csInterface.evalScript("alert('ExtendScript working')", (result) => {
    console.log("ExtendScript result:", result);
});
```

#### **Solutions:**
1. **Verify JSON Format:**
   ```python
   # Ensure whisper_jumpcut.py outputs correct format
   result = {"silences": [[start, end], [start, end], alignment_flag]}
   print(json.dumps(result))
   ```

2. **Check ExtendScript Integration:**
   ```javascript
   // In runJumpCut(), log the data being sent
   console.log("Sending to ExtendScript:", silences);
   
   csInterface.evalScript(`jumpCutActiveSequence("${silences}", "${backup}")`, 
       (result) => {
           console.log("ExtendScript returned:", result);
       }
   );
   ```

3. **Test with Sample Data:**
   ```javascript
   // Test ExtendScript with known good data
   var testSilences = '[[1.5, 3.0], [5.0, 7.0], 1]';
   csInterface.evalScript(`jumpCutActiveSequence("${testSilences}", "false")`);
   ```

### 4. Cross-Platform Path Issues

#### **Symptoms:**
- Works on one OS but not another
- "File not found" errors
- Permission denied errors

#### **Solutions:**
1. **Normalize Paths:**
   ```javascript
   // Use path.normalize() for all file paths
   exe_path = path.normalize(exe_path);
   media_path = path.normalize(media_path);
   ```

2. **Handle OS Differences:**
   ```javascript
   // Detect OS and use appropriate executable
   var EXE_NAME = "";
   if (operating_system == "WIN") {
       EXE_NAME = "whisper_jumpcut.exe";
   } else {
       EXE_NAME = "whisper_jumpcut";
   }
   ```

3. **Set Working Directory:**
   ```javascript
   // Ensure correct working directory
   let cwd = path.dirname(exe_path);
   command_prompt = child_process.spawn(exe_path, args, { cwd });
   ```

## 🛠️ Debugging Tools

### Debug Console
Open `/app/debug_console.html` to test:
- CEP Interface availability
- Parameter collection
- Event listeners
- Path resolution

### Command Line Testing
```bash
# Run the debug suite
python3 /app/debug_suite.py

# Test Whisper script directly
python3 /app/whisper_jumpcut.py test.wav '{"method":"whisper","model":"tiny"}'

# Test original script
python3 /app/jumpcut.py test.wav '{"silenceCutoff":-50}'
```

### JavaScript Console Testing
```javascript
// Test parameter collection
var params = getJumpcutParams();
console.log("Parameters:", params);

// Test progress functions
showProgress(true, "Testing...");
updateProgress(50, "Half way...");
showProgress(false);

// Test OS detection
getOS().then(os => console.log("Detected OS:", os));
```

## 📋 Installation Verification Checklist

### ✅ Files Present
- [ ] `/app/whisper_jumpcut.py` (main script)
- [ ] `/app/dist/whisper_jumpcut` (compiled executable)
- [ ] `/app/client/index.html` (enhanced UI)
- [ ] `/app/client/index.js` (updated JavaScript)
- [ ] `/app/client/style.css` (modern styling)
- [ ] `/app/host/index.jsx` (ExtendScript)
- [ ] `/app/CSXS/manifest.xml` (CEP manifest)

### ✅ Dependencies Available
- [ ] `ffmpeg` command accessible
- [ ] `python3` with required packages
- [ ] `faster-whisper` library installed
- [ ] CEP extension enabled in Premiere Pro

### ✅ Permissions Correct
- [ ] Executable permissions on scripts
- [ ] Read permissions on UI files
- [ ] Write permissions for temporary files

### ✅ Functionality Working
- [ ] UI loads without JavaScript errors
- [ ] Parameter collection works
- [ ] Progress indicators display
- [ ] Whisper detection executes
- [ ] ExtendScript communication works
- [ ] Timeline cuts are applied

## 🚀 Performance Optimization

### Whisper Model Selection
- **Tiny**: Ultra-fast, good for real-time editing
- **Base**: Best balance for most use cases
- **Small**: Better accuracy for professional work
- **Medium/Large**: Maximum accuracy for critical projects

### Processing Tips
- Use lower sample rates (16kHz) for Whisper
- Process shorter segments for faster results
- Enable voice activity detection (VAD)
- Consider GPU acceleration for large models

## 📞 Getting Help

### Error Reporting
When reporting issues, include:
1. Adobe Premiere Pro version
2. Operating system and version
3. Error messages from browser console
4. Output from debug suite: `python3 debug_suite.py`
5. Steps to reproduce the issue

### Useful Log Locations
- CEP Debug Console: Remote debugging tools
- Browser Console: F12 developer tools
- Whisper Logs: `/app/whisper_jumpcut.log`
- Build Logs: `/app/build.log`

Remember: Most issues stem from path resolution, permissions, or missing dependencies. The debug tools provided will help identify and resolve these quickly!