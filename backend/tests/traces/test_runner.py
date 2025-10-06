"""Test runner for simulated customer conversations"""
import asyncio
import json
import sys
from datetime import datetime
import redis

from realtime_client import RealtimeClient
from customer_simulator import CustomerSimulator
from llm_judge import ConversationJudge


def connect_redis():
    """Connect to Redis server"""
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        r.ping()
        return r
    except redis.ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return None


def load_test_data():
    """Load test cases from JSON file"""
    with open('backend/tests/traces/test_cases.json', 'r') as f:
        return json.load(f)


def save_test_result(data, result):
    """Save a single test result to Redis"""
    r = connect_redis()
    if not r:
        print("❌ Cannot save results - Redis connection failed")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f"test_result:{timestamp}:{result['test_name']}"
    
    result_data = {
        'test_suite': json.dumps(data['test_suite']),
        'test_name': result['test_name'],
        'subject': result['subject'],
        'timestamp': result['timestamp'],
        'conversation': json.dumps(result['conversation']),
        'tools_called': json.dumps(result['tools_called']),
        'expected_tools': json.dumps(result['expected_tools']),
        'expected_outcome': result['expected_outcome'],
        'turns': result['turns'],
        'validation': json.dumps(result['validation']),
        'judge_evaluation': json.dumps(result['judge_evaluation'])
    }
    r.hset(key, mapping=result_data)
    r.incr('test_results:count')
    return key


async def run_conversation(test_case, customer, agent, judge):
    """Run a single conversation turn-by-turn"""
    conversation, evaluations = [], []
    status_emoji = {'success': '✅', 'failed': '❌', 'in_progress': '⏳'}
    
    for turn in range(10):  # max_turns
        customer_msg = customer.generate_message(conversation)
        if customer_msg is None:
            await asyncio.sleep(0.5)
            continue
        
        print(f"👤 Customer: {customer_msg}")
        conversation.append({"role": "customer", "content": customer_msg})
        
        agent_response = await agent.send_message(customer_msg)
        print(f"🤖 Agent: {agent_response}\n")
        conversation.append({"role": "agent", "content": agent_response})
        
        evaluation = judge.evaluate_conversation(conversation, test_case['goal'], test_case['expected_outcome'])
        evaluations.append(evaluation)
        print(f"  {status_emoji.get(evaluation['status'], '❓')} Judge: {evaluation['status']} - {evaluation['reason']} (confidence: {evaluation['confidence']:.2f})")
        
        tools_called = [t['name'] for t in agent.tools_called]
        all_tools_called = all(tool in tools_called for tool in test_case['expected_tools'])
        
        if all_tools_called:
            print(f"  🎯 All expected tools called: {test_case['expected_tools']}")
            if not evaluation['should_continue'] or (evaluation['status'] in ['success', 'failed'] and agent_response.strip()):
                print(f"\n{'='*80}\nConversation ended: All tools called | Status: {evaluation['status']}\n{'='*80}\n")
                break
        
        if not evaluation['should_continue']:
            print(f"\n{'='*80}\nConversation ended: {evaluation['status']} - {evaluation['reason']}\n{'='*80}\n")
            break
    
    return conversation, evaluations


async def run_test(test_case):
    """Run a single test case"""
    print(f"\n{'='*80}\nRunning: {test_case['test_name']}\nSubject: {test_case['subject']}\n{'='*80}\n")
    
    customer = CustomerSimulator(test_case['customer_id'], test_case['customer_name'],
                                  test_case['story'], test_case['situation'],
                                  test_case['goal'], test_case['behavior_notes'])
    agent = RealtimeClient()
    await agent.connect()
    print("✅ Connected to agent\n")
    
    try:
        conversation, evaluations = await run_conversation(test_case, customer, agent, ConversationJudge())
        
        tools_called = [t['name'] for t in agent.tools_called]
        tools_match = all(tool in tools_called for tool in test_case['expected_tools'])
        final_eval = evaluations[-1] if evaluations else {}
        
        result = {
            "test_name": test_case['test_name'], "subject": test_case['subject'],
            "conversation": conversation, "tools_called": agent.tools_called,
            "expected_tools": test_case['expected_tools'], "expected_outcome": test_case['expected_outcome'],
            "turns": len(conversation) // 2, "timestamp": datetime.now().isoformat(),
            "validation": {"expected_tools_called": tools_match, "tools_called": tools_called},
            "judge_evaluation": {
                "final_status": final_eval.get('status', 'unknown'),
                "final_reason": final_eval.get('reason', 'No evaluation'),
                "confidence": final_eval.get('confidence', 0.0),
                "all_evaluations": evaluations
            }
        }
        
        print(f"{'='*80}\nTest: {test_case['test_name']}\n")
        print(f"Judge Status: {final_eval.get('status', 'unknown')} | Tools Match: {tools_match}")
        print(f"Expected Tools: {test_case['expected_tools']}")
        print(f"Called Tools: {tools_called}\n{'='*80}\n")
        return result
    finally:
        await agent.close()


async def run_tests(test_num=None):
    """Run either a single test or all tests"""
    data = load_test_data()
    test_cases = data['test_cases']
    
    if test_num:
        if test_num < 1 or test_num > len(test_cases):
            print(f"❌ Test number {test_num} out of range (1-{len(test_cases)})")
            return
        print(f"\n{'='*80}\nRunning test #{test_num}: {data['test_suite']['name']}\n{'='*80}\n")
        result = await run_test(test_cases[test_num - 1])
        redis_key = save_test_result(data, result)
        tools_passed = result.get('validation', {}).get('expected_tools_called', False)
        judge_passed = result.get('judge_evaluation', {}).get('final_status') == 'success'
        overall_passed = tools_passed and judge_passed
        
        print(f"Result saved to Redis: {redis_key}")
        print(f"Summary: Test {'PASSED ✅' if overall_passed else 'FAILED ❌'}")
        print(f"  - Tools validation: {'✅ PASS' if tools_passed else '❌ FAIL'}")
        print(f"  - Judge evaluation: {'✅ PASS' if judge_passed else '❌ FAIL'}")
    else:
        print(f"\n{'='*80}\nTest suite: {data['test_suite']['name']} | Total: {len(test_cases)}\n{'='*80}\n")
        results = []
        for test_case in test_cases:
            try:
                result = await run_test(test_case)
                results.append(result)
                save_test_result(data, result)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Test failed: {e}")
                error_result = {"test_name": test_case['test_name'], "error": str(e),
                               "timestamp": datetime.now().isoformat()}
                results.append(error_result)
        
        passed = sum(1 for r in results if (
            r.get('validation', {}).get('expected_tools_called', False) and
            r.get('judge_evaluation', {}).get('final_status') == 'success'
        ))
        print(f"All tests completed!\nResults saved to Redis (individual test results)\nSummary: {passed}/{len(results)} passed")


if __name__ == "__main__":
    test_num = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    if len(sys.argv) > 1 and not test_num:
        print(f"❌ Invalid test number. Usage:\n  python test_runner.py [test_number]\n  python test_runner.py 1  # Run test #1")
    else:
        asyncio.run(run_tests(test_num))