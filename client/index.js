const fs = require('fs');
const path = require('path');
const child_process = require('child_process');

let csInterface = new CSInterface();
let operating_system = getOS();
initFrontend();
init();

// Name of executable file varies by OS - now supports both original and Whisper versions
var EXE_NAME = "";
var WHISPER_EXE_NAME = "";
if (operating_system == "WIN")
{
  EXE_NAME = "jumpcut.exe";
  WHISPER_EXE_NAME = "whisper_jumpcut.exe";
} else {
  EXE_NAME = "jumpcut";
  WHISPER_EXE_NAME = "whisper_jumpcut";
}
var EXE_PATH = path.join(path.normalize(csInterface.getSystemPath(SystemPath.EXTENSION)), "/dist/" + EXE_NAME);
var WHISPER_EXE_PATH = path.join(path.normalize(csInterface.getSystemPath(SystemPath.EXTENSION)), "/dist/" + WHISPER_EXE_NAME);

async function init() {
  operating_system = await getOS();
  setupDetectionMethodToggle();
}

function setupDetectionMethodToggle() {
  const detectionMethod = document.getElementById('detectionMethod');
  const whisperOptions = document.getElementById('whisperOptions');
  const loudnessOptions = document.getElementById('loudnessOptions');
  const cutoffNote = document.getElementById('cutoffNote');
  
  function toggleOptions() {
    if (detectionMethod.value === 'whisper') {
      whisperOptions.style.display = 'block';
      cutoffNote.style.display = 'inline';
    } else {
      whisperOptions.style.display = 'none';  
      cutoffNote.style.display = 'none';
    }
  }
  
  detectionMethod.addEventListener('change', toggleOptions);
  toggleOptions(); // Set initial state
}

function showProgress(show = true, text = "Processing...") {
  const progressSection = document.getElementById('progressSection');
  const progressText = document.getElementById('progressText');
  const button = document.getElementById('jumpcutbutton');
  
  if (show) {
    progressSection.style.display = 'block';
    progressText.textContent = text;
    button.disabled = true;
    button.textContent = 'Processing...';
  } else {
    progressSection.style.display = 'none';
    button.disabled = false;
    button.textContent = 'Run Jump Cut';
  }
}

function updateProgress(percentage, text) {
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  
  progressBar.style.width = percentage + '%';
  if (text) {
    progressText.textContent = text;
  }
}

async function runJumpCut() {
  showProgress(true, "Checking prerequisites...");
  
  var isValid = await checkTimelineValidity() // Check that current prerequisites for jumpcuts are met.
  if (isValid === "true")
  {
    updateProgress(20, "Getting media path...");
    let mediaPath = await asyncGetMediaPath();

    updateProgress(30, "Preparing parameters...");
    let jumpcutParams = getJumpcutParams();
    let inoutpoints = await asyncGetInOutStartPoints();
    inoutpoints = JSON.parse(inoutpoints);
    jumpcutParams = JSON.parse(jumpcutParams);
    jumpcutParams["in"] = inoutpoints["in"];
    jumpcutParams["out"] = inoutpoints["out"];
    jumpcutParams["start"] = inoutpoints["start"];
    jumpcutParams = JSON.stringify(jumpcutParams);

    let jumpcutData = "";
    
    // Determine which executable to use
    const detectionMethod = document.getElementById('detectionMethod').value;
    const exePath = detectionMethod === 'whisper' ? WHISPER_EXE_PATH : EXE_PATH;
    const progressText = detectionMethod === 'whisper' ? "Running AI speech detection..." : "Running loudness detection...";
    
    updateProgress(40, progressText);
  
    // Run the Python script to calculate jump cut locations.
    try {
      if (detectionMethod === 'whisper') {
        jumpcutData = await asyncCallWhisperJumpcut(exePath, mediaPath, jumpcutParams);
      } else {
        jumpcutData = await asyncCallPythonJumpcut(exePath, mediaPath, jumpcutParams);
      }
      updateProgress(80, "Analysis complete!");
    } catch (error) {
      showProgress(false);
      alert("Failure executing script: " + error);
      return;
    }

    updateProgress(85, "Processing results...");
    // Prepare data to send to ExtendScript.
    let dataJSON = ""
    try {
      // Parse just the JSON part if there are multiple lines
      const lines = jumpcutData.trim().split('\n');
      let jsonLine = null;
      for (const line of lines) {
        if (line.trim().startsWith('{')) {
          jsonLine = line.trim();
          break;
        }
      }
      dataJSON = JSON.parse(jsonLine || jumpcutData);
    } catch (error) {
      showProgress(false);
      alert("Error parsing results: " + error);
      return;
    }
  
    // If no silences were returned, alert the user and exit.
    if (!dataJSON['silences'] || dataJSON['silences'].length === 0) { 
      showProgress(false);
      alert("No silences detected.");
      return;
    }
  
    updateProgress(90, "Applying cuts to timeline...");
    let silences = JSON.stringify(dataJSON['silences']);
  
    let checkBox = document.getElementById("backupCheck");
    let checked = checkBox.checked;

    try {
      await runPremiereJumpCut(silences, checked);
      updateProgress(100, "Complete!");
      setTimeout(() => showProgress(false), 1000);
      alert("Success! Applied " + (dataJSON['silences'].length - 1) + " cuts.");
    } catch (error) {
      showProgress(false);
      alert("Failure executing jump cuts in Premiere: " + error);
    }
  } else {
    showProgress(false);
    alert ("Timeline prerequisites not met. There must be a single linked video/audio pair on tracks V1 and A1.");
  }
}

async function runPremiereJumpCut(silences, backup) {
  return new Promise((resolve, reject) => {
    csInterface.evalScript(`jumpCutActiveSequence("${silences}", "${backup}")`, (result) => {
      if (result) {
        resolve(result);
      } else {
        reject("Error executing jump cuts.")
      }
    });
  });
}

// Gets the absolute filepath of the requested media.
async function asyncGetMediaPath() {
  return new Promise((resolve, reject) => {
    csInterface.evalScript("getMediaPath()", (result) => {
      if (result) {
        resolve(result);
      } else {
        reject("Error getting media path.");
      }
    });
  });
}

async function checkTimelineValidity() {
  return new Promise((resolve, reject) => {
    csInterface.evalScript("checkOneLinkedClipPair()", (result) => {
      resolve(result);
    });
  });
}

async function asyncGetInOutStartPoints()
{
  return new Promise((resolve, reject) => {
    csInterface.evalScript(`getInOutStartPoints()`, (result) => {
      if (result) {
        resolve(result);
      } else {
        reject("Error getting in and out points.");
      }
    });
  });
}

// Enhanced Whisper jumpcut caller with progress feedback
async function asyncCallWhisperJumpcut(exe_path, media_path, jumpcutParams) {
  return new Promise((resolve, reject) => {
    let command_prompt;
  
    // Normalize paths
    exe_path = path.normalize(exe_path);
    media_path = path.normalize(media_path);
    let cwd = path.dirname(exe_path);

    // Parse parameters to add Whisper-specific options
    let params = JSON.parse(jumpcutParams);
    const whisperModel = document.getElementById('whisperModel').value;
    const whisperLanguage = document.getElementById('whisperLanguage').value;
    
    params.method = 'whisper';
    params.model = whisperModel;
    if (whisperLanguage) {
      params.language = whisperLanguage;
    }
    
    const enhancedParams = JSON.stringify(params);

    try {
      // Call the Whisper jumpcut script
      command_prompt = child_process.spawn(exe_path, [
        media_path, 
        enhancedParams,
        '--method', 'whisper',
        '--model', whisperModel
      ], { cwd });
    } catch (error) {
      reject(error);
      return;
    }

    let outputData = "";
    let progressCounter = 40;

    command_prompt.stdout.on('data', function (data) {
      const output = data.toString();
      outputData += output;
      
      // Update progress based on output keywords
      if (output.includes('Loading Whisper model')) {
        updateProgress(50, "Loading AI model...");
      } else if (output.includes('Transcribing audio')) {
        updateProgress(60, "Transcribing speech...");
      } else if (output.includes('Detected') && output.includes('silence')) {
        updateProgress(75, "Detecting silence gaps...");
      }
    });
  
    command_prompt.stderr.on('data', function (data) {
      reject(data.toString());
    });
  
    command_prompt.on('exit', function (code) {
      if (code === 0) {
        resolve(outputData);
      } else {
        reject(`Process exited with code ${code}`);
      }
    });

  });
}

// Original jumpcut caller (for loudness-based detection)
async function asyncCallPythonJumpcut(exe_path, media_path, jumpcutParams) {
  return new Promise((resolve, reject) => {
    let command_prompt;
  
    // Normalize paths
    exe_path = path.normalize(exe_path);
    media_path = path.normalize(media_path);
    let cwd = path.dirname(exe_path);

    try {
      // Call the Python jumpcut calculator
      command_prompt = child_process.spawn(exe_path, [media_path, jumpcutParams], { cwd });
    } catch (error) {
      reject(error);
      return;
    }

    let outputData = "";

    command_prompt.stdout.on('data', function (data) {
      outputData += data.toString();
      updateProgress(60, "Analyzing audio levels...");
    });
  
    command_prompt.stderr.on('data', function (data) {
      reject(data.toString());
    });
  
    command_prompt.on('exit', function (code) {
      if (code === 0) {
        resolve(outputData);
      } else {
        reject(`Process exited with code ${code}`);
      }
    });

  });
}

async function getOS() {
  let os = null;
  if (navigator.userAgentData) {
      const brands = await navigator.userAgentData.getHighEntropyValues(["platform"]);
      if (brands.platform.includes('macOS')) {
          os = "MAC";
      } else if (brands.platform.includes('Windows')) {
          os = "WIN";
      }
  } else {
      // Fallback for browsers that do not support userAgentData
      var platform = window.navigator.platform;
      var macosPlatforms = ['Macintosh', 'MacIntel', 'MacPPC', 'Mac68K'];
      var windowsPlatforms = ['Win32', 'Win64', 'Windows', 'WinCE'];

      if (macosPlatforms.indexOf(platform) != -1) {
          os = "MAC";
      } else if (windowsPlatforms.indexOf(platform) != -1) {
          os = "WIN";
      }
  }
  return os;
}

// Frontend functions
function initFrontend() {

  document.addEventListener('DOMContentLoaded', () => {
    let sliderIds = ['silenceCutoff', 'removeOver', 'keepOver', 'padding'];
  
    sliderIds.forEach(function(id) {
      let slider = document.getElementById(id);
      let numberInput = slider.nextElementSibling; // Assumes the number input is right after the slider
  
      slider.oninput = function() {
          numberInput.value = slider.value;
      };
  
      numberInput.oninput = function() {
          slider.value = numberInput.value;
      };
    });
  }); 

}

function getJumpcutParams() {
  let sliderIds = ['silenceCutoff', 'removeOver', 'keepOver', 'padding'];
  let jumpcutParams = {};
  
  sliderIds.forEach(function(id) {
    let slider = document.getElementById(id);
    let numberInput = slider.nextElementSibling;
    jumpcutParams[id] = numberInput.value;
  });

  // Add detection method and Whisper parameters
  const detectionMethod = document.getElementById('detectionMethod').value;
  jumpcutParams['method'] = detectionMethod;
  
  if (detectionMethod === 'whisper') {
    jumpcutParams['model'] = document.getElementById('whisperModel').value;
    const language = document.getElementById('whisperLanguage').value;
    if (language) {
      jumpcutParams['language'] = language;
    }
  }

  return JSON.stringify(jumpcutParams);
}