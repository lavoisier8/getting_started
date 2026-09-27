const expressionDisplay = document.querySelector('#expression');
const resultDisplay = document.querySelector('#result');
const errorDisplay = document.querySelector('#error');
let expression = '';

function render() {
  expressionDisplay.textContent = expression || '0';
  errorDisplay.textContent = '';
}

function append(value) {
  if (expression.length < 256) expression += value;
  render();
}

async function calculate() {
  if (!expression.trim()) return;
  errorDisplay.textContent = '';
  try {
    const response = await fetch('/api/calc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expression }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not calculate this expression');
    resultDisplay.textContent = String(data.result);
    expression = String(data.result);
    render();
  } catch (error) {
    errorDisplay.textContent = error.message || 'Unable to reach the calculator';
  }
}

function handleAction(action) {
  if (action === 'clear') {
    expression = '';
    resultDisplay.textContent = '0';
    render();
  } else if (action === 'backspace') {
    expression = expression.slice(0, -1);
    render();
  } else if (action === 'sign') {
    if (expression) expression = `-(${expression})`;
    render();
  } else if (action === 'percent') {
    if (expression) expression += '/100';
    render();
  } else if (action === 'equals') {
    calculate();
  }
}

document.querySelector('.keypad').addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  if (button.dataset.action) handleAction(button.dataset.action);
  else append(button.dataset.value);
});

document.addEventListener('keydown', (event) => {
  if (/^[0-9.+*/()-]$/.test(event.key)) {
    event.preventDefault();
    append(event.key);
  } else if (event.key === 'Enter' || event.key === '=') {
    event.preventDefault();
    calculate();
  } else if (event.key === 'Backspace') {
    handleAction('backspace');
  } else if (event.key === 'Escape') {
    handleAction('clear');
  } else if (event.key === '%') {
    handleAction('percent');
  }
});