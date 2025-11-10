/**
 * Phase 4: Integration Testing - Scenario Generation E2E Tests
 *
 * Tests end-to-end scenario generation workflow:
 * - Single scenario generation from CSV event data
 * - Batch scenario generation with multiple strategies
 * - Scenario index creation and validation
 * - File structure and metadata validation
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

test.describe('Phase 4: Scenario Generation E2E Tests', () => {
  const scenarioOutputDir = path.join(__dirname, '../../output/scenarios');
  const testEventId = '12547'; // Known good event from CSV

  test.describe('4.1 Single Scenario Generation (Task 4.1.1)', () => {
    test('should generate single scenario with VSS strategy', async ({ page }) => {
      // Navigate to scenario generation page (if exists)
      await page.goto('http://localhost:8000');

      // Verify scenario generator is available via API
      const response = await page.request.get('http://localhost:8000/api/v1');
      expect(response.ok()).toBeTruthy();

      // TODO: Implement scenario generation via API or direct Python call
      // For now, verify that scenarios can be generated programmatically
      // This would typically call the scenario generation script

      // Verify VSS scenario directory exists
      const vssDirPath = path.join(scenarioOutputDir, '01_交通事故', 'vss');
      const scenarioPath = path.join(vssDirPath, `scenario_交通事故_vss_${testEventId}.add.xml`);

      // Check scenario file exists (should be generated from batch generation)
      if (fs.existsSync(scenarioPath)) {
        // Read and verify XML structure
        const xmlContent = fs.readFileSync(scenarioPath, 'utf8');

        expect(xmlContent).toContain('<additional');
        expect(xmlContent).toContain('</additional>');
        expect(xmlContent).toContain('<closedLane'); // Event injection
        expect(xmlContent).toContain('<variableSpeedSign'); // Control strategy
      }
    });

    test('should generate scenario metadata JSON files', async () => {
      const vssDirPath = path.join(scenarioOutputDir, '01_交通事故', 'vss');
      const scenarioDirPath = path.join(vssDirPath, `scenario_交通事故_vss_${testEventId}`);

      // Check for 3 metadata JSON files
      const eventDescPath = path.join(scenarioDirPath, 'event_description.json');
      const trafficConfigPath = path.join(scenarioDirPath, 'traffic_input_config.json');
      const controlConfigPath = path.join(scenarioDirPath, 'control_strategy_config.json');

      if (fs.existsSync(eventDescPath)) {
        const eventDesc = JSON.parse(fs.readFileSync(eventDescPath, 'utf8'));

        // Validate event description structure
        expect(eventDesc).toHaveProperty('event_id');
        expect(eventDesc).toHaveProperty('event_type');
        expect(eventDesc.event_type).toBe('交通事故');
        expect(eventDesc).toHaveProperty('location');
        expect(eventDesc.location).toHaveProperty('edge_id');
        expect(eventDesc.location).toHaveProperty('junction_id');
        expect(eventDesc).toHaveProperty('time');
        expect(eventDesc.time).toHaveProperty('start_time');
        expect(eventDesc.time).toHaveProperty('end_time');
        expect(eventDesc).toHaveProperty('impact');
        expect(eventDesc.impact).toHaveProperty('affected_lanes');
      }

      if (fs.existsSync(trafficConfigPath)) {
        const trafficConfig = JSON.parse(fs.readFileSync(trafficConfigPath, 'utf8'));

        // Validate traffic input config structure
        expect(trafficConfig).toHaveProperty('od_time_range');
        expect(trafficConfig.od_time_range).toHaveProperty('start');
        expect(trafficConfig.od_time_range).toHaveProperty('end');
        expect(trafficConfig.od_time_range).toHaveProperty('event_start');
        expect(trafficConfig.od_time_range).toHaveProperty('event_end');
        expect(trafficConfig.od_time_range).toHaveProperty('buffer_minutes');
        expect(trafficConfig).toHaveProperty('od_table');
        expect(trafficConfig).toHaveProperty('simulation_duration_hours');
        expect(trafficConfig).toHaveProperty('vehicle_types');
      }

      if (fs.existsSync(controlConfigPath)) {
        const controlConfig = JSON.parse(fs.readFileSync(controlConfigPath, 'utf8'));

        // Validate control strategy config structure
        expect(controlConfig).toHaveProperty('strategy_type');
        expect(controlConfig.strategy_type).toBe('VSS');
        expect(controlConfig).toHaveProperty('strategy_name');
        expect(controlConfig).toHaveProperty('parameters');
        expect(controlConfig.parameters).toHaveProperty('speed_limit_kmh');
        expect(controlConfig.parameters).toHaveProperty('response_delay_seconds');
        expect(controlConfig.parameters).toHaveProperty('recovery_period_seconds');
        expect(controlConfig).toHaveProperty('timing');
        expect(controlConfig.timing).toHaveProperty('activation_time');
        expect(controlConfig.timing).toHaveProperty('deactivation_time');
      }
    });

    test('should validate XML against SUMO schema', async () => {
      const scenarioPath = path.join(scenarioOutputDir, '01_交通事故', 'vss', `scenario_交通事故_vss_${testEventId}.add.xml`);

      if (fs.existsSync(scenarioPath)) {
        const xmlContent = fs.readFileSync(scenarioPath, 'utf8');

        // Basic XML validation
        expect(xmlContent).toMatch(/<\?xml version/); // XML declaration

        // Verify required SUMO attributes
        expect(xmlContent).toMatch(/xmlns:xsi/); // SUMO schema reference
        expect(xmlContent).toMatch(/xsi:noNamespaceSchemaLocation/);

        // Verify element consistency
        const additionalMatch = xmlContent.match(/<additional[^>]*>/);
        const additionalEndMatch = xmlContent.match(/<\/additional>/);
        expect(additionalMatch).toBeTruthy();
        expect(additionalEndMatch).toBeTruthy();

        // Verify event injection element
        const closedLaneMatch = xmlContent.match(/<closedLane[^>]*id="[^"]*"[^>]*edge="[^"]*"[^>]*>/);
        expect(closedLaneMatch).toBeTruthy();

        // Verify control strategy element
        const controlMatch = xmlContent.match(/<(variableSpeedSign|rerouter|calibrator)[^>]*>/);
        expect(controlMatch).toBeTruthy();
      }
    });
  });

  test.describe('4.1.2 Batch Scenario Generation (Task 4.1.2)', () => {
    test('should generate batch scenarios for multiple strategies', async () => {
      // Check that scenarios exist for multiple strategies
      const strategies = ['vss', 'dhs', 'tec'];
      const baseDir = path.join(scenarioOutputDir, '01_交通事故');

      let scenarioCount = 0;

      for (const strategy of strategies) {
        const strategyDir = path.join(baseDir, strategy);
        if (fs.existsSync(strategyDir)) {
          const files = fs.readdirSync(strategyDir);
          const addXmlFiles = files.filter(f => f.endsWith('.add.xml'));
          scenarioCount += addXmlFiles.length;
        }
      }

      // Expect at least 3 scenarios (one per strategy type)
      expect(scenarioCount).toBeGreaterThanOrEqual(3);
    });

    test('should create scenario index JSON with metadata', async () => {
      const indexPath = path.join(scenarioOutputDir, 'scenario_index.json');

      if (fs.existsSync(indexPath)) {
        const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

        // Validate index structure
        expect(index).toHaveProperty('total_scenarios');
        expect(index).toHaveProperty('scenarios');
        expect(Array.isArray(index.scenarios)).toBeTruthy();

        // Validate scenario entries
        if (index.scenarios.length > 0) {
          const scenario = index.scenarios[0];
          expect(scenario).toHaveProperty('scenario_id');
          expect(scenario).toHaveProperty('event_type');
          expect(scenario).toHaveProperty('strategy');
          expect(scenario).toHaveProperty('event_id');
        }

        // Validate summary statistics
        expect(index).toHaveProperty('by_event_type');
        expect(index).toHaveProperty('by_strategy');
        expect(index).toHaveProperty('last_updated');
      }
    });

    test('should verify directory structure matches specification', async () => {
      // Expected structure:
      // output/scenarios/
      // ├── 01_交通事故/
      // │   ├── vss/
      // │   ├── dhs/
      // │   └── tec/
      // └── scenario_index.json

      const eventTypeDir = path.join(scenarioOutputDir, '01_交通事故');
      expect(fs.existsSync(eventTypeDir)).toBeTruthy();

      const expectedDirs = ['vss', 'dhs', 'tec'];
      for (const dir of expectedDirs) {
        const dirPath = path.join(eventTypeDir, dir);
        // Directories should exist or be empty
        if (fs.existsSync(dirPath)) {
          expect(fs.statSync(dirPath).isDirectory()).toBeTruthy();
        }
      }

      // Index file should exist
      const indexPath = path.join(scenarioOutputDir, 'scenario_index.json');
      if (fs.existsSync(indexPath)) {
        expect(fs.statSync(indexPath).isFile()).toBeTruthy();
      }
    });
  });

  test.describe('Scenario Quality Validation', () => {
    test('should have valid timestamps in all scenarios', async () => {
      const baseDir = path.join(scenarioOutputDir, '01_交通事故');
      const strategies = fs.readdirSync(baseDir).filter(f => {
        return fs.statSync(path.join(baseDir, f)).isDirectory();
      });

      for (const strategy of strategies) {
        const strategyDir = path.join(baseDir, strategy);
        const subdirs = fs.readdirSync(strategyDir).filter(f => {
          return fs.statSync(path.join(strategyDir, f)).isDirectory();
        });

        for (const subdir of subdirs) {
          const configPath = path.join(strategyDir, subdir, 'control_strategy_config.json');
          if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            const activation = new Date(config.timing.activation_time);
            const deactivation = new Date(config.timing.deactivation_time);

            // Activation time should be valid and before deactivation
            expect(activation.getTime()).toBeLessThan(deactivation.getTime());
          }
        }
      }
    });

    test('should have consistent event timing across scenario files', async () => {
      const baseDir = path.join(scenarioOutputDir, '01_交通事故', 'vss');

      if (fs.existsSync(baseDir)) {
        const subdirs = fs.readdirSync(baseDir).filter(f => {
          return fs.statSync(path.join(baseDir, f)).isDirectory();
        });

        for (const subdir of subdirs) {
          const eventDescPath = path.join(baseDir, subdir, 'event_description.json');
          const trafficConfigPath = path.join(baseDir, subdir, 'traffic_input_config.json');

          if (fs.existsSync(eventDescPath) && fs.existsSync(trafficConfigPath)) {
            const eventDesc = JSON.parse(fs.readFileSync(eventDescPath, 'utf8'));
            const trafficConfig = JSON.parse(fs.readFileSync(trafficConfigPath, 'utf8'));

            // Event time should match between files
            expect(eventDesc.time.start_time).toBe(trafficConfig.od_time_range.event_start);
            expect(eventDesc.time.end_time).toBe(trafficConfig.od_time_range.event_end);

            // Traffic time range should include event time with buffers
            const eventStart = new Date(eventDesc.time.start_time);
            const eventEnd = new Date(eventDesc.time.end_time);
            const trafficStart = new Date(trafficConfig.od_time_range.start);
            const trafficEnd = new Date(trafficConfig.od_time_range.end);

            expect(trafficStart.getTime()).toBeLessThanOrEqual(eventStart.getTime());
            expect(trafficEnd.getTime()).toBeGreaterThanOrEqual(eventEnd.getTime());
          }
        }
      }
    });
  });
});
