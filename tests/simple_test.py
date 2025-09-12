#!/usr/bin/env python3
"""
Simple test for ContractCritic backend core functionality
"""
import os
import sys

def test_imports():
    """Test that all modules can be imported correctly"""
    print("🧪 Testing Module Imports")
    print("=" * 40)
    
    try:
        from src.models.contract import Contract, ContractAnalysis, RiskFactor
        print("✅ Contract models imported successfully")
    except Exception as e:
        print(f"❌ Contract models import failed: {e}")
        return False
    
    try:
        from src.models.user import User, db
        print("✅ User model imported successfully")
    except Exception as e:
        print(f"❌ User model import failed: {e}")
        return False
    
    try:
        from src.services.contract_analyzer import ContractAnalyzer
        print("✅ ContractAnalyzer service imported successfully")
    except Exception as e:
        print(f"❌ ContractAnalyzer import failed: {e}")
        return False
    
    try:
        from src.routes.contract import contract_bp
        print("✅ Contract routes imported successfully")
    except Exception as e:
        print(f"❌ Contract routes import failed: {e}")
        return False
    
    return True

def test_contract_analyzer():
    """Test ContractAnalyzer functionality"""
    print("\n🔬 Testing ContractAnalyzer")
    print("=" * 40)
    
    try:
        from src.services.contract_analyzer import ContractAnalyzer
        
        analyzer = ContractAnalyzer()
        
        # Test text cleaning
        sample_text = "This is a   test   contract with\nexcessive\twhitespace."
        cleaned = analyzer._clean_text(sample_text)
        print(f"✅ Text cleaning: '{sample_text[:20]}...' -> '{cleaned[:20]}...'")
        
        # Test model selection
        model = analyzer.select_ai_model(5000, "quick_summary")
        print(f"✅ Model selection: {model} for 5000 chars")
        
        # Test cost estimation
        cost = analyzer.estimate_analysis_cost(5000, "gpt-3.5-turbo")
        print(f"✅ Cost estimation: ${cost:.4f} for 5000 chars")
        
        # Test risk score calculation
        sample_analysis = {
            'risk_assessment': {
                'overall_risk_level': 'Medium',
                'risk_factors': ['Payment terms unclear', 'No termination clause'],
                'red_flags': ['Unlimited liability'],
                'missing_clauses': ['Data protection', 'IP ownership']
            }
        }
        
        risk_score = analyzer._calculate_risk_score(sample_analysis)
        risk_level = analyzer._get_risk_level(risk_score)
        print(f"✅ Risk calculation: {risk_score:.1f}/100 ({risk_level})")
        
        # Test risk factor extraction
        risk_factors = analyzer.extract_risk_factors(sample_analysis)
        print(f"✅ Risk factor extraction: {len(risk_factors)} factors found")
        
        return True
        
    except Exception as e:
        print(f"❌ ContractAnalyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test database models"""
    print("\n🗄️  Testing Database Models")
    print("=" * 40)
    
    try:
        from src.models.contract import Contract, ContractAnalysis, RiskFactor
        from datetime import datetime
        
        # Test Contract model
        contract = Contract(
            user_id=1,
            filename="test.pdf",
            original_filename="test_contract.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        
        contract_dict = contract.to_dict()
        print(f"✅ Contract model: {contract_dict['filename']}")
        
        # Test ContractAnalysis model
        analysis = ContractAnalysis(
            contract_id=1,
            ai_model_used="gpt-3.5-turbo",
            analysis_type="comprehensive",
            risk_score=65.5,
            risk_level="Medium"
        )
        
        # Test JSON handling
        test_results = {"test": "data", "risk_level": "Medium"}
        analysis.set_analysis_results(test_results)
        retrieved_results = analysis.get_analysis_results()
        
        print(f"✅ Analysis model: JSON handling works")
        print(f"   Stored: {test_results}")
        print(f"   Retrieved: {retrieved_results}")
        
        # Test RiskFactor model
        risk_factor = RiskFactor(
            analysis_id=1,
            category="Payment Risk",
            severity="high",
            description="Payment terms are unclear",
            recommendation="Clarify payment schedule"
        )
        
        risk_dict = risk_factor.to_dict()
        print(f"✅ RiskFactor model: {risk_dict['category']} ({risk_dict['severity']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask app creation"""
    print("\n🌐 Testing Flask App")
    print("=" * 40)
    
    try:
        from src.main import app
        
        with app.app_context():
            print("✅ Flask app created successfully")
            print(f"   App name: {app.name}")
            print(f"   Debug mode: {app.debug}")
            
            # Test that database tables can be created
            from src.models.user import db
            db.create_all()
            print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 ContractCritic Backend - Core Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Models", test_models),
        ("ContractAnalyzer Service", test_contract_analyzer),
        ("Flask Application", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

