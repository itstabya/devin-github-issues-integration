#!/usr/bin/env python3
"""
Test script for Option B endpoint verification.
Tests the Devin API endpoints: POST /v1/sessions and GET /v1/session/{id}
"""

import os
import time
import requests
import json
from typing import Optional, Dict, Any

class OptionBEndpointTester:
    def __init__(self, devin_token: Optional[str] = None):
        self.devin_token = devin_token or os.getenv('DEVIN_API_TOKEN')
        self.devin_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.devin_token}' if self.devin_token else None
        }
        self.devin_base_url = 'https://api.devin.ai'
        
    def test_session_creation_endpoint(self) -> Dict[str, Any]:
        """Test POST /v1/sessions endpoint (session creation)."""
        print("🧪 Testing session creation endpoint: POST /v1/sessions")
        
        if not self.devin_token:
            return {
                'success': False,
                'error': 'No Devin API token available',
                'endpoint': 'POST /v1/sessions'
            }
        
        url = f"{self.devin_base_url}/v1/sessions"
        payload = {
            "prompt": "Test prompt for endpoint verification - please respond with a simple JSON object containing 'test': 'success'",
            "unlisted": True
        }
        
        try:
            print(f"  📤 Making request to: {url}")
            response = requests.post(url, headers=self.devin_headers, json=payload, timeout=30)
            
            print(f"  📊 Response status: {response.status_code}")
            print(f"  📊 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                session_id = result.get('session_id')
                print(f"  ✅ Session created successfully: {session_id}")
                return {
                    'success': True,
                    'session_id': session_id,
                    'response': result,
                    'endpoint': 'POST /v1/sessions'
                }
            else:
                print(f"  ❌ Session creation failed: {response.status_code}")
                print(f"  📄 Response body: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'response_text': response.text,
                    'endpoint': 'POST /v1/sessions'
                }
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'endpoint': 'POST /v1/sessions'
            }
    
    def test_session_polling_endpoint(self, session_id: str, max_polls: int = 5) -> Dict[str, Any]:
        """Test GET /v1/session/{id} endpoint (Option B polling)."""
        print(f"🧪 Testing session polling endpoint: GET /v1/session/{session_id}")
        
        if not self.devin_token:
            return {
                'success': False,
                'error': 'No Devin API token available',
                'endpoint': f'GET /v1/session/{session_id}'
            }
        
        url = f"{self.devin_base_url}/v1/session/{session_id}"
        poll_results = []
        
        try:
            for poll_num in range(max_polls):
                print(f"  📤 Poll #{poll_num + 1}: Making request to: {url}")
                response = requests.get(url, headers=self.devin_headers, timeout=30)
                
                print(f"  📊 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    latest_status = result.get('latest_status_contents', {})
                    agent_status = latest_status.get('agent_status', '')
                    status_enum = latest_status.get('enum', '')
                    
                    poll_result = {
                        'poll_number': poll_num + 1,
                        'agent_status': agent_status,
                        'status_enum': status_enum,
                        'response': result
                    }
                    poll_results.append(poll_result)
                    
                    print(f"  📊 Agent status: {agent_status}, Enum: {status_enum}")
                    
                    if agent_status == 'finished':
                        print(f"  ✅ Session completed after {poll_num + 1} polls")
                        return {
                            'success': True,
                            'session_id': session_id,
                            'polls': poll_results,
                            'final_status': agent_status,
                            'endpoint': f'GET /v1/session/{session_id}'
                        }
                    elif status_enum in ['expired', 'failed']:
                        print(f"  ⚠️ Session ended with status: {status_enum}")
                        return {
                            'success': True,
                            'session_id': session_id,
                            'polls': poll_results,
                            'final_status': status_enum,
                            'endpoint': f'GET /v1/session/{session_id}'
                        }
                    
                    if poll_num < max_polls - 1:
                        print(f"  ⏳ Waiting 10 seconds before next poll...")
                        time.sleep(10)
                        
                else:
                    print(f"  ❌ Polling failed: {response.status_code}")
                    print(f"  📄 Response body: {response.text}")
                    return {
                        'success': False,
                        'status_code': response.status_code,
                        'response_text': response.text,
                        'polls': poll_results,
                        'endpoint': f'GET /v1/session/{session_id}'
                    }
            
            print(f"  ⏰ Reached maximum polls ({max_polls}), session still running")
            return {
                'success': True,
                'session_id': session_id,
                'polls': poll_results,
                'final_status': 'timeout',
                'endpoint': f'GET /v1/session/{session_id}'
            }
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'polls': poll_results,
                'endpoint': f'GET /v1/session/{session_id}'
            }
    
    def test_invalid_session_polling(self) -> Dict[str, Any]:
        """Test polling with invalid session ID to verify error handling."""
        print("🧪 Testing invalid session polling (error handling)")
        
        if not self.devin_token:
            return {
                'success': False,
                'error': 'No Devin API token available',
                'endpoint': 'GET /v1/session/invalid'
            }
        
        invalid_session_id = "invalid-session-id-12345"
        url = f"{self.devin_base_url}/v1/session/{invalid_session_id}"
        
        try:
            print(f"  📤 Making request to: {url}")
            response = requests.get(url, headers=self.devin_headers, timeout=30)
            
            print(f"  📊 Response status: {response.status_code}")
            print(f"  📄 Response body: {response.text}")
            
            if response.status_code in [404, 400, 401, 403]:
                print(f"  ✅ Error handling works correctly: {response.status_code}")
                return {
                    'success': True,
                    'expected_error': True,
                    'status_code': response.status_code,
                    'response_text': response.text,
                    'endpoint': f'GET /v1/session/{invalid_session_id}'
                }
            else:
                print(f"  ⚠️ Unexpected response for invalid session: {response.status_code}")
                return {
                    'success': False,
                    'unexpected_response': True,
                    'status_code': response.status_code,
                    'response_text': response.text,
                    'endpoint': f'GET /v1/session/{invalid_session_id}'
                }
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'endpoint': f'GET /v1/session/{invalid_session_id}'
            }
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete Option B endpoint verification."""
        print("🚀 Starting Option B Endpoint Verification")
        print("=" * 60)
        
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'devin_api_base_url': self.devin_base_url,
            'has_token': bool(self.devin_token),
            'tests': {}
        }
        
        print("\n1️⃣ Testing Session Creation Endpoint")
        creation_result = self.test_session_creation_endpoint()
        results['tests']['session_creation'] = creation_result
        
        if creation_result.get('success') and creation_result.get('session_id'):
            print("\n2️⃣ Testing Session Polling Endpoint")
            polling_result = self.test_session_polling_endpoint(creation_result['session_id'])
            results['tests']['session_polling'] = polling_result
        else:
            print("\n2️⃣ Skipping Session Polling (creation failed)")
            results['tests']['session_polling'] = {
                'success': False,
                'skipped': True,
                'reason': 'Session creation failed'
            }
        
        print("\n3️⃣ Testing Error Handling")
        error_result = self.test_invalid_session_polling()
        results['tests']['error_handling'] = error_result
        
        print("\n" + "=" * 60)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for test_name, test_result in results['tests'].items():
            status = "✅ PASS" if test_result.get('success') else "❌ FAIL"
            if test_result.get('skipped'):
                status = "⏭️ SKIP"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            if not test_result.get('success') and not test_result.get('skipped'):
                all_passed = False
        
        results['overall_success'] = all_passed
        print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return results

def main():
    """Main function to run the verification."""
    tester = OptionBEndpointTester()
    results = tester.run_full_verification()
    
    results_file = 'option_b_verification_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return 0 if results['overall_success'] else 1

if __name__ == '__main__':
    exit(main())
