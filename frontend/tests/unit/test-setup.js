/**
 * Test Setup and Global Configuration
 * Sets up jsdom and loads functions from templates.html
 */

const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

// Create a new JSDOM instance for each test file
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
  resources: 'usable',
  beforeParse(window) {
    // Disable fetch to avoid network errors
    window.fetch = () => Promise.reject(new Error('Fetch disabled in tests'));
  }
});

global.document = dom.window.document;
global.window = dom.window;
global.navigator = dom.window.navigator;
global.Element = dom.window.Element;
global.HTMLElement = dom.window.HTMLElement;

// Read templates.html and extract JavaScript functions
const templatesPath = path.join(__dirname, '../../control/templates.html');
let templatesContent = '';

try {
  templatesContent = fs.readFileSync(templatesPath, 'utf-8');
} catch (err) {
  console.error(`Error reading templates.html: ${err.message}`);
  process.exit(1);
}

// Extract JavaScript code from the HTML file
// We'll look for <script> tags and extract the content
const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let allScriptContent = '';
let match;

while ((match = scriptRegex.exec(templatesContent)) !== null) {
  allScriptContent += '\n' + match[1];
}

// Create a wrapper that exposes functions globally
const wrappedCode = `
(function() {
  ${allScriptContent}

  // Export functions to global scope
  if (typeof updateTemplateSummary !== 'undefined') {
    global.updateTemplateSummary = updateTemplateSummary;
  }
  if (typeof updateEdgeSummary !== 'undefined') {
    global.updateEdgeSummary = updateEdgeSummary;
  }
  if (typeof updateEdgeList !== 'undefined') {
    global.updateEdgeList = updateEdgeList;
  }
  if (typeof updateConfigSummary !== 'undefined') {
    global.updateConfigSummary = updateConfigSummary;
  }
  if (typeof createStringControl !== 'undefined') {
    global.createStringControl = createStringControl;
  }
  if (typeof createNumberControl !== 'undefined') {
    global.createNumberControl = createNumberControl;
  }
  if (typeof createSelectControl !== 'undefined') {
    global.createSelectControl = createSelectControl;
  }
  if (typeof createStepArrayControl !== 'undefined') {
    global.createStepArrayControl = createStepArrayControl;
  }
  if (typeof addStepRow !== 'undefined') {
    global.addStepRow = addStepRow;
  }
  if (typeof createDHSIntervalControl !== 'undefined') {
    global.createDHSIntervalControl = createDHSIntervalControl;
  }
  if (typeof addDHSIntervalRow !== 'undefined') {
    global.addDHSIntervalRow = addDHSIntervalRow;
  }
  if (typeof createFlowIntervalControl !== 'undefined') {
    global.createFlowIntervalControl = createFlowIntervalControl;
  }
  if (typeof addFlowIntervalRow !== 'undefined') {
    global.addFlowIntervalRow = addFlowIntervalRow;
  }
  if (typeof createVehicleTypeControl !== 'undefined') {
    global.createVehicleTypeControl = createVehicleTypeControl;
  }
  if (typeof renderParameterControl !== 'undefined') {
    global.renderParameterControl = renderParameterControl;
  }
  if (typeof renderParametersSection !== 'undefined') {
    global.renderParametersSection = renderParametersSection;
  }
  if (typeof attachParameterListeners !== 'undefined') {
    global.attachParameterListeners = attachParameterListeners;
  }
  if (typeof validateParameterValue !== 'undefined') {
    global.validateParameterValue = validateParameterValue;
  }
  // Phase 1 Day 3: Parameter collection and validation functions
  if (typeof collectParameterValues !== 'undefined') {
    global.collectParameterValues = collectParameterValues;
  }
  if (typeof validateAllParameters !== 'undefined') {
    global.validateAllParameters = validateAllParameters;
  }
  if (typeof prepareStrategySubmission !== 'undefined') {
    global.prepareStrategySubmission = prepareStrategySubmission;
  }
  // Phase 1 Day 4-5: createStrategy() refactored functions
  if (typeof collectBasicStrategyInfo !== 'undefined') {
    global.collectBasicStrategyInfo = collectBasicStrategyInfo;
  }
  if (typeof extractTableParameters !== 'undefined') {
    global.extractTableParameters = extractTableParameters;
  }
  if (typeof collectParameterValues !== 'undefined') {
    global.collectParameterValues = collectParameterValues;
  }
  if (typeof validateStrategyInput !== 'undefined') {
    global.validateStrategyInput = validateStrategyInput;
  }
  if (typeof validateStrategyParameters !== 'undefined') {
    global.validateStrategyParameters = validateStrategyParameters;
  }
  if (typeof buildStrategyPayload !== 'undefined') {
    global.buildStrategyPayload = buildStrategyPayload;
  }
  if (typeof submitStrategyToAPI !== 'undefined') {
    global.submitStrategyToAPI = submitStrategyToAPI;
  }
  if (typeof handleStrategyCreationResponse !== 'undefined') {
    global.handleStrategyCreationResponse = handleStrategyCreationResponse;
  }
  if (typeof createStrategy !== 'undefined') {
    global.createStrategy = createStrategy;
  }
})();
`;

// Execute the wrapped code
try {
  eval(wrappedCode);
} catch (err) {
  // Log warnings but don't fail - some functions may depend on context
  if (err.message.includes('Cannot read properties of null')) {
    // Expected - DOM elements may not exist yet
    console.warn(`⚠️  Note: Some initialization code failed (expected): ${err.message.split('\n')[0]}`);
  } else {
    console.error(`Error loading templates: ${err.message}`);
  }
}

// Make sure the key functions we need are available globally
// Export the expect function
const expect = require('chai').expect;
const sinon = require('sinon');

global.expect = expect;
global.sinon = sinon;

// Mock window.alert globally
dom.window.alert = sinon.stub();
global.alert = sinon.stub();

console.log('✅ Test environment initialized');
