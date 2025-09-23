#!/usr/bin/env python3
"""
Demonstration of compliance matrix generation
"""

# Sample requirements extracted from SOW
demo_requirements = [
    {
        'requirement_text': 'The contractor shall provide comprehensive cybersecurity assessment and cloud migration services',
        'sow_section': '1.1 Overview'
    },
    {
        'requirement_text': 'The contractor must deliver secure, scalable, and compliant cloud solutions',
        'sow_section': '1.1 Overview'
    },
    {
        'requirement_text': 'The system will support multi-factor authentication across all platforms',
        'sow_section': '1.2 Technical Requirements'
    },
    {
        'requirement_text': 'The contractor must ensure 99.9% uptime for all migrated services',
        'sow_section': '1.2 Technical Requirements'
    },
    {
        'requirement_text': 'The offeror shall provide 24/7 monitoring and incident response capabilities',
        'sow_section': '1.2 Technical Requirements'
    },
    {
        'requirement_text': 'The contractor will implement zero-trust security architecture',
        'sow_section': '1.2 Technical Requirements'
    },
    {
        'requirement_text': 'The system must comply with FedRAMP High authorization requirements',
        'sow_section': '1.2 Technical Requirements'
    },
    {
        'requirement_text': 'Response time for critical incidents must not exceed 15 minutes',
        'sow_section': '1.3 Performance Standards'
    },
    {
        'requirement_text': 'The contractor will maintain security logs for a minimum of 7 years',
        'sow_section': '1.3 Performance Standards'
    },
    {
        'requirement_text': 'The offeror must provide monthly security reports and quarterly assessments',
        'sow_section': '1.3 Performance Standards'
    }
]

print("🎯 COMPLIANCE MATRIX GENERATOR DEMONSTRATION")
print("=" * 60)
print(f"Extracted {len(demo_requirements)} requirements from sample SOW:")
print()

for i, req in enumerate(demo_requirements, 1):
    print(f"{i:2d}. [{req['sow_section']}]")
    print(f"    {req['requirement_text']}")
    print()

print("=" * 60)
print("📊 COMPLIANCE MATRIX CSV OUTPUT:")
print("=" * 60)
print("Requirement,SOW Section,Our Approach")
print("-" * 60)

for req in demo_requirements:
    # Escape quotes for CSV
    req_text = req['requirement_text'].replace('"', '""')
    section = req['sow_section'].replace('"', '""')
    print(f'"{req_text}","{section}",""')

print()
print("✅ SUCCESS: Compliance matrix generated!")
print(f"📈 Total requirements: {len(demo_requirements)}")
print("💾 Ready for CSV download in Streamlit UI")
