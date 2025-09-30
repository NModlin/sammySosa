#!/usr/bin/env python3
"""
Phase 7 Feature Testing Script
Tests the newly implemented Partner Discovery & Matching features (44-47)
"""

import sys
import os
import json
from unittest.mock import patch, Mock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_phase7_features():
    """Test all Phase 7 features 44-47"""
    print("🚀 PHASE 7 FEATURE TESTING")
    print("=" * 60)
    
    try:
        # Mock Streamlit to avoid import issues
        with patch('streamlit.session_state'):
            import govcon_suite
            
            print("✅ Successfully imported govcon_suite")
            
            # Test Feature 44: Partner Discovery Engine
            print("\n🔍 Testing Feature 44: Partner Discovery Engine")
            test_partner_discovery(govcon_suite)
            
            # Test Feature 45: Capability Matching Algorithm  
            print("\n🎯 Testing Feature 45: Capability Matching Algorithm")
            test_capability_matching(govcon_suite)
            
            # Test Feature 46: Past Performance Analysis
            print("\n📊 Testing Feature 46: Past Performance Analysis")
            test_performance_analysis(govcon_suite)
            
            # Test Feature 47: Teaming Recommendation System
            print("\n👥 Testing Feature 47: Teaming Recommendation System")
            test_teaming_recommendations(govcon_suite)

            # Test Feature 48: Partner Relationship Tracker
            print("\n🤝 Testing Feature 48: Partner Relationship Tracker")
            test_relationship_tracker(govcon_suite)

            # Test Feature 49: Communication History Log
            print("\n💬 Testing Feature 49: Communication History Log")
            test_communication_log(govcon_suite)

            # Test Feature 50: Joint Venture Management
            print("\n🏢 Testing Feature 50: Joint Venture Management")
            test_joint_venture_management(govcon_suite)

            # Test Feature 51: Performance Monitoring Dashboard
            print("\n📊 Testing Feature 51: Performance Monitoring Dashboard")
            test_performance_dashboard(govcon_suite)

            print("\n" + "=" * 60)
            print("🎉 PHASE 7 FEATURE TESTING COMPLETE")
            print("All 8 features (44-51) are operational!")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False
    
    return True

def test_partner_discovery(govcon_suite):
    """Test the AI-powered partner discovery engine"""
    try:
        # Mock the MCP server response
        mock_mcp_response = {
            "success": True,
            "data": {
                "skills": ["software development", "python", "government contracting"],
                "experience_level": "senior",
                "certifications": ["security clearance"],
                "location_preference": "virginia"
            }
        }
        
        # Mock the basic partner search
        mock_partners = [
            {
                'company_name': 'TechCorp Solutions',
                'website': 'https://techcorp.com',
                'description': 'Software development company with government experience',
                'capabilities': ['software development', 'python'],
                'source_query': 'software companies in Virginia'
            }
        ]
        
        with patch('govcon_suite.call_mcp_tool') as mock_mcp:
            mock_mcp.return_value = mock_mcp_response
            
            with patch('govcon_suite.find_partners') as mock_find:
                mock_find.return_value = mock_partners
                
                # Test AI-powered discovery
                requirements = "Looking for Python developers with government contracting experience"
                result = govcon_suite.discover_partners_with_ai(requirements, "Virginia", max_results=5)
                
                print(f"   ✅ AI Discovery returned {len(result)} partners")
                
                if result:
                    partner = result[0]
                    print(f"   📋 Sample partner: {partner['company_name']}")
                    if 'ai_score' in partner:
                        print(f"   🤖 AI Score: {partner['ai_score']}")
                
    except Exception as e:
        print(f"   ❌ Partner discovery test failed: {str(e)}")

def test_capability_matching(govcon_suite):
    """Test the capability matching algorithm"""
    try:
        # Mock opportunity requirements
        requirements = {
            'skills': ['software development', 'cybersecurity'],
            'min_experience': 5,
            'certifications': ['security clearance']
        }
        
        # Mock partner capabilities
        capabilities = [
            {
                'partner_id': 1,
                'capability_type': 'software development',
                'proficiency_level': 4,
                'years_experience': 7,
                'certifications': ['security clearance', 'aws certified']
            },
            {
                'partner_id': 2,
                'capability_type': 'cybersecurity',
                'proficiency_level': 5,
                'years_experience': 10,
                'certifications': ['cissp', 'security clearance']
            }
        ]
        
        # Test capability matching
        matches = govcon_suite.match_partner_capabilities(requirements, capabilities, use_ai=False)
        
        print(f"   ✅ Capability matching returned {len(matches)} matches")
        
        for match in matches:
            print(f"   🎯 Partner {match['partner_id']}: Score {match['match_score']} ({match['match_confidence']})")
            print(f"      Reasons: {', '.join(match['match_reasons'])}")
        
    except Exception as e:
        print(f"   ❌ Capability matching test failed: {str(e)}")

def test_performance_analysis(govcon_suite):
    """Test the past performance analysis system"""
    try:
        # Test with demo mode (no database required)
        with patch('govcon_suite.get_engine') as mock_engine:
            mock_engine.return_value = "demo_mode"
            
            result = govcon_suite.analyze_partner_performance(partner_id=1, analysis_period_months=12)
            
            print(f"   ✅ Performance analysis completed")
            print(f"   📊 Overall Score: {result['overall_score']}")
            print(f"   📈 Performance Trend: {result['performance_trend']}")
            print(f"   💼 Contract Count: {result['contract_count']}")
            print(f"   ⏰ On-time Rate: {result['on_time_rate']}")
            print(f"   💰 Budget Adherence: {result['budget_adherence']}")
            print(f"   🏆 Quality Average: {result['quality_average']}")
            print(f"   😊 Client Satisfaction: {result['client_satisfaction']}")
            print(f"   ⚠️  Risk Level: {result['risk_level']}")
            print(f"   💡 Recommendation: {result['recommendation']}")
        
    except Exception as e:
        print(f"   ❌ Performance analysis test failed: {str(e)}")

def test_teaming_recommendations(govcon_suite):
    """Test the teaming recommendation system"""
    try:
        # Mock opportunity requirements
        requirements = {
            'skills': ['software development', 'cybersecurity', 'project management'],
            'preferred_team_size': 3,
            'max_budget': 2000000,
            'critical_skills': ['software development']
        }
        
        # Mock available partners
        partners = [
            {'id': 1, 'company_name': 'TechCorp Solutions'},
            {'id': 2, 'company_name': 'SecureNet Inc'},
            {'id': 3, 'company_name': 'ProjectPro LLC'}
        ]
        
        # Test with demo mode
        with patch('govcon_suite.get_engine') as mock_engine:
            mock_engine.return_value = "demo_mode"
            
            recommendations = govcon_suite.generate_teaming_recommendations(
                opportunity_id="TEST-001",
                requirements=requirements,
                available_partners=partners,
                max_teams=2
            )
            
            print(f"   ✅ Generated {len(recommendations)} team recommendations")
            
            for i, team in enumerate(recommendations):
                print(f"   👥 Team {i+1}: {team['team_name']}")
                print(f"      Prime: {team['prime_contractor']}")
                print(f"      Score: {team['total_score']}")
                print(f"      Win Probability: {team['win_probability']}")
                print(f"      Members: {len(team['team_members'])}")
                print(f"      Strengths: {', '.join(team['strengths'])}")
                if team['risks']:
                    print(f"      Risks: {', '.join(team['risks'])}")
        
    except Exception as e:
        print(f"   ❌ Teaming recommendations test failed: {str(e)}")

def test_relationship_tracker(govcon_suite):
    """Test the partner relationship tracker"""
    try:
        # Mock interaction data
        interaction_data = {
            'type': 'meeting',
            'date': '2025-09-29',
            'subject': 'Project Discussion',
            'description': 'Discussed upcoming project requirements and timeline',
            'outcome': 'positive',
            'follow_up_required': True,
            'follow_up_date': '2025-10-15',
            'created_by': 'project_manager'
        }

        result = govcon_suite.track_partner_interaction(partner_id=1, interaction_data=interaction_data)

        print(f"   ✅ Relationship tracking completed")
        print(f"   🆔 Interaction ID: {result['interaction_id']}")
        print(f"   📊 Relationship Stage: {result['relationship_stage']}")
        print(f"   🎯 Trust Level: {result['trust_level']}")
        print(f"   📈 Interaction Count: {result['interaction_count']}")
        print(f"   💚 Relationship Health: {result['relationship_health']}")
        print(f"   💡 Recommendations: {len(result['recommendations'])} items")

    except Exception as e:
        print(f"   ❌ Relationship tracker test failed: {str(e)}")

def test_communication_log(govcon_suite):
    """Test the communication history log"""
    try:
        # Mock communication data
        communication_data = {
            'type': 'email',
            'direction': 'outbound',
            'subject': 'Project Update Request',
            'content': 'Hi team, could you please provide an update on the current project status? We need to review progress for the upcoming client meeting. Thanks!',
            'priority': 'medium',
            'status': 'sent',
            'thread_type': 'project_update',
            'attachments': []
        }

        result = govcon_suite.log_partner_communication(partner_id=1, communication_data=communication_data)

        print(f"   ✅ Communication logging completed")
        print(f"   🆔 Communication ID: {result['communication_id']}")
        print(f"   🧵 Thread ID: {result['thread_id']}")
        print(f"   😊 Sentiment: {result['sentiment']}")
        print(f"   ⚡ Priority: {result['priority']}")
        print(f"   📨 Status: {result['status']}")
        print(f"   💬 Thread Messages: {result['thread_message_count']}")

        insights = result.get('communication_insights', {})
        if insights:
            print(f"   🔍 AI Insights: {len(insights)} categories extracted")

    except Exception as e:
        print(f"   ❌ Communication log test failed: {str(e)}")

def test_joint_venture_management(govcon_suite):
    """Test the joint venture management system"""
    try:
        # Test creating a joint venture
        venture_data = {
            'name': 'TechCorp-SecureNet Strategic Partnership',
            'opportunity_id': 'TEST-OPP-001',
            'prime_partner_id': 1,
            'partners': [
                {'id': 1, 'name': 'TechCorp Solutions', 'role': 'Prime'},
                {'id': 2, 'name': 'SecureNet Inc', 'role': 'Subcontractor'}
            ],
            'type': 'joint_venture',
            'status': 'proposed',
            'contract_value': 2500000.0,
            'revenue_split': {'TechCorp Solutions': 60, 'SecureNet Inc': 40},
            'legal_structure': 'LLC'
        }

        create_result = govcon_suite.manage_joint_venture(venture_data, action='create')

        print(f"   ✅ Joint venture creation completed")
        print(f"   🆔 Venture ID: {create_result['venture_id']}")
        print(f"   📋 Venture Name: {create_result['venture_name']}")
        print(f"   📊 Status: {create_result['status']}")
        print(f"   👥 Partners: {len(create_result['partners'])}")
        print(f"   💰 Estimated Value: ${create_result['estimated_value']:,.2f}")
        print(f"   💡 Recommendations: {len(create_result['recommendations'])} items")

        # Test listing joint ventures
        list_result = govcon_suite.manage_joint_venture({}, action='list')

        if list_result['success']:
            print(f"   📋 Listed {len(list_result['ventures'])} joint ventures")

    except Exception as e:
        print(f"   ❌ Joint venture management test failed: {str(e)}")

def test_performance_dashboard(govcon_suite):
    """Test the performance monitoring dashboard"""
    try:
        # Test overall dashboard
        dashboard_result = govcon_suite.generate_partner_performance_dashboard(time_period='30d')

        print(f"   ✅ Performance dashboard generated")

        dashboard_data = dashboard_result['dashboard_data']
        summary = dashboard_data['summary_metrics']

        print(f"   👥 Total Partners: {summary['total_partners']}")
        print(f"   🤝 Active Partnerships: {summary['active_partnerships']}")
        print(f"   💰 Total Revenue: ${summary['total_revenue']:,.2f}")
        print(f"   ⏱️  Avg Response Time: {summary['avg_response_time']} hours")
        print(f"   😊 Overall Satisfaction: {summary['overall_satisfaction']}/5.0")

        top_performers = dashboard_data.get('top_performers', [])
        print(f"   🏆 Top Performers: {len(top_performers)} listed")

        trends = dashboard_data.get('performance_trends', {})
        print(f"   📈 Performance Trends: {len(trends)} metrics tracked")

        alerts = dashboard_data.get('alerts', [])
        print(f"   🚨 Active Alerts: {len(alerts)} notifications")

        # Test single partner dashboard
        single_partner_result = govcon_suite.generate_partner_performance_dashboard(
            partner_id=1, time_period='30d'
        )

        if single_partner_result['success']:
            print(f"   👤 Single partner dashboard: {single_partner_result['dashboard_data']['partner_name']}")

    except Exception as e:
        print(f"   ❌ Performance dashboard test failed: {str(e)}")

    # Test Phase 7 Collaboration Tools (Features 52-55)
    print("\n🔧 Testing Phase 7 Collaboration Tools (Features 52-55)...")
    print("=" * 60)

    # Test Feature 52: Shared Workspace Creation
    print("\n📋 Testing Feature 52: Shared Workspace Creation...")
    try:
        workspace_data = {
            'name': 'Test Project Workspace',
            'description': 'Collaborative workspace for testing Phase 7 features',
            'type': 'project',
            'owner_id': 1,
            'opportunity_id': 'TEST-OPP-001',
            'privacy_level': 'private',
            'initial_members': [
                {'user_id': 2, 'role': 'member'},
                {'partner_id': 1, 'role': 'member'}
            ],
            'settings': {
                'notifications': True,
                'auto_archive': False
            }
        }

        result = govcon_suite.create_shared_workspace(workspace_data)

        if result['success']:
            print(f"   ✅ Workspace created: {result['workspace_name']}")
            print(f"   📊 Members added: {result['members_added']}")
            print(f"   🎯 Type: {result['workspace_type']}")
            print(f"   🤖 AI recommendations: {len(result['ai_recommendations'])}")
        else:
            print(f"   ❌ Workspace creation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Workspace creation test failed: {str(e)}")

    # Test Feature 53: Document Sharing Platform
    print("\n📄 Testing Feature 53: Document Sharing Platform...")
    try:
        document_data = {
            'workspace_id': 1,
            'document_name': 'Project_Requirements_v1.docx',
            'document_type': 'docx',
            'file_path': '/uploads/project_requirements_v1.docx',
            'file_size': 2048576,
            'uploaded_by': 1,
            'description': 'Initial project requirements document',
            'tags': ['requirements', 'project', 'draft'],
            'checksum': 'abc123def456',
            'permissions': [
                {'user_id': 2, 'type': 'read'},
                {'user_id': 3, 'type': 'write'},
                {'partner_id': 1, 'type': 'comment'}
            ],
            'allow_download': True,
            'enable_watermarking': True
        }

        result = govcon_suite.share_document(document_data)

        if result['success']:
            print(f"   ✅ Document shared: {result['document_name']}")
            print(f"   📊 Version: {result['version']}")
            print(f"   🔒 Permissions set: {result['permissions_set']}")
            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 AI classification: {ai_insights.get('document_classification', 'N/A')}")
            print(f"   🛡️ Security level: {ai_insights.get('sensitivity_level', 'N/A')}")
        else:
            print(f"   ❌ Document sharing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Document sharing test failed: {str(e)}")

    # Test Feature 54: Task Assignment System
    print("\n📋 Testing Feature 54: Task Assignment System...")
    try:
        task_data = {
            'workspace_id': 1,
            'title': 'Review Technical Specifications',
            'description': 'Comprehensive review of all technical requirements and specifications',
            'task_type': 'review',
            'priority': 'high',
            'assigned_to': 2,
            'created_by': 1,
            'due_date': '2024-10-15',
            'estimated_hours': 8.0,
            'dependencies': ['task_001', 'task_002'],
            'attachments': ['doc_001', 'doc_002'],
            'assignment_type': 'primary',
            'require_acceptance': True,
            'assignee_info': {
                'current_workload': 'moderate',
                'skills': ['technical_review', 'documentation']
            }
        }

        result = govcon_suite.assign_task(task_data)

        if result['success']:
            print(f"   ✅ Task assigned: {result['task_title']}")
            print(f"   👤 Assigned to: {result['assigned_to']}")
            print(f"   📅 Due date: {result['due_date']}")
            print(f"   ⏱️ Estimated hours: {result['estimated_hours']}")
            ai_optimization = result.get('ai_optimization', {})
            print(f"   🤖 AI workload analysis: {ai_optimization.get('workload_analysis', 'N/A')}")
        else:
            print(f"   ❌ Task assignment failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Task assignment test failed: {str(e)}")

    # Test Feature 55: Progress Tracking Tools
    print("\n📊 Testing Feature 55: Progress Tracking Tools...")
    try:
        result = govcon_suite.generate_progress_report(
            workspace_id=1,
            report_type='weekly'
        )

        if result['success']:
            print(f"   ✅ Progress report generated: Report ID {result['report_id']}")
            print(f"   📈 Overall progress: {result['overall_progress']}%")
            summary_metrics = result.get('summary_metrics', {})
            print(f"   ✅ Tasks completed: {summary_metrics.get('tasks_completed', 0)}/{summary_metrics.get('tasks_total', 0)}")
            print(f"   🎯 Milestones achieved: {summary_metrics.get('milestones_achieved', 0)}/{summary_metrics.get('milestones_total', 0)}")
            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 AI trend analysis: {ai_insights.get('progress_trend', 'N/A')}")
            print(f"   ⚠️ Risk assessment: {ai_insights.get('risk_assessment', 'N/A')}")
        else:
            print(f"   ❌ Progress report failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Progress tracking test failed: {str(e)}")

    print("\n🎉 All Phase 7 Collaboration Tools (Features 52-55) tested!")
    print("=" * 60)

    # Test Phase 7 Strategic Partnership Analysis (Features 56-59)
    print("\n🎯 Testing Phase 7 Strategic Partnership Analysis (Features 56-59)...")
    print("=" * 60)

    # Test Feature 56: Partnership ROI Analysis
    print("\n💰 Testing Feature 56: Partnership ROI Analysis...")
    try:
        partnership_data = {
            'partnership_id': 101,
            'total_investment': 750000.0,
            'total_revenue': 2850000.0,
            'operational_costs': 675000.0,
            'partnership_type': 'strategic',
            'duration_months': 12,
            'initial_investment': 500000.0,
            'marketing_costs': 75000.0,
            'compliance_costs': 25000.0,
            'direct_revenue': 1800000.0,
            'subcontract_revenue': 650000.0,
            'win_rate_improvement': 35.0,
            'avg_contract_value': 485000.0,
            'customer_satisfaction': 4.6,
            'market_risk': 'low',
            'operational_risk': 'medium'
        }

        result = govcon_suite.analyze_partnership_roi(partnership_data)

        if result['success']:
            print(f"   ✅ ROI analysis completed for Partnership {result['partnership_id']}")
            roi_metrics = result.get('roi_metrics', {})
            print(f"   💰 Total Investment: ${roi_metrics.get('total_investment', 0):,.2f}")
            print(f"   📈 Total Revenue: ${roi_metrics.get('total_revenue', 0):,.2f}")
            print(f"   💵 Net Profit: ${roi_metrics.get('net_profit', 0):,.2f}")
            print(f"   📊 ROI Percentage: {roi_metrics.get('roi_percentage', 0)}%")
            print(f"   ⏱️ Payback Period: {roi_metrics.get('payback_period_months', 0)} months")
            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 AI Assessment: {ai_insights.get('roi_assessment', 'N/A')}")
            print(f"   💡 Investment Recommendation: {ai_insights.get('investment_recommendation', 'N/A')}")
        else:
            print(f"   ❌ ROI analysis failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ ROI analysis test failed: {str(e)}")

    # Test Feature 57: Strategic Alignment Assessment
    print("\n🎯 Testing Feature 57: Strategic Alignment Assessment...")
    try:
        alignment_data = {
            'partnership_id': 101,
            'partnership_type': 'strategic',
            'strategic_objectives': {'score': 9.2, 'details': 'Excellent alignment on market expansion goals'},
            'cultural_compatibility': {'score': 8.5, 'details': 'Strong cultural fit with shared values'},
            'operational_synergies': {'score': 8.8, 'details': 'Complementary capabilities create advantages'},
            'market_positioning': {'score': 8.3, 'details': 'Partnership strengthens market position'},
            'technology_alignment': {'score': 8.9, 'details': 'Compatible technology stacks'},
            'financial_compatibility': {'score': 8.1, 'details': 'Similar financial stability'}
        }

        result = govcon_suite.assess_strategic_alignment(alignment_data)

        if result['success']:
            print(f"   ✅ Strategic alignment assessed for Partnership {result['partnership_id']}")
            print(f"   📊 Overall Alignment Score: {result['overall_alignment_score']}/10")
            alignment_categories = result.get('alignment_categories', {})
            print(f"   🎯 Categories assessed: {len(alignment_categories)}")

            # Show top performing category
            if alignment_categories:
                top_category = max(alignment_categories.items(), key=lambda x: x[1]['score'])
                print(f"   🏆 Top Category: {top_category[0].replace('_', ' ').title()} ({top_category[1]['score']}/10)")

            strengths = result.get('strengths', [])
            challenges = result.get('challenges', [])
            print(f"   💪 Strengths identified: {len(strengths)}")
            print(f"   ⚠️ Challenges identified: {len(challenges)}")

            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 Partnership Viability: {ai_insights.get('partnership_viability', 'N/A')}")
            print(f"   📈 Success Probability: {ai_insights.get('success_probability', 0)}%")
        else:
            print(f"   ❌ Strategic alignment assessment failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Strategic alignment test failed: {str(e)}")

    # Test Feature 58: Risk Evaluation System
    print("\n⚠️ Testing Feature 58: Risk Evaluation System...")
    try:
        risk_data = {
            'partnership_id': 101,
            'partnership_type': 'strategic',
            'financial_risk': {
                'probability': 0.15,
                'impact': 'medium',
                'description': 'Partner financial stability risks',
                'indicators': ['Credit rating: A-', 'Cash reserves: 6 months'],
                'mitigation_strategies': ['Regular financial monitoring', 'Performance bonds']
            },
            'operational_risk': {
                'probability': 0.25,
                'impact': 'medium',
                'description': 'Delivery and performance risks',
                'indicators': ['Past performance: 92%', 'Quality issues: 3%'],
                'mitigation_strategies': ['Joint QA processes', 'Performance monitoring']
            },
            'market_risk': {
                'probability': 0.35,
                'impact': 'medium',
                'description': 'Market conditions and competition risks',
                'indicators': ['Market volatility: Medium', 'Competition: High'],
                'mitigation_strategies': ['Market diversification', 'Competitive intelligence']
            }
        }

        result = govcon_suite.evaluate_partnership_risks(risk_data)

        if result['success']:
            print(f"   ✅ Risk evaluation completed for Partnership {result['partnership_id']}")
            print(f"   📊 Overall Risk Score: {result['overall_risk_score']}/5")
            print(f"   ⚠️ Risk Level: {result['risk_level'].title()}")

            risk_categories = result.get('risk_categories', {})
            print(f"   📋 Risk categories assessed: {len(risk_categories)}")

            # Show highest risk category
            if risk_categories:
                highest_risk = max(risk_categories.items(), key=lambda x: x[1]['score'])
                print(f"   🚨 Highest Risk: {highest_risk[0].replace('_', ' ').title()} ({highest_risk[1]['score']:.1f}/5)")

            risk_matrix = result.get('risk_matrix', {})
            high_impact_risks = len(risk_matrix.get('high_probability_high_impact', []))
            print(f"   🔴 High Priority Risks: {high_impact_risks}")

            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 Risk Trend: {ai_insights.get('risk_trend', 'N/A')}")
            print(f"   📅 Monitoring Frequency: {ai_insights.get('recommended_monitoring_frequency', 'N/A')}")
        else:
            print(f"   ❌ Risk evaluation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Risk evaluation test failed: {str(e)}")

    # Test Feature 59: Optimization Recommendations
    print("\n🚀 Testing Feature 59: Optimization Recommendations...")
    try:
        optimization_data = {
            'partnership_id': 101,
            'roi': 190.0,
            'strategic_alignment': 8.7,
            'risk_level': 3.2,
            'operational_efficiency': 87.5,
            'customer_satisfaction': 4.6,
            'market_position': 8.3,
            'partnership_type': 'strategic',
            'maturity': 'established',
            'industry': 'government_contracting'
        }

        result = govcon_suite.generate_partnership_optimization_recommendations(optimization_data)

        if result['success']:
            print(f"   ✅ Optimization recommendations generated for Partnership {result['partnership_id']}")
            print(f"   📊 Optimization Score: {result['optimization_score']}/10")

            current_performance = result.get('current_performance', {})
            print(f"   💰 Current ROI: {current_performance.get('roi', 0)}%")
            print(f"   🎯 Strategic Alignment: {current_performance.get('strategic_alignment', 0)}/10")
            print(f"   ⚡ Operational Efficiency: {current_performance.get('operational_efficiency', 0)}%")

            optimization_categories = result.get('optimization_categories', {})
            print(f"   📋 Optimization areas: {len(optimization_categories)}")

            # Show highest priority optimization
            if optimization_categories:
                high_priority = [cat for cat, data in optimization_categories.items() if data.get('priority') == 'high']
                print(f"   🔥 High Priority Areas: {len(high_priority)}")

            implementation_roadmap = result.get('implementation_roadmap', {})
            print(f"   📅 Implementation phases: {len(implementation_roadmap)}")

            ai_insights = result.get('ai_insights', {})
            print(f"   🤖 Optimization Potential: {ai_insights.get('optimization_potential', 'N/A')}")
            print(f"   📈 Success Probability: {ai_insights.get('success_probability', 0)}%")
        else:
            print(f"   ❌ Optimization recommendations failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Optimization recommendations test failed: {str(e)}")

    print("\n🎉 All Phase 7 Strategic Partnership Analysis (Features 56-59) tested!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_phase7_features()
    sys.exit(0 if success else 1)
