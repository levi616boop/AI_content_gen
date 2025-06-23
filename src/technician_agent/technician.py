import os
import re
import json
import importlib
import subprocess
import platform
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from src.utils.logging_utils import setup_logging, log_operation
from src.utils.file_utils import (
    create_directory_if_not_exists,
    save_json_file,
    load_json_file,
    save_text_file
)
from .config import config

# Initialize logging
logger = setup_logging("technician_agent")

class TechnicianAgent:
    """Self-aware system maintenance and optimization agent"""
    
    def __init__(self):
        create_directory_if_not_exists(config.diagnostic_dir)
        self.system_report = self._generate_system_report()
        self.findings = {
            "errors": [],
            "warnings": [],
            "performance_issues": [],
            "dependency_issues": [],
            "hardware_issues": []
        }
        logger.info("Technician Agent initialized")
        
    def _generate_system_report(self) -> Dict[str, Any]:
        """Generate system hardware and software report"""
        return {
            "system": {
                "os": platform.system(),
                "os_version": platform.version(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "timings": {},
            "resource_usage": {}  # Placeholder for actual monitoring
        }
    
    def _parse_log_file(self, log_path: Path) -> Dict[str, Any]:
        """Parse a single log file for errors and warnings"""
        log_data = {
            "errors": [],
            "warnings": [],
            "performance": []
        }
        
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    if '"level": "ERROR"' in line:
                        try:
                            error_data = json.loads(line.split('|')[-1])
                            log_data["errors"].append({
                                "module": error_data.get("name", "unknown"),
                                "message": error_data.get("error", "unknown"),
                                "timestamp": error_data.get("timestamp", "")
                            })
                        except json.JSONDecodeError:
                            log_data["errors"].append({
                                "module": "unknown",
                                "message": line.strip(),
                                "timestamp": ""
                            })
                    elif '"level": "WARNING"' in line:
                        log_data["warnings"].append(line.strip())
                    
                    # Extract performance data
                    if "duration_sec" in line:
                        try:
                            perf_data = json.loads(line.split('|')[-1])
                            if "duration_sec" in perf_data:
                                log_data["performance"].append({
                                    "module": perf_data.get("name", "unknown"),
                                    "operation": perf_data.get("operation", "unknown"),
                                    "duration": perf_data.get("duration_sec", 0)
                                })
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Failed to parse log file {log_path}: {str(e)}")
            
        return log_data
    
    def _check_dependencies(self) -> List[Dict[str, str]]:
        """Check for missing or broken dependencies"""
        issues = []
        required_modules = [
            "pytesseract", "ffmpeg", "manimgl", "whisper",
            "openai", "elevenlabs", "svgwrite"
        ]
        
        for module in required_modules:
            try:
                importlib.import_module(module)
            except ImportError as e:
                issues.append({
                    "module": module,
                    "issue": "missing",
                    "message": str(e),
                    "alternatives": config.tool_alternatives.get(module, [])
                })
        
        # Check pip conflicts
        try:
            result = subprocess.run(
                ["pip", "check"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                for line in result.stderr.splitlines():
                    issues.append({
                        "module": "pip_conflict",
                        "issue": "dependency_conflict",
                        "message": line.strip(),
                        "alternatives": []
                    })
        except Exception as e:
            logger.error(f"Failed to run pip check: {str(e)}")
            
        return issues
    
    def _analyze_performance(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze performance against expected benchmarks"""
        issues = []
        
        # Group performance data by module
        perf_df = pd.DataFrame(log_data["performance"])
        if not perf_df.empty:
            avg_times = perf_df.groupby("module")["duration"].mean()
            
            for module, avg_time in avg_times.items():
                expected = config.expected_timings.get(module, 0)
                if expected and avg_time > expected * 1.5:  # 50% over expected
                    issues.append({
                        "module": module,
                        "actual_time": avg_time,
                        "expected_time": expected,
                        "issue": "performance_bottleneck"
                    })
        
        return issues
    
    def analyze_logs(
        self,
        log_directory: Path = None,
        qc_report_directory: Path = None
    ) -> Dict[str, Any]:
        """
        Analyze system logs and QC reports for issues
        
        Args:
            log_directory: Directory containing log files
            qc_report_directory: Directory containing QC reports
            
        Returns:
            dict: Analysis results with found issues
        """
        start_time = time.time()
        log_directory = log_directory or config.log_dir
        qc_report_directory = qc_report_directory or config.qc_report_dir
        
        log_operation(logger, "analyze_logs", "started", {
            "log_dir": str(log_directory),
            "qc_dir": str(qc_report_directory)
        })
        
        try:
            # Process log files
            all_log_data = {"errors": [], "warnings": [], "performance": []}
            for log_file in log_directory.glob("*.log"):
                log_data = self._parse_log_file(log_file)
                all_log_data["errors"].extend(log_data["errors"])
                all_log_data["warnings"].extend(log_data["warnings"])
                all_log_data["performance"].extend(log_data["performance"])
            
            # Process QC reports
            qc_issues = []
            for qc_file in qc_report_directory.glob("*.json"):
                try:
                    report = load_json_file(qc_file)
                    if report.get("summary", {}).get("status") == "needs_revision":
                        qc_issues.append({
                            "source": qc_file.stem,
                            "issues": report["summary"].get("critical_issues", 0),
                            "score": report["summary"].get("overall_score", 0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to process QC report {qc_file}: {str(e)}")
            
            # Analyze findings
            self.findings["errors"] = all_log_data["errors"]
            self.findings["warnings"] = all_log_data["warnings"]
            self.findings["performance_issues"] = self._analyze_performance(all_log_data)
            self.findings["dependency_issues"] = self._check_dependencies()
            self.findings["qc_issues"] = qc_issues
            
            # Check hardware (placeholder)
            self.findings["hardware_issues"] = self._check_hardware()
            
            duration = time.time() - start_time
            log_operation(logger, "analyze_logs", "completed", {
                "errors_found": len(self.findings["errors"]),
                "warnings_found": len(self.findings["warnings"]),
                "performance_issues": len(self.findings["performance_issues"]),
                "duration_sec": duration
            })
            
            return self.findings
            
        except Exception as e:
            log_operation(logger, "analyze_logs", "failed", {
                "error": str(e)
            }, level="ERROR")
            return {}
    
    def _check_hardware(self) -> List[Dict[str, Any]]:
        """Check system hardware against requirements (placeholder)"""
        issues = []
        
        # In production, would use psutil or similar
        if not config.hardware_requirements["gpu_recommended"]:
            issues.append({
                "issue": "hardware_limitation",
                "message": "GPU acceleration recommended for better performance",
                "severity": "warning"
            })
        
        return issues
    
    def suggest_improvements(self) -> Dict[str, Any]:
        """
        Generate improvement suggestions based on analysis
        
        Returns:
            dict: Suggested improvements and alternatives
        """
        suggestions = {
            "critical": [],
            "recommended": [],
            "optional": []
        }
        
        # Dependency issues
        for issue in self.findings["dependency_issues"]:
            if issue["issue"] == "missing":
                suggestions["critical"].append({
                    "action": f"Install missing module: {issue['module']}",
                    "command": f"pip install {issue['module']}",
                    "alternatives": issue["alternatives"]
                })
            else:
                suggestions["critical"].append({
                    "action": f"Resolve dependency conflict: {issue['message']}",
                    "command": "pip check --fix",
                    "alternatives": []
                })
        
        # Performance issues
        for issue in self.findings["performance_issues"]:
            alternatives = config.tool_alternatives.get(issue["module"], [])
            suggestion = {
                "action": f"Optimize {issue['module']} (took {issue['actual_time']:.1f}s, expected {issue['expected_time']:.1f}s)",
                "alternatives": alternatives
            }
            
            if issue["actual_time"] > issue["expected_time"] * 2:
                suggestions["critical"].append(suggestion)
            elif alternatives:
                suggestions["recommended"].append(suggestion)
            else:
                suggestions["optional"].append(suggestion)
        
        # QC issues
        for issue in self.findings["qc_issues"]:
            if issue["score"] < 3.0:
                suggestions["critical"].append({
                    "action": f"Review QC issues in {issue['source']} (score: {issue['score']}/5)",
                    "alternatives": []
                })
        
        return suggestions
    
    def perform_maintenance_actions(self) -> Dict[str, Any]:
        """
        Perform automated maintenance actions (conceptual)
        
        Returns:
            dict: Results of maintenance actions
        """
        results = {
            "completed": [],
            "skipped": [],
            "failed": []
        }
        
        # In production, this would be more sophisticated with:
        # - Proper privilege checks
        # - Rollback capability
        # - Dry-run mode
        # - User confirmation
        
        suggestions = self.suggest_improvements()
        
        for suggestion in suggestions["critical"]:
            if "command" in suggestion:
                try:
                    # Simulate running command
                    logger.info(f"Would execute: {suggestion['command']}")
                    results["completed"].append(suggestion["action"])
                except Exception as e:
                    results["failed"].append({
                        "action": suggestion["action"],
                        "error": str(e)
                    })
        
        return results
    
    def generate_diagnostic_report(self) -> Tuple[Path, Path]:
        """
        Generate comprehensive diagnostic reports
        
        Returns:
            tuple: Paths to (diagnostic.log, upgrade_plan.md)
        """
        log_path = config.diagnostic_dir / "diagnostic.log"
        md_path = config.diagnostic_dir / "upgrade_plan.md"
        
        # Save raw diagnostic data
        save_json_file(self.findings, log_path)
        
        # Generate human-readable markdown report
        md_content = self._generate_markdown_report()
        save_text_file(md_content, md_path)
        
        return (log_path, md_path)
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown format upgrade plan"""
        suggestions = self.suggest_improvements()
        
        md_lines = [
            "# AutoEd System Upgrade Plan",
            f"Generated: {time.ctime()}",
            "",
            "## Critical Issues",
            "These require immediate attention:",
            ""
        ]
        
        # Critical issues
        if not suggestions["critical"]:
            md_lines.append("- No critical issues found")
        else:
            for item in suggestions["critical"]:
                md_lines.append(f"- {item['action']}")
                if item.get("alternatives"):
                    md_lines.append(f"  - Alternatives: {', '.join(item['alternatives'])}")
        
        # Recommended improvements
        md_lines.extend([
            "",
            "## Recommended Improvements",
            ""
        ])
        
        if not suggestions["recommended"]:
            md_lines.append("- No recommended improvements at this time")
        else:
            for item in suggestions["recommended"]:
                md_lines.append(f"- {item['action']}")
                if item.get("alternatives"):
                    md_lines.append(f"  - Alternatives: {', '.join(item['alternatives'])}")
        
        # Optional improvements
        md_lines.extend([
            "",
            "## Optional Optimizations",
            ""
        ])
        
        if not suggestions["optional"]:
            md_lines.append("- No optional optimizations suggested")
        else:
            for item in suggestions["optional"]:
                md_lines.append(f"- {item['action']}")
        
        # System information
        md_lines.extend([
            "",
            "## System Information",
            f"- OS: {self.system_report['system']['os']} {self.system_report['system']['os_version']}",
            f"- Processor: {self.system_report['system']['processor']}",
            f"- Python: {self.system_report['system']['python_version']}",
            ""
        ])
        
        return "\n".join(md_lines)
