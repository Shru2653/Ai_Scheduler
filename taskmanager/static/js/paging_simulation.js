const canvas = document.getElementById('pagingCanvas');
const ctx = canvas.getContext('2d');

const graphCanvas = document.getElementById('pagingGraphCanvas');
const graphCtx = graphCanvas.getContext('2d');

let frameCount = 3;
let pageRefs = [];
let frames = [];
let faults = 0;
let algorithm = 'fifo';
let running = false;
let currentStep = 0;
let queue = [];
let lastUsed = new Map();
let history = [];
let animTimeout = null;

function drawFrame(x, y, w, h, text, highlight) {
  ctx.fillStyle = highlight ? '#ffdede' : '#e0f7fa';
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = '#000';
  ctx.strokeRect(x, y, w, h);
  ctx.fillStyle = '#000';
  ctx.font = '16px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x + w / 2, y + h / 2);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function resetSim() {
  running = false;
  currentStep = 0;
  frames = [];
  faults = 0;
  queue = [];
  lastUsed = new Map();
  history = [];
  if (animTimeout) clearTimeout(animTimeout);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawGraphTraversal(step) {
  // Setup
  if (!pageRefs.length) return;
  // Unique pages as nodes
  const uniquePages = Array.from(new Set(pageRefs));
  const nodeCount = uniquePages.length;
  const width = Math.max(600, nodeCount * 80 + 60);
  const height = 180;
  graphCanvas.width = width;
  graphCanvas.height = height;
  graphCtx.clearRect(0, 0, width, height);

  // Node positions (horizontal line)
  const nodePos = {};
  for (let i = 0; i < uniquePages.length; i++) {
    nodePos[uniquePages[i]] = {
      x: 40 + i * 80,
      y: height / 2
    };
  }

  // Draw arrows for reference order
  graphCtx.strokeStyle = '#aaa';
  graphCtx.lineWidth = 2;
  for (let i = 0; i < pageRefs.length - 1; i++) {
    const from = nodePos[pageRefs[i]];
    const to = nodePos[pageRefs[i + 1]];
    if (from && to) {
      graphCtx.beginPath();
      graphCtx.moveTo(from.x, from.y + 20);
      graphCtx.lineTo(to.x, to.y - 20);
      graphCtx.stroke();
      // Arrowhead
      const angle = Math.atan2(to.y - from.y, to.x - from.x);
      const arrowLen = 10;
      graphCtx.beginPath();
      graphCtx.moveTo(to.x, to.y - 20);
      graphCtx.lineTo(to.x - arrowLen * Math.cos(angle - Math.PI / 6), to.y - 20 - arrowLen * Math.sin(angle - Math.PI / 6));
      graphCtx.lineTo(to.x - arrowLen * Math.cos(angle + Math.PI / 6), to.y - 20 - arrowLen * Math.sin(angle + Math.PI / 6));
      graphCtx.closePath();
      graphCtx.fillStyle = '#aaa';
      graphCtx.fill();
    }
  }

  // Draw nodes
  for (let i = 0; i < uniquePages.length; i++) {
    const page = uniquePages[i];
    const pos = nodePos[page];
    // Highlight if in memory at this step
    let inMemory = false;
    let isFault = false;
    if (step >= 0 && step < pageRefs.length) {
      // Reconstruct memory at this step
      let simFrames = [];
      let simQueue = [];
      let simLastUsed = new Map();
      for (let s = 0; s <= step; s++) {
        const p = pageRefs[s];
        if (algorithm === 'fifo') {
          if (!simFrames.includes(p)) {
            if (simFrames.length < frameCount) {
              simFrames.push(p);
              simQueue.push(p);
            } else {
              const removed = simQueue.shift();
              const idx = simFrames.indexOf(removed);
              simFrames[idx] = p;
              simQueue.push(p);
            }
          }
        } else if (algorithm === 'lru') {
          simLastUsed.set(p, s);
          if (!simFrames.includes(p)) {
            if (simFrames.length < frameCount) {
              simFrames.push(p);
            } else {
              let lru = Infinity, lruIdx = 0;
              for (let j = 0; j < simFrames.length; j++) {
                const last = simLastUsed.get(simFrames[j]) || -1;
                if (last < lru) {
                  lru = last;
                  lruIdx = j;
                }
              }
              simFrames[lruIdx] = p;
            }
          }
          simLastUsed.set(p, s);
        } else if (algorithm === 'optimal') {
          if (!simFrames.includes(p)) {
            if (simFrames.length < frameCount) {
              simFrames.push(p);
            } else {
              let farthest = -1, idx = 0;
              for (let j = 0; j < simFrames.length; j++) {
                const next = pageRefs.indexOf(simFrames[j], s + 1);
                if (next === -1) {
                  idx = j;
                  break;
                }
                if (next > farthest) {
                  farthest = next;
                  idx = j;
                }
              }
              simFrames[idx] = p;
            }
          }
        }
        if (s === step) {
          inMemory = simFrames.includes(page);
          isFault = (p === page && !simFrames.slice(0, simFrames.length - 1).includes(p));
        }
      }
    }
    // Node style
    graphCtx.beginPath();
    graphCtx.arc(pos.x, pos.y, 28, 0, 2 * Math.PI);
    graphCtx.fillStyle = inMemory ? (isFault ? '#ff4444' : '#44ff44') : '#222';
    graphCtx.fill();
    graphCtx.lineWidth = 3;
    graphCtx.strokeStyle = (step >= 0 && pageRefs[step] === page) ? '#44f' : '#aaa';
    graphCtx.stroke();
    // Page number
    graphCtx.font = 'bold 22px Arial';
    graphCtx.fillStyle = '#fff';
    graphCtx.textAlign = 'center';
    graphCtx.textBaseline = 'middle';
    graphCtx.fillText(page, pos.x, pos.y);
  }

  // Legend
  graphCtx.font = '14px Arial';
  graphCtx.textAlign = 'left';
  graphCtx.fillStyle = '#44ff44';
  graphCtx.fillText('In Memory', 20, height - 40);
  graphCtx.fillStyle = '#ff4444';
  graphCtx.fillText('Page Fault', 120, height - 40);
  graphCtx.fillStyle = '#44f';
  graphCtx.fillText('Current Reference', 220, height - 40);
}

async function runStep(step) {
  if (step >= pageRefs.length) return;
  const page = pageRefs[step];
  let fault = false;
  let replacedIdx = -1;

  if (algorithm === 'fifo') {
    if (!frames.includes(page)) {
      fault = true;
      faults++;
      if (frames.length < frameCount) {
        frames.push(page);
        queue.push(page);
      } else {
        const removed = queue.shift();
        replacedIdx = frames.indexOf(removed);
        frames[replacedIdx] = page;
        queue.push(page);
      }
    }
  } else if (algorithm === 'lru') {
    lastUsed.set(page, step);
    if (!frames.includes(page)) {
      fault = true;
      faults++;
      if (frames.length < frameCount) {
        frames.push(page);
      } else {
        let lru = Infinity, lruIdx = 0;
        for (let i = 0; i < frames.length; i++) {
          const last = lastUsed.get(frames[i]) || -1;
          if (last < lru) {
            lru = last;
            lruIdx = i;
          }
        }
        replacedIdx = lruIdx;
        frames[lruIdx] = page;
      }
    }
    lastUsed.set(page, step);
  } else if (algorithm === 'optimal') {
    if (!frames.includes(page)) {
      fault = true;
      faults++;
      if (frames.length < frameCount) {
        frames.push(page);
      } else {
        let farthest = -1, idx = 0;
        for (let i = 0; i < frames.length; i++) {
          const next = pageRefs.indexOf(frames[i], step + 1);
          if (next === -1) {
            idx = i;
            break;
          }
          if (next > farthest) {
            farthest = next;
            idx = i;
          }
        }
        replacedIdx = idx;
        frames[idx] = page;
      }
    }
  }

  // Draw current step
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#000';
  ctx.font = '18px Arial';
  ctx.textAlign = 'left';
  ctx.fillText('Step ' + (step + 1) + ' - Page: ' + page + (fault ? ' ✴️ Page Fault' : ''), 20, 30);

  for (let i = 0; i < frameCount; i++) {
    drawFrame(100 + i * 70, 60, 60, 60, frames[i] !== undefined ? frames[i] : '', fault && frames[i] === page && (replacedIdx === -1 || replacedIdx === i));
  }

  // Draw timeline
  ctx.font = '15px Arial';
  ctx.textAlign = 'center';
  ctx.fillStyle = '#333';
  for (let i = 0; i < pageRefs.length; i++) {
    ctx.fillText(pageRefs[i], 100 + i * 40, 160);
    if (i === step) {
      ctx.beginPath();
      ctx.moveTo(100 + i * 40, 170);
      ctx.lineTo(100 + i * 40, 190);
      ctx.strokeStyle = '#44f';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(100 + i * 40, 195, 6, 0, 2 * Math.PI);
      ctx.fillStyle = '#44f';
      ctx.fill();
    }
  }

  ctx.fillStyle = '#000';
  ctx.textAlign = 'left';
  ctx.font = '16px Arial';
  ctx.fillText('Total Page Faults: ' + faults, 20, 250);

  // Draw graph traversal below
  drawGraphTraversal(step);
}

async function animateSimulation() {
  running = true;
  for (let step = currentStep; step < pageRefs.length; step++) {
    if (!running) break;
    currentStep = step;
    await runStep(step);
    await sleep(900);
  }
  running = false;
}

function stepSimulation() {
  if (currentStep < pageRefs.length) {
    runStep(currentStep);
    currentStep++;
  }
}

function startSimulation() {
  resetSim();
  // Get values from Django form
  const form = document.querySelector('form[action*="paging"]');
  const algorithmSelect = form.querySelector('select[name="paging_algorithm"]');
  const referenceInput = form.querySelector('input[name="reference_string"]');
  const framesInput = form.querySelector('input[name="frames"]');
  pageRefs = referenceInput.value.split(',').map(p => parseInt(p.trim())).filter(x => !isNaN(x));
  frameCount = parseInt(framesInput.value);
  algorithm = algorithmSelect.value;
  currentStep = 0;
  stepSimulation();
}

// Controls
function addPagingControls() {
  let panel = document.getElementById('pagingControls');
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'pagingControls';
    panel.style.display = 'flex';
    panel.style.gap = '10px';
    panel.style.justifyContent = 'center';
    panel.style.margin = '10px 0';
    canvas.parentNode.insertBefore(panel, canvas);
  }
  panel.innerHTML = '';
  // Play
  const playBtn = document.createElement('button');
  playBtn.textContent = 'Play';
  playBtn.onclick = () => {
    if (!running) {
      animateSimulation();
    }
  };
  // Pause
  const pauseBtn = document.createElement('button');
  pauseBtn.textContent = 'Pause';
  pauseBtn.onclick = () => { running = false; };
  // Next
  const nextBtn = document.createElement('button');
  nextBtn.textContent = 'Next';
  nextBtn.onclick = () => { if (!running) stepSimulation(); };
  // Reset
  const resetBtn = document.createElement('button');
  resetBtn.textContent = 'Reset';
  resetBtn.onclick = () => { resetSim(); };
  [playBtn, pauseBtn, nextBtn, resetBtn].forEach(btn => {
    btn.style.padding = '6px 16px';
    btn.style.borderRadius = '6px';
    btn.style.border = 'none';
    btn.style.background = '#444';
    btn.style.color = '#fff';
    btn.style.fontWeight = 'bold';
    btn.style.cursor = 'pointer';
  });
  panel.append(playBtn, pauseBtn, nextBtn, resetBtn);
}

document.addEventListener('DOMContentLoaded', function() {
  addPagingControls();
  // Hook Django form submit
  const form = document.querySelector('form[action*="paging"]');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      startSimulation();
    });
  }
}); 