// ==================== Unified Timeline Update Functions ====================

/**
 * Timeline configuration presets for different strategy types.
 * Each config defines how to extract data from table rows and update timeline.
 */
const TIMELINE_CONFIGS = {
  vss: {
    containerClass: '.step-array-control-enhanced',
    rowSelector: '.step-row',
    timelineType: 'speed',
    extractData: (row) => {
      const timeInput = row.querySelector('.step-time');
      const speedInput = row.querySelector('.step-speed');
      if (timeInput && speedInput) {
        return {
          time_hours: parseFloat(timeInput.value) || 0,
          speed_kmh: parseFloat(speedInput.value) || 0
        };
      }
      return null;
    },
    sortData: (data) => data.sort((a, b) => a.time_hours - b.time_hours)
  },
  dhs: {
    containerClass: '.dhs-interval-control-enhanced',
    rowSelector: '.dhs-interval-row',
    timelineType: 'dhs',
    extractData: (row) => {
      const beginInput = row.querySelector('.dhs-interval-begin');
      const endInput = row.querySelector('.dhs-interval-end');
      const statusSelect = row.querySelector('.dhs-interval-status');
      if (beginInput && endInput && statusSelect) {
        return {
          begin_hours: parseFloat(beginInput.value) || 0,
          end_hours: parseFloat(endInput.value) || 0,
          status: statusSelect.value || 'CLOSED'
        };
      }
      return null;
    }
  },
  flow: {
    containerClass: '.flow-interval-control-enhanced',
    rowSelector: '.interval-row',
    timelineType: 'flow',
    extractData: (row) => {
      const beginInput = row.querySelector('.interval-begin');
      const endInput = row.querySelector('.interval-end');
      const flowInput = row.querySelector('.interval-flow');
      if (beginInput && endInput && flowInput) {
        return {
          begin_hours: parseFloat(beginInput.value) || 0,
          end_hours: parseFloat(endInput.value) || 0,
          flow_vph: parseFloat(flowInput.value) || 0
        };
      }
      return null;
    }
  },
  tec_simple: {
    containerClass: '.tec-interval-control-enhanced',
    rowSelector: '.tec-interval-row',
    timelineType: 'simple_interval',
    extractData: (row) => {
      const beginInput = row.querySelector('.tec-interval-begin');
      const endInput = row.querySelector('.tec-interval-end');
      if (beginInput && endInput) {
        const beginHours = parseFloat(beginInput.value) || 0;
        const endHours = parseFloat(endInput.value) || 0;
        if (endHours > beginHours && beginHours >= 0 && endHours <= 24) {
          return { begin_hours: beginHours, end_hours: endHours };
        }
      }
      return null;
    }
  }
};

/**
 * Unified timeline update function - handles all strategy types.
 * Replaces 4 duplicate functions: updateTimelineFromTable, updateDHSTimelineFromTable,
 * updateFlowTimelineFromTable, updateTECTimelineFromTable.
 *
 * @param {HTMLElement} tbody - Table body element containing parameter rows
 * @param {Object} config - Configuration object with extraction logic
 * @param {string} config.containerClass - CSS class of the container element
 * @param {string} config.rowSelector - CSS selector for table rows
 * @param {string} config.timelineType - Timeline visualization type
 * @param {Function} config.extractData - Function to extract data from a row
 * @param {Function} [config.sortData] - Optional function to sort extracted data
 */
function updateTimeline(tbody, config) {
  if (!window.TimelineVisualizer) {
    console.warn('[updateTimeline] TimelineVisualizer not available');
    return;
  }

  const container = tbody.closest(config.containerClass);
  if (!container) {
    console.warn(`[updateTimeline] Container ${config.containerClass} not found`);
    return;
  }

  const timelineElement = container.querySelector('.parameter-timeline');
  if (!timelineElement) {
    console.warn('[updateTimeline] Timeline element not found');
    return;
  }

  const rows = tbody.querySelectorAll(config.rowSelector);
  const data = [];

  rows.forEach(row => {
    const extracted = config.extractData(row);
    if (extracted !== null) {
      data.push(extracted);
    }
  });

  const finalData = config.sortData ? config.sortData(data) : data;

  try {
    const paramName = tbody.dataset.parameterName;
    if (config.timelineType === 'simple_interval' && paramName) {
      // TEC uses a different signature with paramName
      window.TimelineVisualizer.updateTimeline(timelineElement, paramName, finalData, { type: config.timelineType });
    } else {
      // Standard signature for VSS, DHS, Flow
      window.TimelineVisualizer.updateTimeline(timelineElement, finalData, { type: config.timelineType });
    }
    console.log(`[updateTimeline] Updated timeline (${config.timelineType}) with ${finalData.length} items`);
  } catch (err) {
    console.error(`[updateTimeline] Failed to update timeline:`, err);
  }
}

/**
 * Simplified wrapper for updating timeline by strategy type.
 * Uses preset configurations from TIMELINE_CONFIGS.
 *
 * @param {HTMLElement} tbody - Table body element
 * @param {string} type - Strategy type: 'vss', 'dhs', 'flow', or 'tec_simple'
 */
function updateTimelineByType(tbody, type) {
  const config = TIMELINE_CONFIGS[type];
  if (!config) {
    console.error(`[updateTimelineByType] Unknown type: ${type}`);
    return;
  }
  updateTimeline(tbody, config);
}

// Create debounced versions for each type
const debouncedUpdateTimeline = {
  vss: debounce((tbody) => updateTimelineByType(tbody, 'vss'), 300),
  dhs: debounce((tbody) => updateTimelineByType(tbody, 'dhs'), 300),
  flow: debounce((tbody) => updateTimelineByType(tbody, 'flow'), 300),
  tec_simple: debounce((tbody) => updateTimelineByType(tbody, 'tec_simple'), 300)
};
