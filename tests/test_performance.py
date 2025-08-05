#!/usr/bin/env python3
"""
JARVIS Performance Optimization Test Suite
Demonstrates before/after performance improvements.
"""

import time
import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_jarvis():
    """Test basic JARVIS performance"""
    print("🧪 Testing Basic JARVIS Performance")
    print("=" * 50)
    
    try:
        from jarvis import ask_jarvis
        
        test_queries = [
            "Hello JARVIS",
            "How are you today?",
            "What's the weather like?",
            "Thank you"
        ]
        
        times = []
        for query in test_queries:
            start = time.time()
            response = ask_jarvis(query, text_mode=True, speaker="Test")
            duration = (time.time() - start) * 1000
            times.append(duration)
            print(f"   {query}: {duration:.1f}ms -> {response[:50]}...")
        
        avg_time = sum(times) / len(times)
        print(f"\n📊 Basic JARVIS Average: {avg_time:.1f}ms")
        return avg_time
        
    except Exception as e:
        print(f"❌ Basic JARVIS test failed: {e}")
        return None

def test_optimized_jarvis():
    """Test optimized JARVIS performance"""
    print("\n🚀 Testing Optimized JARVIS Performance")
    print("=" * 50)
    
    try:
        from jarvis_optimized import ask_jarvis_optimized, benchmark_jarvis
        
        # Run comprehensive benchmark
        results = benchmark_jarvis(num_tests=4)
        
        if "summary" in results:
            summary = results["summary"]
            print(f"   Average total time: {summary['avg_total_time_ms']:.1f}ms")
            print(f"   Average first token: {summary['avg_first_token_ms']:.1f}ms")
            print(f"   Fastest response: {summary['min_total_time_ms']:.1f}ms")
            print(f"   Success rate: {summary['success_rate']:.1f}%")
            
            return summary['avg_total_time_ms']
        else:
            print("❌ Optimized benchmark failed")
            return None
            
    except Exception as e:
        print(f"❌ Optimized JARVIS test failed: {e}")
        return None

async def test_streaming_performance():
    """Test streaming performance specifically"""
    print("\n⚡ Testing Streaming Performance")
    print("=" * 50)
    
    try:
        from jarvis_optimized import ask_jarvis_streaming
        
        query = "Tell me about artificial intelligence in simple terms"
        
        start_time = time.time()
        metrics = await ask_jarvis_streaming(query, "StreamTest")
        
        print(f"   Total response time: {metrics.total_response_time*1000:.1f}ms")
        print(f"   First token time: {metrics.llm_first_token_time*1000:.1f}ms")
        print(f"   LLM completion: {metrics.llm_complete_time*1000:.1f}ms")
        print(f"   TTS completion: {metrics.tts_complete_time*1000:.1f}ms")
        
        return metrics.total_response_time * 1000
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return None

def main():
    """Run complete performance test suite"""
    print("🎯 JARVIS Performance Optimization Test Suite")
    print("=" * 60)
    
    # Test basic performance
    basic_time = test_basic_jarvis()
    
    # Test optimized performance
    optimized_time = test_optimized_jarvis()
    
    # Test streaming performance
    streaming_time = asyncio.run(test_streaming_performance())
    
    # Performance summary
    print("\n🏆 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if basic_time and optimized_time:
        improvement = ((basic_time - optimized_time) / basic_time) * 100
        print(f"📈 Performance Improvement: {improvement:.1f}%")
        print(f"⏱️  Basic JARVIS: {basic_time:.1f}ms")
        print(f"🚀 Optimized JARVIS: {optimized_time:.1f}ms")
        
        if streaming_time:
            streaming_improvement = ((basic_time - streaming_time) / basic_time) * 100
            print(f"⚡ Streaming JARVIS: {streaming_time:.1f}ms ({streaming_improvement:.1f}% improvement)")
    
    print("\n🎯 OPTIMIZATION TECHNIQUES USED:")
    print("   ✅ Token streaming (immediate response start)")
    print("   ✅ Fast model selection (gpt-3.5-turbo for simple queries)")
    print("   ✅ Response caching (repeated queries)")
    print("   ✅ Persistent HTTP sessions (connection reuse)")
    print("   ✅ Async TTS processing (overlapped speech synthesis)")
    print("   ✅ Connection pre-warming (reduced cold starts)")
    print("   ✅ Minimal prompt optimization (reduced token overhead)")
    
    print("\n💡 RECOMMENDATIONS:")
    print("   • Use --speed flag for maximum performance")
    print("   • Deploy in same region as OpenAI (us-east-1)")
    print("   • Consider ElevenLabs for fastest TTS")
    print("   • Monitor cache hit rate for optimization")

if __name__ == "__main__":
    main()
