# **sammySosa MCP Server Endpoints Specification**

**Document Version:** 1.0  
**Purpose:** Complete specification of MCP endpoints needed for Apollo GovCon features  
**Target:** MCP Server implementation for sammySosa integration

---

## **🔗 Connection Configuration**

### **sammySosa Configuration**
```toml
# .streamlit/secrets.toml
MCP_SERVER_ENDPOINT = "http://localhost:8000/api/v1/mcp/"  # GremlinsAI MCP endpoint
MCP_API_KEY = "your_gremlins_api_key"                      # GremlinsAI authentication key
MCP_CLIENT_ID = "sammySosa"                                # Client identifier
MCP_TIMEOUT = 30                                           # Request timeout in seconds
MCP_MAX_RETRIES = 3                                        # Max retry attempts
```

### **MCP JSON-RPC 2.0 Integration**
```python
# sammySosa integration with GremlinsAI MCP server
def call_mcp_tool(tool_name, arguments):
    """Call GremlinsAI MCP tool via JSON-RPC 2.0"""
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['MCP_API_KEY']}",
        "Content-Type": "application/json",
        "X-Client-ID": "sammySosa",
        "X-Client-Version": "1.0.0"
    }

    response = requests.post(
        st.secrets["MCP_SERVER_ENDPOINT"],
        headers=headers,
        json=payload,
        timeout=30
    )

    return response.json()
```

---

## **📋 Core Endpoint Categories**

### **🔍 Text Analysis & Processing**
| Endpoint | Method | Purpose | Features Used |
|----------|--------|---------|---------------|
| `/ai/extract-keywords` | POST | Extract keywords from text | 3, 16 |
| `/ai/extract-technical-keywords` | POST | Extract technical terms | 16 |
| `/ai/extract-domain-keywords` | POST | Extract domain-specific keywords | 16 |
| `/ai/rank-keyword-importance` | POST | Rank keywords by relevance | 16 |
| `/ai/categorize-keywords` | POST | Categorize keywords by type | 16 |
| `/ai/extract-locations` | POST | Extract location information | 8 |
| `/ai/extract-requirements` | POST | Extract SOW requirements | Multiple |
| `/ai/analyze-document` | POST | General document analysis | Multiple |
| `/ai/summarize-text` | POST | Generate text summaries | Multiple |
| `/ai/extract-entities` | POST | Extract named entities | Multiple |

### **🔍 Opportunity Analysis**
| Endpoint | Method | Purpose | Features Used |
|----------|--------|---------|---------------|
| `/ai/find-similar-opportunities` | POST | Find similar opportunities | 11 |
| `/ai/calculate-similarity-score` | POST | Calculate similarity scores | 11 |
| `/ai/extract-opportunity-features` | POST | Extract features for matching | 11 |
| `/ai/analyze-buying-patterns` | POST | Analyze agency patterns | 12 |
| `/ai/predict-future-opportunities` | POST | Predict future opportunities | 12 |
| `/ai/generate-pattern-insights` | POST | Generate pattern insights | 12 |
| `/ai/assess-opportunity-fit` | POST | Assess company fit | Multiple |
| `/ai/calculate-p-win-score` | POST | Calculate probability of win | Multiple |

### **⚖️ Compliance & Risk Analysis**
| Endpoint | Method | Purpose | Features Used |
|----------|--------|---------|---------------|
| `/ai/analyze-far-clauses` | POST | Analyze FAR clauses | 15 |
| `/ai/detect-clause-anomalies` | POST | Detect clause anomalies | 15 |
| `/ai/explain-far-clause` | POST | Explain FAR clauses | 15 |
| `/ai/assess-compliance-risk` | POST | Assess compliance risk | 15 |
| `/ai/validate-requirements` | POST | Validate requirement compliance | Multiple |
| `/ai/detect-red-flags` | POST | Detect opportunity red flags | Multiple |
| `/ai/analyze-terms-conditions` | POST | Analyze T&Cs for risks | Multiple |

### **🗺️ Geographic & Location Services**
| Endpoint | Method | Purpose | Features Used |
|----------|--------|---------|---------------|
| `/ai/geocode-address` | POST | Convert addresses to coordinates | 8 |
| `/ai/validate-location` | POST | Validate location information | 8 |
| `/ai/extract-geographic-scope` | POST | Extract geographic requirements | 8 |
| `/ai/analyze-location-preferences` | POST | Analyze location preferences | 8 |

### **📊 Content Generation**
| Endpoint | Method | Purpose | Features Used |
|----------|--------|---------|---------------|
| `/ai/generate-search-queries` | POST | Generate smart search queries | 14 |
| `/ai/generate-summary` | POST | Generate opportunity summaries | Multiple |
| `/ai/generate-recommendations` | POST | Generate actionable recommendations | Multiple |
| `/ai/generate-insights` | POST | Generate business insights | Multiple |
| `/ai/generate-proposal-outline` | POST | Generate proposal outlines | Future |
| `/ai/generate-capability-statement` | POST | Generate capability statements | Future |
| `/ai/generate-teaming-suggestions` | POST | Suggest teaming partners | Future |

---

## **📝 Request/Response Formats**

### **Standard Request Format**
```json
{
    "text": "Text content to analyze",
    "options": {
        "max_results": 10,
        "confidence_threshold": 0.7,
        "categories": ["technical", "compliance", "geographic"]
    },
    "context": {
        "opportunity_id": "12345",
        "agency": "DOD",
        "naics_code": "541511"
    }
}
```

### **Standard Response Format**
```json
{
    "success": true,
    "data": {
        "results": [...],
        "confidence": 0.85,
        "processing_time": 1.23
    },
    "metadata": {
        "model_used": "gpt-4",
        "tokens_used": 1500,
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "error": null
}
```

### **Error Response Format**
```json
{
    "success": false,
    "data": null,
    "error": {
        "code": "ANALYSIS_FAILED",
        "message": "Unable to analyze the provided text",
        "details": "Insufficient context for meaningful analysis"
    },
    "metadata": {
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_12345"
    }
}
```

---

## **🔧 Utility & Management Endpoints**

### **Health & Status**
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/health` | GET | Service health check | `{"status": "healthy", "uptime": 3600}` |
| `/status` | GET | Service status | `{"models": [...], "load": 0.75}` |
| `/capabilities` | GET | Service capabilities | `{"features": [...], "limits": {...}}` |

### **Model Management**
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/models` | GET | Available AI models | `{"models": [{"name": "gpt-4", "status": "active"}]}` |
| `/models/switch` | POST | Switch between models | `{"switched_to": "gpt-4", "success": true}` |

### **Usage & Analytics**
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/usage/stats` | GET | Usage statistics | `{"requests": 1500, "tokens": 50000}` |
| `/usage/limits` | GET | Rate limits | `{"daily_limit": 10000, "remaining": 8500}` |

---

## **🔐 Authentication Endpoints**

| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|--------------|
| `/auth/token` | POST | Get auth token | `{"client_id": "sammySosa", "secret": "..."}` |
| `/auth/refresh` | POST | Refresh token | `{"refresh_token": "..."}` |
| `/auth/validate` | GET | Validate token | Headers: `Authorization: Bearer <token>` |
| `/auth/logout` | POST | Logout/invalidate | `{"token": "..."}` |

---

## **🔄 Revised MCP Tool Strategy for Multi-Client Architecture**

### **Generic MCP Tools (Domain-Agnostic)**
Instead of GovCon-specific endpoints, GremlinsAI should implement these **generic, configurable tools**:

#### **1. Structured Data Extraction**
```json
{
    "name": "extract_structured_data",
    "description": "Extract structured information using configurable schemas",
    "parameters": {
        "text": "Content to analyze",
        "schema": "Extraction schema with field definitions",
        "domain_context": "Optional domain context (government_contracting, legal, etc.)"
    }
}
```

#### **2. Pattern Analysis**
```json
{
    "name": "analyze_patterns",
    "description": "Analyze patterns in data with configurable analysis types",
    "parameters": {
        "data": "Dataset to analyze",
        "pattern_types": ["temporal", "categorical", "behavioral", "seasonal"],
        "analysis_context": "Domain context for pattern interpretation"
    }
}
```

#### **3. Content Classification**
```json
{
    "name": "classify_content",
    "description": "Classify content using configurable taxonomies",
    "parameters": {
        "content": "Content to classify",
        "classification_scheme": "Taxonomy to use",
        "risk_assessment": "Include risk/anomaly detection",
        "domain_rules": "Domain-specific classification rules"
    }
}
```

#### **4. Similarity Analysis**
```json
{
    "name": "calculate_similarity",
    "description": "Calculate similarity using configurable algorithms",
    "parameters": {
        "target_item": "Reference item",
        "comparison_items": "Items to compare",
        "similarity_factors": ["text", "metadata", "structure"],
        "domain_context": "Domain-specific similarity considerations"
    }
}
```

#### **5. Geographic Processing**
```json
{
    "name": "process_geographic_data",
    "description": "Extract and process geographic information",
    "parameters": {
        "text": "Content with geographic references",
        "extraction_types": ["addresses", "regions", "coordinates"],
        "geocoding": "Convert addresses to coordinates",
        "context_type": "Geographic context type"
    }
}
```

#### **6. Insight Generation**
```json
{
    "name": "generate_insights",
    "description": "Generate insights with configurable focus areas",
    "parameters": {
        "content": "Content to analyze",
        "insight_type": "Type of insights to generate",
        "context": "Domain and user context",
        "output_format": "Desired output format"
    }
}
```

### **⚡ High-Priority Generic Tools for Phase 5**

### **Immediate Implementation (Week 1-2)**
1. **`extract_structured_data`** - Replaces keyword/location extraction endpoints
2. **`classify_content`** - Replaces FAR clause analysis endpoints
3. **`/health`** - Basic health monitoring
4. **`/auth/token`** - Authentication setup

### **Phase 5 Core (Week 3-6)**
5. **`calculate_similarity`** - Replaces similar opportunity finder
6. **`analyze_patterns`** - Replaces buying pattern analysis
7. **`process_geographic_data`** - Replaces location processing
8. **`generate_insights`** - Replaces various generation endpoints

### **Phase 5 Advanced (Week 7-8)**
9. **Enhanced domain contexts** - GovCon, legal, e-commerce configurations
10. **Advanced pattern recognition** - Cross-domain pattern analysis
11. **Multi-client learning** - Shared insights across domains
12. **`/usage/stats`** - Usage monitoring

---

## **🚀 Implementation Notes**

### **Performance Requirements**
- **Response Time**: < 5 seconds for most endpoints
- **Throughput**: Handle 100+ concurrent requests
- **Availability**: 99.5% uptime target
- **Rate Limiting**: 1000 requests/hour per client

### **Error Handling**
- Implement exponential backoff for retries
- Graceful degradation when AI services unavailable
- Comprehensive error logging and monitoring
- Fallback responses for critical features

### **Security Considerations**
- API key authentication required
- Request/response logging for audit
- Input sanitization and validation
- Rate limiting to prevent abuse

---

*This specification provides the complete MCP server interface needed for sammySosa's Apollo GovCon features.*
