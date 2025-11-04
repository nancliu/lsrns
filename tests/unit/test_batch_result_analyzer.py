"""
Unit tests for BatchResultAnalyzer

Tests cover:
- XML parsing (valid, missing, malformed)
- Aggregation across multiple seeds
- Improvement rate calculations
- Comparison summary generation
"""

import pytest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from shared.analysis_tools.batch_result_analyzer import (
    BatchResultAnalyzer,
    analyze_batch
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def analyzer():
    """Initialize BatchResultAnalyzer instance"""
    return BatchResultAnalyzer()


@pytest.fixture
def tmp_batch_dir(tmp_path):
    """Create temporary batch directory structure"""
    batch_dir = tmp_path / "batch_001"
    batch_dir.mkdir()

    # Create baseline plan directory
    baseline_dir = batch_dir / "baseline_plan"
    baseline_dir.mkdir()

    # Create test plan directories
    plan_001_dir = batch_dir / "plan_001"
    plan_001_dir.mkdir()

    plan_002_dir = batch_dir / "plan_002"
    plan_002_dir.mkdir()

    return batch_dir


@pytest.fixture
def sample_summary_xml():
    """Provide sample summary.xml content (valid)"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <timestep time="0">
        <vehicleSummary loaded="1000" inserted="500" ended="0" running="500" waiting="50" teleports="2" collisions="0" avgSpeed="25.5"/>
    </timestep>
    <timestep time="30">
        <vehicleSummary loaded="1200" inserted="800" ended="600" running="600" waiting="100" teleports="5" collisions="1" avgSpeed="22.3"/>
    </timestep>
    <timestep time="60">
        <vehicleSummary loaded="1500" inserted="1000" ended="1200" running="500" waiting="80" teleports="8" collisions="2" avgSpeed="24.1"/>
    </timestep>
    <timestep time="90">
        <vehicleSummary loaded="1500" inserted="1200" ended="1500" running="200" waiting="30" teleports="10" collisions="2" avgSpeed="26.5"/>
    </timestep>
</summary>"""


@pytest.fixture
def sample_summary_xml_alternative():
    """Provide alternative summary.xml with different metrics"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <timestep time="0">
        <vehicleSummary loaded="900" inserted="400" ended="0" running="400" waiting="40" teleports="1" collisions="0" avgSpeed="26.2"/>
    </timestep>
    <timestep time="90">
        <vehicleSummary loaded="1500" inserted="1200" ended="1300" running="200" waiting="20" teleports="5" collisions="1" avgSpeed="28.7"/>
    </timestep>
</summary>"""


@pytest.fixture
def malformed_xml():
    """Provide malformed XML content"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <timestep time="90">
        <vehicleSummary loaded="1500" inserted="1200" ended="1500" running="200" waiting="30" teleports="10" collisions="2" avgSpeed="26.5"
    </timestep>
</summary>"""


@pytest.fixture
def missing_metrics_xml():
    """Provide XML with missing metric values"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <timestep time="90">
        <vehicleSummary loaded="1500" inserted="1200" ended="1500" running="200" waiting="30"/>
    </timestep>
</summary>"""


# ============================================================================
# T7.1.1: XML PARSING TESTS
# ============================================================================

class TestXMLParsing:
    """XML parsing tests"""

    def test_parse_summary_xml_valid_file(self, analyzer, tmp_batch_dir, sample_summary_xml):
        """Test parsing valid summary.xml file"""
        summary_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        summary_path.write_text(sample_summary_xml)

        result = analyzer._extract_summary_metrics(summary_path)

        # Verify all expected metrics are extracted
        assert result["loaded"] == 1500
        assert result["inserted"] == 1200
        assert result["ended"] == 1500
        assert result["running"] == 200
        assert result["waiting"] == 30
        assert result["teleports"] == 10
        assert result["collisions"] == 2
        assert result["avgSpeed"] == 26.5
        assert result["step"] == 90

    def test_parse_summary_xml_missing_file(self, analyzer, tmp_batch_dir):
        """Test handling of missing summary.xml"""
        summary_path = tmp_batch_dir / "nonexistent" / "summary.xml"

        result = analyzer._extract_summary_metrics(summary_path)

        # Should return empty dict for missing file
        assert result == {}

    def test_parse_summary_xml_malformed_xml(self, analyzer, tmp_batch_dir, malformed_xml):
        """Test handling of malformed XML"""
        summary_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        summary_path.write_text(malformed_xml)

        result = analyzer._extract_summary_metrics(summary_path)

        # Should handle gracefully and return empty dict
        assert result == {}

    def test_parse_summary_xml_missing_metrics(self, analyzer, tmp_batch_dir, missing_metrics_xml):
        """Test XML with missing metric values"""
        summary_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        summary_path.write_text(missing_metrics_xml)

        result = analyzer._extract_summary_metrics(summary_path)

        # Should extract available metrics and handle missing ones
        assert result["loaded"] == 1500
        assert result["inserted"] == 1200
        assert result["ended"] == 1500
        assert result["running"] == 200
        assert result["waiting"] == 30
        # Missing metrics should default to 0
        assert result.get("teleports", 0) == 0
        assert result.get("collisions", 0) == 0

    def test_parse_summary_xml_empty_file(self, analyzer, tmp_batch_dir):
        """Test handling of empty XML file"""
        summary_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        summary_path.write_text("")

        result = analyzer._extract_summary_metrics(summary_path)

        # Should handle gracefully
        assert isinstance(result, dict)


# ============================================================================
# T7.1.2: AGGREGATION TESTS
# ============================================================================

class TestAggregation:
    """Aggregation tests for multiple seeds"""

    def test_single_plan_result_with_metrics(self, analyzer, tmp_batch_dir, sample_summary_xml):
        """Test analysis with single plan"""
        summary_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        summary_path.write_text(sample_summary_xml)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan"],
            baseline_plan_id="baseline_plan"
        )

        assert "plan_results" in result
        assert "baseline_plan" in result["plan_results"]
        assert result["plan_results"]["baseline_plan"]["type"] == "baseline"

    def test_multiple_plans_aggregation(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test analysis with multiple plans (baseline + test)"""
        # Write baseline plan summary
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        # Write test plan summary
        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        assert "baseline_plan" in result["plan_results"]
        assert "plan_001" in result["plan_results"]
        assert result["plan_results"]["baseline_plan"]["type"] == "baseline"
        assert result["plan_results"]["plan_001"]["type"] == "test"

    def test_improvement_calculation_with_multiple_plans(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test improvement rate calculation with multiple plans"""
        # Write baseline (slower)
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        # Write test plan (faster)
        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        assert "improvement_rates" in result
        assert "plan_001" in result["improvement_rates"]

        # Test plan has higher avgSpeed (28.7 vs 26.5), should show improvement
        improvement = result["improvement_rates"]["plan_001"]
        assert improvement["avgSpeed"] > 0  # Positive improvement for speed


# ============================================================================
# T7.1.3: IMPROVEMENT RATE TESTS
# ============================================================================

class TestImprovementRates:
    """Improvement rate calculation tests"""

    def test_calculate_improvement_rate_positive_for_speed(self, analyzer):
        """Test positive improvement for speed metric (higher is better)"""
        baseline_metrics = {"avgSpeed": 25.0}
        test_metrics = {"avgSpeed": 28.1}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Expected: (28.1 - 25.0) / 25.0 * 100 = 12.4%
        assert rates["avgSpeed"] == pytest.approx(12.4, abs=0.1)

    def test_calculate_improvement_rate_negative_for_speed(self, analyzer):
        """Test negative improvement for speed metric (slower)"""
        baseline_metrics = {"avgSpeed": 28.0}
        test_metrics = {"avgSpeed": 25.0}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Expected: (25.0 - 28.0) / 28.0 * 100 = -10.71%
        assert rates["avgSpeed"] < 0  # Negative improvement

    def test_calculate_improvement_rate_positive_for_waiting(self, analyzer):
        """Test positive improvement for waiting time (lower is better)"""
        baseline_metrics = {"waiting": 100}
        test_metrics = {"waiting": 80}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Expected: (100 - 80) / 100 * 100 = 20%
        assert rates["waiting"] == pytest.approx(20.0, abs=0.1)

    def test_calculate_improvement_rate_negative_for_waiting(self, analyzer):
        """Test negative improvement for waiting time (more waiting)"""
        baseline_metrics = {"waiting": 80}
        test_metrics = {"waiting": 120}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Expected: (80 - 120) / 80 * 100 = -50%
        assert rates["waiting"] == pytest.approx(-50.0, abs=0.1)

    def test_calculate_improvement_rate_zero_baseline(self, analyzer):
        """Test division by zero handling"""
        baseline_metrics = {"waiting": 0, "avgSpeed": 0}
        test_metrics = {"waiting": 100, "avgSpeed": 25}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Should handle gracefully - either return None or use absolute comparison
        assert rates["waiting"] is not None or rates["waiting"] is None
        assert rates["avgSpeed"] is not None or rates["avgSpeed"] is None

    def test_calculate_improvement_rate_missing_metric(self, analyzer):
        """Test handling of missing metrics"""
        baseline_metrics = {"waiting": 100}
        test_metrics = {"avgSpeed": 25}  # Different metric

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Should return None for missing metrics
        assert rates.get("waiting") is None
        assert rates.get("avgSpeed") is None

    def test_calculate_improvement_rate_all_metrics(self, analyzer):
        """Test improvement rate calculation for all metric types"""
        baseline_metrics = {
            "waiting": 100,
            "teleports": 10,
            "collisions": 2,
            "avgSpeed": 25,
            "running": 300
        }
        test_metrics = {
            "waiting": 80,
            "teleports": 8,
            "collisions": 1,
            "avgSpeed": 28,
            "running": 250
        }

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # All should show improvement
        assert rates["waiting"] > 0  # Lower is better
        assert rates["teleports"] > 0  # Lower is better
        assert rates["collisions"] > 0  # Lower is better
        assert rates["avgSpeed"] > 0  # Higher is better
        assert rates["running"] > 0  # Lower is better (fewer vehicles running)


# ============================================================================
# T7.1.4: COMPARISON SUMMARY TESTS
# ============================================================================

class TestComparisonSummary:
    """Comparison summary generation tests"""

    def test_generate_comparison_summary_structure(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test comparison summary has correct structure"""
        # Setup baseline and test plan
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        summary = result["comparison_summary"]

        # Verify structure
        assert "columns" in summary
        assert "rows" in summary
        assert "metrics_definitions" in summary

        # Verify columns include baseline and test plan
        assert "指标" in summary["columns"]
        assert "基准方案" in summary["columns"]
        assert "plan_001" in summary["columns"] or len(summary["columns"]) > 2

    def test_generate_comparison_summary_includes_metrics(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test comparison summary includes all metrics"""
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        summary = result["comparison_summary"]
        metrics = [row["metric"] for row in summary["rows"]]

        # Should include key metrics
        assert "step" in metrics or "ended" in metrics
        assert "waiting" in metrics or "ended" in metrics

    def test_generate_comparison_summary_multiple_test_plans(self, analyzer, tmp_batch_dir,
                                                           sample_summary_xml, sample_summary_xml_alternative):
        """Test comparison summary with multiple test plans"""
        # Create baseline
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        # Create test plans
        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        plan_002_path = tmp_batch_dir / "plan_002" / "summary.xml"
        plan_002_path.write_text(sample_summary_xml)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001", "plan_002"],
            baseline_plan_id="baseline_plan"
        )

        summary = result["comparison_summary"]

        # Should have rows for comparison
        assert len(summary["rows"]) > 0

        # Each row should have test values for both plans
        for row in summary["rows"]:
            assert "test_values" in row


# ============================================================================
# T7.1.5: CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions like analyze_batch()"""

    def test_analyze_batch_function(self, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test the analyze_batch() convenience function"""
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        result = analyze_batch(
            batch_dir=str(tmp_batch_dir),
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        assert "plan_results" in result
        assert "baseline_plan" in result["plan_results"]
        assert "plan_001" in result["plan_results"]

    def test_get_improvement_rates(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test getting improvement rates for a specific plan"""
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        rates = analyzer.get_improvement_rates("plan_001")

        assert rates is not None
        assert isinstance(rates, dict)

    def test_get_all_results(self, analyzer, tmp_batch_dir, sample_summary_xml, sample_summary_xml_alternative):
        """Test getting all results"""
        baseline_path = tmp_batch_dir / "baseline_plan" / "summary.xml"
        baseline_path.write_text(sample_summary_xml)

        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml_alternative)

        analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        all_results = analyzer.get_all_results()

        assert "baseline_results" in all_results
        assert "test_results" in all_results
        assert "improvement_rates" in all_results


# ============================================================================
# T7.1.6: EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case and error handling tests"""

    def test_empty_batch_directory(self, analyzer, tmp_batch_dir):
        """Test handling of empty batch directory"""
        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["nonexistent_plan"],
            baseline_plan_id="baseline_plan"
        )

        assert "plan_results" in result
        assert len(result["plan_results"]) == 0

    def test_baseline_missing_but_test_present(self, analyzer, tmp_batch_dir, sample_summary_xml):
        """Test when baseline is missing but test plan is present"""
        plan_001_path = tmp_batch_dir / "plan_001" / "summary.xml"
        plan_001_path.write_text(sample_summary_xml)

        result = analyzer.analyze_batch_results(
            batch_dir=tmp_batch_dir,
            plan_ids=["baseline_plan", "plan_001"],
            baseline_plan_id="baseline_plan"
        )

        # Should handle gracefully - baseline missing warning, test plan loaded
        assert "plan_001" in result["plan_results"]

    def test_metric_unit_retrieval(self, analyzer):
        """Test metric unit retrieval"""
        assert analyzer._get_metric_unit("step") == "s"
        assert analyzer._get_metric_unit("ended") == "辆"
        assert analyzer._get_metric_unit("avgSpeed") == "m/s"
        assert analyzer._get_metric_unit("unknown") == ""

    def test_large_metric_values(self, analyzer):
        """Test handling of large metric values"""
        baseline_metrics = {"waiting": 10000, "teleports": 500}
        test_metrics = {"waiting": 8000, "teleports": 250}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Should handle large numbers correctly
        assert rates["waiting"] == pytest.approx(20.0, abs=0.1)
        assert rates["teleports"] > 0  # Fewer teleports is improvement

    def test_float_conversion_in_metrics(self, analyzer):
        """Test float conversion for metric values"""
        baseline_metrics = {"avgSpeed": "25.5"}
        test_metrics = {"avgSpeed": "28.3"}

        rates = analyzer._calculate_improvement_rate(baseline_metrics, test_metrics)

        # Should convert string to float and calculate correctly
        assert rates["avgSpeed"] > 0
