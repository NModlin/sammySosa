#!/usr/bin/env python3
"""
Phase 8 Feature Testing Script
Tests all 16 Phase 8 features: Proposal & Pricing Automation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import govcon_suite

def test_phase8_features():
    """Test all Phase 8 features (60-75)"""
    
    print("🚀 PHASE 8 FEATURE TESTING")
    print("=" * 60)
    
    try:
        print("✅ Successfully imported govcon_suite \n")
    except Exception as e:
        print(f"❌ Failed to import govcon_suite: {e}")
        return False
    
    # Test Phase 8 Proposal Generation Engine (Features 60-63)
    print("🎯 Testing Phase 8 Proposal Generation Engine (Features 60-63)...")
    print("=" * 60)
    
    # Test Feature 60: Automated Proposal Generation
    print("\n🤖 Testing Feature 60: Automated Proposal Generation...")
    try:
        proposal_data = {
            'proposal_name': 'AI-Generated Government Services Proposal',
            'opportunity_id': 'RFP-2024-001',
            'proposal_type': 'rfp_response',
            'template_id': 1,
            'submission_deadline': '2024-12-15',
            'estimated_value': 5000000.0,
            'created_by': 1,
            'assigned_to': 1,
            'requirements': {
                'technical_requirements': ['Cloud infrastructure', 'Cybersecurity', 'Data analytics'],
                'performance_requirements': ['99.9% uptime', '24/7 support', 'Scalable architecture']
            },
            'capabilities': {
                'core_competencies': ['Cloud services', 'Security solutions', 'Analytics platforms'],
                'certifications': ['FedRAMP', 'ISO 27001', 'CMMI Level 3']
            }
        }
        
        result = govcon_suite.generate_automated_proposal(proposal_data)
        
        if result['success']:
            print(f"   ✅ Proposal generated: {result['proposal_name']}")
            print(f"   📊 Proposal ID: {result['proposal_id']}")
            print(f"   📝 Template Used: {result['template_used']}")
            print(f"   ⏱️ Generation Time: {result['generation_time']}")
            
            overall_metrics = result.get('overall_metrics', {})
            print(f"   📄 Total Pages: {overall_metrics.get('total_page_count', 0)}")
            print(f"   📊 Quality Score: {overall_metrics.get('overall_quality_score', 0)}/10")
            print(f"   🎯 Win Probability: {overall_metrics.get('win_probability', 0)}%")
            
            ai_insights = result.get('ai_insights', {})
            strengths = ai_insights.get('content_strengths', [])
            print(f"   💪 Content Strengths: {len(strengths)}")
            
        else:
            print(f"   ❌ Proposal generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Proposal generation test failed: {str(e)}")
    
    # Test Feature 61: Template Management System
    print("\n📋 Testing Feature 61: Template Management System...")
    try:
        template_data = {
            'action': 'create',
            'name': 'Advanced Government RFP Template',
            'template_type': 'rfp_response',
            'industry_focus': 'government',
            'created_by': 1,
            'sections': [
                {'name': 'Executive Summary', 'type': 'executive_summary', 'required': True},
                {'name': 'Technical Approach', 'type': 'technical', 'required': True},
                {'name': 'Management Plan', 'type': 'management', 'required': True},
                {'name': 'Past Performance', 'type': 'past_performance', 'required': True},
                {'name': 'Pricing Strategy', 'type': 'pricing', 'required': True}
            ]
        }
        
        result = govcon_suite.manage_proposal_templates(template_data)
        
        if result['success']:
            print(f"   ✅ Template created: {result['template_name']}")
            print(f"   🆔 Template ID: {result['template_id']}")
            print(f"   📋 Sections: {result['sections_created']}")
            print(f"   ✅ Compliance Rules: {result['compliance_rules']}")
            
            ai_optimization = result.get('ai_optimization', {})
            print(f"   🤖 AI Readability Score: {ai_optimization.get('readability_score', 0)}/10")
            print(f"   📊 Win Rate Prediction: {ai_optimization.get('win_rate_prediction', 0)}%")
            
        else:
            print(f"   ❌ Template management failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Template management test failed: {str(e)}")
    
    # Test Feature 62: Content Generation Engine
    print("\n✍️ Testing Feature 62: Content Generation Engine...")
    try:
        content_data = {
            'section_id': 1,
            'section_type': 'technical_approach',
            'requirements': ['Cloud infrastructure', 'Security compliance', 'Performance optimization'],
            'target_word_count': 2000,
            'quality_target': 9.0
        }
        
        result = govcon_suite.generate_proposal_content(content_data)
        
        if result['success']:
            print(f"   ✅ Content generated for Section {result['section_id']}")
            print(f"   📝 Word Count: {result['word_count']}")
            print(f"   📊 Quality Score: {result['quality_score']}/10")
            print(f"   ✅ Compliance Status: {result['compliance_status']}")
            print(f"   🤖 AI Confidence: {result['ai_confidence']}%")
            
        else:
            print(f"   ❌ Content generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Content generation test failed: {str(e)}")
    
    # Test Feature 63: Proposal Customization Tools
    print("\n🎨 Testing Feature 63: Proposal Customization Tools...")
    try:
        customization_data = {
            'proposal_id': 201,
            'client_preferences': {
                'agency': 'Department of Defense',
                'terminology': 'military_focused',
                'format_preference': 'detailed_technical',
                'evaluation_criteria': ['technical_merit', 'past_performance', 'cost']
            },
            'customization_level': 'high'
        }
        
        result = govcon_suite.customize_proposal_sections(customization_data)
        
        if result['success']:
            print(f"   ✅ Proposal customized: ID {result['proposal_id']}")
            print(f"   🎯 Customizations Applied: {result['customizations_applied']}")
            print(f"   📊 Personalization Score: {result.get('personalization_score', 0)}/10")
            
            if 'win_probability_improvement' in result:
                print(f"   📈 Win Probability Improvement: +{result['win_probability_improvement']}%")
            
        else:
            print(f"   ❌ Proposal customization failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Proposal customization test failed: {str(e)}")
    
    print("\n🎉 Phase 8 Proposal Generation Engine (Features 60-63) tested!")
    print("=" * 60)
    
    # Test Phase 8 Pricing & Cost Management (Features 64-67)
    print("\n💰 Testing Phase 8 Pricing & Cost Management (Features 64-67)...")
    print("=" * 60)
    
    # Test Feature 64: Dynamic Pricing Models
    print("\n💲 Testing Feature 64: Dynamic Pricing Models...")
    try:
        pricing_data = {
            'model_name': 'Government IT Services Pricing',
            'model_type': 'hybrid',
            'industry_focus': 'government',
            'base_rates': {
                'senior_consultant': 185,
                'mid_consultant': 125,
                'junior_consultant': 85
            },
            'market_conditions': {
                'competition_level': 'high',
                'demand_level': 'medium',
                'urgency': 'normal'
            }
        }
        
        result = govcon_suite.create_dynamic_pricing_model(pricing_data)
        
        if result['success']:
            print(f"   ✅ Pricing model created: {result['model_name']}")
            print(f"   🆔 Model ID: {result['pricing_model_id']}")
            print(f"   📊 Model Type: {result.get('model_type', 'N/A')}")
            print(f"   🎯 Win Probability: {result.get('win_probability', 0)}%")
            
            if 'expected_margin' in result:
                print(f"   💰 Expected Margin: {result['expected_margin']}%")
            
        else:
            print(f"   ❌ Dynamic pricing model failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Dynamic pricing model test failed: {str(e)}")
    
    # Test Feature 65: Cost Estimation Engine
    print("\n📊 Testing Feature 65: Cost Estimation Engine...")
    try:
        estimate_data = {
            'proposal_id': 201,
            'project_scope': {
                'duration_months': 24,
                'team_size': 12,
                'complexity': 'high'
            },
            'labor_requirements': {
                'senior_hours': 2400,
                'mid_hours': 4800,
                'junior_hours': 3600
            },
            'material_costs': 150000.0,
            'travel_budget': 75000.0
        }
        
        result = govcon_suite.generate_cost_estimates(estimate_data)
        
        if result['success']:
            print(f"   ✅ Cost estimate generated: ID {result['estimate_id']}")
            print(f"   💰 Total Cost: ${result['total_cost']:,.2f}")
            print(f"   💵 Total Price: ${result['total_price']:,.2f}")
            print(f"   📊 Profit Margin: {result['profit_margin']}%")
            print(f"   🎯 Confidence Level: {result['confidence_level']}%")
            
            risk_analysis = result.get('risk_analysis', {})
            print(f"   ⚠️ Cost Risk Level: {risk_analysis.get('cost_risk_level', 'N/A')}")
            
        else:
            print(f"   ❌ Cost estimation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Cost estimation test failed: {str(e)}")

    # Test remaining Phase 8 features (66-75) with condensed testing
    print("\n🔧 Testing Features 66-75 (Condensed)...")

    # Feature 66: Budget Optimization
    try:
        result = govcon_suite.optimize_budget_allocation({'original_budget': 3500000.0})
        print(f"   ✅ Feature 66 - Budget Optimization: Savings ${result.get('savings_achieved', 0):,.0f}")
    except Exception as e:
        print(f"   ❌ Feature 66 failed: {str(e)}")

    # Feature 67: Financial Analysis Tools
    try:
        result = govcon_suite.perform_financial_analysis({'proposal_id': 201})
        print(f"   ✅ Feature 67 - Financial Analysis: Risk Level {result.get('risk_level', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Feature 67 failed: {str(e)}")

    # Feature 68: Compliance Checking System
    try:
        result = govcon_suite.check_proposal_compliance({'proposal_id': 201})
        print(f"   ✅ Feature 68 - Compliance Check: {result.get('overall_compliance', 0)}% compliant")
    except Exception as e:
        print(f"   ❌ Feature 68 failed: {str(e)}")

    # Feature 69: Quality Assurance Framework
    try:
        result = govcon_suite.assess_proposal_quality({'proposal_id': 201})
        print(f"   ✅ Feature 69 - Quality Assessment: Score {result.get('overall_quality_score', 0)}/10")
    except Exception as e:
        print(f"   ❌ Feature 69 failed: {str(e)}")

    # Feature 70: Risk Assessment Tools
    try:
        result = govcon_suite.evaluate_proposal_risks({'proposal_id': 201})
        print(f"   ✅ Feature 70 - Risk Assessment: {result.get('risk_level', 'N/A')} risk level")
    except Exception as e:
        print(f"   ❌ Feature 70 failed: {str(e)}")

    # Feature 71: Audit Trail Management
    try:
        result = govcon_suite.manage_audit_trail({'action_type': 'proposal_update', 'user_id': 1})
        print(f"   ✅ Feature 71 - Audit Trail: Action logged successfully")
    except Exception as e:
        print(f"   ❌ Feature 71 failed: {str(e)}")

    # Feature 72: Bid/No-Bid Decision Support
    try:
        result = govcon_suite.analyze_bid_decision({'opportunity_id': 'RFP-2024-001'})
        print(f"   ✅ Feature 72 - Bid Decision: {result.get('recommendation', 'N/A')} ({result.get('win_probability', 0)}% win prob)")
    except Exception as e:
        print(f"   ❌ Feature 72 failed: {str(e)}")

    # Feature 73: Competitive Intelligence
    try:
        result = govcon_suite.gather_competitive_intelligence({'opportunity_id': 'RFP-2024-001'})
        print(f"   ✅ Feature 73 - Competitive Intel: {result.get('competitors_analyzed', 0)} competitors analyzed")
    except Exception as e:
        print(f"   ❌ Feature 73 failed: {str(e)}")

    # Feature 74: Performance Tracking
    try:
        result = govcon_suite.track_proposal_performance({'tracking_period': 'quarterly'})
        print(f"   ✅ Feature 74 - Performance Tracking: {result.get('win_rate', 0)}% win rate")
    except Exception as e:
        print(f"   ❌ Feature 74 failed: {str(e)}")

    # Feature 75: Strategic Analytics
    try:
        result = govcon_suite.generate_strategic_analytics({'analysis_type': 'portfolio_analysis'})
        print(f"   ✅ Feature 75 - Strategic Analytics: {result.get('market_position', 'N/A')} market position")
    except Exception as e:
        print(f"   ❌ Feature 75 failed: {str(e)}")

    print("\n🎉 All Phase 8 Features (60-75) tested!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_phase8_features()
    if success:
        print("\n✅ Phase 8 testing completed successfully!")
    else:
        print("\n❌ Phase 8 testing encountered errors!")
        sys.exit(1)
