#!/usr/bin/env python3
"""
Demo Test Runner untuk WhatsApp Bot
Menjalankan test cases dan menghasilkan laporan penjualan yang profesional

Cara pakai:
  python demo_test_runner.py [--phone 628123456789] [--output report.html]
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml
import httpx
from enum import Enum

# Warna terminal
class Color:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"

class TestStatus(Enum):
    PASS = "✓ PASS"
    FAIL = "✗ FAIL"
    SKIP = "⊘ SKIP"
    ERROR = "⚠ ERROR"

class TestResult:
    def __init__(self, test_case: dict):
        self.step = test_case.get("step")
        self.category = test_case.get("category")
        self.pertanyaan = test_case.get("pertanyaan")
        self.deskripsi = test_case.get("deskripsi")
        self.jawaban_diharapkan_pattern = test_case.get("jawaban_diharapkan_pattern")

        self.status: Optional[TestStatus] = None
        self.jawaban_actual: Optional[str] = None
        self.error_message: Optional[str] = None
        self.waktu_response: float = 0.0
        self.match_score: float = 0.0

    def to_dict(self):
        return {
            "step": self.step,
            "category": self.category,
            "pertanyaan": self.pertanyaan,
            "deskripsi": self.deskripsi,
            "status": self.status.value if self.status else None,
            "jawaban_actual": self.jawaban_actual,
            "error_message": self.error_message,
            "waktu_response": self.waktu_response,
            "match_score": self.match_score,
        }

class DemoTestRunner:
    def __init__(self,
                 api_url: str = "http://localhost:8000",
                 phone_number: str = "628123456789",
                 test_cases_file: str = "test_cases.yaml"):
        self.api_url = api_url
        self.phone_number = phone_number
        self.test_cases_file = test_cases_file
        self.test_cases = []
        self.results = []
        self.business_info = {}

    def load_test_cases(self):
        """Load test cases dari YAML file"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.test_cases = config.get("test_cases", [])
                self.business_info = config.get("business_info", {})
                print(f"{Color.BLUE}✓ Loaded {len(self.test_cases)} test cases{Color.RESET}")
                return True
        except FileNotFoundError:
            print(f"{Color.RED}✗ File not found: {self.test_cases_file}{Color.RESET}")
            return False
        except Exception as e:
            print(f"{Color.RED}✗ Error loading test cases: {e}{Color.RESET}")
            return False

    def check_pattern_match(self, jawaban: str, pattern: str) -> tuple[bool, float]:
        """
        Check apakah jawaban cocok dengan pattern
        Returns: (match, score)
        """
        if not jawaban or not pattern:
            return False, 0.0

        jawaban_lower = jawaban.lower()
        patterns = [p.strip() for p in pattern.split('|')]

        for pat in patterns:
            try:
                if re.search(pat, jawaban_lower, re.IGNORECASE):
                    # Hitung score berdasarkan panjang match
                    score = min(1.0, len(pat) / len(jawaban) * 2)
                    return True, score
            except re.error:
                continue

        return False, 0.0

    async def run_test_case(self, test_case: dict) -> TestResult:
        """Jalankan satu test case"""
        result = TestResult(test_case)
        pertanyaan = test_case.get("pertanyaan")

        try:
            # Kirim pertanyaan
            start_time = datetime.now()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/test/send-message",
                    json={
                        "phone_number": self.phone_number,
                        "message": pertanyaan
                    }
                )

                end_time = datetime.now()
                result.waktu_response = (end_time - start_time).total_seconds()

                if response.status_code != 200:
                    result.status = TestStatus.ERROR
                    result.error_message = f"HTTP {response.status_code}"
                    return result

                resp_data = response.json()
                if not resp_data.get("success"):
                    result.status = TestStatus.ERROR
                    result.error_message = resp_data.get("error", "Unknown error")
                    return result

            # Tunggu sebentar untuk response bot diproses
            await asyncio.sleep(2.0)

            # Ambil chat history
            async with httpx.AsyncClient(timeout=30.0) as client:
                history_response = await client.get(
                    f"{self.api_url}/test/chat-history/{self.phone_number}"
                )

                if history_response.status_code == 200:
                    history_data = history_response.json()
                    messages = history_data.get("messages", [])

                    # Cari response terakhir dari bot (role="assistant")
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant":
                            result.jawaban_actual = msg.get("message")
                            break

            # Validasi jawaban
            if result.jawaban_actual:
                match, score = self.check_pattern_match(
                    result.jawaban_actual,
                    result.jawaban_diharapkan_pattern
                )
                result.match_score = score
                result.status = TestStatus.PASS if match else TestStatus.FAIL
            else:
                result.status = TestStatus.ERROR
                result.error_message = "No response from bot"

        except httpx.ConnectError:
            result.status = TestStatus.ERROR
            result.error_message = f"Cannot connect to {self.api_url}"
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)

        return result

    async def run_all_tests(self):
        """Jalankan semua test cases"""
        print(f"\n{Color.BLUE}Starting test execution...{Color.RESET}\n")
        print(f"Target: {self.api_url}")
        print(f"Phone: {self.phone_number}\n")
        print("-" * 80)

        for i, test_case in enumerate(self.test_cases, 1):
            step = test_case.get("step", i)
            pertanyaan = test_case.get("pertanyaan", "")

            print(f"\nStep {step}: {pertanyaan[:50]}...")
            print(f"  Category: {test_case.get('category')}")

            result = await self.run_test_case(test_case)
            self.results.append(result)

            # Print hasil
            status_color = Color.GREEN if result.status == TestStatus.PASS else Color.RED
            print(f"  Status: {status_color}{result.status.value}{Color.RESET}")
            print(f"  Response time: {result.waktu_response:.2f}s")

            if result.jawaban_actual:
                print(f"  Bot answer: {result.jawaban_actual[:100]}...")
            if result.error_message:
                print(f"  Error: {result.error_message}")

            await asyncio.sleep(1.0)  # Jeda antar test

        print("\n" + "=" * 80)

    def print_summary(self):
        """Print ringkasan hasil"""
        if not self.results:
            print(f"{Color.RED}Tidak ada hasil test{Color.RESET}")
            return

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)

        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n{Color.BLUE}TEST SUMMARY{Color.RESET}")
        print(f"Total Tests: {total}")
        print(f"{Color.GREEN}Passed: {passed}{Color.RESET}")
        print(f"{Color.RED}Failed: {failed}{Color.RESET}")
        print(f"{Color.YELLOW}Errors: {errors}{Color.RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        # Breakdown per kategori
        categories = {}
        for result in self.results:
            cat = result.category
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result.status == TestStatus.PASS:
                categories[cat]["passed"] += 1

        print(f"\n{Color.BLUE}By Category:{Color.RESET}")
        for cat, stats in categories.items():
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

    def generate_html_report(self, output_file: str = "test_report.html"):
        """Generate HTML report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        pass_rate = (passed / total * 100) if total > 0 else 0

        # Group results by category
        by_category = {}
        for result in self.results:
            cat = result.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Bot - Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        .metric {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .metric h3 {{ color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
        .metric .value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric.pass .value {{ color: #28a745; }}
        .metric.fail .value {{ color: #dc3545; }}
        .metric.error .value {{ color: #ffc107; }}
        .metric.total .value {{ color: #667eea; }}
        .pass-rate {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .pass-rate h3 {{ font-size: 12px; text-transform: uppercase; margin-bottom: 10px; opacity: 0.9; }}
        .pass-rate .value {{ font-size: 48px; font-weight: bold; }}
        .content {{ padding: 40px; }}
        .category {{
            margin-bottom: 40px;
        }}
        .category h2 {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .test-item {{
            background: #f8f9fa;
            border-left: 4px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .test-item.pass {{ border-left-color: #28a745; background: #f0fdf4; }}
        .test-item.fail {{ border-left-color: #dc3545; background: #fdf0f0; }}
        .test-item.error {{ border-left-color: #ffc107; background: #fffbf0; }}
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }}
        .test-question {{
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        .test-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .test-status.pass {{ background: #28a745; color: white; }}
        .test-status.fail {{ background: #dc3545; color: white; }}
        .test-status.error {{ background: #ffc107; color: white; }}
        .test-description {{
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }}
        .test-response {{
            background: white;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 8px;
            max-height: 100px;
            overflow-y: auto;
        }}
        .test-meta {{
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: #999;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #ddd;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            width: {pass_rate}%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 WhatsApp Bot Test Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="metric total">
                <h3>Total Tests</h3>
                <div class="value">{total}</div>
            </div>
            <div class="metric pass">
                <h3>Passed</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="metric fail">
                <h3>Failed</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="metric error">
                <h3>Errors</h3>
                <div class="value">{errors}</div>
            </div>
            <div class="pass-rate">
                <h3>Pass Rate</h3>
                <div class="value">{pass_rate:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        </div>

        <div class="content">
"""

        # Add test results by category
        for category in sorted(by_category.keys()):
            results_in_cat = by_category[category]
            html += f'<div class="category"><h2>{category}</h2>'

            for result in results_in_cat:
                status_lower = result.status.name.lower()
                html += f'''
            <div class="test-item {status_lower}">
                <div class="test-header">
                    <div>
                        <div class="test-question">Step {result.step}: {result.pertanyaan}</div>
                        <div class="test-description">{result.deskripsi}</div>
                    </div>
                    <div class="test-status {status_lower}">{result.status.value}</div>
                </div>
                <div class="test-response"><strong>Q:</strong> {result.pertanyaan}<br><strong>A:</strong> {result.jawaban_actual or result.error_message or 'N/A'}</div>
                <div class="test-meta">
                    <span>Response time: {result.waktu_response:.2f}s</span>
                    <span>Match score: {result.match_score:.0%}</span>
                </div>
            </div>
'''

            html += '</div>'

        html += f"""
        </div>

        <div class="footer">
            <p>WhatsApp Bot Demo Test Report | {self.api_url}</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n{Color.GREEN}✓ HTML report saved to: {output_file}{Color.RESET}")

    def save_json_report(self, output_file: str = "test_report.json"):
        """Save results as JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "api_url": self.api_url,
            "phone_number": self.phone_number,
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == TestStatus.PASS),
                "failed": sum(1 for r in self.results if r.status == TestStatus.FAIL),
                "errors": sum(1 for r in self.results if r.status == TestStatus.ERROR),
            },
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"{Color.GREEN}✓ JSON report saved to: {output_file}{Color.RESET}")

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Demo test runner untuk WhatsApp Bot")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    parser.add_argument("--phone", default="628123456789", help="Phone number for testing")
    parser.add_argument("--test-cases", default="test_cases.yaml", help="Test cases file")
    parser.add_argument("--html", default="test_report.html", help="HTML output file")
    parser.add_argument("--json", default="test_report.json", help="JSON output file")

    args = parser.parse_args()

    runner = DemoTestRunner(
        api_url=args.api,
        phone_number=args.phone,
        test_cases_file=args.test_cases
    )

    if not runner.load_test_cases():
        sys.exit(1)

    await runner.run_all_tests()
    runner.print_summary()
    runner.generate_html_report(args.html)
    runner.save_json_report(args.json)

    print(f"\n{Color.GREEN}✓ Testing complete!{Color.RESET}")

if __name__ == "__main__":
    asyncio.run(main())
