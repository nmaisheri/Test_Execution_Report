import json
import random
import time
from datetime import datetime, timedelta
import threading
import os
import argparse

class TestRunner:
    def __init__(self, selected_markers=None):
        self.tests_per_marker = 5
        self.tests = []
        self.start_time = datetime.now()
        self.current_test_index = 0
        self.running = True
        self.selected_markers = selected_markers or []
        
        # Define available markers (simplified to 5)
        self.available_markers = {
            "smoke": "Quick smoke tests for basic functionality",
            "regression": "Comprehensive regression tests",
            "ui": "User interface tests",
            "performance": "Performance and load tests",
            "security": "Security and authentication tests"
        }
        
        # Initialize all tests with markers
        self.initialize_tests()
        
    def initialize_tests(self):
        """Initialize tests with specific pass/fail/error distribution per marker"""
        test_counter = 1
        
        for marker in self.available_markers.keys():
            # For each marker, create 5 tests: 2 pass, 2 fail, 1 error
            outcomes = ["Passed", "Passed", "Failed", "Failed", "Error"]
            random.shuffle(outcomes)  # Randomize the order
            
            for i in range(self.tests_per_marker):
                # Determine if this test should run based on selected markers
                should_run = (
                    not self.selected_markers or  # Run all if no markers selected
                    marker in self.selected_markers
                )
                
                self.tests.append({
                    "name": f"test_{marker}_{i+1}",
                    "status": "Not Started" if should_run else "Not Tested",
                    "markers": [marker],
                    "predetermined_outcome": outcomes[i] if should_run else "Not Tested",
                    "start_time": "",
                    "end_time": "",
                    "execution_time": "",
                    "exception_log": ""
                })
                test_counter += 1
    
    def run_single_test(self, test_index):
        """Simulate running a single test"""
        test = self.tests[test_index]
        
        # Skip if test is not selected to run
        if test["status"] == "Not Tested":
            return
        
        # Mark as in progress
        test["status"] = "In Progress"
        test["start_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_results()
        
        # Simulate different execution times based on markers
        marker = test["markers"][0]
        if marker == "performance":
            base_time = random.randint(8, 15)
        elif marker == "ui":
            base_time = random.randint(5, 10)
        elif marker == "smoke":
            base_time = random.randint(1, 3)
        else:
            base_time = random.randint(2, 6)
        
        time.sleep(base_time)
        
        # Use predetermined outcome
        outcome = test["predetermined_outcome"]
        test["status"] = outcome
        test["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate execution time
        start_dt = datetime.strptime(test["start_time"], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(test["end_time"], '%Y-%m-%d %H:%M:%S')
        duration = end_dt - start_dt
        test["execution_time"] = f"{duration.seconds // 60:02d}:{duration.seconds % 60:02d}"
        
        # Add exception log for failed tests and errors
        if outcome in ["Failed", "Error"]:
            test["exception_log"] = self.generate_marker_specific_error(marker, outcome, test["name"])
        
        self.save_results()

    def generate_marker_specific_error(self, marker, outcome_type, test_name):
        """Generate marker-specific error messages"""
        error_map = {
            "smoke": {
                "Failed": [
                    "AssertionError: Basic health check failed - service not responding",
                    "ConnectionError: Unable to connect to main application endpoint"
                ],
                "Error": [
                    "Exception: Critical service dependency unavailable",
                    "RuntimeError: Application startup sequence failed"
                ]
            },
            "regression": {
                "Failed": [
                    "AssertionError: Feature behavior changed from previous version",
                    "ValueError: Data validation rules have been modified unexpectedly"
                ],
                "Error": [
                    "Exception: Legacy compatibility check crashed",
                    "SystemError: Backward compatibility module not found"
                ]
            },
            "ui": {
                "Failed": [
                    "selenium.common.exceptions.NoSuchElementException: Button 'Submit' not found",
                    "AssertionError: Expected page title 'Dashboard' but got 'Error 404'"
                ],
                "Error": [
                    "selenium.common.exceptions.WebDriverException: Chrome browser crashed",
                    "Exception: UI automation framework initialization failed"
                ]
            },
            "performance": {
                "Failed": [
                    "AssertionError: Response time 5.2s exceeded threshold of 2.0s",
                    "TimeoutError: Load test failed - too many concurrent users"
                ],
                "Error": [
                    "Exception: Performance monitoring tools crashed during test",
                    "MemoryError: System ran out of memory during load testing"
                ]
            },
            "security": {
                "Failed": [
                    "AssertionError: Unauthorized access was not properly blocked",
                    "SecurityError: Weak password was accepted by system"
                ],
                "Error": [
                    "Exception: Security scanner tool encountered fatal error",
                    "CertificateError: SSL certificate validation framework crashed"
                ]
            }
        }
        
        error_list = error_map.get(marker, {}).get(outcome_type, ["Generic error occurred"])
        selected_error = random.choice(error_list)
        
        stack_trace = f"""Traceback (most recent call last):
  File "/opt/app/tests/{marker}/test_{test_name}.py", line {random.randint(25, 75)}, in {test_name}
    result = execute_{marker}_test(test_data)
  File "/opt/app/lib/{marker}_utils.py", line {random.randint(45, 120)}, in execute_{marker}_test
    response = {marker}_client.run_test(params)
  File "/opt/app/lib/{marker}_client.py", line {random.randint(70, 150)}, in run_test
    return self.process_request(params)
{selected_error}

Test Details:
- Test Category: {marker}
- Test Name: {test_name}
- Outcome Type: {outcome_type}
- Test Environment: staging
- Error Code: {marker.upper()}_{random.randint(1000, 9999)}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return stack_trace
    
    def save_results(self):
        """Save current state to JSON file"""
        # Calculate counts
        passed = sum(1 for t in self.tests if t["status"] == "Passed")
        failed = sum(1 for t in self.tests if t["status"] == "Failed")
        error = sum(1 for t in self.tests if t["status"] == "Error")
        skipped = sum(1 for t in self.tests if t["status"] == "Skipped")
        inprogress = sum(1 for t in self.tests if t["status"] == "In Progress")
        not_started = sum(1 for t in self.tests if t["status"] == "Not Started")
        not_tested = sum(1 for t in self.tests if t["status"] == "Not Tested")
        
        # Calculate marker statistics
        marker_stats = {}
        for marker in self.available_markers:
            marker_tests = [t for t in self.tests if marker in t.get("markers", [])]
            if marker_tests:
                marker_stats[marker] = {
                    "total": len(marker_tests),
                    "passed": sum(1 for t in marker_tests if t["status"] == "Passed"),
                    "failed": sum(1 for t in marker_tests if t["status"] == "Failed"),
                    "error": sum(1 for t in marker_tests if t["status"] == "Error"),
                    "skipped": sum(1 for t in marker_tests if t["status"] == "Skipped"),
                    "in_progress": sum(1 for t in marker_tests if t["status"] == "In Progress"),
                    "not_started": sum(1 for t in marker_tests if t["status"] == "Not Started"),
                    "not_tested": sum(1 for t in marker_tests if t["status"] == "Not Tested")
                }
        
        # Determine overall status
        if not_started > 0 or inprogress > 0:
            overall_status = "Running"
        else:
            overall_status = "Completed"
        
        # Calculate overall execution time by summing individual test times
        total_execution_seconds = 0
        completed_tests = [t for t in self.tests if t["status"] in ["Passed", "Failed", "Error", "Skipped"] and t["execution_time"]]
        
        for test in completed_tests:
            if test["execution_time"]:
                # Parse execution time (format: "MM:SS")
                try:
                    time_parts = test["execution_time"].split(":")
                    if len(time_parts) == 2:
                        minutes = int(time_parts[0])
                        seconds = int(time_parts[1])
                        total_execution_seconds += (minutes * 60) + seconds
                except (ValueError, IndexError):
                    # Skip if execution time format is invalid
                    continue
        
        # Format total execution time
        if overall_status == "Completed" and total_execution_seconds > 0:
            total_hours = total_execution_seconds // 3600
            total_minutes = (total_execution_seconds % 3600) // 60
            remaining_seconds = total_execution_seconds % 60
            
            if total_hours > 0:
                overall_time = f"{total_hours:02d}:{total_minutes:02d}:{remaining_seconds:02d}"
            else:
                overall_time = f"{total_minutes:02d}:{remaining_seconds:02d}"
        else:
            # While running, show elapsed wall clock time
            current_time = datetime.now()
            overall_duration = current_time - self.start_time
            wall_clock_seconds = overall_duration.total_seconds()
            hours = int(wall_clock_seconds // 3600)
            minutes = int((wall_clock_seconds % 3600) // 60)
            seconds = int(wall_clock_seconds % 60)
            
            if hours > 0:
                overall_time = f"{hours:02d}:{minutes:02d}:{seconds:02d} (elapsed)"
            else:
                overall_time = f"{minutes:02d}:{seconds:02d} (elapsed)"
        
        # Calculate end time - only set when completed
        current_time = datetime.now()
        end_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S') if overall_status == "Completed" else ""
        
        data = {
            "status": overall_status,
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_time_str,
            "overall_time": overall_time,
            "total_execution_seconds": total_execution_seconds if overall_status == "Completed" else 0,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "inprogress": inprogress,
            "not_tested": not_tested,
            "selected_markers": self.selected_markers,
            "available_markers": self.available_markers,
            "marker_statistics": marker_stats,
            "tests": self.tests
        }
        
        # Write to file
        with open("results.json", "w") as f:
            json.dump(data, f, indent=2)
        
        selected_count = passed + failed + error + skipped + inprogress + not_started
        if overall_status == "Running":
            print(f"Updated: {passed} passed, {failed} failed, {error} errors, {skipped} skipped, {inprogress} in progress, {not_started} not started ({selected_count} selected, {not_tested} not tested) - Elapsed: {overall_time}")
        else:
            print(f"Completed: {passed} passed, {failed} failed, {error} errors, {skipped} skipped ({selected_count} total selected, {not_tested} not tested) - Total execution time: {overall_time}")

    def run_all_tests(self):
        """Run all selected tests sequentially"""
        if self.selected_markers:
            print(f"Starting test execution for markers: {', '.join(self.selected_markers)}")
        else:
            print("Starting test execution for all tests...")
        
        self.save_results()  # Save initial state
        
        for i in range(len(self.tests)):
            if not self.running:
                break
            
            test = self.tests[i]
            if test["status"] != "Not Tested":
                print(f"Running test {i+1}/{len(self.tests)}: {test['name']} (markers: {', '.join(test['markers'])})")
                self.run_single_test(i)
                
                # Small delay between tests
                time.sleep(random.uniform(0.5, 2.0))
        
        print("All selected tests completed!")
        self.running = False
    
    def stop(self):
        """Stop the test runner"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Run pytest simulation with markers')
    parser.add_argument('-m', '--markers', 
                        help='Comma-separated list of markers to run (e.g., "smoke,ui,security")',
                        default='')
    args = parser.parse_args()
    
    # Parse selected markers
    selected_markers = []
    if args.markers:
        selected_markers = [m.strip() for m in args.markers.split(',')]
    
    runner = TestRunner(selected_markers)
    
    # Show available markers
    print("Available markers:")
    for marker, description in runner.available_markers.items():
        status = "SELECTED" if marker in selected_markers else ""
        print(f"  @pytest.mark.{marker}: {description} {status}")
    print()
    
    try:
        # Run tests in a separate thread so we can handle interrupts
        test_thread = threading.Thread(target=runner.run_all_tests)
        test_thread.start()
        
        # Wait for completion or interruption
        test_thread.join()
        
    except KeyboardInterrupt:
        print("\nStopping test execution...")
        runner.stop()

if __name__ == "__main__":
    main()

