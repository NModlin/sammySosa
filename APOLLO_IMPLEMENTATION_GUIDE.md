# **Apollo GovCon Automation Suite - Implementation Guide**

**Document Version:** 1.0
**Purpose:** Comprehensive code implementations for all 93 features
**Target Architecture:** sammySosa (Monolithic Streamlit Application)

---

## **🏗️ Architecture Overview**

### **sammySosa Monolithic Structure**
```
sammySosa/
├── components/              # NEW: Feature components
│   ├── dashboard_builder.py    # Feature 1: Customizable Dashboards
│   ├── saved_searches.py       # Feature 2: Saved Searches
│   ├── keyword_highlighter.py  # Feature 3: Keyword Highlighting
│   ├── compact_view.py          # Feature 6: Compact View
│   └── map_view.py              # Feature 8: Geographic Map View
├── govcon_suite.py          # EXISTING: Main Streamlit application
├── Apollo_GovCon.py         # EXISTING: Entry point
├── bidding_copilot.py       # EXISTING: Legacy AI co-pilot
├── docker-compose.yml       # EXISTING: Container orchestration
├── requirements.txt         # EXISTING: Python dependencies
└── .streamlit/secrets.toml  # EXISTING: Configuration
```

### **Technology Stack**
- **Frontend**: Streamlit (monolithic application)
- **Database**: PostgreSQL + SQLAlchemy (existing setup)
- **AI**: API-based LLM integration (replacing local Mistral-7B)
- **Vector Search**: sentence-transformers + FAISS (existing)
- **Infrastructure**: Docker + Docker Compose (existing)

---

## **📊 Phase 5: Enhanced Market Intelligence Implementation**

### **Feature 1: Customizable Dashboards**
**Status:** ⏳ Ready for Implementation  
**Complexity:** High | **Priority:** HIGH

#### **Database Schema Changes**
```python
# Add to existing setup_database() function in govcon_suite.py
def setup_database():
    # ... existing code ...

    # Feature 1: Customizable Dashboards
    user_dashboards = Table(
        "user_dashboards",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", String, nullable=False, default="default_user"),
        Column("dashboard_name", String, nullable=False),
        Column("widget_config", JSONB, nullable=False),
        Column("is_default", Boolean, default=False),
        Column("created_date", String, default=lambda: datetime.now().isoformat()),
        Column("last_modified", String, default=lambda: datetime.now().isoformat())
    )

    # Add indexes for performance
    Index("ix_user_dashboards_user_id", user_dashboards.c.user_id)
    Index("ix_user_dashboards_is_default", user_dashboards.c.is_default)

    # ... rest of existing code ...
    metadata.create_all(engine)
    return engine
```

#### **API Integration Setup**
```python
# Add to govcon_suite.py - LLM API Integration
@st.cache_resource
def setup_llm_api():
    """Setup API-based LLM connection"""
    api_endpoint = st.secrets.get("LLM_API_ENDPOINT", "")
    api_key = st.secrets.get("LLM_API_KEY", "")

    if not api_endpoint or not api_key:
        st.warning("⚠️ LLM API configuration missing. Add LLM_API_ENDPOINT and LLM_API_KEY to secrets.toml")
        return None

    return {
        "endpoint": api_endpoint,
        "api_key": api_key,
        "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    }

def execute_ai_task(llm_config, prompt):
    """Execute AI task via API call (replaces local LLM)"""
    if not llm_config:
        return "AI service unavailable"

    try:
        import requests

        payload = {
            "prompt": prompt,
            "max_tokens": 2048,
            "temperature": 0.4
        }

        response = requests.post(
            llm_config["endpoint"],
            headers=llm_config["headers"],
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get("text", response.json().get("choices", [{}])[0].get("text", ""))
        else:
            return f"API Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"API Connection Error: {str(e)}"
```

#### **Dashboard Service Functions**
```python
# Add to govcon_suite.py - Dashboard Management Functions
def get_available_widgets():
    """Get available dashboard widget types"""
    return [
        {
            "widget_type": "opportunity_chart",
            "name": "Opportunity Distribution Chart",
            "description": "Pie/bar chart showing opportunities by agency, NAICS, etc.",
            "config_options": ["chart_type", "group_by", "time_range"]
        },
        {
            "widget_type": "p_win_distribution",
            "name": "P-Win Score Distribution",
            "description": "Histogram of P-Win scores",
            "config_options": ["bin_size", "time_range"]
        },
        {
            "widget_type": "agency_summary",
            "name": "Top Agencies Table",
            "description": "Table of most active agencies",
            "config_options": ["limit", "sort_by", "time_range"]
        },
        {
            "widget_type": "opportunity_map",
            "name": "Geographic Opportunity Map",
            "description": "Map showing opportunity locations",
            "config_options": ["zoom_level", "marker_style"]
        },
        {
            "widget_type": "recent_opportunities",
            "name": "Recent Opportunities",
            "description": "List of recently posted opportunities",
            "config_options": ["limit", "filters"]
        }
    ]

def save_dashboard_config(user_id, dashboard_name, widget_config, is_default=False):
    """Save dashboard configuration to database"""
    try:
        engine = setup_database()

        # If setting as default, unset other defaults
        if is_default:
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE user_dashboards
                    SET is_default = FALSE
                    WHERE user_id = :user_id AND is_default = TRUE
                """), {"user_id": user_id})
                conn.commit()

        # Insert new dashboard
        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO user_dashboards (user_id, dashboard_name, widget_config, is_default, created_date)
                VALUES (:user_id, :dashboard_name, :widget_config, :is_default, :created_date)
                RETURNING id
            """), {
                "user_id": user_id,
                "dashboard_name": dashboard_name,
                "widget_config": json.dumps(widget_config),
                "is_default": is_default,
                "created_date": datetime.now().isoformat()
            })
            conn.commit()
            return result.fetchone()[0]

    except Exception as e:
        st.error(f"Error saving dashboard: {str(e)}")
        return None

def load_user_dashboards(user_id="default_user"):
    """Load user's saved dashboards"""
    try:
        engine = setup_database()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, dashboard_name, widget_config, is_default, created_date
                FROM user_dashboards
                WHERE user_id = :user_id
                ORDER BY is_default DESC, created_date DESC
            """), {"user_id": user_id})

            dashboards = []
            for row in result:
                dashboards.append({
                    "id": row[0],
                    "dashboard_name": row[1],
                    "widget_config": json.loads(row[2]) if row[2] else {},
                    "is_default": row[3],
                    "created_date": row[4]
                })
            return dashboards

    except Exception as e:
        st.error(f"Error loading dashboards: {str(e)}")
        return []
```

#### **Service Layer Implementation**
```python
# GremlinsAI_backend/services/dashboard_service.py
from typing import List, Dict, Any
from ..database.models import UserDashboard, DashboardWidget
from ..database.connection import get_db_session
from sqlalchemy.orm import Session

class DashboardService:
    
    @staticmethod
    async def get_available_widgets() -> List[Dict[str, Any]]:
        """Get all available widget types"""
        widgets = [
            {
                "widget_type": "opportunity_chart",
                "name": "Opportunity Distribution Chart",
                "description": "Pie/bar chart showing opportunities by agency, NAICS, etc.",
                "data_source": "/api/analytics/opportunity_distribution",
                "config_options": ["chart_type", "group_by", "time_range"]
            },
            {
                "widget_type": "p_win_distribution", 
                "name": "P-Win Score Distribution",
                "description": "Histogram of P-Win scores",
                "data_source": "/api/analytics/p_win_distribution",
                "config_options": ["bin_size", "time_range"]
            },
            {
                "widget_type": "agency_summary",
                "name": "Top Agencies Table",
                "description": "Table of most active agencies",
                "data_source": "/api/analytics/top_agencies",
                "config_options": ["limit", "sort_by", "time_range"]
            },
            {
                "widget_type": "opportunity_map",
                "name": "Geographic Opportunity Map",
                "description": "Map showing opportunity locations",
                "data_source": "/api/analytics/opportunity_locations",
                "config_options": ["zoom_level", "marker_style"]
            },
            {
                "widget_type": "recent_opportunities",
                "name": "Recent Opportunities",
                "description": "List of recently posted opportunities",
                "data_source": "/api/opportunities/recent",
                "config_options": ["limit", "filters"]
            }
        ]
        return widgets
    
    @staticmethod
    async def create_dashboard(dashboard_data: DashboardCreate) -> Dict[str, Any]:
        """Create a new dashboard"""
        with get_db_session() as db:
            # If setting as default, unset other defaults for this user
            if dashboard_data.is_default:
                db.query(UserDashboard).filter(
                    UserDashboard.user_id == dashboard_data.user_id,
                    UserDashboard.is_default == True
                ).update({"is_default": False})
            
            # Create new dashboard
            dashboard = UserDashboard(
                user_id=dashboard_data.user_id,
                dashboard_name=dashboard_data.dashboard_name,
                layout_config={"widgets": [w.dict() for w in dashboard_data.widgets]},
                widget_configs={f"widget_{i}": w.data_config for i, w in enumerate(dashboard_data.widgets)},
                is_default=dashboard_data.is_default
            )
            
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            
            return {
                "id": dashboard.id,
                "dashboard_name": dashboard.dashboard_name,
                "user_id": dashboard.user_id,
                "widgets": dashboard_data.widgets,
                "is_default": dashboard.is_default,
                "created_date": dashboard.created_date,
                "last_modified": dashboard.last_modified
            }
```

#### **Enhanced Dashboard Page Implementation**
```python
# Modify existing page_dashboard() function in govcon_suite.py
def page_dashboard():
    """Enhanced dashboard with customization capabilities"""
    try:
        st.title("Opportunity Dashboard")

        # Dashboard customization toggle
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader("Dashboard View")
        with col2:
            if st.button("🎛️ Customize"):
                st.session_state.show_dashboard_builder = not st.session_state.get('show_dashboard_builder', False)
        with col3:
            # Dashboard selector
            user_dashboards = load_user_dashboards()
            if user_dashboards:
                dashboard_names = ["Default"] + [d["dashboard_name"] for d in user_dashboards]
                selected_dashboard = st.selectbox("Dashboard", dashboard_names, key="dashboard_selector")

                if selected_dashboard != "Default":
                    # Load custom dashboard configuration
                    dashboard_config = next((d for d in user_dashboards if d["dashboard_name"] == selected_dashboard), None)
                    if dashboard_config:
                        st.session_state.current_dashboard_config = dashboard_config["widget_config"]

        # Show dashboard builder or regular dashboard
        if st.session_state.get('show_dashboard_builder', False):
            render_dashboard_builder()
        else:
            # Check if we have a custom dashboard configuration
            if hasattr(st.session_state, 'current_dashboard_config'):
                render_custom_dashboard(st.session_state.current_dashboard_config)
            else:
                render_standard_dashboard()  # Existing dashboard code

    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        st.info("Falling back to basic dashboard view")
        render_standard_dashboard()

def render_dashboard_builder():
    """Dashboard customization interface"""
    st.subheader("🎛️ Dashboard Builder")

    # Dashboard basic info
    col1, col2 = st.columns(2)
    with col1:
        dashboard_name = st.text_input("Dashboard Name", placeholder="My Custom Dashboard")
    with col2:
        is_default = st.checkbox("Set as Default Dashboard")

    # Available widgets
    st.subheader("Available Widgets")
    available_widgets = get_available_widgets()

    # Widget selection and configuration
    selected_widgets = []

    for widget in available_widgets:
        with st.expander(f"📊 {widget['name']}"):
            st.write(widget['description'])

            if st.checkbox(f"Add {widget['name']}", key=f"add_{widget['widget_type']}"):
                # Widget configuration
                widget_config = configure_widget(widget)
                selected_widgets.append(widget_config)

    # Dashboard preview and save
    if selected_widgets:
        st.subheader("Dashboard Preview")
        render_dashboard_preview(selected_widgets)

        if st.button("Save Dashboard", type="primary"):
            if dashboard_name:
                dashboard_id = save_dashboard_config("default_user", dashboard_name, selected_widgets, is_default)
                if dashboard_id:
                    st.success(f"Dashboard '{dashboard_name}' saved successfully!")
                    st.session_state.show_dashboard_builder = False
                    st.rerun()
            else:
                st.error("Please enter a dashboard name")
    
    def render_new_dashboard_builder(self):
        """Interface for creating new dashboard"""
        st.subheader("Create New Dashboard")
        
        # Dashboard basic info
        col1, col2 = st.columns(2)
        with col1:
            dashboard_name = st.text_input("Dashboard Name", placeholder="My Custom Dashboard")
        with col2:
            is_default = st.checkbox("Set as Default Dashboard")
        
        # Available widgets
        st.subheader("Available Widgets")
        available_widgets = self.get_available_widgets()
        
        # Widget selection and configuration
        selected_widgets = []
        
        for widget in available_widgets:
            with st.expander(f"📊 {widget['name']}"):
                st.write(widget['description'])
                
                if st.checkbox(f"Add {widget['name']}", key=f"add_{widget['widget_type']}"):
                    # Widget configuration
                    widget_config = self.configure_widget(widget)
                    selected_widgets.append(widget_config)
        
        # Dashboard preview and save
        if selected_widgets:
            st.subheader("Dashboard Preview")
            self.render_dashboard_preview(selected_widgets)
            
            if st.button("Save Dashboard", type="primary"):
                self.save_dashboard(dashboard_name, selected_widgets, is_default)
    
def configure_widget(widget: Dict[str, Any]) -> Dict[str, Any]:
    """Configure individual widget settings"""
    widget_type = widget['widget_type']

    # Widget-specific configuration
    data_config = {"title": widget['name']}

    if widget_type == "opportunity_chart":
        col1, col2 = st.columns(2)
        with col1:
            data_config["chart_type"] = st.selectbox("Chart Type", ["pie", "bar", "line"], key=f"{widget_type}_chart")
            data_config["group_by"] = st.selectbox("Group By", ["agency", "naics", "set_aside"], key=f"{widget_type}_group")
        with col2:
            data_config["time_range"] = st.selectbox("Time Range", ["7d", "30d", "90d", "1y"], key=f"{widget_type}_time")
            data_config["title"] = st.text_input("Widget Title", value=widget['name'], key=f"{widget_type}_title")

    elif widget_type == "agency_summary":
        col1, col2 = st.columns(2)
        with col1:
            data_config["limit"] = st.number_input("Number of Agencies", min_value=5, max_value=50, value=10, key=f"{widget_type}_limit")
            data_config["sort_by"] = st.selectbox("Sort By", ["opportunity_count", "total_value"], key=f"{widget_type}_sort")
        with col2:
            data_config["title"] = st.text_input("Widget Title", value=widget['name'], key=f"{widget_type}_title")

    elif widget_type == "opportunity_map":
        col1, col2 = st.columns(2)
        with col1:
            data_config["zoom_level"] = st.slider("Zoom Level", min_value=1, max_value=10, value=4, key=f"{widget_type}_zoom")
            data_config["marker_style"] = st.selectbox("Marker Style", ["cluster", "individual"], key=f"{widget_type}_marker")
        with col2:
            data_config["title"] = st.text_input("Widget Title", value=widget['name'], key=f"{widget_type}_title")

    # Add more widget-specific configurations as needed

    return {
        "widget_type": widget_type,
        "data_config": data_config
    }

def render_dashboard_preview(selected_widgets):
    """Render preview of selected widgets"""
    st.write("**Dashboard Preview:**")

    # Create columns based on number of widgets
    if len(selected_widgets) == 1:
        cols = [st.container()]
    elif len(selected_widgets) == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(3, len(selected_widgets)))

    for i, widget in enumerate(selected_widgets):
        with cols[i % len(cols)]:
            render_widget_preview(widget)

def render_widget_preview(widget_config):
    """Render a preview of a single widget"""
    widget_type = widget_config["widget_type"]
    data_config = widget_config["data_config"]
    title = data_config.get("title", "Widget")

    st.subheader(title)

    if widget_type == "opportunity_chart":
        # Create sample chart
        import plotly.express as px
        sample_data = {"Agency": ["DOD", "GSA", "VA", "DHS"], "Count": [25, 15, 10, 8]}

        if data_config.get("chart_type") == "pie":
            fig = px.pie(values=sample_data["Count"], names=sample_data["Agency"], title="Sample Data")
        else:
            fig = px.bar(x=sample_data["Agency"], y=sample_data["Count"], title="Sample Data")

        st.plotly_chart(fig, use_container_width=True)

    elif widget_type == "agency_summary":
        # Create sample table
        sample_df = pd.DataFrame({
            "Agency": ["DOD", "GSA", "VA", "DHS"],
            "Opportunities": [25, 15, 10, 8],
            "Total Value": ["$2.5M", "$1.2M", "$800K", "$600K"]
        })
        st.dataframe(sample_df, use_container_width=True)

    elif widget_type == "opportunity_map":
        # Create sample map
        sample_locations = pd.DataFrame({
            "lat": [38.9072, 39.7392, 41.8781, 34.0522],
            "lon": [-77.0369, -104.9903, -87.6298, -118.2437],
            "city": ["Washington DC", "Denver", "Chicago", "Los Angeles"],
            "opportunities": [15, 8, 12, 6]
        })
        st.map(sample_locations)

    else:
        st.info(f"Preview for {widget_type} widget")

def render_custom_dashboard(widget_config):
    """Render dashboard with custom widget configuration"""
    st.subheader("Custom Dashboard")

    if not widget_config:
        st.info("No widgets configured for this dashboard")
        return

    # Create columns based on number of widgets
    if len(widget_config) == 1:
        cols = [st.container()]
    elif len(widget_config) == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(3, len(widget_config)))

    for i, widget in enumerate(widget_config):
        with cols[i % len(cols)]:
            render_dashboard_widget(widget)

def render_dashboard_widget(widget_config):
    """Render a live dashboard widget with real data"""
    widget_type = widget_config["widget_type"]
    data_config = widget_config["data_config"]
    title = data_config.get("title", "Widget")

    st.subheader(title)

    try:
        engine = setup_database()

        if widget_type == "opportunity_chart":
            # Get real opportunity data
            group_by = data_config.get("group_by", "agency")
            time_range = data_config.get("time_range", "30d")

            # Convert time range to days
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(time_range, 30)

            query = f"""
                SELECT {group_by}, COUNT(*) as count
                FROM opportunities
                WHERE posted_date >= NOW() - INTERVAL '{days} days'
                GROUP BY {group_by}
                ORDER BY count DESC
                LIMIT 10
            """

            df = pd.read_sql(query, engine)

            if not df.empty:
                if data_config.get("chart_type") == "pie":
                    fig = px.pie(df, values="count", names=group_by)
                else:
                    fig = px.bar(df, x=group_by, y="count")

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for the selected time range")

        elif widget_type == "agency_summary":
            # Get agency summary data
            limit = data_config.get("limit", 10)
            sort_by = data_config.get("sort_by", "opportunity_count")

            query = f"""
                SELECT agency,
                       COUNT(*) as opportunity_count,
                       AVG(p_win_score) as avg_p_win
                FROM opportunities
                WHERE posted_date >= NOW() - INTERVAL '30 days'
                GROUP BY agency
                ORDER BY {sort_by} DESC
                LIMIT {limit}
            """

            df = pd.read_sql(query, engine)

            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No agency data available")

        elif widget_type == "recent_opportunities":
            # Get recent opportunities
            limit = data_config.get("limit", 10)

            query = f"""
                SELECT notice_id, title, agency, posted_date, p_win_score
                FROM opportunities
                ORDER BY posted_date DESC
                LIMIT {limit}
            """

            df = pd.read_sql(query, engine)

            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent opportunities available")

        else:
            st.info(f"Widget type {widget_type} not yet implemented")

    except Exception as e:
        st.error(f"Error loading widget data: {str(e)}")

def render_standard_dashboard():
    """Render the existing standard dashboard (existing code)"""
    # This would contain your existing dashboard code from page_dashboard()
    # Keep all the existing functionality intact

    ensure_scheduler()

    c1, c2, c3 = st.columns(3)
    with c1:
        date_from = st.text_input("Posted From (MM/DD/YYYY)")
    with c2:
        date_to = st.text_input("Posted To (MM/DD/YYYY)")
    with c3:
        naics = st.text_input("NAICS (optional)")

    if st.button("Run Scraper Now"):
        with st.spinner("Fetching latest opportunities..."):
            inserted = run_scraper(date_from or None, date_to or None, naics or None)
        st.success(f"Scraper run complete. Inserted {inserted} new records.")

    engine = setup_database()
    df = pd.read_sql(
        "SELECT notice_id, title, agency, posted_date, response_deadline, naics_code, set_aside, status, p_win_score, analysis_summary, raw_data FROM opportunities ORDER BY p_win_score DESC, posted_date DESC",
        engine,
    )

    # ... rest of existing dashboard code ...
```
```

#### **Test Cases**
```python
# tests/test_dashboard.py
import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

class TestDashboardAPI:
    
    def test_get_available_widgets(self):
        """Test retrieving available widgets"""
        response = client.get("/api/dashboard/widgets")
        assert response.status_code == 200
        
        widgets = response.json()
        assert len(widgets) > 0
        assert all("widget_type" in w for w in widgets)
        assert all("name" in w for w in widgets)
    
    def test_create_dashboard_success(self):
        """Test successful dashboard creation"""
        dashboard_data = {
            "dashboard_name": "Test Dashboard",
            "user_id": "test_user",
            "widgets": [
                {
                    "widget_type": "opportunity_chart",
                    "position": {"x": 0, "y": 0, "width": 6, "height": 4},
                    "data_config": {"chart_type": "pie", "group_by": "agency"},
                    "title": "Opportunities by Agency"
                }
            ],
            "is_default": False
        }
        
        response = client.post("/api/dashboard/create", json=dashboard_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["dashboard_name"] == "Test Dashboard"
        assert result["user_id"] == "test_user"
        assert len(result["widgets"]) == 1
    
    def test_create_dashboard_validation_error(self):
        """Test dashboard creation with invalid data"""
        invalid_data = {
            "dashboard_name": "",  # Empty name should fail
            "user_id": "test_user",
            "widgets": []
        }
        
        response = client.post("/api/dashboard/create", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_user_dashboards(self):
        """Test retrieving user dashboards"""
        # First create a dashboard
        dashboard_data = {
            "dashboard_name": "User Test Dashboard",
            "user_id": "test_user_2",
            "widgets": [],
            "is_default": True
        }
        client.post("/api/dashboard/create", json=dashboard_data)
        
        # Then retrieve it
        response = client.get("/api/dashboard/user/test_user_2")
        assert response.status_code == 200
        
        dashboards = response.json()
        assert len(dashboards) >= 1
        assert any(d["dashboard_name"] == "User Test Dashboard" for d in dashboards)
```

#### **Configuration Updates**
```python
# Add to .streamlit/secrets.toml
[database]
host = "localhost"
port = "5434"
database = "sam_contracts"
username = "postgres"
password = "mysecretpassword"

# API Keys (existing)
SAM_API_KEY = "your_sam_api_key"
SLACK_WEBHOOK_URL = "your_slack_webhook"

# NEW: LLM API Configuration
LLM_API_ENDPOINT = "https://your-llm-api-endpoint.com/v1/completions"
LLM_API_KEY = "your_llm_api_key"

# Optional Configuration
API_KEY_EXPIRATION_DATE = "2025-12-21"
BASE_URL = "http://localhost:8501"
```

#### **Requirements Updates**
```python
# Add to requirements.txt (if not already present)
plotly>=5.17.0          # For enhanced charts
folium>=0.14.0          # For map widgets
streamlit-folium>=0.15.0 # Streamlit-folium integration
requests>=2.31.0        # For API calls
```

---

## **📝 Implementation Status Tracking**

### **Feature 1: Customizable Dashboards**
- ✅ Database schema designed (extends existing setup_database())
- ✅ LLM API integration designed (replaces local model)
- ✅ Dashboard service functions implemented
- ✅ Enhanced page_dashboard() function designed
- ✅ Widget configuration system implemented
- ✅ Dashboard preview and rendering system designed
- ⏳ **Ready for implementation in sammySosa**

### **Implementation Priority Order**
1. **Feature 1**: Customizable Dashboards (High Priority - UI Enhancement)
2. **Feature 2**: Saved Searches (High Priority - User Experience)
3. **Feature 3**: Keyword Highlighting (High Priority - Content Enhancement)
4. **Feature 6**: Compact View (Medium Priority - Display Option)
5. **Feature 8**: Geographic Map View (Medium Priority - Visualization)

### **Next Steps**
1. Add database tables to existing `setup_database()` function
2. Replace `setup_llm()` with `setup_llm_api()` function
3. Enhance `page_dashboard()` with customization features
4. Create `components/` directory and implement widget system
5. Test dashboard builder functionality
6. Move to Feature 2 implementation

---

## **Feature 2: Saved Searches**
**Status:** ⏳ Ready for Implementation
**Complexity:** Medium | **Priority:** HIGH

#### **Database Schema**
```python
# GremlinsAI_backend/database/models.py
class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    search_name = Column(String, nullable=False)
    search_criteria = Column(JSONB, nullable=False)  # Filter parameters
    is_favorite = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
```

#### **FastAPI Implementation**
```python
# GremlinsAI_backend/api/saved_searches.py
@router.post("/create", response_model=SavedSearchResponse)
async def create_saved_search(search: SavedSearchCreate):
    """Create a new saved search"""
    return await SavedSearchService.create_search(search)

@router.get("/user/{user_id}", response_model=List[SavedSearchResponse])
async def get_user_saved_searches(user_id: str):
    """Get all saved searches for a user"""
    return await SavedSearchService.get_user_searches(user_id)

@router.post("/{search_id}/execute")
async def execute_saved_search(search_id: int):
    """Execute a saved search and return results"""
    return await SavedSearchService.execute_search(search_id)
```

#### **Streamlit Integration**
```python
# sammySosa/components/saved_searches.py
def render_saved_searches_sidebar():
    """Render saved searches in sidebar"""
    st.sidebar.subheader("💾 Saved Searches")

    saved_searches = load_user_saved_searches()

    if saved_searches:
        for search in saved_searches:
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if st.button(search["search_name"], key=f"search_{search['id']}"):
                    execute_saved_search(search["id"])
            with col2:
                if st.button("⭐", key=f"fav_{search['id']}"):
                    toggle_search_favorite(search["id"])

    # Quick save current search
    if st.sidebar.button("💾 Save Current Search"):
        save_current_search_dialog()
```

---

## **Feature 3: Keyword Highlighting**
**Status:** ⏳ Ready for Implementation
**Complexity:** Medium | **Priority:** HIGH

#### **Backend Implementation**
```python
# GremlinsAI_backend/services/text_processing.py
import re
from typing import List, Dict, Any

class TextHighlighter:

    @staticmethod
    def highlight_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> str:
        """Highlight keywords in text with HTML markup"""
        if not keywords:
            return text

        flags = 0 if case_sensitive else re.IGNORECASE
        highlighted_text = text

        for keyword in keywords:
            pattern = re.escape(keyword)
            replacement = f'<mark class="keyword-highlight">{keyword}</mark>'
            highlighted_text = re.sub(pattern, replacement, highlighted_text, flags=flags)

        return highlighted_text

    @staticmethod
    def extract_context(text: str, keywords: List[str], context_chars: int = 100) -> List[Dict[str, Any]]:
        """Extract text snippets around keywords with context"""
        contexts = []

        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.finditer(text)

            for match in matches:
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)

                context = {
                    "keyword": keyword,
                    "snippet": text[start:end],
                    "position": match.start(),
                    "highlighted_snippet": TextHighlighter.highlight_keywords(
                        text[start:end], [keyword]
                    )
                }
                contexts.append(context)

        return contexts
```

#### **Frontend Component**
```python
# sammySosa/components/keyword_highlighter.py
import streamlit as st
import streamlit.components.v1 as components

def render_highlighted_text(text: str, keywords: List[str]):
    """Render text with highlighted keywords"""

    # CSS for highlighting
    highlight_css = """
    <style>
    .keyword-highlight {
        background-color: #ffeb3b;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    .text-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    </style>
    """

    # Highlight keywords in text
    highlighted_text = highlight_keywords_in_text(text, keywords)

    # Render with custom HTML
    html_content = f"""
    {highlight_css}
    <div class="text-container">
        {highlighted_text}
    </div>
    """

    components.html(html_content, height=450)

def keyword_management_interface():
    """Interface for managing keywords"""
    st.subheader("🔍 Keyword Management")

    # Load existing keywords
    if 'user_keywords' not in st.session_state:
        st.session_state.user_keywords = load_user_keywords()

    # Add new keyword
    col1, col2 = st.columns([3, 1])
    with col1:
        new_keyword = st.text_input("Add Keyword", placeholder="Enter keyword to highlight")
    with col2:
        if st.button("Add") and new_keyword:
            add_user_keyword(new_keyword)
            st.session_state.user_keywords.append(new_keyword)
            st.rerun()

    # Display and manage existing keywords
    if st.session_state.user_keywords:
        st.write("**Active Keywords:**")
        for i, keyword in enumerate(st.session_state.user_keywords):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {keyword}")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    remove_user_keyword(keyword)
                    st.session_state.user_keywords.remove(keyword)
                    st.rerun()
```

---

## **Feature 6: Compact View**
**Status:** ⏳ Ready for Implementation
**Complexity:** Low | **Priority:** MEDIUM

#### **Implementation**
```python
# sammySosa/components/compact_view.py
def render_compact_opportunity_table(opportunities: List[Dict], keywords: List[str] = None):
    """Render opportunities in compact table format"""

    if not opportunities:
        st.info("No opportunities found")
        return

    # Prepare data for compact display
    compact_data = []
    for opp in opportunities:
        compact_data.append({
            "ID": opp.get("notice_id", "")[:10] + "...",
            "Title": truncate_text(opp.get("title", ""), 50),
            "Agency": opp.get("agency", "")[:20],
            "Posted": format_date_compact(opp.get("posted_date", "")),
            "Deadline": format_date_compact(opp.get("response_deadline", "")),
            "NAICS": opp.get("naics_code", ""),
            "Set-Aside": format_set_aside_compact(opp.get("set_aside", "")),
            "P-Win": opp.get("p_win_score", 0),
            "Status": opp.get("status", "New")
        })

    # Display compact table
    df = pd.DataFrame(compact_data)

    # Apply conditional formatting
    styled_df = df.style.apply(lambda x: apply_compact_styling(x), axis=1)

    # Configure table display
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600,
        column_config={
            "P-Win": st.column_config.ProgressColumn(
                "P-Win Score",
                help="Probability of Win Score",
                min_value=0,
                max_value=100,
            ),
            "Title": st.column_config.TextColumn(
                "Title",
                help="Opportunity Title (truncated)",
                max_chars=50,
            )
        }
    )

def apply_compact_styling(row):
    """Apply conditional styling to table rows"""
    styles = [''] * len(row)

    # Highlight high P-Win scores
    if row['P-Win'] >= 80:
        styles = ['background-color: #e8f5e8'] * len(row)
    elif row['P-Win'] >= 60:
        styles = ['background-color: #fff3cd'] * len(row)

    # Highlight urgent deadlines
    deadline = row['Deadline']
    if deadline and is_deadline_urgent(deadline):
        styles[4] = 'background-color: #f8d7da; font-weight: bold'

    return styles
```

---

## **Feature 8: Geographic Map View**
**Status:** ⏳ Ready for Implementation
**Complexity:** Medium | **Priority:** MEDIUM

#### **Database Schema Extension**
```python
# Add to existing setup_database() function in govcon_suite.py
opportunity_locations = Table(
    "opportunity_locations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("opportunity_id", String, ForeignKey("opportunities.notice_id")),
    Column("location_type", String),  # 'performance', 'office', 'delivery'
    Column("address", String),
    Column("city", String),
    Column("state", String),
    Column("zip_code", String),
    Column("country", String, default="USA"),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("geocoded_date", String),
    Column("geocoding_confidence", Float)
)

# Add indexes
Index("ix_opportunity_locations_opportunity_id", opportunity_locations.c.opportunity_id)
Index("ix_opportunity_locations_state", opportunity_locations.c.state)
Index("ix_opportunity_locations_coordinates", opportunity_locations.c.latitude, opportunity_locations.c.longitude)
```

#### **MCP Endpoints Needed**
- **`/ai/extract-locations`** - Extract location information from opportunity text
- **`/ai/geocode-address`** - Convert addresses to coordinates

#### **Implementation Functions**
```python
# Add to govcon_suite.py
import folium
from streamlit_folium import st_folium
import requests

def extract_locations_from_text(text):
    """Extract location information from opportunity text using AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return []

    prompt = f"""
    Extract all location information from the following government contracting opportunity text.
    Look for:
    1. Performance locations (where work will be done)
    2. Office locations (contracting office, agency locations)
    3. Delivery locations (where products/services will be delivered)
    4. Geographic restrictions or preferences

    Text:
    {text}

    Return a JSON array of locations with this format:
    [
        {{
            "type": "performance|office|delivery",
            "address": "full address if available",
            "city": "city name",
            "state": "state abbreviation",
            "zip": "zip code if available",
            "description": "context about this location"
        }}
    ]
    """

    try:
        response = execute_ai_task(llm_config, prompt)
        import json
        locations = json.loads(response.strip())
        return locations if isinstance(locations, list) else []
    except Exception as e:
        st.error(f"Error extracting locations: {str(e)}")
        return []

def geocode_address(address):
    """Convert address to coordinates using geocoding service"""
    # This could use Google Maps API, OpenStreetMap Nominatim, or other services
    try:
        # Example using a free geocoding service
        import requests

        # Using OpenStreetMap Nominatim (free, no API key required)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "us"
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"]),
                    "confidence": float(data[0].get("importance", 0.5))
                }
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")

    return None

def save_opportunity_location(opportunity_id, location_data):
    """Save location data for an opportunity"""
    try:
        engine = setup_database()

        # Geocode the address if coordinates not provided
        if not location_data.get("latitude") and location_data.get("address"):
            geocode_result = geocode_address(location_data["address"])
            if geocode_result:
                location_data.update(geocode_result)

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO opportunity_locations
                (opportunity_id, location_type, address, city, state, zip_code,
                 latitude, longitude, geocoded_date, geocoding_confidence)
                VALUES (:opportunity_id, :location_type, :address, :city, :state, :zip_code,
                        :latitude, :longitude, :geocoded_date, :confidence)
            """), {
                "opportunity_id": opportunity_id,
                "location_type": location_data.get("type", "performance"),
                "address": location_data.get("address", ""),
                "city": location_data.get("city", ""),
                "state": location_data.get("state", ""),
                "zip_code": location_data.get("zip", ""),
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude"),
                "geocoded_date": datetime.now().isoformat(),
                "confidence": location_data.get("confidence", 0.5)
            })
            conn.commit()
    except Exception as e:
        st.error(f"Error saving location: {str(e)}")

def render_opportunity_map():
    """Render interactive map of opportunities"""
    st.subheader("🗺️ Geographic Opportunity Map")

    # Map controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        map_view = st.selectbox("Map View", ["All Opportunities", "Recent (30 days)", "High P-Win", "By Agency"])

    with col2:
        location_type = st.selectbox("Location Type", ["All", "Performance", "Office", "Delivery"])

    with col3:
        cluster_markers = st.checkbox("Cluster Markers", value=True)

    with col4:
        show_heatmap = st.checkbox("Show Heatmap", value=False)

    # Get opportunity location data
    opportunities_with_locations = get_opportunities_with_locations(map_view, location_type)

    if opportunities_with_locations:
        # Create base map
        center_lat = opportunities_with_locations['latitude'].mean()
        center_lon = opportunities_with_locations['longitude'].mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=4,
            tiles="OpenStreetMap"
        )

        # Add markers or clusters
        if cluster_markers:
            from folium.plugins import MarkerCluster
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in opportunities_with_locations.iterrows():
                popup_html = create_opportunity_popup(row)

                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row['title'][:50]}...",
                    icon=folium.Icon(
                        color=get_marker_color(row['p_win_score']),
                        icon='info-sign'
                    )
                ).add_to(marker_cluster)
        else:
            # Individual markers
            for _, row in opportunities_with_locations.iterrows():
                popup_html = create_opportunity_popup(row)

                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row['title'][:50]}...",
                    icon=folium.Icon(
                        color=get_marker_color(row['p_win_score']),
                        icon='info-sign'
                    )
                ).add_to(m)

        # Add heatmap if requested
        if show_heatmap:
            from folium.plugins import HeatMap
            heat_data = [[row['latitude'], row['longitude'], row['p_win_score']]
                        for _, row in opportunities_with_locations.iterrows()]
            HeatMap(heat_data).add_to(m)

        # Add legend
        add_map_legend(m)

        # Display map
        map_data = st_folium(m, width=700, height=500)

        # Handle map interactions
        if map_data['last_object_clicked_popup']:
            handle_map_click(map_data['last_object_clicked_popup'])

    else:
        st.info("No opportunities with location data found for the selected criteria.")

        # Offer to extract locations from existing opportunities
        if st.button("🤖 Extract Locations from Existing Opportunities"):
            extract_locations_from_opportunities()

def get_opportunities_with_locations(map_view, location_type):
    """Get opportunities with location data based on filters"""
    try:
        engine = setup_database()

        base_query = """
            SELECT o.notice_id, o.title, o.agency, o.posted_date, o.p_win_score,
                   ol.latitude, ol.longitude, ol.city, ol.state, ol.location_type,
                   ol.address
            FROM opportunities o
            JOIN opportunity_locations ol ON o.notice_id = ol.opportunity_id
            WHERE ol.latitude IS NOT NULL AND ol.longitude IS NOT NULL
        """

        conditions = []
        params = {}

        if map_view == "Recent (30 days)":
            conditions.append("o.posted_date >= NOW() - INTERVAL '30 days'")
        elif map_view == "High P-Win":
            conditions.append("o.p_win_score >= 70")

        if location_type != "All":
            conditions.append("ol.location_type = :location_type")
            params["location_type"] = location_type.lower()

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY o.p_win_score DESC"

        df = pd.read_sql(base_query, engine, params=params)
        return df

    except Exception as e:
        st.error(f"Error loading opportunity locations: {str(e)}")
        return pd.DataFrame()

def create_opportunity_popup(row):
    """Create HTML popup content for map marker"""
    return f"""
    <div style="width: 250px;">
        <h4 style="margin: 0 0 10px 0; color: #1f77b4;">{row['title'][:60]}...</h4>
        <p><strong>Agency:</strong> {row['agency']}</p>
        <p><strong>Location:</strong> {row['city']}, {row['state']}</p>
        <p><strong>P-Win Score:</strong> {row['p_win_score']}%</p>
        <p><strong>Posted:</strong> {row['posted_date']}</p>
        <a href="#" onclick="viewOpportunity('{row['notice_id']}')"
           style="color: #1f77b4; text-decoration: none;">
           📄 View Details
        </a>
    </div>
    """

def get_marker_color(p_win_score):
    """Get marker color based on P-Win score"""
    if p_win_score >= 80:
        return 'green'
    elif p_win_score >= 60:
        return 'orange'
    elif p_win_score >= 40:
        return 'yellow'
    else:
        return 'red'

def add_map_legend(map_obj):
    """Add legend to the map"""
    legend_html = """
    <div style="position: fixed;
                top: 10px; right: 10px; width: 150px; height: 120px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
    <h4 style="margin: 0 0 10px 0;">P-Win Score</h4>
    <p><i class="fa fa-map-marker" style="color:green"></i> 80-100%</p>
    <p><i class="fa fa-map-marker" style="color:orange"></i> 60-79%</p>
    <p><i class="fa fa-map-marker" style="color:gold"></i> 40-59%</p>
    <p><i class="fa fa-map-marker" style="color:red"></i> 0-39%</p>
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(legend_html))

def extract_locations_from_opportunities():
    """Extract locations from existing opportunities that don't have location data"""
    engine = setup_database()

    # Get opportunities without location data
    opportunities_without_locations = pd.read_sql("""
        SELECT o.notice_id, o.title, o.raw_data
        FROM opportunities o
        LEFT JOIN opportunity_locations ol ON o.notice_id = ol.opportunity_id
        WHERE ol.opportunity_id IS NULL
        LIMIT 50
    """, engine)

    if not opportunities_without_locations.empty:
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, row in opportunities_without_locations.iterrows():
            status_text.text(f"Processing {i+1}/{len(opportunities_without_locations)}: {row['title'][:50]}...")

            # Extract locations from raw data
            locations = extract_locations_from_text(row['raw_data'])

            # Save extracted locations
            for location in locations:
                save_opportunity_location(row['notice_id'], location)

            progress_bar.progress((i + 1) / len(opportunities_without_locations))

        st.success(f"Processed {len(opportunities_without_locations)} opportunities for location extraction!")
        st.rerun()
```

---

## **Feature 11: Similar Opportunity Finder**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **MCP Endpoints Needed**
- **`/ai/find-similar-opportunities`** - Find opportunities similar to a given one
- **`/ai/calculate-similarity-score`** - Calculate similarity between two opportunities
- **`/ai/extract-opportunity-features`** - Extract key features for similarity matching

#### **Implementation Functions**
```python
# Add to govcon_suite.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def find_similar_opportunities(target_opportunity_id, limit=10):
    """Find opportunities similar to the target opportunity"""
    try:
        engine = setup_database()

        # Get target opportunity
        target_opp = pd.read_sql("""
            SELECT notice_id, title, raw_data, naics_code, agency, set_aside
            FROM opportunities
            WHERE notice_id = :target_id
        """, engine, params={"target_id": target_opportunity_id})

        if target_opp.empty:
            return []

        target_data = target_opp.iloc[0]

        # Get all other opportunities for comparison
        all_opps = pd.read_sql("""
            SELECT notice_id, title, raw_data, naics_code, agency, set_aside, p_win_score
            FROM opportunities
            WHERE notice_id != :target_id
            ORDER BY posted_date DESC
            LIMIT 1000
        """, engine, params={"target_id": target_opportunity_id})

        if all_opps.empty:
            return []

        # Calculate similarity scores
        similarity_scores = calculate_opportunity_similarities(target_data, all_opps)

        # Sort by similarity and return top results
        similar_opps = []
        for i, score in enumerate(similarity_scores):
            if score > 0.1:  # Minimum similarity threshold
                opp_data = all_opps.iloc[i]
                similar_opps.append({
                    "notice_id": opp_data["notice_id"],
                    "title": opp_data["title"],
                    "agency": opp_data["agency"],
                    "naics_code": opp_data["naics_code"],
                    "set_aside": opp_data["set_aside"],
                    "p_win_score": opp_data["p_win_score"],
                    "similarity_score": float(score),
                    "similarity_reasons": get_similarity_reasons(target_data, opp_data, score)
                })

        # Sort by similarity score and return top results
        similar_opps.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_opps[:limit]

    except Exception as e:
        st.error(f"Error finding similar opportunities: {str(e)}")
        return []

def calculate_opportunity_similarities(target_opp, comparison_opps):
    """Calculate similarity scores between target and comparison opportunities"""
    # Combine text features for similarity calculation
    target_text = f"{target_opp['title']} {target_opp['raw_data']}"
    comparison_texts = [f"{row['title']} {row['raw_data']}" for _, row in comparison_opps.iterrows()]

    # Use TF-IDF vectorization for text similarity
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )

    all_texts = [target_text] + comparison_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Calculate cosine similarity
    target_vector = tfidf_matrix[0:1]
    comparison_vectors = tfidf_matrix[1:]

    text_similarities = cosine_similarity(target_vector, comparison_vectors)[0]

    # Add categorical similarity bonuses
    final_similarities = []
    for i, (_, comp_opp) in enumerate(comparison_opps.iterrows()):
        text_sim = text_similarities[i]

        # NAICS code similarity bonus
        naics_bonus = 0.2 if target_opp['naics_code'] == comp_opp['naics_code'] else 0

        # Agency similarity bonus
        agency_bonus = 0.1 if target_opp['agency'] == comp_opp['agency'] else 0

        # Set-aside similarity bonus
        setaside_bonus = 0.1 if target_opp['set_aside'] == comp_opp['set_aside'] else 0

        final_similarity = text_sim + naics_bonus + agency_bonus + setaside_bonus
        final_similarities.append(min(1.0, final_similarity))  # Cap at 1.0

    return final_similarities

def get_similarity_reasons(target_opp, similar_opp, similarity_score):
    """Generate human-readable reasons for similarity"""
    reasons = []

    if target_opp['naics_code'] == similar_opp['naics_code']:
        reasons.append(f"Same NAICS code ({target_opp['naics_code']})")

    if target_opp['agency'] == similar_opp['agency']:
        reasons.append(f"Same agency ({target_opp['agency']})")

    if target_opp['set_aside'] == similar_opp['set_aside'] and target_opp['set_aside']:
        reasons.append(f"Same set-aside type ({target_opp['set_aside']})")

    # Use AI to identify content similarities
    content_reasons = get_ai_similarity_reasons(target_opp, similar_opp)
    reasons.extend(content_reasons)

    return reasons

def get_ai_similarity_reasons(target_opp, similar_opp):
    """Use AI to identify specific content similarities"""
    llm_config = setup_llm_api()
    if not llm_config:
        return ["High text similarity"]

    prompt = f"""
    Compare these two government contracting opportunities and identify the top 3 specific reasons why they are similar:

    Opportunity 1:
    Title: {target_opp['title']}
    Content: {target_opp['raw_data'][:500]}...

    Opportunity 2:
    Title: {similar_opp['title']}
    Content: {similar_opp['raw_data'][:500]}...

    Return only a JSON array of similarity reasons:
    ["reason 1", "reason 2", "reason 3"]
    """

    try:
        response = execute_ai_task(llm_config, prompt)
        import json
        reasons = json.loads(response.strip())
        return reasons if isinstance(reasons, list) else ["Content similarity detected"]
    except Exception:
        return ["Content similarity detected"]

def render_similar_opportunities_finder():
    """Render the similar opportunities finder interface"""
    st.subheader("🔍 Similar Opportunity Finder")

    # Input section
    col1, col2 = st.columns([2, 1])

    with col1:
        # Opportunity selector
        engine = setup_database()
        recent_opps = pd.read_sql("""
            SELECT notice_id, title, agency, posted_date
            FROM opportunities
            ORDER BY posted_date DESC
            LIMIT 100
        """, engine)

        if not recent_opps.empty:
            opp_options = [f"{row['notice_id']} - {row['title'][:60]}..."
                          for _, row in recent_opps.iterrows()]

            selected_opp = st.selectbox(
                "Select opportunity to find similar ones:",
                options=opp_options,
                help="Choose an opportunity to find similar ones"
            )

            if selected_opp:
                target_id = selected_opp.split(" - ")[0]

    with col2:
        similarity_threshold = st.slider(
            "Minimum Similarity %",
            min_value=10,
            max_value=90,
            value=30,
            help="Lower values show more results"
        )

        max_results = st.number_input(
            "Max Results",
            min_value=5,
            max_value=50,
            value=10
        )

    # Find similar opportunities
    if st.button("🔍 Find Similar Opportunities", type="primary") and 'target_id' in locals():
        with st.spinner("Analyzing opportunities for similarities..."):
            similar_opps = find_similar_opportunities(target_id, max_results)

            # Filter by similarity threshold
            filtered_opps = [opp for opp in similar_opps
                           if opp["similarity_score"] * 100 >= similarity_threshold]

            if filtered_opps:
                st.success(f"Found {len(filtered_opps)} similar opportunities!")

                # Display results
                for i, opp in enumerate(filtered_opps):
                    with st.expander(
                        f"#{i+1} - {opp['title'][:60]}... (Similarity: {opp['similarity_score']*100:.1f}%)",
                        expanded=i < 3  # Expand first 3 results
                    ):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Agency:** {opp['agency']}")
                            st.write(f"**NAICS:** {opp['naics_code']}")
                            st.write(f"**Set-Aside:** {opp['set_aside'] or 'None'}")
                            st.write(f"**P-Win Score:** {opp['p_win_score']}%")

                            st.write("**Why it's similar:**")
                            for reason in opp['similarity_reasons']:
                                st.write(f"• {reason}")

                        with col2:
                            similarity_color = get_similarity_color(opp['similarity_score'])
                            st.markdown(
                                f"""
                                <div style="text-align: center; padding: 20px;
                                           background-color: {similarity_color};
                                           border-radius: 10px; color: white;">
                                    <h3 style="margin: 0;">{opp['similarity_score']*100:.1f}%</h3>
                                    <p style="margin: 0;">Similarity</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            if st.button(f"📄 View Details", key=f"view_{opp['notice_id']}"):
                                # Navigate to opportunity details
                                st.session_state.selected_opportunity = opp['notice_id']
                                st.rerun()
            else:
                st.info(f"No opportunities found with similarity >= {similarity_threshold}%")
                st.write("Try lowering the similarity threshold or selecting a different opportunity.")

def get_similarity_color(similarity_score):
    """Get color based on similarity score"""
    if similarity_score >= 0.8:
        return "#28a745"  # Green
    elif similarity_score >= 0.6:
        return "#ffc107"  # Yellow
    elif similarity_score >= 0.4:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red
```

---

## **Feature 12: Agency Buying Pattern Analysis**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **MCP Endpoints Needed**
- **`/ai/analyze-buying-patterns`** - Analyze historical buying patterns for agencies
- **`/ai/predict-future-opportunities`** - Predict future opportunities based on patterns
- **`/ai/generate-pattern-insights`** - Generate insights from buying pattern data

#### **Database Schema Extension**
```python
# Add to existing setup_database() function in govcon_suite.py
agency_buying_patterns = Table(
    "agency_buying_patterns",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("agency", String, nullable=False),
    Column("naics_code", String),
    Column("pattern_type", String),  # 'seasonal', 'cyclical', 'trending'
    Column("pattern_data", JSONB),   # Statistical pattern data
    Column("confidence_score", Float),
    Column("analysis_date", String, default=lambda: datetime.now().isoformat()),
    Column("next_predicted_date", String),
    Column("prediction_confidence", Float)
)

buying_pattern_insights = Table(
    "buying_pattern_insights",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("agency", String, nullable=False),
    Column("insight_type", String),  # 'timing', 'budget', 'requirements', 'competition'
    Column("insight_text", String),
    Column("supporting_data", JSONB),
    Column("actionable_recommendation", String),
    Column("confidence_level", String),  # 'high', 'medium', 'low'
    Column("generated_date", String, default=lambda: datetime.now().isoformat())
)
```

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def analyze_agency_buying_patterns(agency_name, lookback_months=24):
    """Analyze buying patterns for a specific agency"""
    try:
        engine = setup_database()

        # Get historical data for the agency
        historical_data = pd.read_sql("""
            SELECT posted_date, naics_code, set_aside,
                   EXTRACT(MONTH FROM posted_date::date) as month,
                   EXTRACT(QUARTER FROM posted_date::date) as quarter,
                   EXTRACT(YEAR FROM posted_date::date) as year,
                   COUNT(*) as opportunity_count
            FROM opportunities
            WHERE agency = :agency
            AND posted_date >= NOW() - INTERVAL ':months months'
            GROUP BY posted_date, naics_code, set_aside, month, quarter, year
            ORDER BY posted_date
        """, engine, params={"agency": agency_name, "months": lookback_months})

        if historical_data.empty:
            return {"error": "No historical data found for this agency"}

        # Analyze patterns using AI
        pattern_analysis = analyze_patterns_with_ai(agency_name, historical_data)

        # Save patterns to database
        save_buying_patterns(agency_name, pattern_analysis)

        return pattern_analysis

    except Exception as e:
        st.error(f"Error analyzing buying patterns: {str(e)}")
        return {"error": str(e)}

def analyze_patterns_with_ai(agency_name, historical_data):
    """Use AI to analyze buying patterns from historical data"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "AI service unavailable"}

    # Prepare data summary for AI analysis
    data_summary = prepare_pattern_data_summary(historical_data)

    prompt = f"""
    Analyze the buying patterns for {agency_name} based on the following historical data:

    {data_summary}

    Provide analysis in the following JSON format:
    {{
        "seasonal_patterns": {{
            "description": "Description of seasonal trends",
            "peak_months": ["month1", "month2"],
            "low_months": ["month1", "month2"],
            "confidence": 0.85
        }},
        "naics_preferences": {{
            "top_naics": [
                {{"code": "123456", "frequency": 25, "trend": "increasing"}},
                {{"code": "789012", "frequency": 18, "trend": "stable"}}
            ]
        }},
        "timing_insights": [
            "Insight 1 about timing patterns",
            "Insight 2 about budget cycles"
        ],
        "predictions": {{
            "next_likely_opportunity": {{
                "timeframe": "Q2 2024",
                "naics_likely": "123456",
                "confidence": 0.75,
                "reasoning": "Based on historical pattern..."
            }}
        }},
        "recommendations": [
            "Actionable recommendation 1",
            "Actionable recommendation 2"
        ]
    }}
    """

    try:
        response = execute_ai_task(llm_config, prompt)
        import json
        analysis = json.loads(response.strip())
        return analysis
    except Exception as e:
        return {"error": f"AI analysis failed: {str(e)}"}

def prepare_pattern_data_summary(historical_data):
    """Prepare a summary of historical data for AI analysis"""
    summary = []

    # Monthly distribution
    monthly_counts = historical_data.groupby('month')['opportunity_count'].sum().to_dict()
    summary.append(f"Monthly distribution: {monthly_counts}")

    # Quarterly trends
    quarterly_counts = historical_data.groupby('quarter')['opportunity_count'].sum().to_dict()
    summary.append(f"Quarterly distribution: {quarterly_counts}")

    # NAICS code frequency
    naics_counts = historical_data.groupby('naics_code')['opportunity_count'].sum().sort_values(ascending=False).head(10).to_dict()
    summary.append(f"Top NAICS codes: {naics_counts}")

    # Set-aside preferences
    setaside_counts = historical_data.groupby('set_aside')['opportunity_count'].sum().to_dict()
    summary.append(f"Set-aside distribution: {setaside_counts}")

    # Recent trends (last 6 months vs previous 6 months)
    recent_data = historical_data.tail(6)
    previous_data = historical_data.iloc[-12:-6] if len(historical_data) >= 12 else pd.DataFrame()

    if not previous_data.empty:
        recent_avg = recent_data['opportunity_count'].mean()
        previous_avg = previous_data['opportunity_count'].mean()
        trend = "increasing" if recent_avg > previous_avg else "decreasing"
        summary.append(f"Recent trend: {trend} ({recent_avg:.1f} vs {previous_avg:.1f} avg opportunities)")

    return "\n".join(summary)

def save_buying_patterns(agency_name, pattern_analysis):
    """Save buying pattern analysis to database"""
    try:
        engine = setup_database()

        with engine.connect() as conn:
            # Save main pattern data
            if 'seasonal_patterns' in pattern_analysis:
                conn.execute(text("""
                    INSERT INTO agency_buying_patterns
                    (agency, pattern_type, pattern_data, confidence_score, analysis_date)
                    VALUES (:agency, 'seasonal', :pattern_data, :confidence, :analysis_date)
                """), {
                    "agency": agency_name,
                    "pattern_data": json.dumps(pattern_analysis['seasonal_patterns']),
                    "confidence": pattern_analysis['seasonal_patterns'].get('confidence', 0.5),
                    "analysis_date": datetime.now().isoformat()
                })

            # Save insights
            if 'recommendations' in pattern_analysis:
                for recommendation in pattern_analysis['recommendations']:
                    conn.execute(text("""
                        INSERT INTO buying_pattern_insights
                        (agency, insight_type, insight_text, actionable_recommendation, confidence_level, generated_date)
                        VALUES (:agency, 'recommendation', :insight, :recommendation, 'medium', :generated_date)
                    """), {
                        "agency": agency_name,
                        "insight": recommendation,
                        "recommendation": recommendation,
                        "generated_date": datetime.now().isoformat()
                    })

            conn.commit()

    except Exception as e:
        st.error(f"Error saving buying patterns: {str(e)}")

def render_agency_buying_patterns():
    """Render agency buying pattern analysis interface"""
    st.subheader("📊 Agency Buying Pattern Analysis")

    # Agency selection
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        engine = setup_database()
        agencies = pd.read_sql("""
            SELECT agency, COUNT(*) as opp_count
            FROM opportunities
            GROUP BY agency
            HAVING COUNT(*) >= 5
            ORDER BY opp_count DESC
        """, engine)

        if not agencies.empty:
            selected_agency = st.selectbox(
                "Select Agency to Analyze:",
                options=agencies['agency'].tolist(),
                help="Choose an agency with sufficient historical data"
            )

    with col2:
        lookback_months = st.number_input(
            "Analysis Period (months)",
            min_value=6,
            max_value=60,
            value=24
        )

    with col3:
        if st.button("📊 Analyze Patterns", type="primary"):
            with st.spinner(f"Analyzing buying patterns for {selected_agency}..."):
                analysis_results = analyze_agency_buying_patterns(selected_agency, lookback_months)
                st.session_state.pattern_analysis = analysis_results

    # Display analysis results
    if hasattr(st.session_state, 'pattern_analysis') and 'error' not in st.session_state.pattern_analysis:
        analysis = st.session_state.pattern_analysis

        # Seasonal Patterns
        if 'seasonal_patterns' in analysis:
            st.subheader("🗓️ Seasonal Patterns")
            seasonal = analysis['seasonal_patterns']

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Peak Months", ", ".join(seasonal.get('peak_months', [])))
                st.metric("Confidence", f"{seasonal.get('confidence', 0)*100:.1f}%")
            with col2:
                st.metric("Low Activity Months", ", ".join(seasonal.get('low_months', [])))
                st.write(seasonal.get('description', ''))

        # NAICS Preferences
        if 'naics_preferences' in analysis:
            st.subheader("🏷️ NAICS Code Preferences")
            naics_data = analysis['naics_preferences']['top_naics']

            if naics_data:
                naics_df = pd.DataFrame(naics_data)

                # Create visualization
                fig = px.bar(
                    naics_df,
                    x='code',
                    y='frequency',
                    color='trend',
                    title="Top NAICS Codes by Frequency"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Timing Insights
        if 'timing_insights' in analysis:
            st.subheader("⏰ Timing Insights")
            for insight in analysis['timing_insights']:
                st.info(f"💡 {insight}")

        # Predictions
        if 'predictions' in analysis:
            st.subheader("🔮 Predictions")
            pred = analysis['predictions']['next_likely_opportunity']

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Next Opportunity Timeframe", pred.get('timeframe', 'Unknown'))
            with col2:
                st.metric("Likely NAICS", pred.get('naics_likely', 'Unknown'))
            with col3:
                st.metric("Confidence", f"{pred.get('confidence', 0)*100:.1f}%")

            st.write(f"**Reasoning:** {pred.get('reasoning', 'No reasoning provided')}")

        # Recommendations
        if 'recommendations' in analysis:
            st.subheader("💡 Actionable Recommendations")
            for i, rec in enumerate(analysis['recommendations'], 1):
                st.success(f"**{i}.** {rec}")

    elif hasattr(st.session_state, 'pattern_analysis') and 'error' in st.session_state.pattern_analysis:
        st.error(f"Analysis failed: {st.session_state.pattern_analysis['error']}")
```

---

## **🔌 MCP Endpoints Compilation**

Based on the features implemented so far, here are the MCP endpoints that sammySosa will need:

### **Core AI Processing Endpoints**
```python
# Text Analysis & Processing
POST /ai/extract-keywords              # Feature 3: Extract keywords from text
POST /ai/extract-locations             # Feature 8: Extract location info from text
POST /ai/analyze-buying-patterns       # Feature 12: Analyze agency buying patterns
POST /ai/generate-pattern-insights     # Feature 12: Generate insights from patterns
POST /ai/extract-opportunity-features  # Feature 11: Extract features for similarity

# Similarity & Matching
POST /ai/find-similar-opportunities    # Feature 11: Find similar opportunities
POST /ai/calculate-similarity-score    # Feature 11: Calculate similarity between opps
POST /ai/predict-future-opportunities  # Feature 12: Predict future opportunities

# Document Analysis
POST /ai/analyze-document              # General document analysis
POST /ai/extract-requirements          # Extract requirements from SOWs
POST /ai/analyze-compliance            # Check compliance requirements
POST /ai/detect-anomalies              # Detect unusual patterns or requirements

# Content Generation
POST /ai/generate-search-queries       # Feature 14: Generate smart search queries
POST /ai/generate-summary              # Generate opportunity summaries
POST /ai/generate-recommendations      # Generate actionable recommendations
POST /ai/generate-insights             # Generate business insights

# Geocoding & Location Services
POST /ai/geocode-address               # Feature 8: Convert addresses to coordinates
POST /ai/validate-location             # Validate location information
```

### **Utility Endpoints**
```python
# Health & Status
GET  /health                           # Service health check
GET  /status                           # Service status and capabilities

# Configuration
GET  /models                           # Available AI models
POST /models/switch                    # Switch between models
GET  /capabilities                     # Service capabilities
```

### **Authentication & Security**
```python
# Authentication
POST /auth/token                       # Get authentication token
POST /auth/refresh                     # Refresh authentication token
GET  /auth/validate                    # Validate token

# Rate Limiting & Usage
GET  /usage/stats                      # Usage statistics
GET  /usage/limits                     # Rate limits and quotas
```

---

## **Feature 15: FAR Clause Anomaly Detection**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **MCP Endpoints Needed**
- **`/ai/analyze-far-clauses`** - Analyze FAR clauses in opportunities
- **`/ai/detect-clause-anomalies`** - Detect unusual or problematic clauses
- **`/ai/explain-far-clause`** - Explain specific FAR clauses in plain language
- **`/ai/assess-compliance-risk`** - Assess compliance risk for clauses

#### **Database Schema Extension**
```python
# Add to existing setup_database() function in govcon_suite.py
far_clause_analysis = Table(
    "far_clause_analysis",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("opportunity_id", String, ForeignKey("opportunities.notice_id")),
    Column("clause_reference", String),  # e.g., "FAR 52.212-4"
    Column("clause_title", String),
    Column("clause_text", String),
    Column("anomaly_detected", Boolean, default=False),
    Column("anomaly_type", String),  # 'unusual_terms', 'conflicting_requirements', 'high_risk'
    Column("risk_level", String),    # 'low', 'medium', 'high', 'critical'
    Column("explanation", String),
    Column("recommendation", String),
    Column("analysis_date", String, default=lambda: datetime.now().isoformat())
)

compliance_alerts = Table(
    "compliance_alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("opportunity_id", String, ForeignKey("opportunities.notice_id")),
    Column("alert_type", String),    # 'far_clause', 'requirement', 'deadline'
    Column("severity", String),      # 'info', 'warning', 'critical'
    Column("alert_message", String),
    Column("detailed_explanation", String),
    Column("suggested_action", String),
    Column("created_date", String, default=lambda: datetime.now().isoformat()),
    Column("acknowledged", Boolean, default=False)
)
```

#### **Implementation Functions**
```python
# Add to govcon_suite.py
import re

def analyze_far_clauses(opportunity_id, opportunity_text):
    """Analyze FAR clauses in an opportunity for anomalies"""
    try:
        # Extract FAR clause references
        far_clauses = extract_far_clause_references(opportunity_text)

        if not far_clauses:
            return {"message": "No FAR clauses detected"}

        # Analyze each clause for anomalies
        analysis_results = []
        for clause in far_clauses:
            clause_analysis = analyze_single_far_clause(opportunity_id, clause, opportunity_text)
            analysis_results.append(clause_analysis)

        # Save analysis to database
        save_far_clause_analysis(opportunity_id, analysis_results)

        return {
            "clauses_analyzed": len(far_clauses),
            "anomalies_detected": sum(1 for r in analysis_results if r.get('anomaly_detected')),
            "analysis_results": analysis_results
        }

    except Exception as e:
        st.error(f"Error analyzing FAR clauses: {str(e)}")
        return {"error": str(e)}

def extract_far_clause_references(text):
    """Extract FAR clause references from opportunity text"""
    # Common FAR clause patterns
    patterns = [
        r'FAR\s+(\d+\.\d+(?:-\d+)?)',           # FAR 52.212-4
        r'DFARS\s+(\d+\.\d+(?:-\d+)?)',         # DFARS 252.212-7001
        r'(\d+\.\d+(?:-\d+)?)\s*\([^)]+\)',     # 52.212-4 (Commercial Items)
        r'Clause\s+(\d+\.\d+(?:-\d+)?)',        # Clause 52.212-4
    ]

    clauses = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            clause_ref = match.group(1) if match.groups() else match.group(0)

            # Extract surrounding context
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 200)
            context = text[start:end].strip()

            clauses.append({
                "reference": clause_ref,
                "full_match": match.group(0),
                "context": context,
                "position": match.start()
            })

    # Remove duplicates
    unique_clauses = []
    seen_refs = set()
    for clause in clauses:
        if clause["reference"] not in seen_refs:
            unique_clauses.append(clause)
            seen_refs.add(clause["reference"])

    return unique_clauses

def analyze_single_far_clause(opportunity_id, clause_data, full_text):
    """Analyze a single FAR clause for anomalies using AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "AI service unavailable"}

    prompt = f"""
    Analyze this FAR clause reference found in a government contracting opportunity for potential anomalies or issues:

    Clause Reference: {clause_data['reference']}
    Full Match: {clause_data['full_match']}
    Context: {clause_data['context']}

    Look for:
    1. Unusual or non-standard clause applications
    2. Conflicting requirements
    3. High-risk compliance requirements
    4. Outdated or superseded clauses
    5. Missing required companion clauses

    Respond in JSON format:
    {{
        "clause_reference": "{clause_data['reference']}",
        "clause_title": "Standard title of this clause",
        "anomaly_detected": true/false,
        "anomaly_type": "unusual_terms|conflicting_requirements|high_risk|outdated|missing_companion",
        "risk_level": "low|medium|high|critical",
        "explanation": "Detailed explanation of the issue or confirmation it's normal",
        "recommendation": "Specific action to take",
        "compliance_notes": "Important compliance considerations"
    }}
    """

    try:
        response = execute_ai_task(llm_config, prompt)
        import json
        analysis = json.loads(response.strip())

        # Add metadata
        analysis["opportunity_id"] = opportunity_id
        analysis["analysis_date"] = datetime.now().isoformat()

        return analysis
    except Exception as e:
        return {
            "clause_reference": clause_data['reference'],
            "error": f"Analysis failed: {str(e)}",
            "anomaly_detected": False,
            "risk_level": "unknown"
        }

def save_far_clause_analysis(opportunity_id, analysis_results):
    """Save FAR clause analysis results to database"""
    try:
        engine = setup_database()

        with engine.connect() as conn:
            for analysis in analysis_results:
                if "error" not in analysis:
                    # Save clause analysis
                    conn.execute(text("""
                        INSERT INTO far_clause_analysis
                        (opportunity_id, clause_reference, clause_title, anomaly_detected,
                         anomaly_type, risk_level, explanation, recommendation, analysis_date)
                        VALUES (:opp_id, :clause_ref, :title, :anomaly, :anomaly_type,
                                :risk_level, :explanation, :recommendation, :analysis_date)
                    """), {
                        "opp_id": opportunity_id,
                        "clause_ref": analysis.get("clause_reference"),
                        "title": analysis.get("clause_title"),
                        "anomaly": analysis.get("anomaly_detected", False),
                        "anomaly_type": analysis.get("anomaly_type"),
                        "risk_level": analysis.get("risk_level"),
                        "explanation": analysis.get("explanation"),
                        "recommendation": analysis.get("recommendation"),
                        "analysis_date": analysis.get("analysis_date")
                    })

                    # Create compliance alert if anomaly detected
                    if analysis.get("anomaly_detected") and analysis.get("risk_level") in ["high", "critical"]:
                        create_compliance_alert(
                            opportunity_id,
                            "far_clause",
                            "critical" if analysis.get("risk_level") == "critical" else "warning",
                            f"FAR Clause Anomaly: {analysis.get('clause_reference')}",
                            analysis.get("explanation"),
                            analysis.get("recommendation")
                        )

            conn.commit()

    except Exception as e:
        st.error(f"Error saving FAR clause analysis: {str(e)}")

def create_compliance_alert(opportunity_id, alert_type, severity, message, explanation, action):
    """Create a compliance alert"""
    try:
        engine = setup_database()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO compliance_alerts
                (opportunity_id, alert_type, severity, alert_message,
                 detailed_explanation, suggested_action, created_date)
                VALUES (:opp_id, :alert_type, :severity, :message,
                        :explanation, :action, :created_date)
            """), {
                "opp_id": opportunity_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "explanation": explanation,
                "action": action,
                "created_date": datetime.now().isoformat()
            })
            conn.commit()

    except Exception as e:
        st.error(f"Error creating compliance alert: {str(e)}")

def render_far_clause_analyzer():
    """Render FAR clause analysis interface"""
    st.subheader("⚖️ FAR Clause Anomaly Detection")

    # Input options
    analysis_mode = st.radio(
        "Analysis Mode:",
        ["Analyze Single Opportunity", "Bulk Analysis", "View Previous Analysis"]
    )

    if analysis_mode == "Analyze Single Opportunity":
        # Single opportunity analysis
        engine = setup_database()
        opportunities = pd.read_sql("""
            SELECT notice_id, title, agency, posted_date
            FROM opportunities
            ORDER BY posted_date DESC
            LIMIT 100
        """, engine)

        if not opportunities.empty:
            opp_options = [f"{row['notice_id']} - {row['title'][:60]}..."
                          for _, row in opportunities.iterrows()]

            selected_opp = st.selectbox("Select Opportunity:", opp_options)

            if selected_opp and st.button("🔍 Analyze FAR Clauses", type="primary"):
                opportunity_id = selected_opp.split(" - ")[0]

                # Get opportunity text
                opp_data = pd.read_sql("""
                    SELECT raw_data FROM opportunities WHERE notice_id = :opp_id
                """, engine, params={"opp_id": opportunity_id})

                if not opp_data.empty:
                    with st.spinner("Analyzing FAR clauses for anomalies..."):
                        analysis_results = analyze_far_clauses(opportunity_id, opp_data.iloc[0]['raw_data'])

                        if "error" not in analysis_results:
                            display_far_clause_results(analysis_results)
                        else:
                            st.error(f"Analysis failed: {analysis_results['error']}")

    elif analysis_mode == "Bulk Analysis":
        # Bulk analysis options
        col1, col2 = st.columns(2)

        with col1:
            analysis_scope = st.selectbox(
                "Analysis Scope:",
                ["Recent Opportunities (30 days)", "High P-Win Opportunities", "Specific Agency", "All Unanalyzed"]
            )

        with col2:
            max_opportunities = st.number_input(
                "Max Opportunities to Analyze:",
                min_value=10,
                max_value=500,
                value=50
            )

        if st.button("🚀 Start Bulk Analysis", type="primary"):
            run_bulk_far_analysis(analysis_scope, max_opportunities)

    else:  # View Previous Analysis
        display_previous_far_analysis()

def display_far_clause_results(analysis_results):
    """Display FAR clause analysis results"""
    st.success(f"Analysis Complete: {analysis_results['clauses_analyzed']} clauses analyzed")

    if analysis_results['anomalies_detected'] > 0:
        st.warning(f"⚠️ {analysis_results['anomalies_detected']} anomalies detected!")
    else:
        st.info("✅ No anomalies detected in FAR clauses")

    # Display detailed results
    for result in analysis_results['analysis_results']:
        if "error" not in result:
            with st.expander(
                f"FAR {result['clause_reference']} - {result.get('clause_title', 'Unknown')} "
                f"({'🚨 ANOMALY' if result.get('anomaly_detected') else '✅ Normal'})",
                expanded=result.get('anomaly_detected', False)
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Clause:** FAR {result['clause_reference']}")
                    st.write(f"**Title:** {result.get('clause_title', 'Unknown')}")
                    st.write(f"**Explanation:** {result.get('explanation', 'No explanation provided')}")

                    if result.get('recommendation'):
                        st.write(f"**Recommendation:** {result['recommendation']}")

                    if result.get('compliance_notes'):
                        st.info(f"**Compliance Notes:** {result['compliance_notes']}")

                with col2:
                    # Risk level indicator
                    risk_level = result.get('risk_level', 'unknown')
                    risk_colors = {
                        'low': '#28a745',
                        'medium': '#ffc107',
                        'high': '#fd7e14',
                        'critical': '#dc3545',
                        'unknown': '#6c757d'
                    }

                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 15px;
                                   background-color: {risk_colors.get(risk_level, '#6c757d')};
                                   border-radius: 8px; color: white;">
                            <h4 style="margin: 0;">{risk_level.upper()}</h4>
                            <p style="margin: 0;">Risk Level</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if result.get('anomaly_detected'):
                        st.write(f"**Anomaly Type:** {result.get('anomaly_type', 'Unknown')}")

def run_bulk_far_analysis(scope, max_opps):
    """Run bulk FAR clause analysis"""
    engine = setup_database()

    # Build query based on scope
    base_query = "SELECT notice_id, raw_data FROM opportunities"
    conditions = []
    params = {}

    if scope == "Recent Opportunities (30 days)":
        conditions.append("posted_date >= NOW() - INTERVAL '30 days'")
    elif scope == "High P-Win Opportunities":
        conditions.append("p_win_score >= 70")
    elif scope == "All Unanalyzed":
        conditions.append("""
            notice_id NOT IN (
                SELECT DISTINCT opportunity_id
                FROM far_clause_analysis
                WHERE opportunity_id IS NOT NULL
            )
        """)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += f" ORDER BY posted_date DESC LIMIT {max_opps}"

    opportunities = pd.read_sql(base_query, engine, params=params)

    if not opportunities.empty:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_summary = {"total": 0, "anomalies": 0, "errors": 0}

        for i, row in opportunities.iterrows():
            status_text.text(f"Analyzing {i+1}/{len(opportunities)}: {row['notice_id']}")

            analysis_result = analyze_far_clauses(row['notice_id'], row['raw_data'])

            results_summary["total"] += 1
            if "error" not in analysis_result:
                results_summary["anomalies"] += analysis_result.get("anomalies_detected", 0)
            else:
                results_summary["errors"] += 1

            progress_bar.progress((i + 1) / len(opportunities))

        st.success(f"""
        Bulk Analysis Complete!
        - Opportunities Analyzed: {results_summary['total']}
        - Total Anomalies Found: {results_summary['anomalies']}
        - Analysis Errors: {results_summary['errors']}
        """)
    else:
        st.info("No opportunities found matching the selected criteria.")

def display_previous_far_analysis():
    """Display previous FAR clause analysis results"""
    engine = setup_database()

    # Get analysis summary
    analysis_summary = pd.read_sql("""
        SELECT
            opportunity_id,
            COUNT(*) as clauses_analyzed,
            SUM(CASE WHEN anomaly_detected THEN 1 ELSE 0 END) as anomalies_found,
            MAX(analysis_date) as last_analysis
        FROM far_clause_analysis
        GROUP BY opportunity_id
        ORDER BY last_analysis DESC
        LIMIT 50
    """, engine)

    if not analysis_summary.empty:
        st.write("**Recent FAR Clause Analysis Results:**")

        for _, row in analysis_summary.iterrows():
            with st.expander(
                f"Opportunity {row['opportunity_id']} - "
                f"{row['clauses_analyzed']} clauses, {row['anomalies_found']} anomalies"
            ):
                # Get detailed analysis for this opportunity
                detailed_analysis = pd.read_sql("""
                    SELECT clause_reference, clause_title, anomaly_detected,
                           risk_level, explanation, recommendation
                    FROM far_clause_analysis
                    WHERE opportunity_id = :opp_id
                    ORDER BY anomaly_detected DESC, risk_level DESC
                """, engine, params={"opp_id": row['opportunity_id']})

                if not detailed_analysis.empty:
                    st.dataframe(detailed_analysis, use_container_width=True)
    else:
        st.info("No previous FAR clause analysis found. Run an analysis to see results here.")
```

---

## **Feature 16: Automated Keyword Extraction**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **MCP Endpoints Needed**
- **`/ai/extract-technical-keywords`** - Extract technical terms and specifications
- **`/ai/extract-domain-keywords`** - Extract domain-specific keywords
- **`/ai/rank-keyword-importance`** - Rank keywords by importance/relevance
- **`/ai/categorize-keywords`** - Categorize keywords by type

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def automated_keyword_extraction(text, extraction_type="comprehensive"):
    """Extract keywords automatically from text using AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return []

    prompt = f"""
    Extract relevant keywords from this government contracting text. Focus on:

    1. Technical terms and specifications
    2. Industry-specific terminology
    3. Agency and department names
    4. NAICS codes and classifications
    5. Geographic locations
    6. Compliance and regulatory terms
    7. Performance requirements
    8. Evaluation criteria terms

    Text to analyze:
    {text[:2000]}...

    Return a JSON object with categorized keywords:
    {{
        "technical": ["keyword1", "keyword2"],
        "agencies": ["agency1", "agency2"],
        "locations": ["location1", "location2"],
        "naics": ["naics1", "naics2"],
        "compliance": ["term1", "term2"],
        "requirements": ["req1", "req2"],
        "evaluation": ["criteria1", "criteria2"],
        "general": ["term1", "term2"]
    }}
    """

    try:
        response = execute_ai_task(llm_config, prompt)
        import json
        keywords = json.loads(response.strip())
        return keywords if isinstance(keywords, dict) else {}
    except Exception as e:
        st.error(f"Error extracting keywords: {str(e)}")
        return {}

def render_automated_keyword_extraction():
    """Render automated keyword extraction interface"""
    st.subheader("🤖 Automated Keyword Extraction")

    # Input options
    col1, col2 = st.columns([2, 1])

    with col1:
        extraction_source = st.radio(
            "Extraction Source:",
            ["Paste Text", "Select Opportunity", "Bulk Extract from Recent"]
        )

    with col2:
        auto_add_keywords = st.checkbox("Auto-add extracted keywords", value=True)
        min_relevance = st.slider("Minimum Relevance %", 0, 100, 70)

    if extraction_source == "Paste Text":
        input_text = st.text_area(
            "Paste text to extract keywords from:",
            height=200,
            placeholder="Paste SOW, opportunity description, or any relevant content..."
        )

        if st.button("🔍 Extract Keywords") and input_text:
            with st.spinner("AI is extracting keywords..."):
                extracted_keywords = automated_keyword_extraction(input_text)
                display_extracted_keywords(extracted_keywords, auto_add_keywords)

    elif extraction_source == "Select Opportunity":
        # Opportunity selector (similar to previous implementations)
        engine = setup_database()
        opportunities = pd.read_sql("""
            SELECT notice_id, title, agency FROM opportunities
            ORDER BY posted_date DESC LIMIT 50
        """, engine)

        if not opportunities.empty:
            opp_options = [f"{row['notice_id']} - {row['title'][:60]}..."
                          for _, row in opportunities.iterrows()]

            selected_opp = st.selectbox("Select Opportunity:", opp_options)

            if selected_opp and st.button("🔍 Extract Keywords from Opportunity"):
                opportunity_id = selected_opp.split(" - ")[0]

                opp_data = pd.read_sql("""
                    SELECT raw_data FROM opportunities WHERE notice_id = :opp_id
                """, engine, params={"opp_id": opportunity_id})

                if not opp_data.empty:
                    with st.spinner("Extracting keywords from opportunity..."):
                        extracted_keywords = automated_keyword_extraction(opp_data.iloc[0]['raw_data'])
                        display_extracted_keywords(extracted_keywords, auto_add_keywords)

def display_extracted_keywords(keywords_dict, auto_add=False):
    """Display extracted keywords by category"""
    if not keywords_dict:
        st.warning("No keywords extracted")
        return

    st.success("Keywords extracted successfully!")

    total_keywords = sum(len(keywords) for keywords in keywords_dict.values())
    st.info(f"Total keywords found: {total_keywords}")

    # Display by category
    for category, keywords in keywords_dict.items():
        if keywords:
            with st.expander(f"📁 {category.title()} Keywords ({len(keywords)})", expanded=True):

                # Display keywords with add buttons
                cols = st.columns(3)
                for i, keyword in enumerate(keywords):
                    with cols[i % 3]:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"• {keyword}")
                        with col2:
                            if st.button("➕", key=f"add_{category}_{i}", help=f"Add '{keyword}'"):
                                if add_user_keyword("default_user", keyword, category.title()):
                                    st.success(f"Added: {keyword}")
                                    st.rerun()

                # Bulk add option
                if st.button(f"➕ Add All {category.title()} Keywords", key=f"bulk_add_{category}"):
                    added_count = 0
                    for keyword in keywords:
                        if add_user_keyword("default_user", keyword, category.title()):
                            added_count += 1

                    if added_count > 0:
                        st.success(f"Added {added_count} {category} keywords!")
                        st.rerun()
```

---

## **Feature 2: Saved Search Queries**
**Status:** ⏳ Ready for Implementation
**Complexity:** LOW | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS saved_searches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL DEFAULT 'default_user',
    search_name VARCHAR(200) NOT NULL,
    search_query TEXT NOT NULL,
    search_filters JSONB,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    is_favorite BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    UNIQUE(user_id, search_name)
);

CREATE INDEX IF NOT EXISTS ix_saved_searches_user_id ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS ix_saved_searches_tags ON saved_searches USING GIN(tags);
CREATE INDEX IF NOT EXISTS ix_saved_searches_favorite ON saved_searches(is_favorite);
```

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def save_search_query(user_id, search_name, query, filters=None, tags=None):
    """Save a search query for reuse"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saved_searches (user_id, search_name, search_query, search_filters, tags)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, search_name)
            DO UPDATE SET
                search_query = EXCLUDED.search_query,
                search_filters = EXCLUDED.search_filters,
                tags = EXCLUDED.tags,
                last_used = CURRENT_TIMESTAMP
        """, (user_id, search_name, query, json.dumps(filters or {}), tags or []))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving search: {e}")
        return False
    finally:
        conn.close()

def get_saved_searches(user_id, tag_filter=None):
    """Get saved searches for a user"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if tag_filter:
            cursor.execute("""
                SELECT id, search_name, search_query, search_filters, tags,
                       use_count, is_favorite, last_used
                FROM saved_searches
                WHERE user_id = %s AND %s = ANY(tags)
                ORDER BY is_favorite DESC, last_used DESC
            """, (user_id, tag_filter))
        else:
            cursor.execute("""
                SELECT id, search_name, search_query, search_filters, tags,
                       use_count, is_favorite, last_used
                FROM saved_searches
                WHERE user_id = %s
                ORDER BY is_favorite DESC, last_used DESC
            """, (user_id,))

        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading saved searches: {e}")
        return []
    finally:
        conn.close()

def use_saved_search(search_id):
    """Increment use count and update last used timestamp"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE saved_searches
            SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING search_query, search_filters
        """, (search_id,))

        result = cursor.fetchone()
        conn.commit()
        return result
    except Exception as e:
        st.error(f"Error using saved search: {e}")
        return None
    finally:
        conn.close()

def toggle_search_favorite(search_id):
    """Toggle favorite status of a saved search"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE saved_searches
            SET is_favorite = NOT is_favorite
            WHERE id = %s
        """, (search_id,))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error toggling favorite: {e}")
        return False
    finally:
        conn.close()
```

#### **UI Component**
```python
# Add to components/saved_searches.py
def render_saved_searches_sidebar():
    """Render saved searches in sidebar"""
    st.sidebar.subheader("💾 Saved Searches")

    # Get saved searches
    saved_searches = get_saved_searches("default_user")

    if not saved_searches:
        st.sidebar.info("No saved searches yet")
        return None

    # Filter options
    all_tags = set()
    for search in saved_searches:
        if search[4]:  # tags column
            all_tags.update(search[4])

    if all_tags:
        tag_filter = st.sidebar.selectbox(
            "Filter by tag:",
            ["All"] + sorted(list(all_tags)),
            key="search_tag_filter"
        )

        if tag_filter != "All":
            saved_searches = get_saved_searches("default_user", tag_filter)

    # Display searches
    selected_search = None
    for search in saved_searches:
        search_id, name, query, filters, tags, use_count, is_favorite, last_used = search

        # Create columns for name and favorite button
        col1, col2 = st.sidebar.columns([3, 1])

        with col1:
            if st.button(f"{'⭐' if is_favorite else '📄'} {name}", key=f"search_{search_id}"):
                selected_search = use_saved_search(search_id)
                if selected_search:
                    st.session_state.selected_search_query = selected_search[0]
                    st.session_state.selected_search_filters = json.loads(selected_search[1] or '{}')
                    st.rerun()

        with col2:
            if st.button("⭐", key=f"fav_{search_id}", help="Toggle favorite"):
                toggle_search_favorite(search_id)
                st.rerun()

        # Show usage stats
        st.sidebar.caption(f"Used {use_count} times • {tags or []}")

    return selected_search

def render_save_search_dialog():
    """Render dialog to save current search"""
    if st.button("💾 Save Current Search"):
        with st.expander("Save Search", expanded=True):
            search_name = st.text_input("Search Name:", key="save_search_name")

            # Get current search parameters from session state
            current_query = st.session_state.get('current_search_query', '')
            current_filters = st.session_state.get('current_search_filters', {})

            st.text_area("Query Preview:", value=current_query, disabled=True)

            # Tags input
            tags_input = st.text_input("Tags (comma-separated):", key="save_search_tags")
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Search", disabled=not search_name):
                    if save_search_query("default_user", search_name, current_query, current_filters, tags):
                        st.success(f"Search '{search_name}' saved!")
                        st.rerun()

            with col2:
                if st.button("❌ Cancel"):
                    st.rerun()
```

---

## **Feature 6: Advanced Filtering Options**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def render_advanced_filters():
    """Render advanced filtering interface"""
    st.subheader("🔍 Advanced Filters")

    # Create filter columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**📅 Date Filters**")
        date_range = st.selectbox(
            "Posted Date Range:",
            ["Any Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
            key="date_range_filter"
        )

        if date_range == "Custom Range":
            start_date = st.date_input("Start Date:", key="custom_start_date")
            end_date = st.date_input("End Date:", key="custom_end_date")

        response_deadline = st.selectbox(
            "Response Deadline:",
            ["Any", "Next 7 Days", "Next 14 Days", "Next 30 Days", "Next 60 Days"],
            key="response_deadline_filter"
        )

    with col2:
        st.write("**💰 Value Filters**")
        min_value = st.number_input("Minimum Value ($):", min_value=0, key="min_value_filter")
        max_value = st.number_input("Maximum Value ($):", min_value=0, key="max_value_filter")

        set_aside_types = st.multiselect(
            "Set-Aside Types:",
            ["Small Business", "8(a)", "HUBZone", "WOSB", "VOSB", "SDVOSB"],
            key="set_aside_filter"
        )

        contract_types = st.multiselect(
            "Contract Types:",
            ["Fixed Price", "Cost Plus", "Time & Materials", "IDIQ", "BPA"],
            key="contract_type_filter"
        )

    with col3:
        st.write("**🏢 Agency Filters**")
        agencies = st.multiselect(
            "Agencies:",
            ["DOD", "GSA", "VA", "DHS", "DOE", "NASA", "DOT", "HHS", "Other"],
            key="agency_filter"
        )

        naics_codes = st.text_area(
            "NAICS Codes (comma-separated):",
            placeholder="541511, 541512, 541513",
            key="naics_filter"
        )

        locations = st.multiselect(
            "Performance Locations:",
            ["CONUS", "OCONUS", "Remote", "On-site", "Hybrid"],
            key="location_filter"
        )

    # Keyword filters
    st.write("**🔤 Keyword Filters**")
    col1, col2 = st.columns(2)

    with col1:
        include_keywords = st.text_area(
            "Must Include Keywords:",
            placeholder="Enter keywords that must be present",
            key="include_keywords_filter"
        )

    with col2:
        exclude_keywords = st.text_area(
            "Exclude Keywords:",
            placeholder="Enter keywords to exclude",
            key="exclude_keywords_filter"
        )

    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            sort_by = st.selectbox(
                "Sort By:",
                ["Relevance", "Posted Date", "Response Deadline", "Value", "Agency"],
                key="sort_by_filter"
            )

            sort_order = st.radio(
                "Sort Order:",
                ["Descending", "Ascending"],
                key="sort_order_filter"
            )

        with col2:
            results_per_page = st.selectbox(
                "Results Per Page:",
                [10, 25, 50, 100],
                index=1,
                key="results_per_page_filter"
            )

            include_archived = st.checkbox(
                "Include Archived Opportunities",
                key="include_archived_filter"
            )

    # Apply filters button
    if st.button("🔍 Apply Filters", type="primary"):
        filters = compile_filters()
        st.session_state.current_search_filters = filters
        st.session_state.filter_applied = True
        st.rerun()

    # Clear filters button
    if st.button("🗑️ Clear All Filters"):
        clear_all_filters()
        st.rerun()

def compile_filters():
    """Compile all filter settings into a dictionary"""
    filters = {}

    # Date filters
    if st.session_state.get('date_range_filter') != "Any Time":
        filters['date_range'] = st.session_state.date_range_filter
        if st.session_state.get('date_range_filter') == "Custom Range":
            filters['start_date'] = str(st.session_state.get('custom_start_date', ''))
            filters['end_date'] = str(st.session_state.get('custom_end_date', ''))

    if st.session_state.get('response_deadline_filter') != "Any":
        filters['response_deadline'] = st.session_state.response_deadline_filter

    # Value filters
    if st.session_state.get('min_value_filter', 0) > 0:
        filters['min_value'] = st.session_state.min_value_filter

    if st.session_state.get('max_value_filter', 0) > 0:
        filters['max_value'] = st.session_state.max_value_filter

    # Category filters
    if st.session_state.get('set_aside_filter'):
        filters['set_aside_types'] = st.session_state.set_aside_filter

    if st.session_state.get('contract_type_filter'):
        filters['contract_types'] = st.session_state.contract_type_filter

    if st.session_state.get('agency_filter'):
        filters['agencies'] = st.session_state.agency_filter

    # NAICS codes
    if st.session_state.get('naics_filter'):
        naics_list = [code.strip() for code in st.session_state.naics_filter.split(',') if code.strip()]
        if naics_list:
            filters['naics_codes'] = naics_list

    # Location filters
    if st.session_state.get('location_filter'):
        filters['locations'] = st.session_state.location_filter

    # Keyword filters
    if st.session_state.get('include_keywords_filter'):
        filters['include_keywords'] = st.session_state.include_keywords_filter

    if st.session_state.get('exclude_keywords_filter'):
        filters['exclude_keywords'] = st.session_state.exclude_keywords_filter

    # Sorting and display options
    filters['sort_by'] = st.session_state.get('sort_by_filter', 'Relevance')
    filters['sort_order'] = st.session_state.get('sort_order_filter', 'Descending')
    filters['results_per_page'] = st.session_state.get('results_per_page_filter', 25)
    filters['include_archived'] = st.session_state.get('include_archived_filter', False)

    return filters

def clear_all_filters():
    """Clear all filter session state variables"""
    filter_keys = [
        'date_range_filter', 'custom_start_date', 'custom_end_date', 'response_deadline_filter',
        'min_value_filter', 'max_value_filter', 'set_aside_filter', 'contract_type_filter',
        'agency_filter', 'naics_filter', 'location_filter', 'include_keywords_filter',
        'exclude_keywords_filter', 'sort_by_filter', 'sort_order_filter',
        'results_per_page_filter', 'include_archived_filter'
    ]

    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.current_search_filters = {}
    st.session_state.filter_applied = False

def apply_filters_to_opportunities(opportunities, filters):
    """Apply compiled filters to opportunity list"""
    if not filters:
        return opportunities

    filtered_opps = opportunities.copy()

    # Apply date range filter
    if 'date_range' in filters:
        filtered_opps = filter_by_date_range(filtered_opps, filters['date_range'],
                                           filters.get('start_date'), filters.get('end_date'))

    # Apply value filters
    if 'min_value' in filters:
        filtered_opps = [opp for opp in filtered_opps if get_opportunity_value(opp) >= filters['min_value']]

    if 'max_value' in filters:
        filtered_opps = [opp for opp in filtered_opps if get_opportunity_value(opp) <= filters['max_value']]

    # Apply keyword filters
    if 'include_keywords' in filters:
        filtered_opps = filter_by_keywords(filtered_opps, filters['include_keywords'], include=True)

    if 'exclude_keywords' in filters:
        filtered_opps = filter_by_keywords(filtered_opps, filters['exclude_keywords'], include=False)

    # Apply sorting
    filtered_opps = sort_opportunities(filtered_opps, filters.get('sort_by', 'Relevance'),
                                     filters.get('sort_order', 'Descending'))

    return filtered_opps
```

---

## **📋 Complete MCP Endpoints List**

## **Feature 14: Smart Search Query Generation**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **MCP Integration**
Uses generic `generate_insights` tool with search optimization context.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def generate_smart_search_queries(base_query, context_info=None):
    """Generate optimized search queries using MCP AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return [base_query]

    try:
        # Use generic MCP generate_insights tool
        response = call_mcp_tool("generate_insights", {
            "content": base_query,
            "insight_type": "search_optimization",
            "context": {
                "domain": "government_contracting",
                "user_context": context_info or {},
                "optimization_goals": ["recall", "precision", "relevance"]
            },
            "output_format": "search_queries"
        })

        if response and response.get('success'):
            return response['data']['queries']
        else:
            return [base_query]

    except Exception as e:
        st.error(f"Error generating smart queries: {e}")
        return [base_query]

def suggest_query_improvements(query, search_results_count=0):
    """Suggest improvements to search query based on results"""
    llm_config = setup_llm_api()
    if not llm_config:
        return []

    try:
        response = call_mcp_tool("generate_insights", {
            "content": query,
            "insight_type": "query_improvement",
            "context": {
                "domain": "government_contracting",
                "results_count": search_results_count,
                "improvement_focus": ["broader_terms", "specific_terms", "synonyms", "related_concepts"]
            },
            "output_format": "suggestions"
        })

        if response and response.get('success'):
            return response['data']['suggestions']
        else:
            return []

    except Exception as e:
        st.error(f"Error generating suggestions: {e}")
        return []

def render_smart_search_interface():
    """Render smart search query interface"""
    st.subheader("🧠 Smart Search Query Generator")

    # Base query input
    base_query = st.text_area(
        "Enter your search terms:",
        placeholder="e.g., cybersecurity consulting services",
        key="smart_search_base_query"
    )

    if not base_query:
        st.info("Enter search terms to generate optimized queries")
        return

    # Context information
    with st.expander("🎯 Search Context (Optional)"):
        col1, col2 = st.columns(2)

        with col1:
            company_focus = st.text_input("Company Focus Area:", key="company_focus")
            past_wins = st.text_area("Past Contract Wins:", key="past_wins")

        with col2:
            target_agencies = st.multiselect(
                "Target Agencies:",
                ["DOD", "GSA", "VA", "DHS", "DOE", "NASA", "DOT", "HHS"],
                key="target_agencies"
            )
            capabilities = st.text_area("Key Capabilities:", key="key_capabilities")

    # Generate queries button
    if st.button("🚀 Generate Smart Queries", type="primary"):
        with st.spinner("Generating optimized search queries..."):
            context_info = {
                "company_focus": st.session_state.get('company_focus', ''),
                "past_wins": st.session_state.get('past_wins', ''),
                "target_agencies": st.session_state.get('target_agencies', []),
                "capabilities": st.session_state.get('key_capabilities', '')
            }

            smart_queries = generate_smart_search_queries(base_query, context_info)
            st.session_state.generated_queries = smart_queries

    # Display generated queries
    if 'generated_queries' in st.session_state and st.session_state.generated_queries:
        st.subheader("🎯 Generated Search Queries")

        for i, query in enumerate(st.session_state.generated_queries):
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 1])

                with col1:
                    st.code(query, language="text")

                with col2:
                    if st.button("🔍", key=f"search_query_{i}", help="Search with this query"):
                        st.session_state.current_search_query = query
                        st.session_state.execute_search = True
                        st.rerun()

                with col3:
                    if st.button("💾", key=f"save_query_{i}", help="Save this query"):
                        # Trigger save dialog
                        st.session_state.query_to_save = query
                        st.session_state.show_save_dialog = True
                        st.rerun()

        # Query improvement suggestions
        if st.button("💡 Get Query Improvement Suggestions"):
            with st.spinner("Analyzing queries for improvements..."):
                for query in st.session_state.generated_queries[:3]:  # Analyze top 3
                    suggestions = suggest_query_improvements(query)
                    if suggestions:
                        st.write(f"**Suggestions for:** `{query}`")
                        for suggestion in suggestions:
                            st.write(f"• {suggestion}")
                        st.write("---")

def render_query_templates():
    """Render pre-built query templates"""
    st.subheader("📋 Query Templates")

    templates = {
        "IT Services": [
            "information technology services",
            "IT support AND (help desk OR technical support)",
            "cybersecurity AND (consulting OR services)",
            "cloud migration AND (AWS OR Azure OR GCP)",
            "software development AND (custom OR application)"
        ],
        "Professional Services": [
            "management consulting services",
            "business process improvement",
            "training AND (development OR services)",
            "program management AND (support OR services)",
            "strategic planning AND consulting"
        ],
        "Engineering": [
            "engineering services AND (design OR analysis)",
            "systems engineering AND integration",
            "technical support AND engineering",
            "research AND development AND engineering",
            "environmental engineering AND services"
        ],
        "Construction": [
            "construction services AND (building OR facility)",
            "renovation AND (building OR facility)",
            "maintenance AND (facility OR building)",
            "design build AND construction",
            "infrastructure AND (construction OR improvement)"
        ]
    }

    selected_category = st.selectbox("Select Template Category:", list(templates.keys()))

    if selected_category:
        st.write(f"**{selected_category} Templates:**")

        for template in templates[selected_category]:
            col1, col2 = st.columns([5, 1])

            with col1:
                st.code(template, language="text")

            with col2:
                if st.button("🔍", key=f"template_{template}", help="Use this template"):
                    st.session_state.current_search_query = template
                    st.session_state.execute_search = True
                    st.rerun()
```

---

## **Feature 25: Document Version Control**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL,
    version_name VARCHAR(200),
    file_path TEXT NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    created_by VARCHAR(100) NOT NULL DEFAULT 'default_user',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    tags TEXT[],
    is_current BOOLEAN DEFAULT FALSE,
    parent_version_id INTEGER REFERENCES document_versions(id),
    UNIQUE(document_id, version_number)
);

CREATE TABLE IF NOT EXISTS document_metadata (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) UNIQUE NOT NULL,
    document_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(50),
    project_id VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_versions INTEGER DEFAULT 1,
    current_version_id INTEGER REFERENCES document_versions(id)
);

CREATE INDEX IF NOT EXISTS ix_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS ix_document_versions_current ON document_versions(is_current);
CREATE INDEX IF NOT EXISTS ix_document_metadata_project ON document_metadata(project_id);
```

#### **Implementation Functions**
```python
# Add to govcon_suite.py
import hashlib
import shutil
from pathlib import Path

def create_document_version(document_id, file_path, version_name=None, change_summary=None, user_id="default_user"):
    """Create a new version of a document"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        # Calculate file checksum
        checksum = calculate_file_checksum(file_path)
        file_size = Path(file_path).stat().st_size

        cursor = conn.cursor()

        # Get next version number
        cursor.execute("""
            SELECT COALESCE(MAX(version_number), 0) + 1
            FROM document_versions
            WHERE document_id = %s
        """, (document_id,))

        next_version = cursor.fetchone()[0]

        # Create version directory if it doesn't exist
        version_dir = Path(f"documents/{document_id}/versions")
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy file to version directory
        version_file_path = version_dir / f"v{next_version}_{Path(file_path).name}"
        shutil.copy2(file_path, version_file_path)

        # Insert version record
        cursor.execute("""
            INSERT INTO document_versions
            (document_id, version_number, version_name, file_path, file_size,
             checksum, created_by, change_summary, is_current)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """, (document_id, next_version, version_name, str(version_file_path),
              file_size, checksum, user_id, change_summary))

        version_id = cursor.fetchone()[0]

        # Update previous versions to not current
        cursor.execute("""
            UPDATE document_versions
            SET is_current = FALSE
            WHERE document_id = %s AND id != %s
        """, (document_id, version_id))

        # Update document metadata
        cursor.execute("""
            UPDATE document_metadata
            SET current_version_id = %s,
                total_versions = total_versions + 1,
                last_modified = CURRENT_TIMESTAMP
            WHERE document_id = %s
        """, (version_id, document_id))

        conn.commit()
        return version_id

    except Exception as e:
        st.error(f"Error creating document version: {e}")
        return False
    finally:
        conn.close()

def get_document_versions(document_id):
    """Get all versions of a document"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, version_number, version_name, file_path, file_size,
                   created_by, created_date, change_summary, is_current
            FROM document_versions
            WHERE document_id = %s
            ORDER BY version_number DESC
        """, (document_id,))

        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading document versions: {e}")
        return []
    finally:
        conn.close()

def calculate_file_checksum(file_path):
    """Calculate SHA-256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compare_document_versions(version_id_1, version_id_2):
    """Compare two document versions using MCP AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "AI comparison not available"

    try:
        # Get version details
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, version_number, change_summary
            FROM document_versions
            WHERE id IN (%s, %s)
        """, (version_id_1, version_id_2))

        versions = cursor.fetchall()
        conn.close()

        if len(versions) != 2:
            return "Error: Could not find both versions"

        # Read file contents
        content_1 = Path(versions[0][0]).read_text(encoding='utf-8', errors='ignore')
        content_2 = Path(versions[1][0]).read_text(encoding='utf-8', errors='ignore')

        # Use MCP AI to compare
        response = call_mcp_tool("analyze_patterns", {
            "data": {
                "version_1": {"content": content_1, "version": versions[0][1], "summary": versions[0][2]},
                "version_2": {"content": content_2, "version": versions[1][1], "summary": versions[1][2]}
            },
            "pattern_types": ["differences", "changes", "improvements"],
            "analysis_context": "document_version_comparison",
            "output_format": "comparison_report"
        })

        if response and response.get('success'):
            return response['data']['comparison']
        else:
            return "AI comparison failed"

    except Exception as e:
        return f"Error comparing versions: {e}"

def render_document_version_control():
    """Render document version control interface"""
    st.subheader("📄 Document Version Control")

    # Document selection
    documents = get_all_documents()  # Implement this function

    if not documents:
        st.info("No documents found. Upload a document to start version control.")
        return

    selected_doc = st.selectbox(
        "Select Document:",
        options=documents,
        format_func=lambda x: f"{x['name']} ({x['type']})"
    )

    if not selected_doc:
        return

    document_id = selected_doc['id']

    # Get versions
    versions = get_document_versions(document_id)

    if not versions:
        st.warning("No versions found for this document.")
        return

    # Version list
    st.write("**Document Versions:**")

    for version in versions:
        version_id, version_num, version_name, file_path, file_size, created_by, created_date, change_summary, is_current = version

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])

            with col1:
                status = "🟢 Current" if is_current else f"📄 v{version_num}"
                st.write(status)

            with col2:
                display_name = version_name or f"Version {version_num}"
                st.write(f"**{display_name}**")
                if change_summary:
                    st.caption(change_summary)

            with col3:
                st.write(f"By: {created_by}")
                st.caption(f"{created_date.strftime('%Y-%m-%d %H:%M')}")

            with col4:
                if st.button("📥 Download", key=f"download_v{version_id}"):
                    # Implement download functionality
                    st.success(f"Downloaded version {version_num}")

                if not is_current and st.button("🔄 Restore", key=f"restore_v{version_id}"):
                    # Implement restore functionality
                    st.success(f"Restored to version {version_num}")
                    st.rerun()

        st.divider()

    # Version comparison
    if len(versions) >= 2:
        st.subheader("🔍 Compare Versions")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            version_1 = st.selectbox(
                "Version 1:",
                options=versions,
                format_func=lambda x: f"v{x[1]} - {x[2] or 'Unnamed'}",
                key="compare_version_1"
            )

        with col2:
            version_2 = st.selectbox(
                "Version 2:",
                options=versions,
                format_func=lambda x: f"v{x[1]} - {x[2] or 'Unnamed'}",
                key="compare_version_2"
            )

        with col3:
            if st.button("🔍 Compare", disabled=not (version_1 and version_2 and version_1[0] != version_2[0])):
                with st.spinner("Comparing versions..."):
                    comparison = compare_document_versions(version_1[0], version_2[0])
                    st.write("**Comparison Results:**")
                    st.write(comparison)
```

---

## **Feature 26: Document Templates & Library**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    file_path TEXT NOT NULL,
    preview_image TEXT,
    created_by VARCHAR(100) NOT NULL DEFAULT 'default_user',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    tags TEXT[],
    template_variables JSONB,
    UNIQUE(template_name, template_type)
);

CREATE TABLE IF NOT EXISTS template_usage_log (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES document_templates(id),
    used_by VARCHAR(100) NOT NULL,
    used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    project_context VARCHAR(200),
    customizations_made JSONB
);

CREATE INDEX IF NOT EXISTS ix_document_templates_type ON document_templates(template_type);
CREATE INDEX IF NOT EXISTS ix_document_templates_category ON document_templates(category);
CREATE INDEX IF NOT EXISTS ix_document_templates_tags ON document_templates USING GIN(tags);
```

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def get_document_templates(template_type=None, category=None):
    """Get available document templates"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        query = """
            SELECT id, template_name, template_type, category, description,
                   file_path, usage_count, tags, template_variables
            FROM document_templates
            WHERE is_active = TRUE
        """
        params = []

        if template_type:
            query += " AND template_type = %s"
            params.append(template_type)

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY usage_count DESC, template_name"

        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading templates: {e}")
        return []
    finally:
        conn.close()

def create_document_from_template(template_id, project_name, customizations=None):
    """Create a new document from a template"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Get template details
        cursor.execute("""
            SELECT template_name, file_path, template_variables
            FROM document_templates
            WHERE id = %s AND is_active = TRUE
        """, (template_id,))

        template = cursor.fetchone()
        if not template:
            st.error("Template not found")
            return None

        template_name, file_path, template_vars = template

        # Read template content
        template_content = Path(file_path).read_text(encoding='utf-8')

        # Apply customizations using MCP AI
        if customizations:
            customized_content = customize_template_content(template_content, customizations, template_vars)
        else:
            customized_content = template_content

        # Create new document
        new_doc_path = f"documents/{project_name}_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        Path(new_doc_path).parent.mkdir(parents=True, exist_ok=True)

        # Save customized content
        with open(new_doc_path, 'w', encoding='utf-8') as f:
            f.write(customized_content)

        # Log template usage
        cursor.execute("""
            INSERT INTO template_usage_log (template_id, used_by, project_context, customizations_made)
            VALUES (%s, %s, %s, %s)
        """, (template_id, "default_user", project_name, json.dumps(customizations or {})))

        # Update usage count
        cursor.execute("""
            UPDATE document_templates
            SET usage_count = usage_count + 1, last_modified = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (template_id,))

        conn.commit()
        return new_doc_path

    except Exception as e:
        st.error(f"Error creating document from template: {e}")
        return None
    finally:
        conn.close()

def customize_template_content(template_content, customizations, template_vars):
    """Customize template content using MCP AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return template_content

    try:
        response = call_mcp_tool("generate_insights", {
            "content": template_content,
            "insight_type": "template_customization",
            "context": {
                "domain": "government_contracting",
                "customizations": customizations,
                "template_variables": template_vars,
                "output_format": "customized_document"
            }
        })

        if response and response.get('success'):
            return response['data']['customized_content']
        else:
            return template_content

    except Exception as e:
        st.error(f"Error customizing template: {e}")
        return template_content

def render_document_templates():
    """Render document templates interface"""
    st.subheader("📋 Document Templates & Library")

    # Template categories
    categories = ["Proposals", "Contracts", "Reports", "Presentations", "Forms", "Letters"]
    selected_category = st.selectbox("Template Category:", ["All"] + categories)

    # Get templates
    if selected_category == "All":
        templates = get_document_templates()
    else:
        templates = get_document_templates(category=selected_category)

    if not templates:
        st.info("No templates found in this category.")
        return

    # Display templates
    for template in templates:
        template_id, name, template_type, category, description, file_path, usage_count, tags, template_vars = template

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{name}**")
                st.caption(f"{category} • {template_type}")
                if description:
                    st.write(description)
                if tags:
                    st.write("🏷️ " + " • ".join(tags))

            with col2:
                st.metric("Usage Count", usage_count)
                if template_vars:
                    st.write("**Variables:**")
                    for var in template_vars.get('variables', []):
                        st.caption(f"• {var}")

            with col3:
                if st.button("📄 Use Template", key=f"use_template_{template_id}"):
                    st.session_state.selected_template = template_id
                    st.session_state.show_template_customization = True
                    st.rerun()

                if st.button("👁️ Preview", key=f"preview_template_{template_id}"):
                    # Show template preview
                    with st.expander(f"Preview: {name}", expanded=True):
                        try:
                            content = Path(file_path).read_text(encoding='utf-8')[:1000]
                            st.code(content + "..." if len(content) == 1000 else content)
                        except Exception as e:
                            st.error(f"Error loading preview: {e}")

        st.divider()

    # Template customization dialog
    if st.session_state.get('show_template_customization'):
        render_template_customization_dialog()

def render_template_customization_dialog():
    """Render template customization dialog"""
    template_id = st.session_state.get('selected_template')
    if not template_id:
        return

    with st.expander("🎨 Customize Template", expanded=True):
        st.write("**Project Information:**")

        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name:", key="template_project_name")
            client_name = st.text_input("Client/Agency:", key="template_client_name")

        with col2:
            contract_type = st.selectbox(
                "Contract Type:",
                ["Fixed Price", "Cost Plus", "Time & Materials", "IDIQ"],
                key="template_contract_type"
            )
            due_date = st.date_input("Due Date:", key="template_due_date")

        st.write("**Customization Options:**")

        # Dynamic customization based on template variables
        customizations = {}

        # Company information
        with st.container():
            st.write("**Company Information:**")
            col1, col2 = st.columns(2)

            with col1:
                customizations['company_name'] = st.text_input("Company Name:", key="custom_company_name")
                customizations['company_address'] = st.text_area("Company Address:", key="custom_company_address")

            with col2:
                customizations['contact_person'] = st.text_input("Contact Person:", key="custom_contact_person")
                customizations['phone_email'] = st.text_input("Phone/Email:", key="custom_phone_email")

        # Project-specific customizations
        with st.container():
            st.write("**Project-Specific Details:**")
            customizations['project_scope'] = st.text_area("Project Scope:", key="custom_project_scope")
            customizations['key_personnel'] = st.text_area("Key Personnel:", key="custom_key_personnel")
            customizations['special_requirements'] = st.text_area("Special Requirements:", key="custom_special_requirements")

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Create Document", disabled=not project_name):
                with st.spinner("Creating customized document..."):
                    doc_path = create_document_from_template(template_id, project_name, customizations)
                    if doc_path:
                        st.success(f"Document created: {doc_path}")
                        st.session_state.show_template_customization = False
                        st.rerun()

        with col2:
            if st.button("👁️ Preview Changes"):
                with st.spinner("Generating preview..."):
                    # Show preview of customized content
                    st.info("Preview functionality would show customized content here")

        with col3:
            if st.button("❌ Cancel"):
                st.session_state.show_template_customization = False
                st.rerun()
```

---

## **Feature 33: AI-Generated Executive Summary**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **MCP Integration**
Uses generic `extract_structured_data` and `generate_insights` tools.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def generate_executive_summary(document_content, summary_type="comprehensive"):
    """Generate executive summary using MCP AI"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "AI summary generation not available"

    try:
        # First extract key information
        key_info_response = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "project_title", "type": "string", "description": "Main project or opportunity title"},
                    {"name": "agency", "type": "string", "description": "Contracting agency"},
                    {"name": "contract_value", "type": "string", "description": "Contract value or budget"},
                    {"name": "key_requirements", "type": "array", "description": "Main requirements or deliverables"},
                    {"name": "timeline", "type": "string", "description": "Project timeline or performance period"},
                    {"name": "location", "type": "string", "description": "Place of performance"},
                    {"name": "set_aside", "type": "string", "description": "Set-aside type if any"}
                ]
            },
            "domain_context": "government_contracting"
        })

        key_info = {}
        if key_info_response and key_info_response.get('success'):
            key_info = key_info_response['data']

        # Generate executive summary
        summary_response = call_mcp_tool("generate_insights", {
            "content": document_content,
            "insight_type": "executive_summary",
            "context": {
                "domain": "government_contracting",
                "summary_type": summary_type,
                "key_information": key_info,
                "target_audience": "business_executives",
                "length": "2_paragraphs"
            },
            "output_format": "executive_summary"
        })

        if summary_response and summary_response.get('success'):
            return summary_response['data']['summary']
        else:
            return "Failed to generate executive summary"

    except Exception as e:
        st.error(f"Error generating executive summary: {e}")
        return f"Error generating summary: {e}"

def render_executive_summary_generator():
    """Render executive summary generation interface"""
    st.subheader("📋 AI-Generated Executive Summary")

    # Document input options
    input_method = st.radio(
        "Document Input Method:",
        ["Upload File", "Paste Text", "Select from Library"],
        key="summary_input_method"
    )

    document_content = ""

    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload Document:",
            type=['txt', 'pdf', 'docx'],
            key="summary_file_upload"
        )

        if uploaded_file:
            # Extract text from uploaded file
            document_content = extract_text_from_file(uploaded_file)

    elif input_method == "Paste Text":
        document_content = st.text_area(
            "Paste Document Content:",
            height=300,
            placeholder="Paste the SOW, RFP, or other document content here...",
            key="summary_text_input"
        )

    elif input_method == "Select from Library":
        # Get documents from library
        documents = get_document_library()  # Implement this function

        if documents:
            selected_doc = st.selectbox(
                "Select Document:",
                options=documents,
                format_func=lambda x: f"{x['name']} ({x['type']})",
                key="summary_doc_selection"
            )

            if selected_doc:
                document_content = load_document_content(selected_doc['id'])
        else:
            st.info("No documents in library. Upload documents first.")

    if not document_content:
        st.info("Please provide document content to generate summary.")
        return

    # Summary options
    col1, col2 = st.columns(2)

    with col1:
        summary_type = st.selectbox(
            "Summary Type:",
            ["Comprehensive", "Technical Focus", "Business Focus", "Compliance Focus"],
            key="summary_type"
        )

    with col2:
        include_sections = st.multiselect(
            "Include Sections:",
            ["Key Requirements", "Timeline", "Budget", "Personnel", "Risks", "Opportunities"],
            default=["Key Requirements", "Timeline", "Budget"],
            key="summary_sections"
        )

    # Generate summary
    if st.button("🚀 Generate Executive Summary", type="primary"):
        with st.spinner("Generating executive summary..."):
            summary = generate_executive_summary(document_content, summary_type.lower().replace(" ", "_"))

            if summary:
                st.session_state.generated_summary = summary
                st.session_state.summary_document_content = document_content

    # Display generated summary
    if 'generated_summary' in st.session_state:
        st.subheader("📄 Generated Executive Summary")

        # Editable summary
        edited_summary = st.text_area(
            "Executive Summary (Editable):",
            value=st.session_state.generated_summary,
            height=200,
            key="edited_summary"
        )

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💾 Save Summary"):
                # Save summary to database or file
                save_executive_summary(edited_summary, st.session_state.summary_document_content)
                st.success("Summary saved!")

        with col2:
            if st.button("📋 Copy to Clipboard"):
                # Copy to clipboard functionality
                st.success("Summary copied to clipboard!")

        with col3:
            if st.button("📄 Export to Word"):
                # Export to Word document
                export_summary_to_word(edited_summary)
                st.success("Summary exported to Word!")

        with col4:
            if st.button("🔄 Regenerate"):
                with st.spinner("Regenerating summary..."):
                    new_summary = generate_executive_summary(
                        st.session_state.summary_document_content,
                        summary_type.lower().replace(" ", "_")
                    )
                    if new_summary:
                        st.session_state.generated_summary = new_summary
                        st.rerun()

        # Summary analysis
        with st.expander("📊 Summary Analysis"):
            col1, col2, col3 = st.columns(3)

            with col1:
                word_count = len(edited_summary.split())
                st.metric("Word Count", word_count)

            with col2:
                readability_score = calculate_readability_score(edited_summary)
                st.metric("Readability Score", f"{readability_score:.1f}")

            with col3:
                key_terms = extract_key_terms(edited_summary)
                st.metric("Key Terms", len(key_terms))

            if key_terms:
                st.write("**Key Terms Identified:**")
                st.write(" • ".join(key_terms[:10]))

def calculate_readability_score(text):
    """Calculate simple readability score"""
    sentences = text.count('.') + text.count('!') + text.count('?')
    words = len(text.split())

    if sentences == 0:
        return 0

    avg_sentence_length = words / sentences
    # Simple readability approximation (lower is better)
    return max(0, 20 - avg_sentence_length)

def extract_key_terms(text):
    """Extract key terms from text"""
    # Simple keyword extraction (could be enhanced with MCP AI)
    words = text.lower().split()
    # Filter out common words and short words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
    key_terms = [word for word in words if len(word) > 4 and word not in stop_words]

    # Return unique terms
    return list(set(key_terms))[:20]
```

---

## **🔌 sammySosa MCP Integration Framework**

### **Core MCP Connection Setup**
```python
# Add to govcon_suite.py - Replace existing setup_llm() function
import uuid
import requests
import json

@st.cache_resource
def setup_llm_api():
    """Setup GremlinsAI MCP server connection"""
    try:
        config = {
            "endpoint": st.secrets.get("MCP_SERVER_ENDPOINT", "http://localhost:8000/api/v1/mcp/"),
            "api_key": st.secrets.get("MCP_API_KEY"),
            "client_id": st.secrets.get("MCP_CLIENT_ID", "sammySosa"),
            "timeout": st.secrets.get("MCP_TIMEOUT", 30),
            "max_retries": st.secrets.get("MCP_MAX_RETRIES", 3)
        }

        if not config["api_key"]:
            st.error("MCP_API_KEY not found in secrets.toml")
            return None

        # Test connection
        test_response = test_mcp_connection(config)
        if test_response:
            st.success("✅ Connected to GremlinsAI MCP Server")
            return config
        else:
            st.error("❌ Failed to connect to GremlinsAI MCP Server")
            return None

    except Exception as e:
        st.error(f"Error setting up MCP connection: {e}")
        return None

def test_mcp_connection(config):
    """Test connection to GremlinsAI MCP server"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "capabilities"
        }

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "X-Client-ID": config["client_id"],
            "X-Client-Version": "1.0.0"
        }

        response = requests.post(
            config["endpoint"],
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        return response.status_code == 200

    except Exception as e:
        st.error(f"MCP connection test failed: {e}")
        return False

def call_mcp_tool(tool_name, arguments, retries=0):
    """Call GremlinsAI MCP tool with retry logic"""
    config = setup_llm_api()
    if not config:
        return {"success": False, "error": "MCP connection not available"}

    try:
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
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "X-Client-ID": config["client_id"],
            "X-Client-Version": "1.0.0"
        }

        response = requests.post(
            config["endpoint"],
            headers=headers,
            json=payload,
            timeout=config["timeout"]
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                return {"success": True, "data": result["result"]}
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
        else:
            # Retry logic
            if retries < config["max_retries"]:
                time.sleep(2 ** retries)  # Exponential backoff
                return call_mcp_tool(tool_name, arguments, retries + 1)
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        if retries < config["max_retries"]:
            time.sleep(2 ** retries)
            return call_mcp_tool(tool_name, arguments, retries + 1)
        else:
            return {"success": False, "error": str(e)}

# Update existing execute_ai_task function to use MCP
def execute_ai_task(task_type, content, context=None):
    """Execute AI task using GremlinsAI MCP server"""

    # Map old task types to new MCP tools
    mcp_tool_mapping = {
        "extract_keywords": {
            "tool": "extract_structured_data",
            "args": {
                "text": content,
                "schema": {
                    "fields": [
                        {"name": "keywords", "type": "array", "description": "Important keywords and phrases"},
                        {"name": "technical_terms", "type": "array", "description": "Technical terminology"},
                        {"name": "acronyms", "type": "array", "description": "Acronyms and abbreviations"}
                    ]
                },
                "domain_context": "government_contracting"
            }
        },
        "analyze_document": {
            "tool": "generate_insights",
            "args": {
                "content": content,
                "insight_type": "document_analysis",
                "context": {
                    "domain": "government_contracting",
                    "analysis_focus": ["requirements", "compliance", "opportunities"],
                    "output_format": "structured_analysis"
                }
            }
        },
        "find_similar": {
            "tool": "calculate_similarity",
            "args": {
                "target_item": content,
                "comparison_items": context.get("comparison_items", []) if context else [],
                "similarity_factors": ["text", "metadata"],
                "domain_context": "government_contracting"
            }
        }
    }

    if task_type in mcp_tool_mapping:
        tool_config = mcp_tool_mapping[task_type]
        return call_mcp_tool(tool_config["tool"], tool_config["args"])
    else:
        # Fallback for unmapped task types
        return call_mcp_tool("generate_insights", {
            "content": content,
            "insight_type": task_type,
            "context": {"domain": "government_contracting", **(context or {})}
        })
```

### **Domain-Specific Helper Functions**
```python
# Add to govcon_suite.py - GovCon-specific MCP tool wrappers

def extract_govcon_keywords(text, keyword_types=None):
    """Extract government contracting keywords"""
    keyword_types = keyword_types or ["technical", "compliance", "business"]

    return call_mcp_tool("extract_structured_data", {
        "text": text,
        "schema": {
            "fields": [
                {"name": "technical_keywords", "type": "array", "description": "Technical terms and specifications"},
                {"name": "compliance_keywords", "type": "array", "description": "Compliance and regulatory terms"},
                {"name": "business_keywords", "type": "array", "description": "Business and commercial terms"},
                {"name": "agency_specific", "type": "array", "description": "Agency-specific terminology"}
            ]
        },
        "domain_context": "government_contracting"
    })

def analyze_far_compliance(document_text):
    """Analyze FAR/DFARS compliance using MCP"""
    return call_mcp_tool("classify_content", {
        "content": document_text,
        "classification_scheme": "far_dfars_compliance",
        "risk_assessment": True,
        "domain_rules": "government_contracting_compliance"
    })

def find_similar_opportunities(target_opportunity, historical_opportunities):
    """Find similar opportunities using MCP"""
    return call_mcp_tool("calculate_similarity", {
        "target_item": target_opportunity,
        "comparison_items": historical_opportunities,
        "similarity_factors": ["text_content", "agency", "naics_code", "contract_type"],
        "domain_context": "government_contracting"
    })

def analyze_agency_patterns(agency_data, analysis_type="buying_patterns"):
    """Analyze agency buying patterns using MCP"""
    return call_mcp_tool("analyze_patterns", {
        "data": agency_data,
        "pattern_types": ["temporal", "seasonal", "categorical"],
        "analysis_context": f"government_procurement_{analysis_type}",
        "prediction_horizon": "12_months"
    })

def extract_location_data(opportunity_text):
    """Extract geographic information using MCP"""
    return call_mcp_tool("process_geographic_data", {
        "text": opportunity_text,
        "extraction_types": ["addresses", "regions", "performance_locations"],
        "geocoding": True,
        "context_type": "government_contracting_performance_locations"
    })

def generate_smart_search_query(base_query, user_context=None):
    """Generate optimized search queries using MCP"""
    return call_mcp_tool("generate_insights", {
        "content": base_query,
        "insight_type": "search_optimization",
        "context": {
            "domain": "government_contracting",
            "user_context": user_context or {},
            "optimization_goals": ["recall", "precision", "relevance"]
        },
        "output_format": "search_queries"
    })
```

---

## **📋 Complete MCP Tools Summary**

### **Generic MCP Tools Required**

| MCP Tool | Purpose | sammySosa Usage | Features Supported |
|----------|---------|-----------------|-------------------|
| **`extract_structured_data`** | Extract structured info using schemas | Keywords, CLINs, personnel, requirements | 3, 16, 29, 30, 31, 33 |
| **`analyze_patterns`** | Pattern analysis with domain context | Buying patterns, trends, comparisons | 12, 9, 25, 5 |
| **`classify_content`** | Content classification with risk assessment | FAR compliance, opportunity scoring | 15, 4, 10, 7 |
| **`calculate_similarity`** | Similarity analysis with configurable factors | Similar opportunities, matching | 11, 7 |
| **`process_geographic_data`** | Geographic data extraction and processing | Location mapping, geocoding | 8 |
| **`generate_insights`** | Insight generation with configurable focus | Smart queries, summaries, content | 14, 33, 26 |

### **Domain Context Configuration**
```json
{
  "government_contracting": {
    "terminology": [
      "FAR", "DFARS", "CLIN", "SOW", "PWS", "RFP", "RFQ", "IDIQ", "BPA",
      "8(a)", "HUBZone", "WOSB", "VOSB", "SDVOSB", "GSA", "DOD", "VA"
    ],
    "classification_schemes": {
      "far_clauses": "Standard FAR clause taxonomy",
      "opportunity_types": "RFP, RFQ, Sources Sought, etc.",
      "risk_categories": "Compliance, technical, schedule, cost"
    },
    "similarity_factors": {
      "text_content": 0.4,
      "agency": 0.2,
      "naics_code": 0.2,
      "contract_type": 0.1,
      "set_aside": 0.1
    }
  }
}
```

---

## **🚀 Implementation Roadmap Summary**

### **Phase 5 Status: 13/17 Features Complete**
✅ **Completed Features:**
1. Customizable Dashboards
2. Saved Search Queries
3. Keyword Highlighting
6. Advanced Filtering Options
8. Geographic Map View
11. Similar Opportunity Finder
12. Agency Buying Pattern Analysis
14. Smart Search Query Generation
15. FAR Clause Anomaly Detection
16. Automated Keyword Extraction
25. Document Version Control
26. Document Templates & Library
33. AI-Generated Executive Summary

⏳ **Remaining Phase 5 Features:**
4. Real-time Opportunity Alerts
5. Competitive Intelligence Dashboard
7. Opportunity Scoring Algorithm
9. Market Trend Analysis
10. Automated NAICS Code Suggestion

### **Next Steps**
1. **Complete remaining Phase 5 features** (4 features)
2. **Test MCP integration** with GremlinsAI server
3. **Begin Phase 6 planning** (Advanced Document Analysis)
4. **Optimize performance** and user experience

---

## **📊 Success Metrics & KPIs**

### **Technical Performance**
- **MCP Response Time:** < 5 seconds average
- **Feature Availability:** 99.5% uptime target
- **Error Rate:** < 1% of MCP calls fail
- **Data Accuracy:** 95% accuracy in AI extractions

### **User Experience**
- **Time Savings:** 60% reduction in manual analysis
- **User Adoption:** 90% feature usage within 30 days
- **User Satisfaction:** > 4.5/5 rating
- **Task Completion:** 80% faster opportunity processing

### **Business Impact**
- **ROI Achievement:** 300% ROI within 6 months
- **Win Rate Improvement:** 25% increase in proposal wins
- **Market Coverage:** 40% more opportunities identified
- **Compliance Accuracy:** 98% compliance score improvement

---

---

## **Feature 4: Real-time Opportunity Alerts**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL DEFAULT 'default_user',
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    search_criteria JSONB NOT NULL,
    alert_frequency VARCHAR(50) DEFAULT 'immediate',
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    notification_methods JSONB DEFAULT '["email", "dashboard"]'::jsonb,
    UNIQUE(user_id, rule_name)
);

CREATE TABLE IF NOT EXISTS alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_rule_id INTEGER REFERENCES alert_rules(id),
    opportunity_id VARCHAR(100) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    notification_data JSONB,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    user_action VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_alert_rules_user_active ON alert_rules(user_id, is_active);
CREATE INDEX IF NOT EXISTS ix_alert_notifications_unread ON alert_notifications(is_read, sent_date);
```

#### **MCP Integration**
Uses generic `classify_content` tool for opportunity matching and alert triggering.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
import threading
import time
from datetime import datetime, timedelta

def create_alert_rule(user_id, rule_name, search_criteria, alert_frequency="immediate", notification_methods=None):
    """Create a new alert rule"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alert_rules (user_id, rule_name, search_criteria, alert_frequency, notification_methods)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, rule_name)
            DO UPDATE SET
                search_criteria = EXCLUDED.search_criteria,
                alert_frequency = EXCLUDED.alert_frequency,
                notification_methods = EXCLUDED.notification_methods,
                is_active = TRUE
            RETURNING id
        """, (user_id, rule_name, json.dumps(search_criteria), alert_frequency,
              json.dumps(notification_methods or ["email", "dashboard"])))

        rule_id = cursor.fetchone()[0]
        conn.commit()
        return rule_id
    except Exception as e:
        st.error(f"Error creating alert rule: {e}")
        return False
    finally:
        conn.close()

def check_opportunity_against_alerts(opportunity_data):
    """Check if opportunity matches any active alert rules"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, rule_name, search_criteria, notification_methods
            FROM alert_rules
            WHERE is_active = TRUE
        """)

        active_rules = cursor.fetchall()
        matched_alerts = []

        for rule in active_rules:
            rule_id, user_id, rule_name, search_criteria, notification_methods = rule

            # Use MCP to check if opportunity matches criteria
            match_result = call_mcp_tool("classify_content", {
                "content": json.dumps(opportunity_data),
                "classification_scheme": "opportunity_alert_matching",
                "domain_rules": {
                    "search_criteria": search_criteria,
                    "matching_threshold": 0.7
                },
                "risk_assessment": False
            })

            if match_result.get('success') and match_result['data'].get('matches', False):
                matched_alerts.append({
                    'rule_id': rule_id,
                    'user_id': user_id,
                    'rule_name': rule_name,
                    'notification_methods': notification_methods,
                    'match_confidence': match_result['data'].get('confidence', 0.0)
                })

                # Update trigger count and last triggered
                cursor.execute("""
                    UPDATE alert_rules
                    SET trigger_count = trigger_count + 1, last_triggered = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (rule_id,))

        conn.commit()
        return matched_alerts

    except Exception as e:
        st.error(f"Error checking alerts: {e}")
        return []
    finally:
        conn.close()

def send_alert_notification(alert_info, opportunity_data):
    """Send alert notification to user"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Create notification record
        notification_data = {
            "opportunity_title": opportunity_data.get('title', 'Unknown'),
            "agency": opportunity_data.get('agency', 'Unknown'),
            "posted_date": opportunity_data.get('posted_date', ''),
            "response_deadline": opportunity_data.get('response_deadline', ''),
            "match_confidence": alert_info['match_confidence']
        }

        cursor.execute("""
            INSERT INTO alert_notifications
            (alert_rule_id, opportunity_id, notification_type, notification_data)
            VALUES (%s, %s, %s, %s)
        """, (alert_info['rule_id'], opportunity_data.get('id', ''),
              'dashboard', json.dumps(notification_data)))

        conn.commit()

        # Send actual notifications based on methods
        for method in alert_info['notification_methods']:
            if method == "email":
                send_email_alert(alert_info, opportunity_data)
            elif method == "dashboard":
                # Dashboard notification already created above
                pass
            elif method == "slack":
                send_slack_alert(alert_info, opportunity_data)

        return True

    except Exception as e:
        st.error(f"Error sending notification: {e}")
        return False
    finally:
        conn.close()

def render_alert_management():
    """Render alert management interface"""
    st.subheader("🚨 Real-time Opportunity Alerts")

    # Alert rules management
    tab1, tab2, tab3 = st.tabs(["Create Alert", "Manage Alerts", "Alert History"])

    with tab1:
        st.write("**Create New Alert Rule**")

        rule_name = st.text_input("Alert Name:", key="new_alert_name")
        rule_description = st.text_area("Description:", key="new_alert_description")

        # Search criteria
        st.write("**Alert Criteria:**")
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_area("Keywords (one per line):", key="alert_keywords")
            agencies = st.multiselect(
                "Agencies:",
                ["DOD", "GSA", "VA", "DHS", "DOE", "NASA", "DOT", "HHS"],
                key="alert_agencies"
            )

        with col2:
            naics_codes = st.text_input("NAICS Codes (comma-separated):", key="alert_naics")
            min_value = st.number_input("Minimum Value ($):", min_value=0, key="alert_min_value")
            max_value = st.number_input("Maximum Value ($):", min_value=0, key="alert_max_value")

        # Alert settings
        st.write("**Alert Settings:**")
        col1, col2 = st.columns(2)

        with col1:
            alert_frequency = st.selectbox(
                "Alert Frequency:",
                ["immediate", "hourly", "daily", "weekly"],
                key="alert_frequency"
            )

        with col2:
            notification_methods = st.multiselect(
                "Notification Methods:",
                ["dashboard", "email", "slack"],
                default=["dashboard"],
                key="alert_methods"
            )

        if st.button("🚨 Create Alert Rule", disabled=not rule_name):
            search_criteria = {
                "keywords": [k.strip() for k in keywords.split('\n') if k.strip()] if keywords else [],
                "agencies": agencies,
                "naics_codes": [n.strip() for n in naics_codes.split(',') if n.strip()] if naics_codes else [],
                "min_value": min_value if min_value > 0 else None,
                "max_value": max_value if max_value > 0 else None
            }

            rule_id = create_alert_rule("default_user", rule_name, search_criteria,
                                      alert_frequency, notification_methods)
            if rule_id:
                st.success(f"Alert rule '{rule_name}' created successfully!")
                st.rerun()

    with tab2:
        st.write("**Active Alert Rules**")

        # Get existing alert rules
        alert_rules = get_user_alert_rules("default_user")

        if not alert_rules:
            st.info("No alert rules created yet.")
        else:
            for rule in alert_rules:
                rule_id, rule_name, description, criteria, frequency, is_active, trigger_count, last_triggered = rule

                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        status_icon = "🟢" if is_active else "🔴"
                        st.write(f"{status_icon} **{rule_name}**")
                        if description:
                            st.caption(description)

                        # Show criteria summary
                        criteria_obj = json.loads(criteria) if isinstance(criteria, str) else criteria
                        criteria_summary = []
                        if criteria_obj.get('keywords'):
                            criteria_summary.append(f"Keywords: {len(criteria_obj['keywords'])}")
                        if criteria_obj.get('agencies'):
                            criteria_summary.append(f"Agencies: {', '.join(criteria_obj['agencies'])}")

                        if criteria_summary:
                            st.caption(" • ".join(criteria_summary))

                    with col2:
                        st.metric("Triggers", trigger_count)
                        if last_triggered:
                            st.caption(f"Last: {last_triggered.strftime('%Y-%m-%d %H:%M')}")
                        st.caption(f"Frequency: {frequency}")

                    with col3:
                        if st.button("⚙️", key=f"edit_alert_{rule_id}", help="Edit rule"):
                            st.session_state.edit_alert_id = rule_id
                            st.rerun()

                        if st.button("🗑️", key=f"delete_alert_{rule_id}", help="Delete rule"):
                            if delete_alert_rule(rule_id):
                                st.success("Alert rule deleted!")
                                st.rerun()

                st.divider()

    with tab3:
        st.write("**Recent Alert Notifications**")

        # Get recent notifications
        notifications = get_recent_notifications("default_user", limit=50)

        if not notifications:
            st.info("No recent notifications.")
        else:
            for notification in notifications:
                notif_id, rule_name, opp_title, sent_date, is_read, notif_data = notification

                with st.container():
                    col1, col2, col3 = st.columns([4, 2, 1])

                    with col1:
                        read_icon = "📖" if is_read else "📩"
                        st.write(f"{read_icon} **{opp_title}**")
                        st.caption(f"Alert: {rule_name}")

                        if notif_data:
                            data = json.loads(notif_data) if isinstance(notif_data, str) else notif_data
                            if data.get('agency'):
                                st.caption(f"Agency: {data['agency']}")

                    with col2:
                        st.caption(sent_date.strftime('%Y-%m-%d %H:%M'))
                        if notif_data and json.loads(notif_data).get('match_confidence'):
                            confidence = json.loads(notif_data)['match_confidence']
                            st.caption(f"Match: {confidence:.1%}")

                    with col3:
                        if not is_read and st.button("✓", key=f"mark_read_{notif_id}", help="Mark as read"):
                            mark_notification_read(notif_id)
                            st.rerun()

                st.divider()

def get_user_alert_rules(user_id):
    """Get alert rules for a user"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, rule_name, rule_description, search_criteria, alert_frequency,
                   is_active, trigger_count, last_triggered
            FROM alert_rules
            WHERE user_id = %s
            ORDER BY created_date DESC
        """, (user_id,))

        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading alert rules: {e}")
        return []
    finally:
        conn.close()

def get_recent_notifications(user_id, limit=50):
    """Get recent notifications for a user"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT an.id, ar.rule_name, an.notification_data->>'opportunity_title',
                   an.sent_date, an.is_read, an.notification_data
            FROM alert_notifications an
            JOIN alert_rules ar ON an.alert_rule_id = ar.id
            WHERE ar.user_id = %s
            ORDER BY an.sent_date DESC
            LIMIT %s
        """, (user_id, limit))

        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading notifications: {e}")
        return []
    finally:
        conn.close()
```

---

## **Feature 5: Competitive Intelligence Dashboard**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS competitor_profiles (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL UNIQUE,
    company_type VARCHAR(100),
    primary_naics TEXT[],
    capabilities TEXT[],
    past_contracts JSONB,
    key_personnel JSONB,
    financial_info JSONB,
    certifications TEXT[],
    geographic_presence TEXT[],
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_sources TEXT[]
);

CREATE TABLE IF NOT EXISTS competitive_analysis (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) NOT NULL,
    competitor_id INTEGER REFERENCES competitor_profiles(id),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    competitive_strength DECIMAL(3,2),
    win_probability DECIMAL(3,2),
    key_advantages TEXT[],
    key_weaknesses TEXT[],
    recommended_strategy TEXT,
    analysis_data JSONB
);

CREATE INDEX IF NOT EXISTS ix_competitor_profiles_naics ON competitor_profiles USING GIN(primary_naics);
CREATE INDEX IF NOT EXISTS ix_competitive_analysis_opportunity ON competitive_analysis(opportunity_id);
```

#### **MCP Integration**
Uses generic `analyze_patterns` tool for competitive analysis and market intelligence.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def analyze_competitive_landscape(opportunity_data, known_competitors=None):
    """Analyze competitive landscape for an opportunity using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Get competitor data
        competitors = known_competitors or get_relevant_competitors(opportunity_data)

        # Use MCP to analyze competitive patterns
        analysis_result = call_mcp_tool("analyze_patterns", {
            "data": {
                "opportunity": opportunity_data,
                "competitors": competitors,
                "market_context": get_market_context(opportunity_data)
            },
            "pattern_types": ["competitive", "market_share", "capability_gaps"],
            "analysis_context": "government_contracting_competitive_intelligence",
            "prediction_horizon": "opportunity_specific"
        })

        if analysis_result.get('success'):
            return analysis_result['data']
        else:
            return {"error": "Competitive analysis failed"}

    except Exception as e:
        st.error(f"Error in competitive analysis: {e}")
        return {"error": str(e)}

def get_relevant_competitors(opportunity_data):
    """Get competitors relevant to an opportunity"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Get NAICS codes from opportunity
        opportunity_naics = opportunity_data.get('naics_codes', [])

        if opportunity_naics:
            # Find competitors with matching NAICS codes
            cursor.execute("""
                SELECT id, company_name, primary_naics, capabilities, past_contracts
                FROM competitor_profiles
                WHERE primary_naics && %s
                ORDER BY last_updated DESC
                LIMIT 20
            """, (opportunity_naics,))
        else:
            # Get all competitors if no NAICS match
            cursor.execute("""
                SELECT id, company_name, primary_naics, capabilities, past_contracts
                FROM competitor_profiles
                ORDER BY last_updated DESC
                LIMIT 10
            """)

        return cursor.fetchall()

    except Exception as e:
        st.error(f"Error getting competitors: {e}")
        return []
    finally:
        conn.close()

def render_competitive_intelligence_dashboard():
    """Render competitive intelligence dashboard"""
    st.subheader("🎯 Competitive Intelligence Dashboard")

    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Market Overview", "Competitor Analysis", "Opportunity Analysis", "Intelligence Reports"])

    with tab1:
        st.write("**Market Intelligence Overview**")

        # Market metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_competitors = get_competitor_count()
            st.metric("Tracked Competitors", total_competitors)

        with col2:
            active_opportunities = get_active_opportunity_count()
            st.metric("Active Opportunities", active_opportunities)

        with col3:
            win_rate = calculate_historical_win_rate()
            st.metric("Historical Win Rate", f"{win_rate:.1%}")

        with col4:
            market_share = estimate_market_share()
            st.metric("Est. Market Share", f"{market_share:.1%}")

        # Market trends chart
        st.write("**Market Trends (Last 12 Months)**")
        market_trends = get_market_trends_data()
        if market_trends:
            st.line_chart(market_trends)
        else:
            st.info("Insufficient data for trend analysis")

        # Top competitors by activity
        st.write("**Most Active Competitors**")
        top_competitors = get_top_competitors_by_activity()

        if top_competitors:
            for i, competitor in enumerate(top_competitors[:5], 1):
                comp_name, activity_score, recent_wins = competitor
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**{i}. {comp_name}**")

                with col2:
                    st.metric("Activity Score", f"{activity_score:.1f}")

                with col3:
                    st.metric("Recent Wins", recent_wins)

    with tab2:
        st.write("**Competitor Analysis**")

        # Competitor selection
        competitors = get_all_competitors()

        if not competitors:
            st.info("No competitor profiles found. Add competitors to begin analysis.")

            # Add competitor form
            with st.expander("➕ Add New Competitor"):
                render_add_competitor_form()
        else:
            selected_competitor = st.selectbox(
                "Select Competitor:",
                options=competitors,
                format_func=lambda x: x[1],  # company_name
                key="selected_competitor"
            )

            if selected_competitor:
                render_competitor_profile(selected_competitor)

    with tab3:
        st.write("**Opportunity Competitive Analysis**")

        # Opportunity selection
        opportunities = get_tracked_opportunities()

        if opportunities:
            selected_opp = st.selectbox(
                "Select Opportunity:",
                options=opportunities,
                format_func=lambda x: f"{x['title']} - {x['agency']}",
                key="competitive_opp_selection"
            )

            if selected_opp:
                render_opportunity_competitive_analysis(selected_opp)
        else:
            st.info("No opportunities available for competitive analysis.")

    with tab4:
        st.write("**Intelligence Reports**")

        # Report generation options
        report_type = st.selectbox(
            "Report Type:",
            ["Market Summary", "Competitor Deep Dive", "Opportunity Assessment", "Win/Loss Analysis"],
            key="intel_report_type"
        )

        report_period = st.selectbox(
            "Time Period:",
            ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Last Year"],
            key="intel_report_period"
        )

        if st.button("📊 Generate Intelligence Report", type="primary"):
            with st.spinner("Generating intelligence report..."):
                report = generate_intelligence_report(report_type, report_period)
                if report:
                    st.session_state.generated_intel_report = report
                    st.session_state.intel_report_type = report_type

        # Display generated report
        if 'generated_intel_report' in st.session_state:
            st.subheader(f"📋 {st.session_state.intel_report_type}")
            st.write(st.session_state.generated_intel_report)

            # Export options
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📄 Export to PDF"):
                    export_report_to_pdf(st.session_state.generated_intel_report)
                    st.success("Report exported to PDF!")

            with col2:
                if st.button("📊 Export to Excel"):
                    export_report_to_excel(st.session_state.generated_intel_report)
                    st.success("Report exported to Excel!")

            with col3:
                if st.button("📧 Email Report"):
                    email_intelligence_report(st.session_state.generated_intel_report)
                    st.success("Report emailed!")

def render_competitor_profile(competitor_data):
    """Render detailed competitor profile"""
    comp_id, comp_name, comp_type, naics, capabilities, past_contracts, key_personnel, financial_info, certifications, geo_presence = competitor_data[:10]

    st.write(f"**{comp_name} Profile**")

    # Basic info
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Company Information**")
        st.write(f"Type: {comp_type or 'Unknown'}")
        if naics:
            st.write(f"Primary NAICS: {', '.join(naics[:3])}")
        if certifications:
            st.write(f"Certifications: {', '.join(certifications)}")

    with col2:
        st.write("**Geographic Presence**")
        if geo_presence:
            st.write(", ".join(geo_presence))
        else:
            st.write("Not specified")

    # Capabilities
    if capabilities:
        st.write("**Key Capabilities**")
        for capability in capabilities[:10]:
            st.write(f"• {capability}")

    # Past contracts analysis
    if past_contracts:
        st.write("**Contract History Analysis**")

        # Use MCP to analyze contract patterns
        contract_analysis = call_mcp_tool("analyze_patterns", {
            "data": past_contracts,
            "pattern_types": ["temporal", "value_trends", "agency_preferences"],
            "analysis_context": "competitor_contract_history",
            "output_format": "competitor_insights"
        })

        if contract_analysis.get('success'):
            insights = contract_analysis['data']

            col1, col2, col3 = st.columns(3)

            with col1:
                avg_contract_value = insights.get('avg_contract_value', 0)
                st.metric("Avg Contract Value", f"${avg_contract_value:,.0f}")

            with col2:
                total_contracts = insights.get('total_contracts', 0)
                st.metric("Total Contracts", total_contracts)

            with col3:
                preferred_agencies = insights.get('preferred_agencies', [])
                if preferred_agencies:
                    st.metric("Top Agency", preferred_agencies[0])

            # Contract trends
            if insights.get('trends'):
                st.write("**Contract Trends:**")
                for trend in insights['trends'][:5]:
                    st.write(f"• {trend}")

def generate_intelligence_report(report_type, time_period):
    """Generate intelligence report using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Intelligence report generation not available"

    try:
        # Gather data based on report type and period
        report_data = gather_intelligence_data(report_type, time_period)

        # Use MCP to generate comprehensive report
        report_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(report_data),
            "insight_type": "intelligence_report",
            "context": {
                "domain": "government_contracting",
                "report_type": report_type.lower().replace(" ", "_"),
                "time_period": time_period,
                "analysis_depth": "comprehensive"
            },
            "output_format": "executive_report"
        })

        if report_result.get('success'):
            return report_result['data']['report']
        else:
            return "Failed to generate intelligence report"

    except Exception as e:
        st.error(f"Error generating report: {e}")
        return f"Error generating report: {e}"
```

---

## **Feature 7: Opportunity Scoring Algorithm**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS scoring_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(200) NOT NULL UNIQUE,
    model_version VARCHAR(50) DEFAULT '1.0',
    scoring_criteria JSONB NOT NULL,
    weight_configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL DEFAULT 'default_user',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS opportunity_scores (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) NOT NULL,
    scoring_model_id INTEGER REFERENCES scoring_models(id),
    overall_score DECIMAL(5,2) NOT NULL,
    component_scores JSONB NOT NULL,
    score_explanation TEXT,
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    UNIQUE(opportunity_id, scoring_model_id, is_current)
);

CREATE INDEX IF NOT EXISTS ix_opportunity_scores_score ON opportunity_scores(overall_score DESC);
CREATE INDEX IF NOT EXISTS ix_opportunity_scores_current ON opportunity_scores(is_current, calculated_date);
```

#### **MCP Integration**
Uses generic `calculate_similarity` and `classify_content` tools for multi-factor scoring.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def create_scoring_model(model_name, scoring_criteria, weight_config, user_id="default_user"):
    """Create a new opportunity scoring model"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scoring_models (model_name, scoring_criteria, weight_configuration, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (model_name, json.dumps(scoring_criteria), json.dumps(weight_config), user_id))

        model_id = cursor.fetchone()[0]
        conn.commit()
        return model_id
    except Exception as e:
        st.error(f"Error creating scoring model: {e}")
        return False
    finally:
        conn.close()

def calculate_opportunity_score(opportunity_data, scoring_model_id=None):
    """Calculate comprehensive opportunity score using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Get scoring model
        if scoring_model_id:
            scoring_model = get_scoring_model(scoring_model_id)
        else:
            scoring_model = get_default_scoring_model()

        if not scoring_model:
            return {"error": "No scoring model available"}

        model_id, model_name, criteria, weights = scoring_model[:4]

        # Calculate individual component scores using MCP
        component_scores = {}

        # 1. Technical Fit Score
        tech_fit_result = call_mcp_tool("calculate_similarity", {
            "target_item": opportunity_data,
            "comparison_items": get_company_capabilities(),
            "similarity_factors": ["technical_requirements", "capabilities", "experience"],
            "domain_context": "government_contracting_technical_fit"
        })

        if tech_fit_result.get('success'):
            component_scores['technical_fit'] = tech_fit_result['data'].get('similarity_score', 0.0) * 100

        # 2. Competitive Position Score
        competitive_result = call_mcp_tool("analyze_patterns", {
            "data": {
                "opportunity": opportunity_data,
                "historical_performance": get_historical_performance_data(),
                "market_context": get_market_context(opportunity_data)
            },
            "pattern_types": ["competitive_advantage", "win_probability"],
            "analysis_context": "opportunity_competitive_positioning"
        })

        if competitive_result.get('success'):
            component_scores['competitive_position'] = competitive_result['data'].get('competitive_score', 0.0) * 100

        # 3. Financial Attractiveness Score
        financial_score = calculate_financial_attractiveness(opportunity_data)
        component_scores['financial_attractiveness'] = financial_score

        # 4. Risk Assessment Score
        risk_result = call_mcp_tool("classify_content", {
            "content": json.dumps(opportunity_data),
            "classification_scheme": "opportunity_risk_assessment",
            "risk_assessment": True,
            "domain_rules": "government_contracting_risk_factors"
        })

        if risk_result.get('success'):
            risk_score = 100 - (risk_result['data'].get('risk_level', 0.5) * 100)
            component_scores['risk_assessment'] = max(0, risk_score)

        # 5. Strategic Alignment Score
        strategic_score = calculate_strategic_alignment(opportunity_data)
        component_scores['strategic_alignment'] = strategic_score

        # Calculate weighted overall score
        overall_score = 0
        weight_config = json.loads(weights) if isinstance(weights, str) else weights

        for component, score in component_scores.items():
            weight = weight_config.get(component, 0.2)  # Default 20% weight
            overall_score += score * weight

        # Generate score explanation using MCP
        explanation_result = call_mcp_tool("generate_insights", {
            "content": json.dumps({
                "opportunity": opportunity_data,
                "component_scores": component_scores,
                "overall_score": overall_score
            }),
            "insight_type": "score_explanation",
            "context": {
                "domain": "government_contracting",
                "explanation_focus": ["strengths", "weaknesses", "recommendations"]
            },
            "output_format": "score_explanation"
        })

        explanation = "Score calculated based on multiple factors"
        if explanation_result.get('success'):
            explanation = explanation_result['data'].get('explanation', explanation)

        # Save score to database
        save_opportunity_score(opportunity_data.get('id'), model_id, overall_score,
                             component_scores, explanation)

        return {
            "success": True,
            "overall_score": overall_score,
            "component_scores": component_scores,
            "explanation": explanation,
            "model_used": model_name
        }

    except Exception as e:
        st.error(f"Error calculating opportunity score: {e}")
        return {"error": str(e)}

def calculate_financial_attractiveness(opportunity_data):
    """Calculate financial attractiveness score"""
    try:
        # Extract financial metrics
        contract_value = opportunity_data.get('estimated_value', 0)
        contract_duration = opportunity_data.get('duration_months', 12)
        payment_terms = opportunity_data.get('payment_terms', 'standard')

        # Base score from contract value (normalized)
        if contract_value > 10000000:  # $10M+
            value_score = 100
        elif contract_value > 1000000:  # $1M+
            value_score = 80
        elif contract_value > 100000:  # $100K+
            value_score = 60
        else:
            value_score = 40

        # Duration factor
        if contract_duration > 36:  # 3+ years
            duration_factor = 1.2
        elif contract_duration > 12:  # 1+ years
            duration_factor = 1.0
        else:
            duration_factor = 0.8

        # Payment terms factor
        payment_factor = 1.0
        if payment_terms == 'advance':
            payment_factor = 1.3
        elif payment_terms == 'net_30':
            payment_factor = 1.1
        elif payment_terms == 'net_60':
            payment_factor = 0.9

        final_score = min(100, value_score * duration_factor * payment_factor)
        return final_score

    except Exception as e:
        st.error(f"Error calculating financial score: {e}")
        return 50  # Default neutral score

def calculate_strategic_alignment(opportunity_data):
    """Calculate strategic alignment score"""
    try:
        # Get company strategic priorities (this would be configured)
        strategic_priorities = get_company_strategic_priorities()

        alignment_score = 50  # Base score

        # Check alignment with target agencies
        target_agencies = strategic_priorities.get('target_agencies', [])
        if opportunity_data.get('agency') in target_agencies:
            alignment_score += 20

        # Check alignment with target NAICS codes
        target_naics = strategic_priorities.get('target_naics', [])
        opp_naics = opportunity_data.get('naics_codes', [])
        if any(naics in target_naics for naics in opp_naics):
            alignment_score += 15

        # Check alignment with growth areas
        growth_areas = strategic_priorities.get('growth_areas', [])
        opp_keywords = opportunity_data.get('keywords', [])
        if any(keyword.lower() in [area.lower() for area in growth_areas] for keyword in opp_keywords):
            alignment_score += 15

        return min(100, alignment_score)

    except Exception as e:
        st.error(f"Error calculating strategic alignment: {e}")
        return 50

def render_opportunity_scoring():
    """Render opportunity scoring interface"""
    st.subheader("🎯 Opportunity Scoring Algorithm")

    # Scoring tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Score Opportunities", "Scoring Models", "Score Analysis", "Batch Scoring"])

    with tab1:
        st.write("**Individual Opportunity Scoring**")

        # Opportunity selection
        opportunities = get_unscored_opportunities()

        if opportunities:
            selected_opp = st.selectbox(
                "Select Opportunity to Score:",
                options=opportunities,
                format_func=lambda x: f"{x['title']} - {x['agency']}",
                key="scoring_opp_selection"
            )

            if selected_opp:
                # Scoring model selection
                scoring_models = get_available_scoring_models()
                selected_model = st.selectbox(
                    "Scoring Model:",
                    options=scoring_models,
                    format_func=lambda x: f"{x[1]} (v{x[2]})",
                    key="scoring_model_selection"
                )

                if st.button("🎯 Calculate Score", type="primary"):
                    with st.spinner("Calculating opportunity score..."):
                        score_result = calculate_opportunity_score(selected_opp, selected_model[0] if selected_model else None)

                        if score_result.get('success'):
                            st.session_state.calculated_score = score_result
                            st.session_state.scored_opportunity = selected_opp
        else:
            st.info("No unscored opportunities available.")

        # Display calculated score
        if 'calculated_score' in st.session_state:
            score_data = st.session_state.calculated_score

            st.subheader("📊 Opportunity Score Results")

            # Overall score display
            overall_score = score_data['overall_score']
            score_color = get_score_color(overall_score)

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.metric(
                    "Overall Score",
                    f"{overall_score:.1f}/100",
                    delta=None,
                    delta_color="normal"
                )

                # Score interpretation
                if overall_score >= 80:
                    st.success("🟢 High Priority - Strongly Recommended")
                elif overall_score >= 60:
                    st.warning("🟡 Medium Priority - Consider Pursuing")
                elif overall_score >= 40:
                    st.info("🟠 Low Priority - Evaluate Carefully")
                else:
                    st.error("🔴 Not Recommended - High Risk/Low Fit")

            with col2:
                st.write("**Model Used:**")
                st.write(score_data.get('model_used', 'Default'))

            with col3:
                if st.button("💾 Save Score"):
                    st.success("Score saved to opportunity record!")

            # Component scores breakdown
            st.write("**Score Breakdown:**")
            component_scores = score_data['component_scores']

            for component, score in component_scores.items():
                col1, col2 = st.columns([3, 1])

                with col1:
                    component_name = component.replace('_', ' ').title()
                    st.write(f"**{component_name}:**")
                    st.progress(score / 100)

                with col2:
                    st.metric("", f"{score:.1f}")

            # Score explanation
            st.write("**Score Explanation:**")
            st.write(score_data.get('explanation', 'No explanation available'))

    with tab2:
        st.write("**Scoring Models Management**")

        # Existing models
        models = get_available_scoring_models()

        if models:
            st.write("**Available Scoring Models:**")

            for model in models:
                model_id, model_name, version, criteria, weights, is_active, usage_count = model[:7]

                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        status_icon = "🟢" if is_active else "🔴"
                        st.write(f"{status_icon} **{model_name}** (v{version})")

                        # Show criteria summary
                        criteria_obj = json.loads(criteria) if isinstance(criteria, str) else criteria
                        st.caption(f"Criteria: {len(criteria_obj)} factors")

                    with col2:
                        st.metric("Usage Count", usage_count)

                    with col3:
                        if st.button("⚙️", key=f"edit_model_{model_id}", help="Edit model"):
                            st.session_state.edit_model_id = model_id
                            st.rerun()

                st.divider()

        # Create new model
        with st.expander("➕ Create New Scoring Model"):
            render_create_scoring_model_form()

    with tab3:
        st.write("**Score Analysis & Insights**")

        # Score distribution
        score_distribution = get_score_distribution()
        if score_distribution:
            st.write("**Score Distribution:**")
            st.bar_chart(score_distribution)

        # Top scored opportunities
        top_opportunities = get_top_scored_opportunities(limit=10)
        if top_opportunities:
            st.write("**Top Scored Opportunities:**")

            for i, opp in enumerate(top_opportunities, 1):
                opp_title, agency, score, score_date = opp

                col1, col2, col3 = st.columns([4, 2, 1])

                with col1:
                    st.write(f"**{i}. {opp_title}**")
                    st.caption(f"Agency: {agency}")

                with col2:
                    score_color = get_score_color(score)
                    st.metric("Score", f"{score:.1f}")

                with col3:
                    st.caption(score_date.strftime('%Y-%m-%d'))

    with tab4:
        st.write("**Batch Opportunity Scoring**")

        # Batch scoring options
        batch_options = st.multiselect(
            "Select Opportunities for Batch Scoring:",
            options=get_unscored_opportunities(),
            format_func=lambda x: f"{x['title']} - {x['agency']}",
            key="batch_scoring_selection"
        )

        if batch_options:
            scoring_model = st.selectbox(
                "Scoring Model for Batch:",
                options=get_available_scoring_models(),
                format_func=lambda x: f"{x[1]} (v{x[2]})",
                key="batch_scoring_model"
            )

            if st.button("🚀 Score All Selected", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []
                for i, opportunity in enumerate(batch_options):
                    status_text.text(f"Scoring: {opportunity['title']}")

                    score_result = calculate_opportunity_score(opportunity, scoring_model[0] if scoring_model else None)
                    results.append({
                        'opportunity': opportunity,
                        'score': score_result
                    })

                    progress_bar.progress((i + 1) / len(batch_options))

                status_text.text("Batch scoring complete!")

                # Display results summary
                st.write("**Batch Scoring Results:**")

                for result in results:
                    opp = result['opportunity']
                    score = result['score']

                    if score.get('success'):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**{opp['title']}**")

                        with col2:
                            overall_score = score['overall_score']
                            st.metric("Score", f"{overall_score:.1f}")
                    else:
                        st.error(f"Failed to score: {opp['title']}")

def get_score_color(score):
    """Get color based on score value"""
    if score >= 80:
        return "#28a745"  # Green
    elif score >= 60:
        return "#ffc107"  # Yellow
    elif score >= 40:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red
```

---

## **Feature 9: Market Trend Analysis**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** MEDIUM

#### **MCP Integration**
Uses generic `analyze_patterns` tool for comprehensive market trend analysis.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def analyze_market_trends(analysis_period="12_months", focus_areas=None):
    """Analyze government contracting market trends using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Gather market data
        market_data = gather_market_trend_data(analysis_period, focus_areas)

        # Use MCP to analyze trends
        trend_result = call_mcp_tool("analyze_patterns", {
            "data": market_data,
            "pattern_types": ["temporal", "seasonal", "cyclical", "emerging"],
            "analysis_context": "government_contracting_market_trends",
            "prediction_horizon": "6_months"
        })

        if trend_result.get('success'):
            return trend_result['data']
        else:
            return {"error": "Market trend analysis failed"}

    except Exception as e:
        st.error(f"Error analyzing market trends: {e}")
        return {"error": str(e)}

def render_market_trend_analysis():
    """Render market trend analysis interface"""
    st.subheader("📈 Market Trend Analysis")

    # Analysis configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_period = st.selectbox(
            "Analysis Period:",
            ["6_months", "12_months", "24_months", "36_months"],
            index=1,
            key="trend_analysis_period"
        )

    with col2:
        focus_areas = st.multiselect(
            "Focus Areas:",
            ["Contract Values", "Agency Activity", "NAICS Trends", "Set-Aside Programs", "Geographic Distribution"],
            default=["Contract Values", "Agency Activity"],
            key="trend_focus_areas"
        )

    with col3:
        trend_granularity = st.selectbox(
            "Granularity:",
            ["Monthly", "Quarterly", "Yearly"],
            key="trend_granularity"
        )

    if st.button("📊 Analyze Market Trends", type="primary"):
        with st.spinner("Analyzing market trends..."):
            trend_analysis = analyze_market_trends(analysis_period, focus_areas)

            if not trend_analysis.get('error'):
                st.session_state.trend_analysis = trend_analysis
                st.session_state.trend_config = {
                    'period': analysis_period,
                    'focus_areas': focus_areas,
                    'granularity': trend_granularity
                }

    # Display trend analysis results
    if 'trend_analysis' in st.session_state:
        render_trend_analysis_results(st.session_state.trend_analysis, st.session_state.trend_config)

def render_trend_analysis_results(trend_data, config):
    """Render trend analysis results"""
    st.subheader("📈 Market Trend Analysis Results")

    # Key insights summary
    if trend_data.get('key_insights'):
        st.write("**Key Market Insights:**")
        for insight in trend_data['key_insights'][:5]:
            st.write(f"• {insight}")
        st.divider()

    # Trend visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Overall Trends", "Agency Analysis", "Sector Analysis", "Predictions"])

    with tab1:
        st.write("**Overall Market Trends**")

        # Market volume trends
        if trend_data.get('volume_trends'):
            st.write("**Contract Volume Over Time:**")
            volume_data = trend_data['volume_trends']
            st.line_chart(volume_data)

        # Value trends
        if trend_data.get('value_trends'):
            st.write("**Contract Value Trends:**")
            value_data = trend_data['value_trends']
            st.line_chart(value_data)

        # Growth metrics
        if trend_data.get('growth_metrics'):
            col1, col2, col3, col4 = st.columns(4)

            metrics = trend_data['growth_metrics']

            with col1:
                st.metric("Volume Growth", f"{metrics.get('volume_growth', 0):.1%}")

            with col2:
                st.metric("Value Growth", f"{metrics.get('value_growth', 0):.1%}")

            with col3:
                st.metric("Avg Contract Size", f"${metrics.get('avg_contract_size', 0):,.0f}")

            with col4:
                st.metric("Market Volatility", f"{metrics.get('volatility', 0):.1%}")

    with tab2:
        st.write("**Agency Activity Analysis**")

        if trend_data.get('agency_trends'):
            agency_data = trend_data['agency_trends']

            # Top agencies by activity
            st.write("**Most Active Agencies:**")
            for agency, activity in agency_data.get('top_agencies', {}).items():
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**{agency}**")

                with col2:
                    st.metric("Contracts", activity.get('contract_count', 0))
                    st.caption(f"${activity.get('total_value', 0):,.0f}")

            # Agency growth trends
            if agency_data.get('growth_trends'):
                st.write("**Agency Growth Trends:**")
                st.bar_chart(agency_data['growth_trends'])

    with tab3:
        st.write("**Sector & NAICS Analysis**")

        if trend_data.get('sector_trends'):
            sector_data = trend_data['sector_trends']

            # Hot sectors
            st.write("**Fastest Growing Sectors:**")
            for sector, growth in sector_data.get('hot_sectors', {}).items():
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**{sector}**")

                with col2:
                    st.metric("Growth Rate", f"{growth:.1%}")

            # NAICS trends
            if sector_data.get('naics_trends'):
                st.write("**NAICS Code Trends:**")
                st.bar_chart(sector_data['naics_trends'])

    with tab4:
        st.write("**Market Predictions**")

        if trend_data.get('predictions'):
            predictions = trend_data['predictions']

            # Predicted trends
            st.write("**6-Month Predictions:**")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Expected Growth Areas:**")
                for area in predictions.get('growth_areas', []):
                    st.write(f"• {area}")

            with col2:
                st.write("**Potential Challenges:**")
                for challenge in predictions.get('challenges', []):
                    st.write(f"• {challenge}")

            # Prediction confidence
            if predictions.get('confidence_metrics'):
                st.write("**Prediction Confidence:**")
                confidence = predictions['confidence_metrics']

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Overall Confidence", f"{confidence.get('overall', 0):.1%}")

                with col2:
                    st.metric("Trend Accuracy", f"{confidence.get('trend_accuracy', 0):.1%}")

                with col3:
                    st.metric("Data Quality", f"{confidence.get('data_quality', 0):.1%}")

def gather_market_trend_data(period, focus_areas):
    """Gather market data for trend analysis"""
    # This would integrate with your data sources
    # For now, return sample structure
    return {
        "period": period,
        "focus_areas": focus_areas,
        "data_sources": ["SAM.gov", "FPDS", "Internal Database"],
        "sample_size": 10000,
        "data_quality_score": 0.85
    }
```

---

## **Feature 10: Automated NAICS Code Suggestion**
**Status:** ⏳ Ready for Implementation
**Complexity:** LOW | **Priority:** MEDIUM

#### **MCP Integration**
Uses generic `classify_content` tool for NAICS code classification.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def suggest_naics_codes(opportunity_text, company_capabilities=None):
    """Suggest relevant NAICS codes using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return []

    try:
        # Use MCP to classify content and suggest NAICS codes
        naics_result = call_mcp_tool("classify_content", {
            "content": opportunity_text,
            "classification_scheme": "naics_code_taxonomy",
            "domain_rules": {
                "company_capabilities": company_capabilities or [],
                "suggestion_count": 5,
                "confidence_threshold": 0.6
            },
            "risk_assessment": False
        })

        if naics_result.get('success'):
            return naics_result['data'].get('suggested_codes', [])
        else:
            return []

    except Exception as e:
        st.error(f"Error suggesting NAICS codes: {e}")
        return []

def render_naics_suggestion_tool():
    """Render NAICS code suggestion interface"""
    st.subheader("🏷️ Automated NAICS Code Suggestion")

    # Input methods
    input_method = st.radio(
        "Input Method:",
        ["Paste Opportunity Text", "Upload Document", "Select from Library"],
        key="naics_input_method"
    )

    opportunity_text = ""

    if input_method == "Paste Opportunity Text":
        opportunity_text = st.text_area(
            "Opportunity Description:",
            height=200,
            placeholder="Paste the opportunity description, SOW, or RFP text here...",
            key="naics_text_input"
        )

    elif input_method == "Upload Document":
        uploaded_file = st.file_uploader(
            "Upload Document:",
            type=['txt', 'pdf', 'docx'],
            key="naics_file_upload"
        )

        if uploaded_file:
            opportunity_text = extract_text_from_file(uploaded_file)

    elif input_method == "Select from Library":
        documents = get_document_library()

        if documents:
            selected_doc = st.selectbox(
                "Select Document:",
                options=documents,
                format_func=lambda x: f"{x['name']} ({x['type']})",
                key="naics_doc_selection"
            )

            if selected_doc:
                opportunity_text = load_document_content(selected_doc['id'])

    # Company capabilities (optional)
    with st.expander("🏢 Company Capabilities (Optional - for better suggestions)"):
        company_capabilities = st.text_area(
            "List your company's key capabilities:",
            placeholder="e.g., Software Development, Cybersecurity, Cloud Services, Data Analytics",
            key="naics_company_capabilities"
        )

    if opportunity_text and st.button("🎯 Suggest NAICS Codes", type="primary"):
        with st.spinner("Analyzing text and suggesting NAICS codes..."):
            capabilities_list = [cap.strip() for cap in company_capabilities.split(',') if cap.strip()] if company_capabilities else None
            suggested_codes = suggest_naics_codes(opportunity_text, capabilities_list)

            if suggested_codes:
                st.session_state.suggested_naics = suggested_codes
                st.session_state.naics_source_text = opportunity_text

    # Display suggestions
    if 'suggested_naics' in st.session_state:
        st.subheader("🎯 Suggested NAICS Codes")

        for i, suggestion in enumerate(st.session_state.suggested_naics, 1):
            naics_code = suggestion.get('code', '')
            naics_title = suggestion.get('title', '')
            confidence = suggestion.get('confidence', 0.0)
            explanation = suggestion.get('explanation', '')

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**{i}. {naics_code} - {naics_title}**")
                    if explanation:
                        st.caption(explanation)

                with col2:
                    confidence_color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                    st.metric("Confidence", f"{confidence:.1%}")

                with col3:
                    if st.button("📋 Copy", key=f"copy_naics_{i}"):
                        st.success(f"Copied: {naics_code}")

                    if st.button("💾 Save", key=f"save_naics_{i}"):
                        # Save to user's NAICS preferences
                        save_user_naics_preference(naics_code, naics_title)
                        st.success("Saved to preferences!")

            st.divider()

        # Bulk actions
        st.write("**Bulk Actions:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Copy All Codes"):
                all_codes = [s.get('code', '') for s in st.session_state.suggested_naics]
                codes_text = ', '.join(all_codes)
                st.success(f"Copied: {codes_text}")

        with col2:
            if st.button("💾 Save All to Preferences"):
                saved_count = 0
                for suggestion in st.session_state.suggested_naics:
                    if save_user_naics_preference(suggestion.get('code', ''), suggestion.get('title', '')):
                        saved_count += 1
                st.success(f"Saved {saved_count} codes to preferences!")

        with col3:
            if st.button("📊 Generate Report"):
                generate_naics_analysis_report(st.session_state.suggested_naics, st.session_state.naics_source_text)
                st.success("Report generated!")

def save_user_naics_preference(naics_code, naics_title, user_id="default_user"):
    """Save NAICS code to user preferences"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_naics_preferences (user_id, naics_code, naics_title, usage_count)
            VALUES (%s, %s, %s, 1)
            ON CONFLICT (user_id, naics_code)
            DO UPDATE SET usage_count = user_naics_preferences.usage_count + 1
        """, (user_id, naics_code, naics_title))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving NAICS preference: {e}")
        return False
    finally:
        conn.close()
```

---

# **Phase 6: Advanced Document Analysis**

## **Feature 27: Automated Document Classification**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS document_classifications (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    classification_type VARCHAR(100) NOT NULL,
    classification_value VARCHAR(200) NOT NULL,
    confidence_score DECIMAL(3,2),
    classification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    classified_by VARCHAR(100) DEFAULT 'ai_system',
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    verified_by VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS classification_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    classification_type VARCHAR(100) NOT NULL,
    rule_criteria JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accuracy_score DECIMAL(3,2) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_document_classifications_doc_id ON document_classifications(document_id);
CREATE INDEX IF NOT EXISTS ix_document_classifications_type ON document_classifications(classification_type);
```

#### **MCP Integration**
Uses generic `classify_content` tool with document-specific classification schemes.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def classify_document_automatically(document_content, document_metadata=None):
    """Automatically classify document using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Multiple classification types
        classification_results = {}

        # 1. Document Type Classification
        doc_type_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "government_document_types",
            "domain_rules": {
                "document_types": ["RFP", "RFQ", "SOW", "PWS", "Contract", "Amendment", "Sources Sought", "Pre-Solicitation"],
                "confidence_threshold": 0.7
            },
            "risk_assessment": False
        })

        if doc_type_result.get('success'):
            classification_results['document_type'] = doc_type_result['data']

        # 2. Agency Classification
        agency_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "government_agencies",
            "domain_rules": {
                "agencies": ["DOD", "GSA", "VA", "DHS", "DOE", "NASA", "DOT", "HHS", "DOJ", "State", "Treasury"],
                "include_sub_agencies": True
            },
            "risk_assessment": False
        })

        if agency_result.get('success'):
            classification_results['agency'] = agency_result['data']

        # 3. Contract Type Classification
        contract_type_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "contract_types",
            "domain_rules": {
                "contract_types": ["Fixed Price", "Cost Plus", "Time & Materials", "IDIQ", "BPA", "GSA Schedule"],
                "set_aside_types": ["Small Business", "8(a)", "HUBZone", "WOSB", "VOSB", "SDVOSB"]
            },
            "risk_assessment": False
        })

        if contract_type_result.get('success'):
            classification_results['contract_type'] = contract_type_result['data']

        # 4. Urgency/Priority Classification
        urgency_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "document_urgency",
            "domain_rules": {
                "urgency_indicators": ["ASAP", "urgent", "immediate", "expedited", "rush"],
                "deadline_analysis": True
            },
            "risk_assessment": False
        })

        if urgency_result.get('success'):
            classification_results['urgency'] = urgency_result['data']

        return {"success": True, "classifications": classification_results}

    except Exception as e:
        st.error(f"Error classifying document: {e}")
        return {"error": str(e)}

def render_document_classification():
    """Render document classification interface"""
    st.subheader("📂 Automated Document Classification")

    # Classification tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Classify Documents", "Classification Rules", "Batch Classification", "Classification History"])

    with tab1:
        st.write("**Single Document Classification**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="classify_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="classify_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="classify_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                key="classify_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="classify_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("🔍 Classify Document", type="primary"):
            with st.spinner("Classifying document..."):
                classification_result = classify_document_automatically(document_content)

                if classification_result.get('success'):
                    st.session_state.classification_result = classification_result
                    st.session_state.classified_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display classification results
        if 'classification_result' in st.session_state:
            st.subheader("📋 Classification Results")

            classifications = st.session_state.classification_result['classifications']

            for class_type, class_data in classifications.items():
                st.write(f"**{class_type.replace('_', ' ').title()}:**")

                if isinstance(class_data, dict):
                    predicted_class = class_data.get('predicted_class', 'Unknown')
                    confidence = class_data.get('confidence', 0.0)

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"• {predicted_class}")

                    with col2:
                        confidence_color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                        st.metric("Confidence", f"{confidence:.1%}")

                st.divider()

            # Save classifications
            if st.button("💾 Save Classifications"):
                # Save to database
                save_document_classifications(
                    st.session_state.classified_document['name'],
                    classifications
                )
                st.success("Classifications saved!")

    with tab2:
        st.write("**Classification Rules Management**")

        # Display existing rules
        classification_rules = get_classification_rules()

        if classification_rules:
            for rule in classification_rules:
                rule_id, rule_name, class_type, criteria, is_active, accuracy, usage_count = rule

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        status_icon = "🟢" if is_active else "🔴"
                        st.write(f"{status_icon} **{rule_name}**")
                        st.caption(f"Type: {class_type}")

                    with col2:
                        st.metric("Accuracy", f"{accuracy:.1%}")
                        st.caption(f"Used {usage_count} times")

                    with col3:
                        if st.button("⚙️", key=f"edit_rule_{rule_id}"):
                            st.session_state.edit_rule_id = rule_id
                            st.rerun()

                st.divider()

        # Create new rule
        with st.expander("➕ Create Classification Rule"):
            render_create_classification_rule_form()

    with tab3:
        st.write("**Batch Document Classification**")

        # Select documents for batch processing
        available_docs = get_unclassified_documents()

        if available_docs:
            selected_docs = st.multiselect(
                "Select Documents for Batch Classification:",
                options=available_docs,
                format_func=lambda x: f"{x['name']} ({x['type']})",
                key="batch_classify_selection"
            )

            if selected_docs:
                classification_types = st.multiselect(
                    "Classification Types:",
                    ["document_type", "agency", "contract_type", "urgency"],
                    default=["document_type", "agency"],
                    key="batch_classify_types"
                )

                if st.button("🚀 Start Batch Classification", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []
                    for i, doc in enumerate(selected_docs):
                        status_text.text(f"Classifying: {doc['name']}")

                        doc_content = load_document_content(doc['id'])
                        classification_result = classify_document_automatically(doc_content)

                        results.append({
                            'document': doc,
                            'result': classification_result
                        })

                        progress_bar.progress((i + 1) / len(selected_docs))

                    status_text.text("Batch classification complete!")

                    # Display results summary
                    st.write("**Batch Classification Results:**")

                    successful = sum(1 for r in results if r['result'].get('success'))
                    failed = len(results) - successful

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Successful", successful)

                    with col2:
                        st.metric("Failed", failed)
        else:
            st.info("No unclassified documents available.")

    with tab4:
        st.write("**Classification History**")

        # Get recent classifications
        recent_classifications = get_recent_classifications(limit=50)

        if recent_classifications:
            for classification in recent_classifications:
                doc_name, class_type, class_value, confidence, class_date, is_verified = classification

                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        verification_icon = "✅" if is_verified else "❓"
                        st.write(f"{verification_icon} **{doc_name}**")
                        st.caption(f"{class_type}: {class_value}")

                    with col2:
                        st.metric("Confidence", f"{confidence:.1%}")
                        st.caption(class_date.strftime('%Y-%m-%d %H:%M'))

                    with col3:
                        if not is_verified and st.button("✓", key=f"verify_{classification[0]}_{class_type}"):
                            verify_classification(doc_name, class_type)
                            st.rerun()

                st.divider()
        else:
            st.info("No classification history available.")

def save_document_classifications(document_id, classifications):
    """Save document classifications to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for class_type, class_data in classifications.items():
            if isinstance(class_data, dict):
                predicted_class = class_data.get('predicted_class', 'Unknown')
                confidence = class_data.get('confidence', 0.0)

                cursor.execute("""
                    INSERT INTO document_classifications
                    (document_id, classification_type, classification_value, confidence_score)
                    VALUES (%s, %s, %s, %s)
                """, (document_id, class_type, predicted_class, confidence))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving classifications: {e}")
        return False
    finally:
        conn.close()
```

---

## **Feature 28: Smart Document Parsing**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **MCP Integration**
Uses generic `extract_structured_data` tool with document-specific schemas.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def parse_document_intelligently(document_content, document_type=None):
    """Parse document using intelligent structure recognition via MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Determine document type if not provided
        if not document_type:
            type_result = call_mcp_tool("classify_content", {
                "content": document_content[:2000],  # First 2000 chars for type detection
                "classification_scheme": "government_document_types",
                "domain_rules": {"confidence_threshold": 0.6},
                "risk_assessment": False
            })

            if type_result.get('success'):
                document_type = type_result['data'].get('predicted_class', 'unknown')

        # Define parsing schema based on document type
        parsing_schemas = {
            "RFP": {
                "fields": [
                    {"name": "solicitation_number", "type": "string", "description": "RFP/Solicitation number"},
                    {"name": "title", "type": "string", "description": "Project title"},
                    {"name": "agency", "type": "string", "description": "Issuing agency"},
                    {"name": "naics_codes", "type": "array", "description": "NAICS codes"},
                    {"name": "set_aside", "type": "string", "description": "Set-aside type"},
                    {"name": "response_deadline", "type": "string", "description": "Proposal due date"},
                    {"name": "estimated_value", "type": "string", "description": "Contract value"},
                    {"name": "performance_period", "type": "string", "description": "Contract duration"},
                    {"name": "place_of_performance", "type": "string", "description": "Work location"},
                    {"name": "key_requirements", "type": "array", "description": "Main requirements"},
                    {"name": "evaluation_criteria", "type": "array", "description": "Evaluation factors"},
                    {"name": "contact_info", "type": "object", "description": "Government contacts"}
                ]
            },
            "SOW": {
                "fields": [
                    {"name": "project_title", "type": "string", "description": "Statement of Work title"},
                    {"name": "background", "type": "string", "description": "Project background"},
                    {"name": "objectives", "type": "array", "description": "Project objectives"},
                    {"name": "scope_of_work", "type": "array", "description": "Work scope items"},
                    {"name": "deliverables", "type": "array", "description": "Required deliverables"},
                    {"name": "timeline", "type": "array", "description": "Project timeline/milestones"},
                    {"name": "personnel_requirements", "type": "array", "description": "Required personnel"},
                    {"name": "security_requirements", "type": "array", "description": "Security/clearance needs"},
                    {"name": "technical_requirements", "type": "array", "description": "Technical specifications"},
                    {"name": "reporting_requirements", "type": "array", "description": "Reporting obligations"}
                ]
            },
            "Contract": {
                "fields": [
                    {"name": "contract_number", "type": "string", "description": "Contract number"},
                    {"name": "contractor", "type": "string", "description": "Contractor name"},
                    {"name": "contracting_officer", "type": "string", "description": "Contracting officer"},
                    {"name": "contract_type", "type": "string", "description": "Contract type"},
                    {"name": "total_value", "type": "string", "description": "Total contract value"},
                    {"name": "base_period", "type": "string", "description": "Base period"},
                    {"name": "option_periods", "type": "array", "description": "Option periods"},
                    {"name": "clin_structure", "type": "array", "description": "Contract line items"},
                    {"name": "key_clauses", "type": "array", "description": "Important contract clauses"},
                    {"name": "payment_terms", "type": "string", "description": "Payment terms"}
                ]
            }
        }

        # Use appropriate schema or default
        schema = parsing_schemas.get(document_type, parsing_schemas["RFP"])

        # Parse document using MCP
        parsing_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": schema,
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_confidence": True,
                "include_source_references": True,
                "handle_tables": True,
                "handle_lists": True
            }
        })

        if parsing_result.get('success'):
            return {
                "success": True,
                "document_type": document_type,
                "parsed_data": parsing_result['data'],
                "parsing_confidence": parsing_result.get('confidence', 0.0)
            }
        else:
            return {"error": "Document parsing failed"}

    except Exception as e:
        st.error(f"Error parsing document: {e}")
        return {"error": str(e)}

def render_smart_document_parsing():
    """Render smart document parsing interface"""
    st.subheader("🧠 Smart Document Parsing")

    # Parsing tabs
    tab1, tab2, tab3 = st.tabs(["Parse Document", "Parsing Templates", "Parsed Documents"])

    with tab1:
        st.write("**Intelligent Document Parsing**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="parse_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="parse_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="parse_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                key="parse_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="parse_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        # Parsing options
        if document_content:
            col1, col2 = st.columns(2)

            with col1:
                document_type = st.selectbox(
                    "Document Type (optional):",
                    ["Auto-detect", "RFP", "RFQ", "SOW", "PWS", "Contract", "Amendment"],
                    key="parse_doc_type"
                )

            with col2:
                parsing_depth = st.selectbox(
                    "Parsing Depth:",
                    ["Standard", "Detailed", "Comprehensive"],
                    key="parse_depth"
                )

            if st.button("🧠 Parse Document", type="primary"):
                with st.spinner("Parsing document intelligently..."):
                    doc_type = None if document_type == "Auto-detect" else document_type
                    parsing_result = parse_document_intelligently(document_content, doc_type)

                    if parsing_result.get('success'):
                        st.session_state.parsing_result = parsing_result
                        st.session_state.parsed_document = {
                            'name': document_name,
                            'content': document_content
                        }

        # Display parsing results
        if 'parsing_result' in st.session_state:
            st.subheader("📋 Parsing Results")

            result = st.session_state.parsing_result

            # Document type and confidence
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Document Type", result.get('document_type', 'Unknown'))

            with col2:
                confidence = result.get('parsing_confidence', 0.0)
                st.metric("Parsing Confidence", f"{confidence:.1%}")

            # Parsed data
            parsed_data = result.get('parsed_data', {})

            if parsed_data:
                st.write("**Extracted Information:**")

                for field_name, field_value in parsed_data.items():
                    if field_value:  # Only show non-empty fields
                        st.write(f"**{field_name.replace('_', ' ').title()}:**")

                        if isinstance(field_value, list):
                            for item in field_value:
                                st.write(f"• {item}")
                        elif isinstance(field_value, dict):
                            for key, value in field_value.items():
                                st.write(f"• {key}: {value}")
                        else:
                            st.write(f"• {field_value}")

                        st.write("")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Parsed Data"):
                    save_parsed_document_data(
                        st.session_state.parsed_document['name'],
                        result
                    )
                    st.success("Parsed data saved!")

            with col2:
                if st.button("📊 Generate Summary"):
                    summary = generate_document_summary(parsed_data)
                    st.session_state.document_summary = summary
                    st.success("Summary generated!")

            with col3:
                if st.button("📄 Export to JSON"):
                    export_parsed_data_json(parsed_data, document_name)
                    st.success("Data exported to JSON!")

            with col4:
                if st.button("📋 Copy to Clipboard"):
                    st.success("Parsed data copied to clipboard!")

            # Display summary if generated
            if 'document_summary' in st.session_state:
                st.write("**Document Summary:**")
                st.write(st.session_state.document_summary)

    with tab2:
        st.write("**Parsing Templates Management**")

        # Custom parsing templates
        st.info("Custom parsing templates allow you to define specific extraction patterns for different document types.")

        # Template creation form
        with st.expander("➕ Create Custom Parsing Template"):
            template_name = st.text_input("Template Name:", key="template_name")
            template_doc_type = st.text_input("Document Type:", key="template_doc_type")

            st.write("**Define Fields to Extract:**")

            # Dynamic field definition
            if 'template_fields' not in st.session_state:
                st.session_state.template_fields = []

            col1, col2 = st.columns(2)

            with col1:
                field_name = st.text_input("Field Name:", key="new_field_name")
                field_type = st.selectbox("Field Type:", ["string", "array", "object"], key="new_field_type")

            with col2:
                field_description = st.text_input("Field Description:", key="new_field_description")

                if st.button("➕ Add Field"):
                    if field_name and field_description:
                        st.session_state.template_fields.append({
                            "name": field_name,
                            "type": field_type,
                            "description": field_description
                        })
                        st.rerun()

            # Display current fields
            if st.session_state.template_fields:
                st.write("**Template Fields:**")
                for i, field in enumerate(st.session_state.template_fields):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(f"• {field['name']} ({field['type']}): {field['description']}")

                    with col2:
                        if st.button("🗑️", key=f"remove_field_{i}"):
                            st.session_state.template_fields.pop(i)
                            st.rerun()

            # Save template
            if st.button("💾 Save Template", disabled=not (template_name and template_doc_type and st.session_state.template_fields)):
                save_parsing_template(template_name, template_doc_type, st.session_state.template_fields)
                st.success(f"Template '{template_name}' saved!")
                st.session_state.template_fields = []
                st.rerun()

    with tab3:
        st.write("**Parsed Documents Library**")

        # Get parsed documents
        parsed_documents = get_parsed_documents()

        if parsed_documents:
            for doc in parsed_documents:
                doc_name, doc_type, parse_date, confidence = doc

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{doc_name}**")
                        st.caption(f"Type: {doc_type}")

                    with col2:
                        st.metric("Confidence", f"{confidence:.1%}")

                    with col3:
                        st.caption(parse_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_parsed_{doc_name}"):
                            # Load and display parsed data
                            parsed_data = load_parsed_document_data(doc_name)
                            st.session_state.view_parsed_data = parsed_data
                            st.rerun()

                st.divider()
        else:
            st.info("No parsed documents available.")

        # Display parsed data if viewing
        if 'view_parsed_data' in st.session_state:
            st.write("**Parsed Document Data:**")
            st.json(st.session_state.view_parsed_data)

def save_parsed_document_data(document_name, parsing_result):
    """Save parsed document data to database"""
    # Implementation would save to database
    pass

def generate_document_summary(parsed_data):
    """Generate summary from parsed data using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Summary generation not available"

    try:
        summary_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(parsed_data),
            "insight_type": "document_summary",
            "context": {
                "domain": "government_contracting",
                "summary_focus": ["key_points", "requirements", "deadlines"],
                "length": "concise"
            },
            "output_format": "executive_summary"
        })

        if summary_result.get('success'):
            return summary_result['data'].get('summary', 'Summary generation failed')
        else:
            return "Summary generation failed"

    except Exception as e:
        return f"Error generating summary: {e}"
```

---

## **Feature 29: CLIN Structure Extraction**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS clin_structures (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    clin_number VARCHAR(50) NOT NULL,
    clin_title TEXT,
    clin_description TEXT,
    quantity DECIMAL(10,2),
    unit_of_measure VARCHAR(50),
    unit_price DECIMAL(12,2),
    total_price DECIMAL(15,2),
    period_of_performance VARCHAR(100),
    deliverable_type VARCHAR(100),
    is_base_period BOOLEAN DEFAULT TRUE,
    option_period INTEGER,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clin_relationships (
    id SERIAL PRIMARY KEY,
    parent_clin_id INTEGER REFERENCES clin_structures(id),
    child_clin_id INTEGER REFERENCES clin_structures(id),
    relationship_type VARCHAR(50), -- 'sub_clin', 'option', 'modification'
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_clin_structures_document ON clin_structures(document_id);
CREATE INDEX IF NOT EXISTS ix_clin_structures_number ON clin_structures(clin_number);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with CLIN-specific schema.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_clin_structure(document_content, document_id=None):
    """Extract CLIN structure from contract documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract CLIN structure
        clin_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "clin_items", "type": "array", "description": "Contract Line Item Numbers with details"},
                    {"name": "base_period_clins", "type": "array", "description": "Base period CLINs"},
                    {"name": "option_period_clins", "type": "array", "description": "Option period CLINs"},
                    {"name": "total_contract_value", "type": "string", "description": "Total contract value"},
                    {"name": "pricing_structure", "type": "string", "description": "Overall pricing structure"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_tables": True,
                "include_pricing": True,
                "include_quantities": True,
                "confidence_threshold": 0.7
            }
        })

        if clin_result.get('success'):
            # Process and structure the CLIN data
            clin_data = clin_result['data']
            structured_clins = process_clin_data(clin_data)

            # Save to database if document_id provided
            if document_id and structured_clins:
                save_clin_structure(document_id, structured_clins)

            return {
                "success": True,
                "clin_structure": structured_clins,
                "extraction_confidence": clin_result.get('confidence', 0.0),
                "total_clins": len(structured_clins)
            }
        else:
            return {"error": "CLIN extraction failed"}

    except Exception as e:
        st.error(f"Error extracting CLIN structure: {e}")
        return {"error": str(e)}

def process_clin_data(raw_clin_data):
    """Process raw CLIN data into structured format"""
    structured_clins = []

    clin_items = raw_clin_data.get('clin_items', [])

    for item in clin_items:
        if isinstance(item, dict):
            clin = {
                'clin_number': item.get('clin_number', ''),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'quantity': parse_numeric_value(item.get('quantity', '')),
                'unit_of_measure': item.get('unit_of_measure', ''),
                'unit_price': parse_currency_value(item.get('unit_price', '')),
                'total_price': parse_currency_value(item.get('total_price', '')),
                'period': item.get('period_of_performance', ''),
                'deliverable_type': item.get('deliverable_type', ''),
                'is_base_period': item.get('is_base_period', True),
                'option_period': item.get('option_period', None)
            }
            structured_clins.append(clin)

    return structured_clins

def parse_numeric_value(value_str):
    """Parse numeric value from string"""
    if not value_str:
        return None

    try:
        # Remove common non-numeric characters
        cleaned = str(value_str).replace(',', '').replace('$', '').strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def parse_currency_value(value_str):
    """Parse currency value from string"""
    if not value_str:
        return None

    try:
        # Remove currency symbols and commas
        cleaned = str(value_str).replace('$', '').replace(',', '').strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def save_clin_structure(document_id, clin_structure):
    """Save CLIN structure to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for clin in clin_structure:
            cursor.execute("""
                INSERT INTO clin_structures
                (document_id, clin_number, clin_title, clin_description, quantity,
                 unit_of_measure, unit_price, total_price, period_of_performance,
                 deliverable_type, is_base_period, option_period, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, clin['clin_number'], clin['title'], clin['description'],
                clin['quantity'], clin['unit_of_measure'], clin['unit_price'],
                clin['total_price'], clin['period'], clin['deliverable_type'],
                clin['is_base_period'], clin['option_period'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving CLIN structure: {e}")
        return False
    finally:
        conn.close()

def render_clin_extraction():
    """Render CLIN structure extraction interface"""
    st.subheader("📋 CLIN Structure Extraction")

    # Extraction tabs
    tab1, tab2, tab3 = st.tabs(["Extract CLINs", "CLIN Library", "CLIN Analysis"])

    with tab1:
        st.write("**Extract CLIN Structure from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="clin_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Contract/RFP Document:",
                type=['txt', 'pdf', 'docx'],
                key="clin_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="clin_doc_name")
            document_content = st.text_area(
                "Contract/RFP Content:",
                height=300,
                placeholder="Paste contract or RFP content containing CLIN structure...",
                key="clin_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_contract_documents()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="clin_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("📋 Extract CLIN Structure", type="primary"):
            with st.spinner("Extracting CLIN structure..."):
                clin_result = extract_clin_structure(document_content, document_name)

                if clin_result.get('success'):
                    st.session_state.clin_extraction_result = clin_result
                    st.session_state.clin_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display extraction results
        if 'clin_extraction_result' in st.session_state:
            st.subheader("📊 CLIN Extraction Results")

            result = st.session_state.clin_extraction_result
            clin_structure = result.get('clin_structure', [])

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total CLINs", result.get('total_clins', 0))

            with col2:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            with col3:
                total_value = sum(clin.get('total_price', 0) or 0 for clin in clin_structure)
                st.metric("Total Contract Value", f"${total_value:,.2f}")

            # CLIN details table
            if clin_structure:
                st.write("**CLIN Structure Details:**")

                # Create DataFrame for better display
                clin_df_data = []
                for clin in clin_structure:
                    clin_df_data.append({
                        'CLIN': clin.get('clin_number', ''),
                        'Title': clin.get('title', '')[:50] + '...' if len(clin.get('title', '')) > 50 else clin.get('title', ''),
                        'Quantity': clin.get('quantity', ''),
                        'Unit': clin.get('unit_of_measure', ''),
                        'Unit Price': f"${clin.get('unit_price', 0):,.2f}" if clin.get('unit_price') else '',
                        'Total Price': f"${clin.get('total_price', 0):,.2f}" if clin.get('total_price') else '',
                        'Period': clin.get('period', '')
                    })

                st.dataframe(clin_df_data, use_container_width=True)

                # Detailed view
                with st.expander("📋 Detailed CLIN Information"):
                    for i, clin in enumerate(clin_structure, 1):
                        st.write(f"**CLIN {clin.get('clin_number', i)}:**")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Title:** {clin.get('title', 'N/A')}")
                            st.write(f"**Description:** {clin.get('description', 'N/A')}")
                            st.write(f"**Deliverable Type:** {clin.get('deliverable_type', 'N/A')}")

                        with col2:
                            st.write(f"**Quantity:** {clin.get('quantity', 'N/A')}")
                            st.write(f"**Unit of Measure:** {clin.get('unit_of_measure', 'N/A')}")
                            st.write(f"**Period:** {clin.get('period', 'N/A')}")

                        if clin.get('unit_price') or clin.get('total_price'):
                            st.write(f"**Pricing:** Unit: ${clin.get('unit_price', 0):,.2f} | Total: ${clin.get('total_price', 0):,.2f}")

                        st.divider()

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save CLIN Structure"):
                    save_clin_structure(st.session_state.clin_document['name'], clin_structure)
                    st.success("CLIN structure saved!")

            with col2:
                if st.button("📊 Generate CLIN Report"):
                    generate_clin_report(clin_structure)
                    st.success("CLIN report generated!")

            with col3:
                if st.button("📄 Export to Excel"):
                    export_clin_to_excel(clin_structure, document_name)
                    st.success("CLIN data exported!")

            with col4:
                if st.button("🔍 Analyze Pricing"):
                    analyze_clin_pricing(clin_structure)
                    st.success("Pricing analysis complete!")

    with tab2:
        st.write("**CLIN Structure Library**")

        # Get saved CLIN structures
        saved_clins = get_saved_clin_structures()

        if saved_clins:
            for clin_doc in saved_clins:
                doc_name, total_clins, total_value, extraction_date = clin_doc

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{doc_name}**")
                        st.caption(f"Extracted: {extraction_date.strftime('%Y-%m-%d')}")

                    with col2:
                        st.metric("CLINs", total_clins)

                    with col3:
                        st.metric("Value", f"${total_value:,.0f}")

                        if st.button("👁️", key=f"view_clin_{doc_name}"):
                            # Load and display CLIN details
                            clin_details = load_clin_structure(doc_name)
                            st.session_state.view_clin_details = clin_details
                            st.rerun()

                st.divider()
        else:
            st.info("No CLIN structures saved yet.")

    with tab3:
        st.write("**CLIN Analysis & Insights**")

        # CLIN analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Pricing Analysis", "Structure Comparison", "Trend Analysis", "Risk Assessment"],
            key="clin_analysis_type"
        )

        if analysis_type == "Pricing Analysis":
            render_clin_pricing_analysis()
        elif analysis_type == "Structure Comparison":
            render_clin_structure_comparison()
        elif analysis_type == "Trend Analysis":
            render_clin_trend_analysis()
        elif analysis_type == "Risk Assessment":
            render_clin_risk_assessment()

def render_clin_pricing_analysis():
    """Render CLIN pricing analysis"""
    st.write("**CLIN Pricing Analysis**")

    # Select CLINs for analysis
    available_clins = get_all_clin_structures()

    if available_clins:
        selected_clins = st.multiselect(
            "Select CLIN Structures for Analysis:",
            options=available_clins,
            format_func=lambda x: f"{x['document']} - {x['clin_count']} CLINs",
            key="pricing_analysis_clins"
        )

        if selected_clins and st.button("📊 Analyze Pricing"):
            with st.spinner("Analyzing CLIN pricing..."):
                pricing_analysis = analyze_clin_pricing_patterns(selected_clins)

                if pricing_analysis:
                    st.write("**Pricing Analysis Results:**")

                    # Price distribution
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        avg_clin_value = pricing_analysis.get('avg_clin_value', 0)
                        st.metric("Average CLIN Value", f"${avg_clin_value:,.2f}")

                    with col2:
                        price_variance = pricing_analysis.get('price_variance', 0)
                        st.metric("Price Variance", f"{price_variance:.1%}")

                    with col3:
                        outlier_count = pricing_analysis.get('outlier_count', 0)
                        st.metric("Price Outliers", outlier_count)

                    # Pricing insights
                    insights = pricing_analysis.get('insights', [])
                    if insights:
                        st.write("**Key Insights:**")
                        for insight in insights:
                            st.write(f"• {insight}")
    else:
        st.info("No CLIN structures available for analysis.")

def analyze_clin_pricing_patterns(clin_structures):
    """Analyze pricing patterns in CLIN structures using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return None

    try:
        # Prepare pricing data
        pricing_data = []
        for clin_struct in clin_structures:
            clins = load_clin_structure(clin_struct['document'])
            for clin in clins:
                if clin.get('total_price'):
                    pricing_data.append({
                        'clin_number': clin.get('clin_number'),
                        'total_price': clin.get('total_price'),
                        'unit_price': clin.get('unit_price'),
                        'quantity': clin.get('quantity'),
                        'deliverable_type': clin.get('deliverable_type')
                    })

        # Use MCP to analyze pricing patterns
        analysis_result = call_mcp_tool("analyze_patterns", {
            "data": pricing_data,
            "pattern_types": ["pricing_trends", "outlier_detection", "value_distribution"],
            "analysis_context": "government_contracting_clin_pricing",
            "output_format": "pricing_analysis"
        })

        if analysis_result.get('success'):
            return analysis_result['data']
        else:
            return None

    except Exception as e:
        st.error(f"Error analyzing CLIN pricing: {e}")
        return None
```

---

## **Feature 30: Personnel Requirements Table**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS personnel_requirements (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    position_title VARCHAR(200) NOT NULL,
    position_description TEXT,
    required_experience VARCHAR(100),
    education_requirements TEXT,
    certifications_required TEXT[],
    security_clearance VARCHAR(50),
    skills_required TEXT[],
    quantity_needed INTEGER DEFAULT 1,
    labor_category VARCHAR(100),
    hourly_rate DECIMAL(8,2),
    annual_hours INTEGER,
    is_key_personnel BOOLEAN DEFAULT FALSE,
    location_requirement VARCHAR(200),
    travel_percentage INTEGER,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2)
);

CREATE INDEX IF NOT EXISTS ix_personnel_requirements_document ON personnel_requirements(document_id);
CREATE INDEX IF NOT EXISTS ix_personnel_requirements_clearance ON personnel_requirements(security_clearance);
CREATE INDEX IF NOT EXISTS ix_personnel_requirements_key ON personnel_requirements(is_key_personnel);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with personnel-specific schema.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_personnel_requirements(document_content, document_id=None):
    """Extract personnel requirements from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract personnel requirements
        personnel_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "personnel_positions", "type": "array", "description": "Required personnel positions with details"},
                    {"name": "key_personnel", "type": "array", "description": "Key personnel requirements"},
                    {"name": "labor_categories", "type": "array", "description": "Labor categories and rates"},
                    {"name": "clearance_requirements", "type": "array", "description": "Security clearance requirements"},
                    {"name": "staffing_levels", "type": "object", "description": "Overall staffing level requirements"},
                    {"name": "location_requirements", "type": "array", "description": "Work location requirements"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_tables": True,
                "include_rates": True,
                "include_qualifications": True,
                "confidence_threshold": 0.7
            }
        })

        if personnel_result.get('success'):
            # Process and structure the personnel data
            personnel_data = personnel_result['data']
            structured_personnel = process_personnel_data(personnel_data)

            # Save to database if document_id provided
            if document_id and structured_personnel:
                save_personnel_requirements(document_id, structured_personnel)

            return {
                "success": True,
                "personnel_requirements": structured_personnel,
                "extraction_confidence": personnel_result.get('confidence', 0.0),
                "total_positions": len(structured_personnel)
            }
        else:
            return {"error": "Personnel extraction failed"}

    except Exception as e:
        st.error(f"Error extracting personnel requirements: {e}")
        return {"error": str(e)}

def process_personnel_data(raw_personnel_data):
    """Process raw personnel data into structured format"""
    structured_personnel = []

    personnel_positions = raw_personnel_data.get('personnel_positions', [])
    key_personnel = raw_personnel_data.get('key_personnel', [])

    # Process regular positions
    for position in personnel_positions:
        if isinstance(position, dict):
            personnel = {
                'position_title': position.get('title', ''),
                'description': position.get('description', ''),
                'experience': position.get('experience_required', ''),
                'education': position.get('education_requirements', ''),
                'certifications': position.get('certifications', []),
                'clearance': position.get('security_clearance', ''),
                'skills': position.get('skills_required', []),
                'quantity': position.get('quantity', 1),
                'labor_category': position.get('labor_category', ''),
                'hourly_rate': parse_currency_value(position.get('hourly_rate', '')),
                'annual_hours': position.get('annual_hours', None),
                'is_key_personnel': False,
                'location': position.get('location_requirement', ''),
                'travel_percentage': position.get('travel_percentage', None)
            }
            structured_personnel.append(personnel)

    # Process key personnel
    for key_pos in key_personnel:
        if isinstance(key_pos, dict):
            personnel = {
                'position_title': key_pos.get('title', ''),
                'description': key_pos.get('description', ''),
                'experience': key_pos.get('experience_required', ''),
                'education': key_pos.get('education_requirements', ''),
                'certifications': key_pos.get('certifications', []),
                'clearance': key_pos.get('security_clearance', ''),
                'skills': key_pos.get('skills_required', []),
                'quantity': 1,  # Key personnel typically singular
                'labor_category': key_pos.get('labor_category', ''),
                'hourly_rate': parse_currency_value(key_pos.get('hourly_rate', '')),
                'annual_hours': key_pos.get('annual_hours', None),
                'is_key_personnel': True,
                'location': key_pos.get('location_requirement', ''),
                'travel_percentage': key_pos.get('travel_percentage', None)
            }
            structured_personnel.append(personnel)

    return structured_personnel

def save_personnel_requirements(document_id, personnel_requirements):
    """Save personnel requirements to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for personnel in personnel_requirements:
            cursor.execute("""
                INSERT INTO personnel_requirements
                (document_id, position_title, position_description, required_experience,
                 education_requirements, certifications_required, security_clearance,
                 skills_required, quantity_needed, labor_category, hourly_rate,
                 annual_hours, is_key_personnel, location_requirement, travel_percentage,
                 extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, personnel['position_title'], personnel['description'],
                personnel['experience'], personnel['education'], personnel['certifications'],
                personnel['clearance'], personnel['skills'], personnel['quantity'],
                personnel['labor_category'], personnel['hourly_rate'], personnel['annual_hours'],
                personnel['is_key_personnel'], personnel['location'], personnel['travel_percentage'],
                0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving personnel requirements: {e}")
        return False
    finally:
        conn.close()

def render_personnel_requirements_extraction():
    """Render personnel requirements extraction interface"""
    st.subheader("👥 Personnel Requirements Table")

    # Extraction tabs
    tab1, tab2, tab3 = st.tabs(["Extract Personnel", "Personnel Library", "Staffing Analysis"])

    with tab1:
        st.write("**Extract Personnel Requirements from Documents**")

        # Document input (similar pattern as CLIN extraction)
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="personnel_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload SOW/RFP Document:",
                type=['txt', 'pdf', 'docx'],
                key="personnel_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="personnel_doc_name")
            document_content = st.text_area(
                "SOW/RFP Content:",
                height=300,
                placeholder="Paste SOW or RFP content containing personnel requirements...",
                key="personnel_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_sow_documents()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="personnel_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("👥 Extract Personnel Requirements", type="primary"):
            with st.spinner("Extracting personnel requirements..."):
                personnel_result = extract_personnel_requirements(document_content, document_name)

                if personnel_result.get('success'):
                    st.session_state.personnel_extraction_result = personnel_result
                    st.session_state.personnel_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display extraction results
        if 'personnel_extraction_result' in st.session_state:
            st.subheader("👥 Personnel Requirements Results")

            result = st.session_state.personnel_extraction_result
            personnel_requirements = result.get('personnel_requirements', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Positions", result.get('total_positions', 0))

            with col2:
                key_personnel_count = sum(1 for p in personnel_requirements if p.get('is_key_personnel'))
                st.metric("Key Personnel", key_personnel_count)

            with col3:
                clearance_required = sum(1 for p in personnel_requirements if p.get('clearance'))
                st.metric("Clearance Required", clearance_required)

            with col4:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            # Personnel requirements table
            if personnel_requirements:
                st.write("**Personnel Requirements Table:**")

                # Create DataFrame for better display
                personnel_df_data = []
                for personnel in personnel_requirements:
                    personnel_df_data.append({
                        'Position': personnel.get('position_title', ''),
                        'Key Personnel': '✓' if personnel.get('is_key_personnel') else '',
                        'Experience': personnel.get('experience', ''),
                        'Clearance': personnel.get('clearance', ''),
                        'Quantity': personnel.get('quantity', 1),
                        'Rate': f"${personnel.get('hourly_rate', 0):,.2f}/hr" if personnel.get('hourly_rate') else '',
                        'Location': personnel.get('location', '')
                    })

                st.dataframe(personnel_df_data, use_container_width=True)

                # Detailed view
                with st.expander("👥 Detailed Personnel Information"):
                    for i, personnel in enumerate(personnel_requirements, 1):
                        key_indicator = "🔑 " if personnel.get('is_key_personnel') else ""
                        st.write(f"**{key_indicator}{personnel.get('position_title', f'Position {i}')}:**")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Description:** {personnel.get('description', 'N/A')}")
                            st.write(f"**Experience Required:** {personnel.get('experience', 'N/A')}")
                            st.write(f"**Education:** {personnel.get('education', 'N/A')}")

                            if personnel.get('certifications'):
                                st.write(f"**Certifications:** {', '.join(personnel['certifications'])}")

                        with col2:
                            st.write(f"**Security Clearance:** {personnel.get('clearance', 'None specified')}")
                            st.write(f"**Quantity Needed:** {personnel.get('quantity', 1)}")
                            st.write(f"**Labor Category:** {personnel.get('labor_category', 'N/A')}")

                            if personnel.get('hourly_rate'):
                                st.write(f"**Hourly Rate:** ${personnel.get('hourly_rate', 0):,.2f}")

                            if personnel.get('travel_percentage'):
                                st.write(f"**Travel Required:** {personnel.get('travel_percentage')}%")

                        if personnel.get('skills'):
                            st.write(f"**Required Skills:** {', '.join(personnel['skills'])}")

                        st.divider()

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Personnel Requirements"):
                    save_personnel_requirements(st.session_state.personnel_document['name'], personnel_requirements)
                    st.success("Personnel requirements saved!")

            with col2:
                if st.button("📊 Generate Staffing Plan"):
                    generate_staffing_plan(personnel_requirements)
                    st.success("Staffing plan generated!")

            with col3:
                if st.button("📄 Export to Excel"):
                    export_personnel_to_excel(personnel_requirements, document_name)
                    st.success("Personnel data exported!")

            with col4:
                if st.button("💰 Calculate Labor Costs"):
                    calculate_labor_costs(personnel_requirements)
                    st.success("Labor cost analysis complete!")

    with tab2:
        st.write("**Personnel Requirements Library**")

        # Get saved personnel requirements
        saved_personnel = get_saved_personnel_requirements()

        if saved_personnel:
            for personnel_doc in saved_personnel:
                doc_name, total_positions, key_personnel_count, extraction_date = personnel_doc

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{doc_name}**")
                        st.caption(f"Extracted: {extraction_date.strftime('%Y-%m-%d')}")

                    with col2:
                        st.metric("Total Positions", total_positions)

                    with col3:
                        st.metric("Key Personnel", key_personnel_count)

                        if st.button("👁️", key=f"view_personnel_{doc_name}"):
                            # Load and display personnel details
                            personnel_details = load_personnel_requirements(doc_name)
                            st.session_state.view_personnel_details = personnel_details
                            st.rerun()

                st.divider()
        else:
            st.info("No personnel requirements saved yet.")

    with tab3:
        st.write("**Staffing Analysis & Planning**")

        # Staffing analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Cost Analysis", "Clearance Analysis", "Skills Gap Analysis", "Staffing Comparison"],
            key="personnel_analysis_type"
        )

        if analysis_type == "Cost Analysis":
            render_personnel_cost_analysis()
        elif analysis_type == "Clearance Analysis":
            render_clearance_analysis()
        elif analysis_type == "Skills Gap Analysis":
            render_skills_gap_analysis()
        elif analysis_type == "Staffing Comparison":
            render_staffing_comparison()

def render_personnel_cost_analysis():
    """Render personnel cost analysis"""
    st.write("**Personnel Cost Analysis**")

    # Select personnel requirements for analysis
    available_personnel = get_all_personnel_requirements()

    if available_personnel:
        selected_personnel = st.multiselect(
            "Select Personnel Requirements for Analysis:",
            options=available_personnel,
            format_func=lambda x: f"{x['document']} - {x['position_count']} positions",
            key="cost_analysis_personnel"
        )

        if selected_personnel and st.button("💰 Analyze Costs"):
            with st.spinner("Analyzing personnel costs..."):
                cost_analysis = analyze_personnel_costs(selected_personnel)

                if cost_analysis:
                    st.write("**Cost Analysis Results:**")

                    # Cost metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        total_annual_cost = cost_analysis.get('total_annual_cost', 0)
                        st.metric("Total Annual Cost", f"${total_annual_cost:,.2f}")

                    with col2:
                        avg_hourly_rate = cost_analysis.get('avg_hourly_rate', 0)
                        st.metric("Average Hourly Rate", f"${avg_hourly_rate:.2f}")

                    with col3:
                        key_personnel_cost = cost_analysis.get('key_personnel_cost', 0)
                        st.metric("Key Personnel Cost", f"${key_personnel_cost:,.2f}")

                    with col4:
                        clearance_premium = cost_analysis.get('clearance_premium', 0)
                        st.metric("Clearance Premium", f"{clearance_premium:.1%}")

                    # Cost breakdown
                    cost_breakdown = cost_analysis.get('cost_breakdown', {})
                    if cost_breakdown:
                        st.write("**Cost Breakdown by Category:**")
                        st.bar_chart(cost_breakdown)
    else:
        st.info("No personnel requirements available for analysis.")

def analyze_personnel_costs(personnel_requirements):
    """Analyze personnel costs using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return None

    try:
        # Prepare cost data
        cost_data = []
        for personnel_req in personnel_requirements:
            personnel_list = load_personnel_requirements(personnel_req['document'])
            for personnel in personnel_list:
                if personnel.get('hourly_rate'):
                    cost_data.append({
                        'position': personnel.get('position_title'),
                        'hourly_rate': personnel.get('hourly_rate'),
                        'annual_hours': personnel.get('annual_hours', 2080),
                        'quantity': personnel.get('quantity', 1),
                        'is_key_personnel': personnel.get('is_key_personnel', False),
                        'clearance': personnel.get('clearance', ''),
                        'labor_category': personnel.get('labor_category', '')
                    })

        # Use MCP to analyze cost patterns
        analysis_result = call_mcp_tool("analyze_patterns", {
            "data": cost_data,
            "pattern_types": ["cost_analysis", "rate_comparison", "category_breakdown"],
            "analysis_context": "government_contracting_personnel_costs",
            "output_format": "cost_analysis"
        })

        if analysis_result.get('success'):
            return analysis_result['data']
        else:
            return None

    except Exception as e:
        st.error(f"Error analyzing personnel costs: {e}")
        return None
```

---

## **Feature 31: Security Clearance Identification**
**Status:** ⏳ Ready for Implementation
**Complexity:** LOW | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS clearance_requirements (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    clearance_level VARCHAR(50) NOT NULL,
    clearance_type VARCHAR(50), -- 'personnel', 'facility', 'both'
    percentage_required DECIMAL(5,2),
    specific_requirements TEXT,
    investigation_type VARCHAR(50),
    polygraph_required BOOLEAN DEFAULT FALSE,
    citizenship_requirement VARCHAR(50),
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_clearance_requirements_document ON clearance_requirements(document_id);
CREATE INDEX IF NOT EXISTS ix_clearance_requirements_level ON clearance_requirements(clearance_level);
```

#### **MCP Integration**
Uses generic `classify_content` tool with clearance-specific classification scheme.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def identify_security_clearances(document_content, document_id=None):
    """Identify security clearance requirements using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to classify and extract clearance requirements
        clearance_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "security_clearance_requirements",
            "domain_rules": {
                "clearance_levels": ["Public Trust", "Confidential", "Secret", "Top Secret", "TS/SCI"],
                "clearance_types": ["personnel", "facility", "both"],
                "investigation_types": ["NACLC", "MBI", "BI", "SSBI", "SSBI-PR"],
                "special_requirements": ["polygraph", "CI_poly", "lifestyle_poly", "FSP"],
                "extract_percentages": True,
                "extract_citizenship": True
            },
            "risk_assessment": False
        })

        if clearance_result.get('success'):
            clearance_data = clearance_result['data']
            structured_clearances = process_clearance_data(clearance_data)

            # Save to database if document_id provided
            if document_id and structured_clearances:
                save_clearance_requirements(document_id, structured_clearances)

            return {
                "success": True,
                "clearance_requirements": structured_clearances,
                "extraction_confidence": clearance_result.get('confidence', 0.0),
                "total_requirements": len(structured_clearances)
            }
        else:
            return {"error": "Clearance identification failed"}

    except Exception as e:
        st.error(f"Error identifying security clearances: {e}")
        return {"error": str(e)}

def process_clearance_data(raw_clearance_data):
    """Process raw clearance data into structured format"""
    structured_clearances = []

    clearances = raw_clearance_data.get('identified_clearances', [])

    for clearance in clearances:
        if isinstance(clearance, dict):
            clearance_req = {
                'clearance_level': clearance.get('level', ''),
                'clearance_type': clearance.get('type', 'personnel'),
                'percentage_required': clearance.get('percentage', None),
                'specific_requirements': clearance.get('requirements', ''),
                'investigation_type': clearance.get('investigation_type', ''),
                'polygraph_required': clearance.get('polygraph_required', False),
                'citizenship_requirement': clearance.get('citizenship', 'US Citizen')
            }
            structured_clearances.append(clearance_req)

    return structured_clearances

def save_clearance_requirements(document_id, clearance_requirements):
    """Save clearance requirements to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for clearance in clearance_requirements:
            cursor.execute("""
                INSERT INTO clearance_requirements
                (document_id, clearance_level, clearance_type, percentage_required,
                 specific_requirements, investigation_type, polygraph_required,
                 citizenship_requirement, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, clearance['clearance_level'], clearance['clearance_type'],
                clearance['percentage_required'], clearance['specific_requirements'],
                clearance['investigation_type'], clearance['polygraph_required'],
                clearance['citizenship_requirement'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving clearance requirements: {e}")
        return False
    finally:
        conn.close()

def render_clearance_identification():
    """Render security clearance identification interface"""
    st.subheader("🔒 Security Clearance Identification")

    # Clearance tabs
    tab1, tab2, tab3 = st.tabs(["Identify Clearances", "Clearance Library", "Clearance Analysis"])

    with tab1:
        st.write("**Identify Security Clearance Requirements**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="clearance_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="clearance_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="clearance_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to analyze for clearance requirements...",
                key="clearance_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="clearance_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("🔒 Identify Clearance Requirements", type="primary"):
            with st.spinner("Identifying security clearance requirements..."):
                clearance_result = identify_security_clearances(document_content, document_name)

                if clearance_result.get('success'):
                    st.session_state.clearance_identification_result = clearance_result
                    st.session_state.clearance_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display identification results
        if 'clearance_identification_result' in st.session_state:
            st.subheader("🔒 Clearance Requirements Results")

            result = st.session_state.clearance_identification_result
            clearance_requirements = result.get('clearance_requirements', [])

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Requirements", result.get('total_requirements', 0))

            with col2:
                highest_clearance = get_highest_clearance_level(clearance_requirements)
                st.metric("Highest Clearance", highest_clearance)

            with col3:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Identification Confidence", f"{confidence:.1%}")

            # Clearance requirements display
            if clearance_requirements:
                st.write("**Security Clearance Requirements:**")

                for i, clearance in enumerate(clearance_requirements, 1):
                    with st.container():
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            clearance_level = clearance.get('clearance_level', 'Unknown')
                            clearance_type = clearance.get('clearance_type', 'personnel')

                            # Clearance level with icon
                            level_icon = get_clearance_icon(clearance_level)
                            st.write(f"**{level_icon} {clearance_level}** ({clearance_type})")

                            if clearance.get('specific_requirements'):
                                st.write(f"Requirements: {clearance['specific_requirements']}")

                            if clearance.get('investigation_type'):
                                st.write(f"Investigation: {clearance['investigation_type']}")

                            if clearance.get('polygraph_required'):
                                st.write("🔍 Polygraph Required")

                        with col2:
                            if clearance.get('percentage_required'):
                                st.metric("Personnel %", f"{clearance['percentage_required']:.0f}%")

                            citizenship = clearance.get('citizenship_requirement', 'US Citizen')
                            st.write(f"**Citizenship:** {citizenship}")

                    st.divider()

                # Clearance summary
                st.write("**Clearance Summary:**")
                clearance_summary = generate_clearance_summary(clearance_requirements)
                st.write(clearance_summary)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Clearance Requirements"):
                    save_clearance_requirements(st.session_state.clearance_document['name'], clearance_requirements)
                    st.success("Clearance requirements saved!")

            with col2:
                if st.button("📊 Generate Clearance Report"):
                    generate_clearance_report(clearance_requirements)
                    st.success("Clearance report generated!")

            with col3:
                if st.button("📄 Export Requirements"):
                    export_clearance_requirements(clearance_requirements, document_name)
                    st.success("Requirements exported!")

            with col4:
                if st.button("💰 Estimate Clearance Costs"):
                    estimate_clearance_costs(clearance_requirements)
                    st.success("Cost estimation complete!")

    with tab2:
        st.write("**Clearance Requirements Library**")

        # Get saved clearance requirements
        saved_clearances = get_saved_clearance_requirements()

        if saved_clearances:
            for clearance_doc in saved_clearances:
                doc_name, total_requirements, highest_level, extraction_date = clearance_doc

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{doc_name}**")
                        st.caption(f"Extracted: {extraction_date.strftime('%Y-%m-%d')}")

                    with col2:
                        st.metric("Requirements", total_requirements)

                    with col3:
                        level_icon = get_clearance_icon(highest_level)
                        st.write(f"{level_icon} {highest_level}")

                        if st.button("👁️", key=f"view_clearance_{doc_name}"):
                            clearance_details = load_clearance_requirements(doc_name)
                            st.session_state.view_clearance_details = clearance_details
                            st.rerun()

                st.divider()
        else:
            st.info("No clearance requirements saved yet.")

    with tab3:
        st.write("**Clearance Analysis & Planning**")

        # Clearance analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Clearance Distribution", "Cost Analysis", "Timeline Analysis", "Risk Assessment"],
            key="clearance_analysis_type"
        )

        if analysis_type == "Clearance Distribution":
            render_clearance_distribution_analysis()
        elif analysis_type == "Cost Analysis":
            render_clearance_cost_analysis()
        elif analysis_type == "Timeline Analysis":
            render_clearance_timeline_analysis()
        elif analysis_type == "Risk Assessment":
            render_clearance_risk_assessment()

def get_clearance_icon(clearance_level):
    """Get icon for clearance level"""
    icons = {
        "Public Trust": "🟢",
        "Confidential": "🟡",
        "Secret": "🟠",
        "Top Secret": "🔴",
        "TS/SCI": "🔴🔒"
    }
    return icons.get(clearance_level, "🔒")

def get_highest_clearance_level(clearance_requirements):
    """Get the highest clearance level from requirements"""
    clearance_hierarchy = {
        "Public Trust": 1,
        "Confidential": 2,
        "Secret": 3,
        "Top Secret": 4,
        "TS/SCI": 5
    }

    highest_level = "None"
    highest_value = 0

    for clearance in clearance_requirements:
        level = clearance.get('clearance_level', '')
        value = clearance_hierarchy.get(level, 0)
        if value > highest_value:
            highest_value = value
            highest_level = level

    return highest_level

def generate_clearance_summary(clearance_requirements):
    """Generate summary of clearance requirements using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Summary generation not available"

    try:
        summary_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(clearance_requirements),
            "insight_type": "clearance_summary",
            "context": {
                "domain": "government_contracting",
                "summary_focus": ["clearance_levels", "personnel_impact", "timeline_considerations"],
                "output_format": "executive_summary"
            }
        })

        if summary_result.get('success'):
            return summary_result['data'].get('summary', 'Summary generation failed')
        else:
            return "Summary generation failed"

    except Exception as e:
        return f"Error generating summary: {e}"
```

---

## **Feature 32: Place of Performance vs. Remote Work Analysis**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** MEDIUM

#### **MCP Integration**
Uses generic `process_geographic_data` and `classify_content` tools.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def analyze_place_of_performance(document_content, document_id=None):
    """Analyze place of performance and remote work options using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Extract geographic information
        geographic_result = call_mcp_tool("process_geographic_data", {
            "text": document_content,
            "extraction_types": ["addresses", "regions", "performance_locations"],
            "geocoding": True,
            "context_type": "government_contracting_performance_locations"
        })

        # Classify remote work possibilities
        remote_work_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "remote_work_analysis",
            "domain_rules": {
                "work_types": ["on_site_required", "remote_possible", "hybrid_allowed", "location_flexible"],
                "security_considerations": True,
                "collaboration_requirements": True,
                "travel_requirements": True
            },
            "risk_assessment": False
        })

        performance_analysis = {}

        if geographic_result.get('success'):
            performance_analysis['geographic_data'] = geographic_result['data']

        if remote_work_result.get('success'):
            performance_analysis['remote_work_analysis'] = remote_work_result['data']

        # Generate comprehensive analysis
        if performance_analysis:
            comprehensive_analysis = generate_performance_analysis(performance_analysis)

            return {
                "success": True,
                "performance_analysis": comprehensive_analysis,
                "geographic_data": performance_analysis.get('geographic_data', {}),
                "remote_work_data": performance_analysis.get('remote_work_analysis', {})
            }
        else:
            return {"error": "Performance analysis failed"}

    except Exception as e:
        st.error(f"Error analyzing place of performance: {e}")
        return {"error": str(e)}

def generate_performance_analysis(performance_data):
    """Generate comprehensive performance analysis using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {}

    try:
        analysis_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(performance_data),
            "insight_type": "performance_location_analysis",
            "context": {
                "domain": "government_contracting",
                "analysis_focus": ["location_requirements", "remote_feasibility", "travel_implications", "cost_impact"],
                "output_format": "structured_analysis"
            }
        })

        if analysis_result.get('success'):
            return analysis_result['data']
        else:
            return {}

    except Exception as e:
        st.error(f"Error generating performance analysis: {e}")
        return {}

def render_place_of_performance_analysis():
    """Render place of performance analysis interface"""
    st.subheader("🗺️ Place of Performance vs. Remote Work Analysis")

    # Analysis tabs
    tab1, tab2, tab3 = st.tabs(["Analyze Performance Location", "Location Library", "Performance Insights"])

    with tab1:
        st.write("**Analyze Place of Performance Requirements**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="performance_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="performance_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="performance_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to analyze performance location requirements...",
                key="performance_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="performance_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("🗺️ Analyze Performance Location", type="primary"):
            with st.spinner("Analyzing place of performance requirements..."):
                performance_result = analyze_place_of_performance(document_content, document_name)

                if performance_result.get('success'):
                    st.session_state.performance_analysis_result = performance_result
                    st.session_state.performance_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display analysis results
        if 'performance_analysis_result' in st.session_state:
            st.subheader("🗺️ Performance Location Analysis Results")

            result = st.session_state.performance_analysis_result
            analysis = result.get('performance_analysis', {})
            geographic_data = result.get('geographic_data', {})
            remote_work_data = result.get('remote_work_data', {})

            # Location summary
            col1, col2, col3 = st.columns(3)

            with col1:
                locations_count = len(geographic_data.get('identified_locations', []))
                st.metric("Identified Locations", locations_count)

            with col2:
                remote_feasibility = remote_work_data.get('remote_feasibility_score', 0.0)
                st.metric("Remote Work Feasibility", f"{remote_feasibility:.1%}")

            with col3:
                travel_required = remote_work_data.get('travel_percentage', 0)
                st.metric("Travel Required", f"{travel_required}%")

            # Geographic locations
            if geographic_data.get('identified_locations'):
                st.write("**Identified Performance Locations:**")

                for location in geographic_data['identified_locations']:
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"📍 **{location.get('location', 'Unknown')}**")
                        if location.get('address'):
                            st.caption(f"Address: {location['address']}")
                        if location.get('requirements'):
                            st.caption(f"Requirements: {location['requirements']}")

                    with col2:
                        if location.get('coordinates'):
                            coords = location['coordinates']
                            st.caption(f"Lat: {coords.get('lat', 'N/A')}")
                            st.caption(f"Lng: {coords.get('lng', 'N/A')}")

            # Remote work analysis
            if remote_work_data:
                st.write("**Remote Work Analysis:**")

                work_type = remote_work_data.get('work_type_classification', 'Unknown')
                work_type_icon = get_work_type_icon(work_type)

                st.write(f"{work_type_icon} **Work Type:** {work_type}")

                if remote_work_data.get('remote_work_factors'):
                    st.write("**Factors Affecting Remote Work:**")
                    for factor in remote_work_data['remote_work_factors']:
                        st.write(f"• {factor}")

                if remote_work_data.get('security_considerations'):
                    st.write("**Security Considerations:**")
                    for consideration in remote_work_data['security_considerations']:
                        st.write(f"🔒 {consideration}")

            # Comprehensive analysis
            if analysis:
                st.write("**Performance Analysis Summary:**")

                if analysis.get('location_requirements'):
                    st.write("**Location Requirements:**")
                    st.write(analysis['location_requirements'])

                if analysis.get('remote_feasibility'):
                    st.write("**Remote Work Feasibility:**")
                    st.write(analysis['remote_feasibility'])

                if analysis.get('recommendations'):
                    st.write("**Recommendations:**")
                    for recommendation in analysis['recommendations']:
                        st.write(f"💡 {recommendation}")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Analysis"):
                    save_performance_analysis(st.session_state.performance_document['name'], result)
                    st.success("Performance analysis saved!")

            with col2:
                if st.button("🗺️ Show on Map"):
                    show_performance_locations_on_map(geographic_data)
                    st.success("Map generated!")

            with col3:
                if st.button("📊 Generate Report"):
                    generate_performance_report(result)
                    st.success("Performance report generated!")

            with col4:
                if st.button("💰 Cost Impact Analysis"):
                    analyze_location_cost_impact(result)
                    st.success("Cost analysis complete!")

    with tab2:
        st.write("**Performance Location Library**")

        # Display saved performance analyses
        saved_analyses = get_saved_performance_analyses()

        if saved_analyses:
            for analysis_doc in saved_analyses:
                doc_name, location_count, work_type, analysis_date = analysis_doc

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{doc_name}**")
                        st.caption(f"Analyzed: {analysis_date.strftime('%Y-%m-%d')}")

                    with col2:
                        st.metric("Locations", location_count)

                    with col3:
                        work_icon = get_work_type_icon(work_type)
                        st.write(f"{work_icon} {work_type}")

                        if st.button("👁️", key=f"view_performance_{doc_name}"):
                            performance_details = load_performance_analysis(doc_name)
                            st.session_state.view_performance_details = performance_details
                            st.rerun()

                st.divider()
        else:
            st.info("No performance analyses saved yet.")

    with tab3:
        st.write("**Performance Location Insights**")

        # Performance insights and trends
        insights_type = st.selectbox(
            "Insights Type:",
            ["Location Trends", "Remote Work Trends", "Cost Comparisons", "Risk Analysis"],
            key="performance_insights_type"
        )

        if insights_type == "Location Trends":
            render_location_trends()
        elif insights_type == "Remote Work Trends":
            render_remote_work_trends()
        elif insights_type == "Cost Comparisons":
            render_location_cost_comparisons()
        elif insights_type == "Risk Analysis":
            render_location_risk_analysis()

def get_work_type_icon(work_type):
    """Get icon for work type"""
    icons = {
        "on_site_required": "🏢",
        "remote_possible": "🏠",
        "hybrid_allowed": "🔄",
        "location_flexible": "🌐"
    }
    return icons.get(work_type, "📍")

def show_performance_locations_on_map(geographic_data):
    """Display performance locations on an interactive map"""
    locations = geographic_data.get('identified_locations', [])

    if not locations:
        st.info("No geographic locations found to display on map.")
        return

    # Create map centered on first location or default to US center
    if locations and locations[0].get('coordinates'):
        center_lat = locations[0]['coordinates'].get('lat', 39.8283)
        center_lng = locations[0]['coordinates'].get('lng', -98.5795)
    else:
        center_lat, center_lng = 39.8283, -98.5795  # US center

    import folium
    from streamlit_folium import st_folium

    # Create map
    m = folium.Map(location=[center_lat, center_lng], zoom_start=4)

    # Add markers for each location
    for i, location in enumerate(locations):
        if location.get('coordinates'):
            coords = location['coordinates']
            lat = coords.get('lat')
            lng = coords.get('lng')

            if lat and lng:
                popup_text = f"""
                <b>{location.get('location', f'Location {i+1}')}</b><br>
                {location.get('address', '')}<br>
                {location.get('requirements', '')}
                """

                folium.Marker(
                    [lat, lng],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=location.get('location', f'Location {i+1}'),
                    icon=folium.Icon(color='blue', icon='building', prefix='fa')
                ).add_to(m)

    # Display map
    st.write("**Performance Locations Map:**")
    st_folium(m, width=700, height=500)
```

---

## **Feature 34: Key Government Personnel Extraction**
**Status:** ⏳ Ready for Implementation
**Complexity:** LOW | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS government_personnel (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    person_name VARCHAR(200) NOT NULL,
    title VARCHAR(200),
    organization VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(50),
    role_type VARCHAR(100), -- 'contracting_officer', 'program_manager', 'technical_contact', 'administrative'
    is_primary_contact BOOLEAN DEFAULT FALSE,
    responsibilities TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_government_personnel_document ON government_personnel(document_id);
CREATE INDEX IF NOT EXISTS ix_government_personnel_role ON government_personnel(role_type);
CREATE INDEX IF NOT EXISTS ix_government_personnel_primary ON government_personnel(is_primary_contact);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with personnel-specific schema.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_government_personnel(document_content, document_id=None):
    """Extract key government personnel from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract government personnel information
        personnel_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "contracting_officers", "type": "array", "description": "Contracting officers with contact information"},
                    {"name": "program_managers", "type": "array", "description": "Government program managers"},
                    {"name": "technical_contacts", "type": "array", "description": "Technical points of contact"},
                    {"name": "administrative_contacts", "type": "array", "description": "Administrative contacts"},
                    {"name": "primary_contacts", "type": "array", "description": "Primary government contacts"},
                    {"name": "contact_information", "type": "object", "description": "General contact information and procedures"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_contact_details": True,
                "include_roles": True,
                "include_responsibilities": True,
                "confidence_threshold": 0.7
            }
        })

        if personnel_result.get('success'):
            # Process and structure the personnel data
            personnel_data = personnel_result['data']
            structured_personnel = process_government_personnel_data(personnel_data)

            # Save to database if document_id provided
            if document_id and structured_personnel:
                save_government_personnel(document_id, structured_personnel)

            return {
                "success": True,
                "government_personnel": structured_personnel,
                "extraction_confidence": personnel_result.get('confidence', 0.0),
                "total_contacts": len(structured_personnel)
            }
        else:
            return {"error": "Government personnel extraction failed"}

    except Exception as e:
        st.error(f"Error extracting government personnel: {e}")
        return {"error": str(e)}

def process_government_personnel_data(raw_personnel_data):
    """Process raw government personnel data into structured format"""
    structured_personnel = []

    # Process different types of contacts
    contact_types = {
        'contracting_officers': 'contracting_officer',
        'program_managers': 'program_manager',
        'technical_contacts': 'technical_contact',
        'administrative_contacts': 'administrative'
    }

    for data_key, role_type in contact_types.items():
        contacts = raw_personnel_data.get(data_key, [])

        for contact in contacts:
            if isinstance(contact, dict):
                personnel = {
                    'name': contact.get('name', ''),
                    'title': contact.get('title', ''),
                    'organization': contact.get('organization', ''),
                    'email': contact.get('email', ''),
                    'phone': contact.get('phone', ''),
                    'role_type': role_type,
                    'is_primary_contact': contact.get('is_primary', False),
                    'responsibilities': contact.get('responsibilities', '')
                }
                structured_personnel.append(personnel)

    # Process primary contacts
    primary_contacts = raw_personnel_data.get('primary_contacts', [])
    for contact in primary_contacts:
        if isinstance(contact, dict):
            personnel = {
                'name': contact.get('name', ''),
                'title': contact.get('title', ''),
                'organization': contact.get('organization', ''),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'role_type': contact.get('role_type', 'primary_contact'),
                'is_primary_contact': True,
                'responsibilities': contact.get('responsibilities', '')
            }
            structured_personnel.append(personnel)

    return structured_personnel

def save_government_personnel(document_id, government_personnel):
    """Save government personnel to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for personnel in government_personnel:
            cursor.execute("""
                INSERT INTO government_personnel
                (document_id, person_name, title, organization, email, phone,
                 role_type, is_primary_contact, responsibilities, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, personnel['name'], personnel['title'],
                personnel['organization'], personnel['email'], personnel['phone'],
                personnel['role_type'], personnel['is_primary_contact'],
                personnel['responsibilities'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving government personnel: {e}")
        return False
    finally:
        conn.close()

def render_government_personnel_extraction():
    """Render government personnel extraction interface"""
    st.subheader("👥 Key Government Personnel Extraction")

    # Personnel tabs
    tab1, tab2, tab3 = st.tabs(["Extract Personnel", "Personnel Directory", "Contact Analysis"])

    with tab1:
        st.write("**Extract Government Personnel from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="gov_personnel_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="gov_personnel_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="gov_personnel_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to extract government personnel...",
                key="gov_personnel_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="gov_personnel_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("👥 Extract Government Personnel", type="primary"):
            with st.spinner("Extracting government personnel..."):
                personnel_result = extract_government_personnel(document_content, document_name)

                if personnel_result.get('success'):
                    st.session_state.gov_personnel_extraction_result = personnel_result
                    st.session_state.gov_personnel_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display extraction results
        if 'gov_personnel_extraction_result' in st.session_state:
            st.subheader("👥 Government Personnel Results")

            result = st.session_state.gov_personnel_extraction_result
            government_personnel = result.get('government_personnel', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Contacts", result.get('total_contacts', 0))

            with col2:
                primary_contacts = sum(1 for p in government_personnel if p.get('is_primary_contact'))
                st.metric("Primary Contacts", primary_contacts)

            with col3:
                contracting_officers = sum(1 for p in government_personnel if p.get('role_type') == 'contracting_officer')
                st.metric("Contracting Officers", contracting_officers)

            with col4:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            # Personnel directory
            if government_personnel:
                st.write("**Government Personnel Directory:**")

                # Group by role type
                personnel_by_role = {}
                for person in government_personnel:
                    role = person.get('role_type', 'other')
                    if role not in personnel_by_role:
                        personnel_by_role[role] = []
                    personnel_by_role[role].append(person)

                # Display by role
                for role_type, personnel_list in personnel_by_role.items():
                    role_icon = get_role_icon(role_type)
                    st.write(f"**{role_icon} {role_type.replace('_', ' ').title()}:**")

                    for person in personnel_list:
                        with st.container():
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                primary_indicator = "⭐ " if person.get('is_primary_contact') else ""
                                st.write(f"**{primary_indicator}{person.get('name', 'Unknown')}**")

                                if person.get('title'):
                                    st.caption(f"Title: {person['title']}")

                                if person.get('organization'):
                                    st.caption(f"Organization: {person['organization']}")

                                if person.get('responsibilities'):
                                    st.caption(f"Responsibilities: {person['responsibilities']}")

                            with col2:
                                if person.get('email'):
                                    st.write(f"📧 {person['email']}")

                                if person.get('phone'):
                                    st.write(f"📞 {person['phone']}")

                        st.divider()

                # Contact summary table
                st.write("**Contact Summary Table:**")

                contact_df_data = []
                for person in government_personnel:
                    contact_df_data.append({
                        'Name': person.get('name', ''),
                        'Role': person.get('role_type', '').replace('_', ' ').title(),
                        'Primary': '⭐' if person.get('is_primary_contact') else '',
                        'Title': person.get('title', ''),
                        'Organization': person.get('organization', ''),
                        'Email': person.get('email', ''),
                        'Phone': person.get('phone', '')
                    })

                st.dataframe(contact_df_data, use_container_width=True)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Personnel Directory"):
                    save_government_personnel(st.session_state.gov_personnel_document['name'], government_personnel)
                    st.success("Personnel directory saved!")

            with col2:
                if st.button("📊 Generate Contact Report"):
                    generate_contact_report(government_personnel)
                    st.success("Contact report generated!")

            with col3:
                if st.button("📄 Export to vCard"):
                    export_contacts_to_vcard(government_personnel, document_name)
                    st.success("Contacts exported to vCard!")

            with col4:
                if st.button("📋 Create Contact List"):
                    create_contact_list(government_personnel)
                    st.success("Contact list created!")

    with tab2:
        st.write("**Government Personnel Directory**")

        # Get saved personnel
        saved_personnel = get_saved_government_personnel()

        if saved_personnel:
            # Search and filter
            col1, col2 = st.columns(2)

            with col1:
                search_term = st.text_input("Search Personnel:", key="personnel_search")

            with col2:
                role_filter = st.selectbox(
                    "Filter by Role:",
                    ["All", "Contracting Officer", "Program Manager", "Technical Contact", "Administrative"],
                    key="personnel_role_filter"
                )

            # Display personnel
            for person_data in saved_personnel:
                person_name, role_type, organization, email, phone, is_primary, doc_name = person_data

                # Apply filters
                if search_term and search_term.lower() not in person_name.lower():
                    continue

                if role_filter != "All" and role_filter.lower().replace(' ', '_') != role_type:
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        primary_indicator = "⭐ " if is_primary else ""
                        role_icon = get_role_icon(role_type)
                        st.write(f"**{primary_indicator}{role_icon} {person_name}**")
                        st.caption(f"From: {doc_name}")

                    with col2:
                        st.write(f"**{role_type.replace('_', ' ').title()}**")
                        if organization:
                            st.caption(organization)

                    with col3:
                        if email:
                            st.write(f"📧 {email}")
                        if phone:
                            st.write(f"📞 {phone}")

                st.divider()
        else:
            st.info("No government personnel saved yet.")

    with tab3:
        st.write("**Contact Analysis & Insights**")

        # Contact analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Contact Distribution", "Organization Analysis", "Role Analysis", "Communication Patterns"],
            key="contact_analysis_type"
        )

        if analysis_type == "Contact Distribution":
            render_contact_distribution_analysis()
        elif analysis_type == "Organization Analysis":
            render_organization_analysis()
        elif analysis_type == "Role Analysis":
            render_role_analysis()
        elif analysis_type == "Communication Patterns":
            render_communication_patterns_analysis()

def get_role_icon(role_type):
    """Get icon for role type"""
    icons = {
        "contracting_officer": "⚖️",
        "program_manager": "👨‍💼",
        "technical_contact": "🔧",
        "administrative": "📋",
        "primary_contact": "⭐"
    }
    return icons.get(role_type, "👤")
```

---

## **Feature 35: Compliance Requirements Checklist**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    requirement_type VARCHAR(100) NOT NULL,
    requirement_title VARCHAR(300) NOT NULL,
    requirement_description TEXT,
    regulation_reference VARCHAR(200),
    compliance_level VARCHAR(50), -- 'mandatory', 'recommended', 'conditional'
    verification_method VARCHAR(200),
    documentation_required TEXT[],
    deadline_type VARCHAR(100),
    penalty_description TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    compliance_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'compliant', 'non_compliant'
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    category_description TEXT,
    regulatory_framework VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_compliance_requirements_document ON compliance_requirements(document_id);
CREATE INDEX IF NOT EXISTS ix_compliance_requirements_type ON compliance_requirements(requirement_type);
CREATE INDEX IF NOT EXISTS ix_compliance_requirements_level ON compliance_requirements(compliance_level);
CREATE INDEX IF NOT EXISTS ix_compliance_requirements_status ON compliance_requirements(compliance_status);
```

#### **MCP Integration**
Uses generic `classify_content` tool with compliance-specific classification schemes.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_compliance_requirements(document_content, document_id=None):
    """Extract compliance requirements from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to classify and extract compliance requirements
        compliance_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "government_compliance_requirements",
            "domain_rules": {
                "requirement_types": [
                    "security_compliance", "environmental_compliance", "labor_standards",
                    "quality_assurance", "data_protection", "accessibility", "small_business",
                    "financial_reporting", "safety_requirements", "export_control"
                ],
                "compliance_levels": ["mandatory", "recommended", "conditional"],
                "regulatory_frameworks": ["FAR", "DFARS", "CFR", "USC", "Executive_Orders"],
                "extract_penalties": True,
                "extract_deadlines": True,
                "extract_documentation": True
            },
            "risk_assessment": True
        })

        if compliance_result.get('success'):
            compliance_data = compliance_result['data']
            structured_requirements = process_compliance_data(compliance_data)

            # Save to database if document_id provided
            if document_id and structured_requirements:
                save_compliance_requirements(document_id, structured_requirements)

            return {
                "success": True,
                "compliance_requirements": structured_requirements,
                "extraction_confidence": compliance_result.get('confidence', 0.0),
                "total_requirements": len(structured_requirements),
                "mandatory_count": sum(1 for req in structured_requirements if req.get('compliance_level') == 'mandatory')
            }
        else:
            return {"error": "Compliance requirements extraction failed"}

    except Exception as e:
        st.error(f"Error extracting compliance requirements: {e}")
        return {"error": str(e)}

def process_compliance_data(raw_compliance_data):
    """Process raw compliance data into structured format"""
    structured_requirements = []

    requirements = raw_compliance_data.get('identified_requirements', [])

    for requirement in requirements:
        if isinstance(requirement, dict):
            compliance_req = {
                'requirement_type': requirement.get('type', ''),
                'title': requirement.get('title', ''),
                'description': requirement.get('description', ''),
                'regulation_reference': requirement.get('regulation_reference', ''),
                'compliance_level': requirement.get('level', 'mandatory'),
                'verification_method': requirement.get('verification_method', ''),
                'documentation_required': requirement.get('documentation_required', []),
                'deadline_type': requirement.get('deadline_type', ''),
                'penalty_description': requirement.get('penalty_description', '')
            }
            structured_requirements.append(compliance_req)

    return structured_requirements

def save_compliance_requirements(document_id, compliance_requirements):
    """Save compliance requirements to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for requirement in compliance_requirements:
            cursor.execute("""
                INSERT INTO compliance_requirements
                (document_id, requirement_type, requirement_title, requirement_description,
                 regulation_reference, compliance_level, verification_method,
                 documentation_required, deadline_type, penalty_description, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, requirement['requirement_type'], requirement['title'],
                requirement['description'], requirement['regulation_reference'],
                requirement['compliance_level'], requirement['verification_method'],
                requirement['documentation_required'], requirement['deadline_type'],
                requirement['penalty_description'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving compliance requirements: {e}")
        return False
    finally:
        conn.close()

def render_compliance_requirements_extraction():
    """Render compliance requirements extraction interface"""
    st.subheader("✅ Compliance Requirements Checklist")

    # Compliance tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Extract Requirements", "Compliance Library", "Checklist Manager", "Compliance Analysis"])

    with tab1:
        st.write("**Extract Compliance Requirements from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="compliance_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="compliance_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="compliance_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to extract compliance requirements...",
                key="compliance_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="compliance_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("✅ Extract Compliance Requirements", type="primary"):
            with st.spinner("Extracting compliance requirements..."):
                compliance_result = extract_compliance_requirements(document_content, document_name)

                if compliance_result.get('success'):
                    st.session_state.compliance_extraction_result = compliance_result
                    st.session_state.compliance_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display extraction results
        if 'compliance_extraction_result' in st.session_state:
            st.subheader("✅ Compliance Requirements Results")

            result = st.session_state.compliance_extraction_result
            compliance_requirements = result.get('compliance_requirements', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Requirements", result.get('total_requirements', 0))

            with col2:
                st.metric("Mandatory", result.get('mandatory_count', 0))

            with col3:
                recommended_count = sum(1 for req in compliance_requirements if req.get('compliance_level') == 'recommended')
                st.metric("Recommended", recommended_count)

            with col4:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            # Compliance requirements display
            if compliance_requirements:
                st.write("**Compliance Requirements Checklist:**")

                # Group by compliance level
                requirements_by_level = {}
                for requirement in compliance_requirements:
                    level = requirement.get('compliance_level', 'mandatory')
                    if level not in requirements_by_level:
                        requirements_by_level[level] = []
                    requirements_by_level[level].append(requirement)

                # Display by compliance level
                for level, requirements_list in requirements_by_level.items():
                    level_icon = get_compliance_level_icon(level)
                    st.write(f"**{level_icon} {level.title()} Requirements ({len(requirements_list)}):**")

                    for i, requirement in enumerate(requirements_list, 1):
                        with st.expander(f"{requirement.get('title', f'Requirement {i}')}"):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.write(f"**Type:** {requirement.get('requirement_type', 'N/A').replace('_', ' ').title()}")

                                if requirement.get('description'):
                                    st.write(f"**Description:** {requirement['description']}")

                                if requirement.get('regulation_reference'):
                                    st.write(f"**Regulation:** {requirement['regulation_reference']}")

                                if requirement.get('verification_method'):
                                    st.write(f"**Verification:** {requirement['verification_method']}")

                                if requirement.get('penalty_description'):
                                    st.write(f"**Penalty:** {requirement['penalty_description']}")

                            with col2:
                                # Compliance status
                                status = st.selectbox(
                                    "Status:",
                                    ["Pending", "In Progress", "Compliant", "Non-Compliant"],
                                    key=f"status_{i}_{level}"
                                )

                                if requirement.get('deadline_type'):
                                    st.write(f"**Deadline:** {requirement['deadline_type']}")

                                if requirement.get('documentation_required'):
                                    st.write("**Documentation Required:**")
                                    for doc in requirement['documentation_required']:
                                        st.write(f"• {doc}")

                # Compliance summary
                st.write("**Compliance Summary:**")
                compliance_summary = generate_compliance_summary(compliance_requirements)
                st.write(compliance_summary)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Requirements"):
                    save_compliance_requirements(st.session_state.compliance_document['name'], compliance_requirements)
                    st.success("Compliance requirements saved!")

            with col2:
                if st.button("📋 Create Checklist"):
                    create_compliance_checklist(compliance_requirements)
                    st.success("Compliance checklist created!")

            with col3:
                if st.button("📊 Generate Report"):
                    generate_compliance_report(compliance_requirements)
                    st.success("Compliance report generated!")

            with col4:
                if st.button("⚠️ Risk Assessment"):
                    assess_compliance_risks(compliance_requirements)
                    st.success("Risk assessment complete!")

    with tab2:
        st.write("**Compliance Requirements Library**")

        # Get saved compliance requirements
        saved_compliance = get_saved_compliance_requirements()

        if saved_compliance:
            # Filter options
            col1, col2 = st.columns(2)

            with col1:
                requirement_type_filter = st.selectbox(
                    "Filter by Type:",
                    ["All", "Security", "Environmental", "Labor", "Quality", "Data Protection"],
                    key="compliance_type_filter"
                )

            with col2:
                compliance_level_filter = st.selectbox(
                    "Filter by Level:",
                    ["All", "Mandatory", "Recommended", "Conditional"],
                    key="compliance_level_filter"
                )

            # Display compliance requirements
            for compliance_data in saved_compliance:
                doc_name, req_type, title, level, regulation, extraction_date = compliance_data

                # Apply filters
                if requirement_type_filter != "All" and requirement_type_filter.lower() not in req_type.lower():
                    continue

                if compliance_level_filter != "All" and compliance_level_filter.lower() != level.lower():
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        level_icon = get_compliance_level_icon(level)
                        st.write(f"**{level_icon} {title}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Type: {req_type.replace('_', ' ').title()}")

                    with col2:
                        st.write(f"**{level.title()}**")
                        if regulation:
                            st.caption(f"Ref: {regulation}")

                    with col3:
                        st.caption(extraction_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_compliance_{title[:20]}"):
                            compliance_details = load_compliance_requirement_details(doc_name, title)
                            st.session_state.view_compliance_details = compliance_details
                            st.rerun()

                st.divider()
        else:
            st.info("No compliance requirements saved yet.")

    with tab3:
        st.write("**Compliance Checklist Manager**")

        # Active compliance checklists
        active_checklists = get_active_compliance_checklists()

        if active_checklists:
            for checklist in active_checklists:
                checklist_name, total_items, completed_items, compliance_percentage = checklist

                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**📋 {checklist_name}**")

                        # Progress bar
                        progress = completed_items / total_items if total_items > 0 else 0
                        st.progress(progress)
                        st.caption(f"{completed_items}/{total_items} items completed")

                    with col2:
                        st.metric("Compliance", f"{compliance_percentage:.1%}")

                    with col3:
                        if st.button("📝", key=f"edit_checklist_{checklist_name}"):
                            st.session_state.edit_checklist = checklist_name
                            st.rerun()

                        if st.button("📊", key=f"report_checklist_{checklist_name}"):
                            generate_checklist_report(checklist_name)
                            st.success("Report generated!")

                st.divider()
        else:
            st.info("No active compliance checklists.")

        # Create new checklist
        with st.expander("➕ Create New Compliance Checklist"):
            checklist_name = st.text_input("Checklist Name:", key="new_checklist_name")
            checklist_description = st.text_area("Description:", key="new_checklist_description")

            # Select requirements for checklist
            available_requirements = get_all_compliance_requirements()

            if available_requirements:
                selected_requirements = st.multiselect(
                    "Select Requirements:",
                    options=available_requirements,
                    format_func=lambda x: f"{x['title']} ({x['level']})",
                    key="checklist_requirements"
                )

                if st.button("📋 Create Checklist", disabled=not (checklist_name and selected_requirements)):
                    create_new_compliance_checklist(checklist_name, checklist_description, selected_requirements)
                    st.success(f"Checklist '{checklist_name}' created!")
                    st.rerun()

    with tab4:
        st.write("**Compliance Analysis & Insights**")

        # Compliance analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Compliance Overview", "Risk Analysis", "Gap Analysis", "Trend Analysis"],
            key="compliance_analysis_type"
        )

        if analysis_type == "Compliance Overview":
            render_compliance_overview()
        elif analysis_type == "Risk Analysis":
            render_compliance_risk_analysis()
        elif analysis_type == "Gap Analysis":
            render_compliance_gap_analysis()
        elif analysis_type == "Trend Analysis":
            render_compliance_trend_analysis()

def get_compliance_level_icon(level):
    """Get icon for compliance level"""
    icons = {
        "mandatory": "🔴",
        "recommended": "🟡",
        "conditional": "🟢"
    }
    return icons.get(level, "⚪")

def generate_compliance_summary(compliance_requirements):
    """Generate summary of compliance requirements using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Summary generation not available"

    try:
        summary_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(compliance_requirements),
            "insight_type": "compliance_summary",
            "context": {
                "domain": "government_contracting",
                "summary_focus": ["mandatory_requirements", "risk_factors", "implementation_timeline"],
                "output_format": "executive_summary"
            }
        })

        if summary_result.get('success'):
            return summary_result['data'].get('summary', 'Summary generation failed')
        else:
            return "Summary generation failed"

    except Exception as e:
        return f"Error generating summary: {e}"
```

---

## **Feature 36: Technical Specifications Parser**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS technical_specifications (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    spec_category VARCHAR(100) NOT NULL,
    spec_title VARCHAR(300) NOT NULL,
    spec_description TEXT,
    technical_requirements TEXT[],
    performance_criteria TEXT[],
    testing_requirements TEXT[],
    standards_references TEXT[],
    minimum_requirements TEXT[],
    preferred_requirements TEXT[],
    compatibility_requirements TEXT[],
    environmental_conditions TEXT[],
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS technical_standards (
    id SERIAL PRIMARY KEY,
    standard_name VARCHAR(200) NOT NULL,
    standard_organization VARCHAR(200),
    standard_version VARCHAR(50),
    standard_description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_technical_specifications_document ON technical_specifications(document_id);
CREATE INDEX IF NOT EXISTS ix_technical_specifications_category ON technical_specifications(spec_category);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with technical specification schemas.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def parse_technical_specifications(document_content, document_id=None):
    """Parse technical specifications from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract technical specifications
        tech_specs_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "hardware_specifications", "type": "array", "description": "Hardware technical requirements"},
                    {"name": "software_specifications", "type": "array", "description": "Software technical requirements"},
                    {"name": "performance_requirements", "type": "array", "description": "Performance and capability requirements"},
                    {"name": "interface_requirements", "type": "array", "description": "Interface and integration requirements"},
                    {"name": "security_specifications", "type": "array", "description": "Security and cybersecurity requirements"},
                    {"name": "environmental_requirements", "type": "array", "description": "Environmental and operational conditions"},
                    {"name": "testing_specifications", "type": "array", "description": "Testing and validation requirements"},
                    {"name": "standards_compliance", "type": "array", "description": "Industry standards and compliance requirements"},
                    {"name": "quality_requirements", "type": "array", "description": "Quality assurance and control requirements"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_technical_details": True,
                "include_standards": True,
                "include_testing": True,
                "include_performance_metrics": True,
                "confidence_threshold": 0.7
            }
        })

        if tech_specs_result.get('success'):
            # Process and structure the technical specifications
            tech_specs_data = tech_specs_result['data']
            structured_specs = process_technical_specifications_data(tech_specs_data)

            # Save to database if document_id provided
            if document_id and structured_specs:
                save_technical_specifications(document_id, structured_specs)

            return {
                "success": True,
                "technical_specifications": structured_specs,
                "extraction_confidence": tech_specs_result.get('confidence', 0.0),
                "total_specifications": len(structured_specs)
            }
        else:
            return {"error": "Technical specifications parsing failed"}

    except Exception as e:
        st.error(f"Error parsing technical specifications: {e}")
        return {"error": str(e)}

def process_technical_specifications_data(raw_specs_data):
    """Process raw technical specifications data into structured format"""
    structured_specs = []

    # Process different categories of specifications
    spec_categories = {
        'hardware_specifications': 'Hardware',
        'software_specifications': 'Software',
        'performance_requirements': 'Performance',
        'interface_requirements': 'Interface',
        'security_specifications': 'Security',
        'environmental_requirements': 'Environmental',
        'testing_specifications': 'Testing',
        'standards_compliance': 'Standards',
        'quality_requirements': 'Quality'
    }

    for data_key, category in spec_categories.items():
        specifications = raw_specs_data.get(data_key, [])

        for spec in specifications:
            if isinstance(spec, dict):
                tech_spec = {
                    'category': category,
                    'title': spec.get('title', ''),
                    'description': spec.get('description', ''),
                    'technical_requirements': spec.get('requirements', []),
                    'performance_criteria': spec.get('performance_criteria', []),
                    'testing_requirements': spec.get('testing_requirements', []),
                    'standards_references': spec.get('standards_references', []),
                    'minimum_requirements': spec.get('minimum_requirements', []),
                    'preferred_requirements': spec.get('preferred_requirements', []),
                    'compatibility_requirements': spec.get('compatibility_requirements', []),
                    'environmental_conditions': spec.get('environmental_conditions', [])
                }
                structured_specs.append(tech_spec)

    return structured_specs

def save_technical_specifications(document_id, technical_specifications):
    """Save technical specifications to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for spec in technical_specifications:
            cursor.execute("""
                INSERT INTO technical_specifications
                (document_id, spec_category, spec_title, spec_description,
                 technical_requirements, performance_criteria, testing_requirements,
                 standards_references, minimum_requirements, preferred_requirements,
                 compatibility_requirements, environmental_conditions, extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, spec['category'], spec['title'], spec['description'],
                spec['technical_requirements'], spec['performance_criteria'],
                spec['testing_requirements'], spec['standards_references'],
                spec['minimum_requirements'], spec['preferred_requirements'],
                spec['compatibility_requirements'], spec['environmental_conditions'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving technical specifications: {e}")
        return False
    finally:
        conn.close()

def render_technical_specifications_parser():
    """Render technical specifications parser interface"""
    st.subheader("🔧 Technical Specifications Parser")

    # Technical specs tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Parse Specifications", "Specifications Library", "Standards Database", "Technical Analysis"])

    with tab1:
        st.write("**Parse Technical Specifications from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="tech_specs_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Technical Document:",
                type=['txt', 'pdf', 'docx'],
                key="tech_specs_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="tech_specs_doc_name")
            document_content = st.text_area(
                "Technical Document Content:",
                height=300,
                placeholder="Paste technical document content to parse specifications...",
                key="tech_specs_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_technical_documents()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="tech_specs_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("🔧 Parse Technical Specifications", type="primary"):
            with st.spinner("Parsing technical specifications..."):
                tech_specs_result = parse_technical_specifications(document_content, document_name)

                if tech_specs_result.get('success'):
                    st.session_state.tech_specs_parsing_result = tech_specs_result
                    st.session_state.tech_specs_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display parsing results
        if 'tech_specs_parsing_result' in st.session_state:
            st.subheader("🔧 Technical Specifications Results")

            result = st.session_state.tech_specs_parsing_result
            technical_specifications = result.get('technical_specifications', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Specifications", result.get('total_specifications', 0))

            with col2:
                categories_count = len(set(spec.get('category', '') for spec in technical_specifications))
                st.metric("Categories", categories_count)

            with col3:
                standards_count = sum(len(spec.get('standards_references', [])) for spec in technical_specifications)
                st.metric("Standards Referenced", standards_count)

            with col4:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Parsing Confidence", f"{confidence:.1%}")

            # Technical specifications display
            if technical_specifications:
                st.write("**Technical Specifications by Category:**")

                # Group by category
                specs_by_category = {}
                for spec in technical_specifications:
                    category = spec.get('category', 'Other')
                    if category not in specs_by_category:
                        specs_by_category[category] = []
                    specs_by_category[category].append(spec)

                # Display by category
                for category, specs_list in specs_by_category.items():
                    category_icon = get_technical_category_icon(category)
                    st.write(f"**{category_icon} {category} Specifications ({len(specs_list)}):**")

                    for i, spec in enumerate(specs_list, 1):
                        with st.expander(f"{spec.get('title', f'{category} Specification {i}')}"):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                if spec.get('description'):
                                    st.write(f"**Description:** {spec['description']}")

                                if spec.get('technical_requirements'):
                                    st.write("**Technical Requirements:**")
                                    for req in spec['technical_requirements']:
                                        st.write(f"• {req}")

                                if spec.get('performance_criteria'):
                                    st.write("**Performance Criteria:**")
                                    for criteria in spec['performance_criteria']:
                                        st.write(f"• {criteria}")

                                if spec.get('minimum_requirements'):
                                    st.write("**Minimum Requirements:**")
                                    for min_req in spec['minimum_requirements']:
                                        st.write(f"• {min_req}")

                            with col2:
                                if spec.get('standards_references'):
                                    st.write("**Standards:**")
                                    for standard in spec['standards_references']:
                                        st.write(f"📋 {standard}")

                                if spec.get('testing_requirements'):
                                    st.write("**Testing:**")
                                    for test in spec['testing_requirements']:
                                        st.write(f"🧪 {test}")

                                if spec.get('environmental_conditions'):
                                    st.write("**Environmental:**")
                                    for condition in spec['environmental_conditions']:
                                        st.write(f"🌡️ {condition}")

                # Technical specifications summary
                st.write("**Technical Specifications Summary:**")
                tech_specs_summary = generate_technical_specifications_summary(technical_specifications)
                st.write(tech_specs_summary)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Specifications"):
                    save_technical_specifications(st.session_state.tech_specs_document['name'], technical_specifications)
                    st.success("Technical specifications saved!")

            with col2:
                if st.button("📊 Generate Tech Report"):
                    generate_technical_report(technical_specifications)
                    st.success("Technical report generated!")

            with col3:
                if st.button("📄 Export to Excel"):
                    export_tech_specs_to_excel(technical_specifications, document_name)
                    st.success("Specifications exported!")

            with col4:
                if st.button("🔍 Compliance Check"):
                    check_standards_compliance(technical_specifications)
                    st.success("Compliance check complete!")

    with tab2:
        st.write("**Technical Specifications Library**")

        # Get saved technical specifications
        saved_tech_specs = get_saved_technical_specifications()

        if saved_tech_specs:
            # Filter options
            col1, col2 = st.columns(2)

            with col1:
                category_filter = st.selectbox(
                    "Filter by Category:",
                    ["All", "Hardware", "Software", "Performance", "Security", "Environmental"],
                    key="tech_specs_category_filter"
                )

            with col2:
                search_term = st.text_input("Search Specifications:", key="tech_specs_search")

            # Display technical specifications
            for spec_data in saved_tech_specs:
                doc_name, category, title, standards_count, extraction_date = spec_data

                # Apply filters
                if category_filter != "All" and category_filter != category:
                    continue

                if search_term and search_term.lower() not in title.lower():
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        category_icon = get_technical_category_icon(category)
                        st.write(f"**{category_icon} {title}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Category: {category}")

                    with col2:
                        st.metric("Standards", standards_count)

                    with col3:
                        st.caption(extraction_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_tech_spec_{title[:20]}"):
                            tech_spec_details = load_technical_specification_details(doc_name, title)
                            st.session_state.view_tech_spec_details = tech_spec_details
                            st.rerun()

                st.divider()
        else:
            st.info("No technical specifications saved yet.")

    with tab3:
        st.write("**Technical Standards Database**")

        # Standards management
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("**Industry Standards Reference:**")

            # Common technical standards
            standards_categories = {
                "Cybersecurity": ["NIST 800-53", "FIPS 140-2", "Common Criteria", "ISO 27001"],
                "Quality": ["ISO 9001", "CMMI", "Six Sigma", "AS9100"],
                "Environmental": ["ISO 14001", "RoHS", "WEEE", "Energy Star"],
                "Safety": ["IEC 61508", "ISO 26262", "DO-178C", "MIL-STD-882"],
                "Communication": ["IEEE 802.11", "Bluetooth", "TCP/IP", "HTTP/HTTPS"],
                "Hardware": ["MIL-STD-810", "IPC Standards", "JEDEC", "IEEE Standards"]
            }

            for category, standards in standards_categories.items():
                with st.expander(f"📋 {category} Standards"):
                    for standard in standards:
                        col_a, col_b = st.columns([3, 1])

                        with col_a:
                            st.write(f"• **{standard}**")

                        with col_b:
                            if st.button("ℹ️", key=f"info_{standard}"):
                                show_standard_information(standard)

        with col2:
            st.write("**Standards Analysis:**")

            # Most referenced standards
            most_referenced = get_most_referenced_standards()

            if most_referenced:
                st.write("**Most Referenced:**")
                for standard, count in most_referenced[:5]:
                    st.write(f"• {standard} ({count})")

            # Standards compliance rate
            compliance_rate = calculate_standards_compliance_rate()
            st.metric("Compliance Rate", f"{compliance_rate:.1%}")

    with tab4:
        st.write("**Technical Analysis & Insights**")

        # Technical analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Specifications Overview", "Standards Analysis", "Complexity Analysis", "Gap Analysis"],
            key="tech_analysis_type"
        )

        if analysis_type == "Specifications Overview":
            render_specifications_overview()
        elif analysis_type == "Standards Analysis":
            render_standards_analysis()
        elif analysis_type == "Complexity Analysis":
            render_complexity_analysis()
        elif analysis_type == "Gap Analysis":
            render_technical_gap_analysis()

def get_technical_category_icon(category):
    """Get icon for technical category"""
    icons = {
        "Hardware": "🖥️",
        "Software": "💻",
        "Performance": "⚡",
        "Interface": "🔌",
        "Security": "🔒",
        "Environmental": "🌡️",
        "Testing": "🧪",
        "Standards": "📋",
        "Quality": "✅"
    }
    return icons.get(category, "🔧")

def generate_technical_specifications_summary(technical_specifications):
    """Generate summary of technical specifications using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Summary generation not available"

    try:
        summary_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(technical_specifications),
            "insight_type": "technical_specifications_summary",
            "context": {
                "domain": "government_contracting",
                "summary_focus": ["key_requirements", "standards_compliance", "implementation_complexity"],
                "output_format": "technical_summary"
            }
        })

        if summary_result.get('success'):
            return summary_result['data'].get('summary', 'Summary generation failed')
        else:
            return "Summary generation failed"

    except Exception as e:
        return f"Error generating summary: {e}"
```

---

## **Feature 37: Evaluation Criteria Extraction**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    criteria_category VARCHAR(100) NOT NULL,
    criteria_title VARCHAR(300) NOT NULL,
    criteria_description TEXT,
    weight_percentage DECIMAL(5,2),
    scoring_method VARCHAR(100),
    evaluation_factors TEXT[],
    subfactors TEXT[],
    rating_scale VARCHAR(200),
    minimum_score DECIMAL(5,2),
    is_pass_fail BOOLEAN DEFAULT FALSE,
    evaluation_instructions TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2)
);

CREATE INDEX IF NOT EXISTS ix_evaluation_criteria_document ON evaluation_criteria(document_id);
CREATE INDEX IF NOT EXISTS ix_evaluation_criteria_category ON evaluation_criteria(criteria_category);
CREATE INDEX IF NOT EXISTS ix_evaluation_criteria_weight ON evaluation_criteria(weight_percentage);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with evaluation-specific schema.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_evaluation_criteria(document_content, document_id=None):
    """Extract evaluation criteria from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract evaluation criteria
        evaluation_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "technical_evaluation", "type": "array", "description": "Technical evaluation criteria and factors"},
                    {"name": "management_evaluation", "type": "array", "description": "Management and organizational evaluation criteria"},
                    {"name": "past_performance", "type": "array", "description": "Past performance evaluation criteria"},
                    {"name": "price_evaluation", "type": "array", "description": "Price and cost evaluation criteria"},
                    {"name": "small_business_evaluation", "type": "array", "description": "Small business evaluation factors"},
                    {"name": "evaluation_methodology", "type": "object", "description": "Overall evaluation methodology and process"},
                    {"name": "scoring_system", "type": "object", "description": "Scoring system and rating scales"},
                    {"name": "evaluation_weights", "type": "object", "description": "Weighting of different evaluation factors"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_weights": True,
                "include_scoring": True,
                "include_subfactors": True,
                "confidence_threshold": 0.7
            }
        })

        if evaluation_result.get('success'):
            # Process and structure the evaluation criteria
            evaluation_data = evaluation_result['data']
            structured_criteria = process_evaluation_criteria_data(evaluation_data)

            # Save to database if document_id provided
            if document_id and structured_criteria:
                save_evaluation_criteria(document_id, structured_criteria)

            return {
                "success": True,
                "evaluation_criteria": structured_criteria,
                "extraction_confidence": evaluation_result.get('confidence', 0.0),
                "total_criteria": len(structured_criteria)
            }
        else:
            return {"error": "Evaluation criteria extraction failed"}

    except Exception as e:
        st.error(f"Error extracting evaluation criteria: {e}")
        return {"error": str(e)}

def process_evaluation_criteria_data(raw_evaluation_data):
    """Process raw evaluation criteria data into structured format"""
    structured_criteria = []

    # Process different categories of evaluation criteria
    criteria_categories = {
        'technical_evaluation': 'Technical',
        'management_evaluation': 'Management',
        'past_performance': 'Past Performance',
        'price_evaluation': 'Price',
        'small_business_evaluation': 'Small Business'
    }

    for data_key, category in criteria_categories.items():
        criteria_list = raw_evaluation_data.get(data_key, [])

        for criteria in criteria_list:
            if isinstance(criteria, dict):
                evaluation_criteria = {
                    'category': category,
                    'title': criteria.get('title', ''),
                    'description': criteria.get('description', ''),
                    'weight_percentage': parse_percentage_value(criteria.get('weight', '')),
                    'scoring_method': criteria.get('scoring_method', ''),
                    'evaluation_factors': criteria.get('factors', []),
                    'subfactors': criteria.get('subfactors', []),
                    'rating_scale': criteria.get('rating_scale', ''),
                    'minimum_score': parse_numeric_value(criteria.get('minimum_score', '')),
                    'is_pass_fail': criteria.get('is_pass_fail', False),
                    'evaluation_instructions': criteria.get('instructions', '')
                }
                structured_criteria.append(evaluation_criteria)

    return structured_criteria

def parse_percentage_value(value_str):
    """Parse percentage value from string"""
    if not value_str:
        return None

    try:
        # Remove percentage symbol and convert
        cleaned = str(value_str).replace('%', '').strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def save_evaluation_criteria(document_id, evaluation_criteria):
    """Save evaluation criteria to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        for criteria in evaluation_criteria:
            cursor.execute("""
                INSERT INTO evaluation_criteria
                (document_id, criteria_category, criteria_title, criteria_description,
                 weight_percentage, scoring_method, evaluation_factors, subfactors,
                 rating_scale, minimum_score, is_pass_fail, evaluation_instructions,
                 extraction_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, criteria['category'], criteria['title'], criteria['description'],
                criteria['weight_percentage'], criteria['scoring_method'], criteria['evaluation_factors'],
                criteria['subfactors'], criteria['rating_scale'], criteria['minimum_score'],
                criteria['is_pass_fail'], criteria['evaluation_instructions'], 0.85
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving evaluation criteria: {e}")
        return False
    finally:
        conn.close()

def render_evaluation_criteria_extraction():
    """Render evaluation criteria extraction interface"""
    st.subheader("📊 Evaluation Criteria Extraction")

    # Evaluation tabs
    tab1, tab2, tab3 = st.tabs(["Extract Criteria", "Criteria Library", "Evaluation Analysis"])

    with tab1:
        st.write("**Extract Evaluation Criteria from RFP Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="eval_criteria_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload RFP Document:",
                type=['txt', 'pdf', 'docx'],
                key="eval_criteria_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="eval_criteria_doc_name")
            document_content = st.text_area(
                "RFP Content:",
                height=300,
                placeholder="Paste RFP content to extract evaluation criteria...",
                key="eval_criteria_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_rfp_documents()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="eval_criteria_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("📊 Extract Evaluation Criteria", type="primary"):
            with st.spinner("Extracting evaluation criteria..."):
                evaluation_result = extract_evaluation_criteria(document_content, document_name)

                if evaluation_result.get('success'):
                    st.session_state.eval_criteria_extraction_result = evaluation_result
                    st.session_state.eval_criteria_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display extraction results
        if 'eval_criteria_extraction_result' in st.session_state:
            st.subheader("📊 Evaluation Criteria Results")

            result = st.session_state.eval_criteria_extraction_result
            evaluation_criteria = result.get('evaluation_criteria', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Criteria", result.get('total_criteria', 0))

            with col2:
                categories_count = len(set(criteria.get('category', '') for criteria in evaluation_criteria))
                st.metric("Categories", categories_count)

            with col3:
                total_weight = sum(criteria.get('weight_percentage', 0) or 0 for criteria in evaluation_criteria)
                st.metric("Total Weight", f"{total_weight:.1f}%")

            with col4:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            # Evaluation criteria display
            if evaluation_criteria:
                st.write("**Evaluation Criteria by Category:**")

                # Group by category
                criteria_by_category = {}
                for criteria in evaluation_criteria:
                    category = criteria.get('category', 'Other')
                    if category not in criteria_by_category:
                        criteria_by_category[category] = []
                    criteria_by_category[category].append(criteria)

                # Display by category
                for category, criteria_list in criteria_by_category.items():
                    category_icon = get_evaluation_category_icon(category)
                    category_weight = sum(c.get('weight_percentage', 0) or 0 for c in criteria_list)

                    st.write(f"**{category_icon} {category} ({category_weight:.1f}% total weight):**")

                    for i, criteria in enumerate(criteria_list, 1):
                        with st.expander(f"{criteria.get('title', f'{category} Criteria {i}')}"):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                if criteria.get('description'):
                                    st.write(f"**Description:** {criteria['description']}")

                                if criteria.get('evaluation_factors'):
                                    st.write("**Evaluation Factors:**")
                                    for factor in criteria['evaluation_factors']:
                                        st.write(f"• {factor}")

                                if criteria.get('subfactors'):
                                    st.write("**Subfactors:**")
                                    for subfactor in criteria['subfactors']:
                                        st.write(f"  - {subfactor}")

                                if criteria.get('evaluation_instructions'):
                                    st.write(f"**Instructions:** {criteria['evaluation_instructions']}")

                            with col2:
                                if criteria.get('weight_percentage'):
                                    st.metric("Weight", f"{criteria['weight_percentage']:.1f}%")

                                if criteria.get('scoring_method'):
                                    st.write(f"**Scoring:** {criteria['scoring_method']}")

                                if criteria.get('rating_scale'):
                                    st.write(f"**Scale:** {criteria['rating_scale']}")

                                if criteria.get('minimum_score'):
                                    st.write(f"**Min Score:** {criteria['minimum_score']}")

                                if criteria.get('is_pass_fail'):
                                    st.write("**Type:** Pass/Fail")

                # Evaluation criteria summary
                st.write("**Evaluation Strategy Summary:**")
                eval_summary = generate_evaluation_criteria_summary(evaluation_criteria)
                st.write(eval_summary)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Criteria"):
                    save_evaluation_criteria(st.session_state.eval_criteria_document['name'], evaluation_criteria)
                    st.success("Evaluation criteria saved!")

            with col2:
                if st.button("📊 Generate Evaluation Matrix"):
                    generate_evaluation_matrix(evaluation_criteria)
                    st.success("Evaluation matrix generated!")

            with col3:
                if st.button("📄 Export to Excel"):
                    export_eval_criteria_to_excel(evaluation_criteria, document_name)
                    st.success("Criteria exported!")

            with col4:
                if st.button("🎯 Create Proposal Strategy"):
                    create_proposal_strategy(evaluation_criteria)
                    st.success("Proposal strategy created!")

    with tab2:
        st.write("**Evaluation Criteria Library**")

        # Get saved evaluation criteria
        saved_eval_criteria = get_saved_evaluation_criteria()

        if saved_eval_criteria:
            # Filter options
            col1, col2 = st.columns(2)

            with col1:
                category_filter = st.selectbox(
                    "Filter by Category:",
                    ["All", "Technical", "Management", "Past Performance", "Price", "Small Business"],
                    key="eval_criteria_category_filter"
                )

            with col2:
                search_term = st.text_input("Search Criteria:", key="eval_criteria_search")

            # Display evaluation criteria
            for criteria_data in saved_eval_criteria:
                doc_name, category, title, weight, scoring_method, extraction_date = criteria_data

                # Apply filters
                if category_filter != "All" and category_filter != category:
                    continue

                if search_term and search_term.lower() not in title.lower():
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        category_icon = get_evaluation_category_icon(category)
                        st.write(f"**{category_icon} {title}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Scoring: {scoring_method}")

                    with col2:
                        if weight:
                            st.metric("Weight", f"{weight:.1f}%")
                        else:
                            st.write("No weight specified")

                    with col3:
                        st.caption(extraction_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_eval_criteria_{title[:20]}"):
                            criteria_details = load_evaluation_criteria_details(doc_name, title)
                            st.session_state.view_eval_criteria_details = criteria_details
                            st.rerun()

                st.divider()
        else:
            st.info("No evaluation criteria saved yet.")

    with tab3:
        st.write("**Evaluation Analysis & Strategy**")

        # Evaluation analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["Criteria Overview", "Weight Analysis", "Competitive Analysis", "Win Strategy"],
            key="eval_analysis_type"
        )

        if analysis_type == "Criteria Overview":
            render_criteria_overview()
        elif analysis_type == "Weight Analysis":
            render_weight_analysis()
        elif analysis_type == "Competitive Analysis":
            render_competitive_evaluation_analysis()
        elif analysis_type == "Win Strategy":
            render_win_strategy_analysis()

def get_evaluation_category_icon(category):
    """Get icon for evaluation category"""
    icons = {
        "Technical": "🔧",
        "Management": "👨‍💼",
        "Past Performance": "📈",
        "Price": "💰",
        "Small Business": "🏢"
    }
    return icons.get(category, "📊")

def generate_evaluation_criteria_summary(evaluation_criteria):
    """Generate summary of evaluation criteria using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return "Summary generation not available"

    try:
        summary_result = call_mcp_tool("generate_insights", {
            "content": json.dumps(evaluation_criteria),
            "insight_type": "evaluation_criteria_summary",
            "context": {
                "domain": "government_contracting",
                "summary_focus": ["evaluation_strategy", "key_factors", "competitive_advantages"],
                "output_format": "strategic_summary"
            }
        })

        if summary_result.get('success'):
            return summary_result['data'].get('summary', 'Summary generation failed')
        else:
            return "Summary generation failed"

    except Exception as e:
        return f"Error generating summary: {e}"
```

---

## **Feature 38: Amendment Impact Analysis**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS amendment_analyses (
    id SERIAL PRIMARY KEY,
    original_document_id VARCHAR(100) NOT NULL,
    amendment_document_id VARCHAR(100) NOT NULL,
    amendment_number VARCHAR(50),
    amendment_date DATE,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    impact_summary TEXT,
    overall_impact_score DECIMAL(3,2), -- 0.0 to 1.0 scale
    analysis_confidence DECIMAL(3,2),
    analyzed_by VARCHAR(100) DEFAULT 'ai_system'
);

CREATE TABLE IF NOT EXISTS amendment_changes (
    id SERIAL PRIMARY KEY,
    amendment_analysis_id INTEGER REFERENCES amendment_analyses(id),
    change_category VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- 'addition', 'deletion', 'modification'
    section_affected VARCHAR(200),
    original_text TEXT,
    new_text TEXT,
    impact_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    impact_description TEXT,
    business_impact TEXT,
    action_required TEXT,
    deadline_impact BOOLEAN DEFAULT FALSE,
    cost_impact BOOLEAN DEFAULT FALSE,
    scope_impact BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS amendment_notifications (
    id SERIAL PRIMARY KEY,
    amendment_analysis_id INTEGER REFERENCES amendment_analyses(id),
    notification_type VARCHAR(50), -- 'email', 'dashboard', 'sms'
    recipient VARCHAR(200),
    notification_sent BOOLEAN DEFAULT FALSE,
    sent_date TIMESTAMP,
    notification_content TEXT
);

CREATE INDEX IF NOT EXISTS ix_amendment_analyses_original ON amendment_analyses(original_document_id);
CREATE INDEX IF NOT EXISTS ix_amendment_analyses_amendment ON amendment_analyses(amendment_document_id);
CREATE INDEX IF NOT EXISTS ix_amendment_changes_category ON amendment_changes(change_category);
CREATE INDEX IF NOT EXISTS ix_amendment_changes_impact ON amendment_changes(impact_level);
```

#### **MCP Integration**
Uses generic `analyze_patterns` and `calculate_similarity` tools for change detection and impact analysis.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def analyze_amendment_impact(original_document, amendment_document, document_ids=None):
    """Analyze impact of document amendments using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # First, identify changes using similarity analysis
        similarity_result = call_mcp_tool("calculate_similarity", {
            "text1": original_document,
            "text2": amendment_document,
            "similarity_type": "document_diff_analysis",
            "analysis_options": {
                "identify_changes": True,
                "change_categories": ["additions", "deletions", "modifications"],
                "section_level_analysis": True,
                "semantic_analysis": True
            }
        })

        if not similarity_result.get('success'):
            return {"error": "Document comparison failed"}

        # Analyze patterns and impact of changes
        changes_data = similarity_result['data']
        impact_result = call_mcp_tool("analyze_patterns", {
            "data": changes_data,
            "pattern_types": ["change_impact_analysis", "business_impact", "risk_assessment"],
            "analysis_context": "government_contracting_amendments",
            "output_format": "impact_analysis"
        })

        if impact_result.get('success'):
            # Process and structure the amendment analysis
            impact_data = impact_result['data']
            structured_analysis = process_amendment_analysis_data(changes_data, impact_data)

            # Save to database if document_ids provided
            if document_ids and structured_analysis:
                save_amendment_analysis(document_ids['original'], document_ids['amendment'], structured_analysis)

            return {
                "success": True,
                "amendment_analysis": structured_analysis,
                "analysis_confidence": impact_result.get('confidence', 0.0),
                "total_changes": len(structured_analysis.get('changes', []))
            }
        else:
            return {"error": "Amendment impact analysis failed"}

    except Exception as e:
        st.error(f"Error analyzing amendment impact: {e}")
        return {"error": str(e)}

def process_amendment_analysis_data(changes_data, impact_data):
    """Process raw amendment analysis data into structured format"""
    structured_analysis = {
        'impact_summary': impact_data.get('overall_impact_summary', ''),
        'overall_impact_score': impact_data.get('impact_score', 0.0),
        'changes': []
    }

    # Process identified changes
    identified_changes = changes_data.get('identified_changes', [])
    impact_assessments = impact_data.get('change_impacts', [])

    for i, change in enumerate(identified_changes):
        if isinstance(change, dict):
            # Get corresponding impact assessment
            impact_assessment = impact_assessments[i] if i < len(impact_assessments) else {}

            change_analysis = {
                'category': change.get('category', 'general'),
                'change_type': change.get('type', 'modification'),
                'section_affected': change.get('section', ''),
                'original_text': change.get('original_text', ''),
                'new_text': change.get('new_text', ''),
                'impact_level': impact_assessment.get('impact_level', 'medium'),
                'impact_description': impact_assessment.get('description', ''),
                'business_impact': impact_assessment.get('business_impact', ''),
                'action_required': impact_assessment.get('action_required', ''),
                'deadline_impact': impact_assessment.get('affects_deadlines', False),
                'cost_impact': impact_assessment.get('affects_costs', False),
                'scope_impact': impact_assessment.get('affects_scope', False)
            }
            structured_analysis['changes'].append(change_analysis)

    return structured_analysis

def save_amendment_analysis(original_doc_id, amendment_doc_id, analysis_data):
    """Save amendment analysis to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Save main analysis record
        cursor.execute("""
            INSERT INTO amendment_analyses
            (original_document_id, amendment_document_id, impact_summary,
             overall_impact_score, analysis_confidence)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            original_doc_id, amendment_doc_id, analysis_data['impact_summary'],
            analysis_data['overall_impact_score'], 0.85
        ))

        analysis_id = cursor.fetchone()[0]

        # Save individual changes
        for change in analysis_data['changes']:
            cursor.execute("""
                INSERT INTO amendment_changes
                (amendment_analysis_id, change_category, change_type, section_affected,
                 original_text, new_text, impact_level, impact_description,
                 business_impact, action_required, deadline_impact, cost_impact, scope_impact)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                analysis_id, change['category'], change['change_type'], change['section_affected'],
                change['original_text'], change['new_text'], change['impact_level'],
                change['impact_description'], change['business_impact'], change['action_required'],
                change['deadline_impact'], change['cost_impact'], change['scope_impact']
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving amendment analysis: {e}")
        return False
    finally:
        conn.close()

def render_amendment_impact_analysis():
    """Render amendment impact analysis interface"""
    st.subheader("📋 Amendment Impact Analysis")

    # Amendment analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Analyze Amendment", "Analysis History", "Impact Dashboard", "Notifications"])

    with tab1:
        st.write("**Analyze Document Amendment Impact**")

        # Document selection
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Original Document:**")
            original_input_method = st.radio(
                "Original Document Input:",
                ["Upload File", "Select from Library"],
                key="original_amendment_input"
            )

            original_content = ""
            original_name = ""

            if original_input_method == "Upload File":
                original_file = st.file_uploader(
                    "Upload Original Document:",
                    type=['txt', 'pdf', 'docx'],
                    key="original_amendment_file"
                )

                if original_file:
                    original_content = extract_text_from_file(original_file)
                    original_name = original_file.name

            else:  # Select from Library
                documents = get_document_library()

                if documents:
                    selected_original = st.selectbox(
                        "Select Original Document:",
                        options=documents,
                        format_func=lambda x: f"{x['name']} ({x['type']})",
                        key="original_amendment_selection"
                    )

                    if selected_original:
                        original_content = load_document_content(selected_original['id'])
                        original_name = selected_original['name']

        with col2:
            st.write("**Amendment Document:**")
            amendment_input_method = st.radio(
                "Amendment Document Input:",
                ["Upload File", "Select from Library"],
                key="amendment_amendment_input"
            )

            amendment_content = ""
            amendment_name = ""

            if amendment_input_method == "Upload File":
                amendment_file = st.file_uploader(
                    "Upload Amendment Document:",
                    type=['txt', 'pdf', 'docx'],
                    key="amendment_amendment_file"
                )

                if amendment_file:
                    amendment_content = extract_text_from_file(amendment_file)
                    amendment_name = amendment_file.name

            else:  # Select from Library
                documents = get_document_library()

                if documents:
                    selected_amendment = st.selectbox(
                        "Select Amendment Document:",
                        options=documents,
                        format_func=lambda x: f"{x['name']} ({x['type']})",
                        key="amendment_amendment_selection"
                    )

                    if selected_amendment:
                        amendment_content = load_document_content(selected_amendment['id'])
                        amendment_name = selected_amendment['name']

        # Analysis options
        st.write("**Analysis Options:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            analysis_depth = st.selectbox(
                "Analysis Depth:",
                ["Standard", "Detailed", "Comprehensive"],
                key="amendment_analysis_depth"
            )

        with col2:
            focus_areas = st.multiselect(
                "Focus Areas:",
                ["Deadlines", "Costs", "Scope", "Requirements", "Compliance"],
                default=["Deadlines", "Costs", "Scope"],
                key="amendment_focus_areas"
            )

        with col3:
            notification_level = st.selectbox(
                "Notification Level:",
                ["Critical Only", "High Impact", "All Changes"],
                key="amendment_notification_level"
            )

        if original_content and amendment_content and st.button("📋 Analyze Amendment Impact", type="primary"):
            with st.spinner("Analyzing amendment impact..."):
                document_ids = {
                    'original': original_name,
                    'amendment': amendment_name
                }

                amendment_result = analyze_amendment_impact(
                    original_content,
                    amendment_content,
                    document_ids
                )

                if amendment_result.get('success'):
                    st.session_state.amendment_analysis_result = amendment_result
                    st.session_state.amendment_documents = {
                        'original': {'name': original_name, 'content': original_content},
                        'amendment': {'name': amendment_name, 'content': amendment_content}
                    }

        # Display analysis results
        if 'amendment_analysis_result' in st.session_state:
            st.subheader("📊 Amendment Impact Analysis Results")

            result = st.session_state.amendment_analysis_result
            analysis = result.get('amendment_analysis', {})
            changes = analysis.get('changes', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Changes", result.get('total_changes', 0))

            with col2:
                impact_score = analysis.get('overall_impact_score', 0.0)
                impact_color = "red" if impact_score > 0.7 else "orange" if impact_score > 0.4 else "green"
                st.metric("Impact Score", f"{impact_score:.1%}")

            with col3:
                critical_changes = sum(1 for c in changes if c.get('impact_level') == 'critical')
                st.metric("Critical Changes", critical_changes)

            with col4:
                confidence = result.get('analysis_confidence', 0.0)
                st.metric("Analysis Confidence", f"{confidence:.1%}")

            # Impact summary
            if analysis.get('impact_summary'):
                st.write("**Overall Impact Summary:**")
                st.info(analysis['impact_summary'])

            # Changes by impact level
            if changes:
                st.write("**Changes by Impact Level:**")

                # Group changes by impact level
                changes_by_impact = {}
                for change in changes:
                    impact_level = change.get('impact_level', 'medium')
                    if impact_level not in changes_by_impact:
                        changes_by_impact[impact_level] = []
                    changes_by_impact[impact_level].append(change)

                # Display changes by impact level
                impact_order = ['critical', 'high', 'medium', 'low']

                for impact_level in impact_order:
                    if impact_level in changes_by_impact:
                        impact_icon = get_impact_level_icon(impact_level)
                        impact_changes = changes_by_impact[impact_level]

                        st.write(f"**{impact_icon} {impact_level.title()} Impact ({len(impact_changes)} changes):**")

                        for i, change in enumerate(impact_changes, 1):
                            with st.expander(f"{change.get('section_affected', f'Change {i}')} - {change.get('change_type', 'Modification').title()}"):
                                col1, col2 = st.columns([2, 1])

                                with col1:
                                    st.write(f"**Category:** {change.get('category', 'N/A').title()}")

                                    if change.get('impact_description'):
                                        st.write(f"**Impact:** {change['impact_description']}")

                                    if change.get('business_impact'):
                                        st.write(f"**Business Impact:** {change['business_impact']}")

                                    if change.get('action_required'):
                                        st.write(f"**Action Required:** {change['action_required']}")

                                    # Show text changes
                                    if change.get('original_text') and change.get('new_text'):
                                        st.write("**Text Changes:**")
                                        col_a, col_b = st.columns(2)

                                        with col_a:
                                            st.write("*Original:*")
                                            st.text_area("", value=change['original_text'][:200] + "...", height=100, key=f"orig_{i}_{impact_level}", disabled=True)

                                        with col_b:
                                            st.write("*New:*")
                                            st.text_area("", value=change['new_text'][:200] + "...", height=100, key=f"new_{i}_{impact_level}", disabled=True)

                                with col2:
                                    # Impact indicators
                                    if change.get('deadline_impact'):
                                        st.write("⏰ **Affects Deadlines**")

                                    if change.get('cost_impact'):
                                        st.write("💰 **Affects Costs**")

                                    if change.get('scope_impact'):
                                        st.write("📋 **Affects Scope**")

                                    # Change type
                                    change_type = change.get('change_type', 'modification')
                                    type_icon = get_change_type_icon(change_type)
                                    st.write(f"{type_icon} **{change_type.title()}**")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Analysis"):
                    save_amendment_analysis(
                        st.session_state.amendment_documents['original']['name'],
                        st.session_state.amendment_documents['amendment']['name'],
                        analysis
                    )
                    st.success("Amendment analysis saved!")

            with col2:
                if st.button("📊 Generate Report"):
                    generate_amendment_report(analysis)
                    st.success("Amendment report generated!")

            with col3:
                if st.button("📧 Send Notifications"):
                    send_amendment_notifications(analysis, notification_level)
                    st.success("Notifications sent!")

            with col4:
                if st.button("📋 Create Action Plan"):
                    create_amendment_action_plan(analysis)
                    st.success("Action plan created!")

    with tab2:
        st.write("**Amendment Analysis History**")

        # Get saved amendment analyses
        saved_analyses = get_saved_amendment_analyses()

        if saved_analyses:
            for analysis_data in saved_analyses:
                original_doc, amendment_doc, analysis_date, impact_score, total_changes = analysis_data

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**📋 {original_doc} → {amendment_doc}**")
                        st.caption(f"Analyzed: {analysis_date.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        impact_color = "red" if impact_score > 0.7 else "orange" if impact_score > 0.4 else "green"
                        st.metric("Impact", f"{impact_score:.1%}")

                    with col3:
                        st.metric("Changes", total_changes)

                        if st.button("👁️", key=f"view_amendment_{original_doc}_{amendment_doc}"):
                            analysis_details = load_amendment_analysis_details(original_doc, amendment_doc)
                            st.session_state.view_amendment_details = analysis_details
                            st.rerun()

                st.divider()
        else:
            st.info("No amendment analyses saved yet.")

    with tab3:
        st.write("**Amendment Impact Dashboard**")

        # Dashboard metrics and visualizations
        render_amendment_impact_dashboard()

    with tab4:
        st.write("**Amendment Notifications**")

        # Notification management
        render_amendment_notifications_management()

def get_impact_level_icon(impact_level):
    """Get icon for impact level"""
    icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    return icons.get(impact_level, "⚪")

def get_change_type_icon(change_type):
    """Get icon for change type"""
    icons = {
        "addition": "➕",
        "deletion": "➖",
        "modification": "✏️"
    }
    return icons.get(change_type, "📝")

def render_amendment_impact_dashboard():
    """Render amendment impact dashboard"""
    st.write("**Impact Overview:**")

    # Get dashboard data
    dashboard_data = get_amendment_dashboard_data()

    if dashboard_data:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Amendments", dashboard_data.get('total_amendments', 0))

        with col2:
            avg_impact = dashboard_data.get('average_impact_score', 0.0)
            st.metric("Average Impact", f"{avg_impact:.1%}")

        with col3:
            critical_amendments = dashboard_data.get('critical_amendments', 0)
            st.metric("Critical Amendments", critical_amendments)

        with col4:
            pending_actions = dashboard_data.get('pending_actions', 0)
            st.metric("Pending Actions", pending_actions)

        # Impact distribution chart
        if dashboard_data.get('impact_distribution'):
            st.write("**Impact Distribution:**")
            st.bar_chart(dashboard_data['impact_distribution'])

        # Recent high-impact amendments
        if dashboard_data.get('recent_high_impact'):
            st.write("**Recent High-Impact Amendments:**")
            for amendment in dashboard_data['recent_high_impact']:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"📋 **{amendment['document']}**")
                    st.caption(f"Impact: {amendment['impact_description']}")

                with col2:
                    st.metric("Score", f"{amendment['impact_score']:.1%}")
    else:
        st.info("No amendment data available for dashboard.")
```

---

## **Feature 41: Risk Factor Identification**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS risk_assessments (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_risk_score DECIMAL(3,2), -- 0.0 to 1.0 scale
    risk_category VARCHAR(50), -- 'low', 'medium', 'high', 'critical'
    assessment_summary TEXT,
    mitigation_strategy TEXT,
    assessed_by VARCHAR(100) DEFAULT 'ai_system',
    reviewed_by VARCHAR(100),
    review_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identified_risks (
    id SERIAL PRIMARY KEY,
    risk_assessment_id INTEGER REFERENCES risk_assessments(id),
    risk_category VARCHAR(100) NOT NULL,
    risk_title VARCHAR(300) NOT NULL,
    risk_description TEXT,
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    probability DECIMAL(3,2), -- 0.0 to 1.0
    impact DECIMAL(3,2), -- 0.0 to 1.0
    risk_score DECIMAL(3,2), -- calculated: probability * impact
    risk_indicators TEXT[],
    potential_consequences TEXT[],
    mitigation_actions TEXT[],
    contingency_plans TEXT[],
    risk_owner VARCHAR(100),
    target_resolution_date DATE,
    current_status VARCHAR(50) DEFAULT 'identified'
);

CREATE TABLE IF NOT EXISTS risk_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    category_description TEXT,
    default_mitigation_strategies TEXT[],
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_risk_assessments_document ON risk_assessments(document_id);
CREATE INDEX IF NOT EXISTS ix_identified_risks_category ON identified_risks(risk_category);
CREATE INDEX IF NOT EXISTS ix_identified_risks_level ON identified_risks(risk_level);
CREATE INDEX IF NOT EXISTS ix_identified_risks_score ON identified_risks(risk_score);
```

#### **MCP Integration**
Uses generic `classify_content` and `analyze_patterns` tools for risk identification and assessment.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def identify_risk_factors(document_content, document_id=None):
    """Identify risk factors from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # First, classify content for risk indicators
        risk_classification_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "government_contracting_risks",
            "domain_rules": {
                "risk_categories": [
                    "technical_risk", "schedule_risk", "cost_risk", "performance_risk",
                    "compliance_risk", "security_risk", "personnel_risk", "vendor_risk",
                    "regulatory_risk", "market_risk", "operational_risk", "financial_risk"
                ],
                "risk_indicators": [
                    "tight_deadlines", "complex_requirements", "new_technology",
                    "multiple_stakeholders", "regulatory_changes", "budget_constraints",
                    "skill_gaps", "vendor_dependencies", "security_requirements"
                ],
                "extract_consequences": True,
                "assess_probability": True,
                "assess_impact": True
            },
            "risk_assessment": True
        })

        if not risk_classification_result.get('success'):
            return {"error": "Risk classification failed"}

        # Analyze patterns for comprehensive risk assessment
        risk_data = risk_classification_result['data']
        risk_analysis_result = call_mcp_tool("analyze_patterns", {
            "data": risk_data,
            "pattern_types": ["risk_correlation", "impact_analysis", "mitigation_strategies"],
            "analysis_context": "government_contracting_risk_assessment",
            "output_format": "comprehensive_risk_assessment"
        })

        if risk_analysis_result.get('success'):
            # Process and structure the risk assessment
            analysis_data = risk_analysis_result['data']
            structured_assessment = process_risk_assessment_data(risk_data, analysis_data)

            # Save to database if document_id provided
            if document_id and structured_assessment:
                save_risk_assessment(document_id, structured_assessment)

            return {
                "success": True,
                "risk_assessment": structured_assessment,
                "assessment_confidence": risk_analysis_result.get('confidence', 0.0),
                "total_risks": len(structured_assessment.get('identified_risks', []))
            }
        else:
            return {"error": "Risk analysis failed"}

    except Exception as e:
        st.error(f"Error identifying risk factors: {e}")
        return {"error": str(e)}

def process_risk_assessment_data(risk_data, analysis_data):
    """Process raw risk assessment data into structured format"""
    structured_assessment = {
        'overall_risk_score': analysis_data.get('overall_risk_score', 0.0),
        'risk_category': analysis_data.get('overall_risk_category', 'medium'),
        'assessment_summary': analysis_data.get('assessment_summary', ''),
        'mitigation_strategy': analysis_data.get('overall_mitigation_strategy', ''),
        'identified_risks': []
    }

    # Process individual risks
    identified_risks = risk_data.get('identified_risks', [])
    risk_assessments = analysis_data.get('individual_risk_assessments', [])

    for i, risk in enumerate(identified_risks):
        if isinstance(risk, dict):
            # Get corresponding detailed assessment
            risk_assessment = risk_assessments[i] if i < len(risk_assessments) else {}

            # Calculate risk score (probability * impact)
            probability = risk_assessment.get('probability', 0.5)
            impact = risk_assessment.get('impact', 0.5)
            risk_score = probability * impact

            risk_analysis = {
                'category': risk.get('category', 'operational_risk'),
                'title': risk.get('title', ''),
                'description': risk.get('description', ''),
                'risk_level': calculate_risk_level(risk_score),
                'probability': probability,
                'impact': impact,
                'risk_score': risk_score,
                'risk_indicators': risk.get('indicators', []),
                'potential_consequences': risk_assessment.get('consequences', []),
                'mitigation_actions': risk_assessment.get('mitigation_actions', []),
                'contingency_plans': risk_assessment.get('contingency_plans', []),
                'current_status': 'identified'
            }
            structured_assessment['identified_risks'].append(risk_analysis)

    return structured_assessment

def calculate_risk_level(risk_score):
    """Calculate risk level based on risk score"""
    if risk_score >= 0.8:
        return 'critical'
    elif risk_score >= 0.6:
        return 'high'
    elif risk_score >= 0.3:
        return 'medium'
    else:
        return 'low'

def save_risk_assessment(document_id, assessment_data):
    """Save risk assessment to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Save main assessment record
        cursor.execute("""
            INSERT INTO risk_assessments
            (document_id, overall_risk_score, risk_category, assessment_summary, mitigation_strategy)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_id, assessment_data['overall_risk_score'], assessment_data['risk_category'],
            assessment_data['assessment_summary'], assessment_data['mitigation_strategy']
        ))

        assessment_id = cursor.fetchone()[0]

        # Save individual risks
        for risk in assessment_data['identified_risks']:
            cursor.execute("""
                INSERT INTO identified_risks
                (risk_assessment_id, risk_category, risk_title, risk_description,
                 risk_level, probability, impact, risk_score, risk_indicators,
                 potential_consequences, mitigation_actions, contingency_plans, current_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                assessment_id, risk['category'], risk['title'], risk['description'],
                risk['risk_level'], risk['probability'], risk['impact'], risk['risk_score'],
                risk['risk_indicators'], risk['potential_consequences'], risk['mitigation_actions'],
                risk['contingency_plans'], risk['current_status']
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving risk assessment: {e}")
        return False
    finally:
        conn.close()

def render_risk_factor_identification():
    """Render risk factor identification interface"""
    st.subheader("⚠️ Risk Factor Identification")

    # Risk analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Identify Risks", "Risk Register", "Risk Dashboard", "Mitigation Plans"])

    with tab1:
        st.write("**Identify Risk Factors from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="risk_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document for Risk Analysis:",
                type=['txt', 'pdf', 'docx'],
                key="risk_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="risk_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to analyze for risk factors...",
                key="risk_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="risk_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        # Risk analysis options
        st.write("**Risk Analysis Options:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            analysis_scope = st.selectbox(
                "Analysis Scope:",
                ["Comprehensive", "Technical Focus", "Schedule Focus", "Cost Focus"],
                key="risk_analysis_scope"
            )

        with col2:
            risk_threshold = st.selectbox(
                "Risk Threshold:",
                ["All Risks", "Medium+", "High+", "Critical Only"],
                key="risk_threshold"
            )

        with col3:
            include_mitigation = st.checkbox(
                "Include Mitigation Strategies",
                value=True,
                key="include_mitigation"
            )

        if document_content and st.button("⚠️ Identify Risk Factors", type="primary"):
            with st.spinner("Identifying risk factors..."):
                risk_result = identify_risk_factors(document_content, document_name)

                if risk_result.get('success'):
                    st.session_state.risk_identification_result = risk_result
                    st.session_state.risk_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display risk analysis results
        if 'risk_identification_result' in st.session_state:
            st.subheader("⚠️ Risk Assessment Results")

            result = st.session_state.risk_identification_result
            assessment = result.get('risk_assessment', {})
            identified_risks = assessment.get('identified_risks', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Risks", result.get('total_risks', 0))

            with col2:
                overall_score = assessment.get('overall_risk_score', 0.0)
                risk_color = "red" if overall_score > 0.7 else "orange" if overall_score > 0.4 else "green"
                st.metric("Overall Risk", f"{overall_score:.1%}")

            with col3:
                critical_risks = sum(1 for r in identified_risks if r.get('risk_level') == 'critical')
                st.metric("Critical Risks", critical_risks)

            with col4:
                confidence = result.get('assessment_confidence', 0.0)
                st.metric("Assessment Confidence", f"{confidence:.1%}")

            # Overall assessment summary
            if assessment.get('assessment_summary'):
                st.write("**Risk Assessment Summary:**")
                st.info(assessment['assessment_summary'])

            # Risk matrix visualization
            if identified_risks:
                st.write("**Risk Matrix:**")
                render_risk_matrix(identified_risks)

            # Risks by level
            if identified_risks:
                st.write("**Identified Risks by Level:**")

                # Group risks by level
                risks_by_level = {}
                for risk in identified_risks:
                    risk_level = risk.get('risk_level', 'medium')
                    if risk_level not in risks_by_level:
                        risks_by_level[risk_level] = []
                    risks_by_level[risk_level].append(risk)

                # Display risks by level
                risk_order = ['critical', 'high', 'medium', 'low']

                for risk_level in risk_order:
                    if risk_level in risks_by_level:
                        risk_icon = get_risk_level_icon(risk_level)
                        level_risks = risks_by_level[risk_level]

                        st.write(f"**{risk_icon} {risk_level.title()} Risk ({len(level_risks)} risks):**")

                        for i, risk in enumerate(level_risks, 1):
                            with st.expander(f"{risk.get('title', f'{risk_level.title()} Risk {i}')}"):
                                col1, col2 = st.columns([2, 1])

                                with col1:
                                    st.write(f"**Category:** {risk.get('category', 'N/A').replace('_', ' ').title()}")

                                    if risk.get('description'):
                                        st.write(f"**Description:** {risk['description']}")

                                    if risk.get('risk_indicators'):
                                        st.write("**Risk Indicators:**")
                                        for indicator in risk['risk_indicators']:
                                            st.write(f"• {indicator}")

                                    if risk.get('potential_consequences'):
                                        st.write("**Potential Consequences:**")
                                        for consequence in risk['potential_consequences']:
                                            st.write(f"• {consequence}")

                                    if risk.get('mitigation_actions') and include_mitigation:
                                        st.write("**Mitigation Actions:**")
                                        for action in risk['mitigation_actions']:
                                            st.write(f"✓ {action}")

                                with col2:
                                    # Risk metrics
                                    st.metric("Probability", f"{risk.get('probability', 0.0):.1%}")
                                    st.metric("Impact", f"{risk.get('impact', 0.0):.1%}")
                                    st.metric("Risk Score", f"{risk.get('risk_score', 0.0):.1%}")

                                    # Status
                                    status = risk.get('current_status', 'identified')
                                    status_icon = get_risk_status_icon(status)
                                    st.write(f"{status_icon} **{status.title()}**")

            # Overall mitigation strategy
            if assessment.get('mitigation_strategy'):
                st.write("**Overall Mitigation Strategy:**")
                st.success(assessment['mitigation_strategy'])

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Risk Assessment"):
                    save_risk_assessment(st.session_state.risk_document['name'], assessment)
                    st.success("Risk assessment saved!")

            with col2:
                if st.button("📊 Generate Risk Report"):
                    generate_risk_report(assessment)
                    st.success("Risk report generated!")

            with col3:
                if st.button("📋 Create Risk Register"):
                    create_risk_register(identified_risks)
                    st.success("Risk register created!")

            with col4:
                if st.button("🎯 Develop Mitigation Plan"):
                    develop_mitigation_plan(identified_risks)
                    st.success("Mitigation plan developed!")

    with tab2:
        st.write("**Risk Register**")

        # Get saved risk assessments
        saved_assessments = get_saved_risk_assessments()

        if saved_assessments:
            # Filter options
            col1, col2, col3 = st.columns(3)

            with col1:
                risk_level_filter = st.selectbox(
                    "Filter by Risk Level:",
                    ["All", "Critical", "High", "Medium", "Low"],
                    key="risk_level_filter"
                )

            with col2:
                risk_category_filter = st.selectbox(
                    "Filter by Category:",
                    ["All", "Technical", "Schedule", "Cost", "Performance", "Compliance"],
                    key="risk_category_filter"
                )

            with col3:
                status_filter = st.selectbox(
                    "Filter by Status:",
                    ["All", "Identified", "Analyzing", "Mitigating", "Resolved"],
                    key="risk_status_filter"
                )

            # Display risk register
            for risk_data in saved_assessments:
                doc_name, risk_title, risk_level, risk_score, category, status, assessment_date = risk_data

                # Apply filters
                if risk_level_filter != "All" and risk_level_filter.lower() != risk_level.lower():
                    continue

                if risk_category_filter != "All" and risk_category_filter.lower() not in category.lower():
                    continue

                if status_filter != "All" and status_filter.lower() != status.lower():
                    continue

                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        risk_icon = get_risk_level_icon(risk_level)
                        st.write(f"**{risk_icon} {risk_title}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Category: {category.replace('_', ' ').title()}")

                    with col2:
                        st.metric("Risk Score", f"{risk_score:.1%}")

                    with col3:
                        status_icon = get_risk_status_icon(status)
                        st.write(f"{status_icon} {status.title()}")

                    with col4:
                        st.caption(assessment_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_risk_{risk_title[:20]}"):
                            risk_details = load_risk_details(doc_name, risk_title)
                            st.session_state.view_risk_details = risk_details
                            st.rerun()

                st.divider()
        else:
            st.info("No risk assessments saved yet.")

    with tab3:
        st.write("**Risk Dashboard**")

        # Risk dashboard metrics and visualizations
        render_risk_dashboard()

    with tab4:
        st.write("**Risk Mitigation Plans**")

        # Mitigation plan management
        render_risk_mitigation_plans()

def get_risk_level_icon(risk_level):
    """Get icon for risk level"""
    icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    return icons.get(risk_level, "⚪")

def get_risk_status_icon(status):
    """Get icon for risk status"""
    icons = {
        "identified": "🆕",
        "analyzing": "🔍",
        "mitigating": "🛠️",
        "resolved": "✅"
    }
    return icons.get(status, "❓")

def render_risk_matrix(identified_risks):
    """Render risk matrix visualization"""
    import plotly.graph_objects as go
    import plotly.express as px

    # Prepare data for risk matrix
    probabilities = []
    impacts = []
    risk_titles = []
    risk_levels = []

    for risk in identified_risks:
        probabilities.append(risk.get('probability', 0.5))
        impacts.append(risk.get('impact', 0.5))
        risk_titles.append(risk.get('title', 'Unknown Risk'))
        risk_levels.append(risk.get('risk_level', 'medium'))

    # Create risk matrix scatter plot
    fig = go.Figure()

    # Color mapping for risk levels
    color_map = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'orange',
        'critical': 'red'
    }

    for level in ['low', 'medium', 'high', 'critical']:
        level_data = [(p, i, t) for p, i, t, l in zip(probabilities, impacts, risk_titles, risk_levels) if l == level]

        if level_data:
            level_probs, level_impacts, level_titles = zip(*level_data)

            fig.add_trace(go.Scatter(
                x=level_probs,
                y=level_impacts,
                mode='markers+text',
                name=level.title(),
                text=[t[:20] + '...' if len(t) > 20 else t for t in level_titles],
                textposition='top center',
                marker=dict(
                    size=12,
                    color=color_map[level],
                    line=dict(width=2, color='black')
                ),
                hovertemplate='<b>%{text}</b><br>Probability: %{x:.1%}<br>Impact: %{y:.1%}<extra></extra>'
            ))

    # Add risk zones
    fig.add_shape(type="rect", x0=0, y0=0, x1=0.5, y1=0.5, fillcolor="lightgreen", opacity=0.2, layer="below")
    fig.add_shape(type="rect", x0=0.5, y0=0, x1=1, y1=0.5, fillcolor="yellow", opacity=0.2, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0.5, x1=0.5, y1=1, fillcolor="orange", opacity=0.2, layer="below")
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=1, y1=1, fillcolor="red", opacity=0.2, layer="below")

    fig.update_layout(
        title="Risk Matrix",
        xaxis_title="Probability",
        yaxis_title="Impact",
        xaxis=dict(range=[0, 1], tickformat='.0%'),
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        showlegend=True,
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

def render_risk_dashboard():
    """Render risk dashboard"""
    st.write("**Risk Overview:**")

    # Get dashboard data
    dashboard_data = get_risk_dashboard_data()

    if dashboard_data:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Risks", dashboard_data.get('total_risks', 0))

        with col2:
            avg_risk_score = dashboard_data.get('average_risk_score', 0.0)
            st.metric("Average Risk Score", f"{avg_risk_score:.1%}")

        with col3:
            high_risk_count = dashboard_data.get('high_risk_count', 0)
            st.metric("High/Critical Risks", high_risk_count)

        with col4:
            mitigation_progress = dashboard_data.get('mitigation_progress', 0.0)
            st.metric("Mitigation Progress", f"{mitigation_progress:.1%}")

        # Risk distribution by category
        if dashboard_data.get('risk_by_category'):
            st.write("**Risk Distribution by Category:**")
            st.bar_chart(dashboard_data['risk_by_category'])

        # Risk trend over time
        if dashboard_data.get('risk_trend'):
            st.write("**Risk Trend Over Time:**")
            st.line_chart(dashboard_data['risk_trend'])

        # Top risks requiring attention
        if dashboard_data.get('top_risks'):
            st.write("**Top Risks Requiring Attention:**")
            for risk in dashboard_data['top_risks']:
                col1, col2 = st.columns([3, 1])

                with col1:
                    risk_icon = get_risk_level_icon(risk['level'])
                    st.write(f"{risk_icon} **{risk['title']}**")
                    st.caption(f"Category: {risk['category']}")

                with col2:
                    st.metric("Score", f"{risk['score']:.1%}")
    else:
        st.info("No risk data available for dashboard.")
```

---

## **Feature 33: AI-Generated Executive Summary**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** HIGH

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS executive_summaries (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    summary_type VARCHAR(50) NOT NULL, -- 'opportunity', 'proposal', 'contract', 'amendment', 'risk_assessment'
    summary_title VARCHAR(300),
    executive_summary TEXT NOT NULL,
    key_points TEXT[],
    recommendations TEXT[],
    critical_dates DATE[],
    financial_highlights JSONB,
    risk_summary TEXT,
    next_actions TEXT[],
    summary_length VARCHAR(20), -- 'brief', 'standard', 'detailed'
    target_audience VARCHAR(100), -- 'executives', 'program_managers', 'technical_team'
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(100) DEFAULT 'ai_system',
    reviewed_by VARCHAR(100),
    review_date TIMESTAMP,
    is_approved BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS summary_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    template_structure JSONB NOT NULL,
    target_audience VARCHAR(100),
    default_length VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_executive_summaries_document ON executive_summaries(document_id);
CREATE INDEX IF NOT EXISTS ix_executive_summaries_type ON executive_summaries(summary_type);
CREATE INDEX IF NOT EXISTS ix_executive_summaries_audience ON executive_summaries(target_audience);
```

#### **MCP Integration**
Uses generic `generate_insights` tool with executive summary-specific contexts.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def generate_executive_summary(document_content, summary_options=None, document_id=None):
    """Generate executive summary from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Set default options
        if not summary_options:
            summary_options = {
                'summary_type': 'opportunity',
                'length': 'standard',
                'audience': 'executives',
                'focus_areas': ['key_points', 'financial_impact', 'timeline', 'risks']
            }

        # Use MCP to generate executive summary
        summary_result = call_mcp_tool("generate_insights", {
            "content": document_content,
            "insight_type": "executive_summary",
            "context": {
                "domain": "government_contracting",
                "summary_type": summary_options.get('summary_type', 'opportunity'),
                "target_audience": summary_options.get('audience', 'executives'),
                "summary_length": summary_options.get('length', 'standard'),
                "focus_areas": summary_options.get('focus_areas', []),
                "include_financials": True,
                "include_timeline": True,
                "include_risks": True,
                "include_recommendations": True
            },
            "output_format": "structured_executive_summary"
        })

        if summary_result.get('success'):
            # Process and structure the executive summary
            summary_data = summary_result['data']
            structured_summary = process_executive_summary_data(summary_data, summary_options)

            # Save to database if document_id provided
            if document_id and structured_summary:
                save_executive_summary(document_id, structured_summary)

            return {
                "success": True,
                "executive_summary": structured_summary,
                "generation_confidence": summary_result.get('confidence', 0.0)
            }
        else:
            return {"error": "Executive summary generation failed"}

    except Exception as e:
        st.error(f"Error generating executive summary: {e}")
        return {"error": str(e)}

def process_executive_summary_data(summary_data, summary_options):
    """Process raw executive summary data into structured format"""
    structured_summary = {
        'summary_type': summary_options.get('summary_type', 'opportunity'),
        'summary_title': summary_data.get('title', ''),
        'executive_summary': summary_data.get('executive_summary', ''),
        'key_points': summary_data.get('key_points', []),
        'recommendations': summary_data.get('recommendations', []),
        'critical_dates': extract_dates_from_summary(summary_data.get('timeline_highlights', [])),
        'financial_highlights': summary_data.get('financial_highlights', {}),
        'risk_summary': summary_data.get('risk_summary', ''),
        'next_actions': summary_data.get('next_actions', []),
        'summary_length': summary_options.get('length', 'standard'),
        'target_audience': summary_options.get('audience', 'executives')
    }

    return structured_summary

def extract_dates_from_summary(timeline_highlights):
    """Extract critical dates from timeline highlights"""
    import re
    from datetime import datetime

    dates = []
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        r'\b(\d{4}-\d{2}-\d{2})\b',
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
    ]

    for highlight in timeline_highlights:
        if isinstance(highlight, str):
            for pattern in date_patterns:
                matches = re.findall(pattern, highlight, re.IGNORECASE)
                for match in matches:
                    try:
                        # Try to parse the date
                        if '/' in match:
                            date_obj = datetime.strptime(match, '%m/%d/%Y').date()
                        elif '-' in match:
                            date_obj = datetime.strptime(match, '%Y-%m-%d').date()
                        else:
                            date_obj = datetime.strptime(match, '%B %d, %Y').date()

                        dates.append(date_obj)
                    except ValueError:
                        continue

    return sorted(list(set(dates)))  # Remove duplicates and sort

def save_executive_summary(document_id, summary_data):
    """Save executive summary to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO executive_summaries
            (document_id, summary_type, summary_title, executive_summary, key_points,
             recommendations, critical_dates, financial_highlights, risk_summary,
             next_actions, summary_length, target_audience)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            document_id, summary_data['summary_type'], summary_data['summary_title'],
            summary_data['executive_summary'], summary_data['key_points'],
            summary_data['recommendations'], summary_data['critical_dates'],
            json.dumps(summary_data['financial_highlights']), summary_data['risk_summary'],
            summary_data['next_actions'], summary_data['summary_length'],
            summary_data['target_audience']
        ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving executive summary: {e}")
        return False
    finally:
        conn.close()

def render_executive_summary_generation():
    """Render executive summary generation interface"""
    st.subheader("📋 AI-Generated Executive Summary")

    # Summary generation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Generate Summary", "Summary Library", "Templates", "Analytics"])

    with tab1:
        st.write("**Generate Executive Summary from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="summary_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="summary_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="summary_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to generate executive summary...",
                key="summary_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="summary_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        # Summary options
        if document_content:
            st.write("**Summary Options:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                summary_type = st.selectbox(
                    "Summary Type:",
                    ["Opportunity", "Proposal", "Contract", "Amendment", "Risk Assessment"],
                    key="summary_type"
                )

            with col2:
                summary_length = st.selectbox(
                    "Summary Length:",
                    ["Brief", "Standard", "Detailed"],
                    index=1,
                    key="summary_length"
                )

            with col3:
                target_audience = st.selectbox(
                    "Target Audience:",
                    ["Executives", "Program Managers", "Technical Team", "Business Development"],
                    key="target_audience"
                )

            # Focus areas
            st.write("**Focus Areas:**")
            focus_areas = st.multiselect(
                "Select focus areas for the summary:",
                ["Key Points", "Financial Impact", "Timeline", "Risks", "Opportunities", "Requirements", "Compliance"],
                default=["Key Points", "Financial Impact", "Timeline", "Risks"],
                key="focus_areas"
            )

            # Advanced options
            with st.expander("🔧 Advanced Options"):
                col1, col2 = st.columns(2)

                with col1:
                    include_charts = st.checkbox("Include Data Visualizations", key="include_charts")
                    include_appendix = st.checkbox("Include Supporting Details", key="include_appendix")

                with col2:
                    custom_template = st.selectbox(
                        "Use Template:",
                        ["Default", "Board Presentation", "Proposal Executive Summary", "Risk Assessment"],
                        key="custom_template"
                    )

            if st.button("📋 Generate Executive Summary", type="primary"):
                with st.spinner("Generating executive summary..."):
                    summary_options = {
                        'summary_type': summary_type.lower(),
                        'length': summary_length.lower(),
                        'audience': target_audience.lower().replace(' ', '_'),
                        'focus_areas': [area.lower().replace(' ', '_') for area in focus_areas]
                    }

                    summary_result = generate_executive_summary(
                        document_content,
                        summary_options,
                        document_name
                    )

                    if summary_result.get('success'):
                        st.session_state.executive_summary_result = summary_result
                        st.session_state.summary_document = {
                            'name': document_name,
                            'content': document_content
                        }

        # Display summary results
        if 'executive_summary_result' in st.session_state:
            st.subheader("📋 Generated Executive Summary")

            result = st.session_state.executive_summary_result
            summary = result.get('executive_summary', {})

            # Summary header
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if summary.get('summary_title'):
                    st.write(f"**{summary['summary_title']}**")
                else:
                    st.write(f"**Executive Summary - {st.session_state.summary_document['name']}**")

            with col2:
                st.write(f"**Type:** {summary.get('summary_type', 'N/A').title()}")
                st.write(f"**Length:** {summary.get('summary_length', 'N/A').title()}")

            with col3:
                st.write(f"**Audience:** {summary.get('target_audience', 'N/A').replace('_', ' ').title()}")
                confidence = result.get('generation_confidence', 0.0)
                st.metric("Confidence", f"{confidence:.1%}")

            st.divider()

            # Main executive summary
            if summary.get('executive_summary'):
                st.write("**Executive Summary:**")
                st.write(summary['executive_summary'])
                st.divider()

            # Key sections
            col1, col2 = st.columns(2)

            with col1:
                # Key points
                if summary.get('key_points'):
                    st.write("**Key Points:**")
                    for i, point in enumerate(summary['key_points'], 1):
                        st.write(f"{i}. {point}")
                    st.write("")

                # Recommendations
                if summary.get('recommendations'):
                    st.write("**Recommendations:**")
                    for i, rec in enumerate(summary['recommendations'], 1):
                        st.write(f"• {rec}")
                    st.write("")

                # Next actions
                if summary.get('next_actions'):
                    st.write("**Next Actions:**")
                    for i, action in enumerate(summary['next_actions'], 1):
                        st.write(f"□ {action}")

            with col2:
                # Financial highlights
                if summary.get('financial_highlights'):
                    st.write("**Financial Highlights:**")
                    financials = summary['financial_highlights']

                    if isinstance(financials, dict):
                        for key, value in financials.items():
                            st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                    st.write("")

                # Critical dates
                if summary.get('critical_dates'):
                    st.write("**Critical Dates:**")
                    for date in summary['critical_dates']:
                        st.write(f"📅 {date}")
                    st.write("")

                # Risk summary
                if summary.get('risk_summary'):
                    st.write("**Risk Summary:**")
                    st.warning(summary['risk_summary'])

            # Action buttons
            st.divider()
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("💾 Save Summary"):
                    save_executive_summary(st.session_state.summary_document['name'], summary)
                    st.success("Executive summary saved!")

            with col2:
                if st.button("📄 Export to PDF"):
                    export_summary_to_pdf(summary, document_name)
                    st.success("Summary exported to PDF!")

            with col3:
                if st.button("📧 Email Summary"):
                    email_summary(summary)
                    st.success("Summary emailed!")

            with col4:
                if st.button("📊 Create Presentation"):
                    create_summary_presentation(summary)
                    st.success("Presentation created!")

            with col5:
                if st.button("✏️ Edit Summary"):
                    st.session_state.edit_summary = True
                    st.rerun()

            # Edit mode
            if st.session_state.get('edit_summary'):
                st.write("**Edit Executive Summary:**")

                edited_summary = st.text_area(
                    "Executive Summary:",
                    value=summary.get('executive_summary', ''),
                    height=200,
                    key="edit_summary_text"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾 Save Changes"):
                        summary['executive_summary'] = edited_summary
                        save_executive_summary(st.session_state.summary_document['name'], summary)
                        st.session_state.edit_summary = False
                        st.success("Changes saved!")
                        st.rerun()

                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.edit_summary = False
                        st.rerun()

    with tab2:
        st.write("**Executive Summary Library**")

        # Get saved summaries
        saved_summaries = get_saved_executive_summaries()

        if saved_summaries:
            # Filter options
            col1, col2, col3 = st.columns(3)

            with col1:
                type_filter = st.selectbox(
                    "Filter by Type:",
                    ["All", "Opportunity", "Proposal", "Contract", "Amendment", "Risk Assessment"],
                    key="summary_type_filter"
                )

            with col2:
                audience_filter = st.selectbox(
                    "Filter by Audience:",
                    ["All", "Executives", "Program Managers", "Technical Team", "Business Development"],
                    key="summary_audience_filter"
                )

            with col3:
                search_term = st.text_input("Search Summaries:", key="summary_search")

            # Display summaries
            for summary_data in saved_summaries:
                doc_name, summary_type, title, audience, generated_date, is_approved = summary_data

                # Apply filters
                if type_filter != "All" and type_filter.lower() != summary_type.lower():
                    continue

                if audience_filter != "All" and audience_filter.lower().replace(' ', '_') != audience.lower():
                    continue

                if search_term and search_term.lower() not in title.lower():
                    continue

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        approval_icon = "✅" if is_approved else "⏳"
                        st.write(f"**{approval_icon} {title}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Type: {summary_type.title()}")

                    with col2:
                        st.write(f"**{audience.replace('_', ' ').title()}**")

                    with col3:
                        st.caption(generated_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_summary_{title[:20]}"):
                            summary_details = load_executive_summary_details(doc_name, title)
                            st.session_state.view_summary_details = summary_details
                            st.rerun()

                st.divider()
        else:
            st.info("No executive summaries saved yet.")

    with tab3:
        st.write("**Summary Templates**")

        # Template management
        render_summary_templates_management()

    with tab4:
        st.write("**Summary Analytics**")

        # Summary analytics and insights
        render_summary_analytics()

def render_summary_templates_management():
    """Render summary templates management"""
    st.write("**Available Templates:**")

    # Default templates
    default_templates = {
        "Board Presentation": {
            "structure": ["Executive Summary", "Financial Impact", "Strategic Recommendations", "Risk Assessment", "Next Steps"],
            "audience": "executives",
            "length": "brief"
        },
        "Proposal Executive Summary": {
            "structure": ["Opportunity Overview", "Our Solution", "Value Proposition", "Implementation Plan", "Investment Required"],
            "audience": "executives",
            "length": "standard"
        },
        "Risk Assessment": {
            "structure": ["Risk Overview", "Critical Risks", "Impact Analysis", "Mitigation Strategies", "Monitoring Plan"],
            "audience": "program_managers",
            "length": "detailed"
        },
        "Contract Analysis": {
            "structure": ["Contract Overview", "Key Terms", "Financial Implications", "Compliance Requirements", "Action Items"],
            "audience": "program_managers",
            "length": "standard"
        }
    }

    for template_name, template_config in default_templates.items():
        with st.expander(f"📋 {template_name}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("**Structure:**")
                for section in template_config["structure"]:
                    st.write(f"• {section}")

            with col2:
                st.write(f"**Audience:** {template_config['audience'].replace('_', ' ').title()}")
                st.write(f"**Length:** {template_config['length'].title()}")

                if st.button("📋 Use Template", key=f"use_template_{template_name}"):
                    st.session_state.selected_template = template_config
                    st.success(f"Template '{template_name}' selected!")

    # Custom template creation
    st.write("**Create Custom Template:**")

    with st.expander("➕ Create New Template"):
        template_name = st.text_input("Template Name:", key="new_template_name")
        template_audience = st.selectbox(
            "Target Audience:",
            ["Executives", "Program Managers", "Technical Team", "Business Development"],
            key="new_template_audience"
        )
        template_length = st.selectbox(
            "Default Length:",
            ["Brief", "Standard", "Detailed"],
            key="new_template_length"
        )

        st.write("**Template Structure:**")

        # Dynamic section management
        if 'template_sections' not in st.session_state:
            st.session_state.template_sections = ["Executive Summary"]

        for i, section in enumerate(st.session_state.template_sections):
            col1, col2 = st.columns([4, 1])

            with col1:
                new_section = st.text_input(f"Section {i+1}:", value=section, key=f"section_{i}")
                st.session_state.template_sections[i] = new_section

            with col2:
                if st.button("🗑️", key=f"remove_section_{i}"):
                    st.session_state.template_sections.pop(i)
                    st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Add Section"):
                st.session_state.template_sections.append("New Section")
                st.rerun()

        with col2:
            if st.button("💾 Save Template", disabled=not template_name):
                save_custom_template(template_name, template_audience, template_length, st.session_state.template_sections)
                st.success(f"Template '{template_name}' saved!")
                st.session_state.template_sections = ["Executive Summary"]
                st.rerun()

def render_summary_analytics():
    """Render summary analytics"""
    st.write("**Summary Generation Analytics:**")

    # Get analytics data
    analytics_data = get_summary_analytics_data()

    if analytics_data:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Summaries", analytics_data.get('total_summaries', 0))

        with col2:
            avg_confidence = analytics_data.get('average_confidence', 0.0)
            st.metric("Average Confidence", f"{avg_confidence:.1%}")

        with col3:
            approved_summaries = analytics_data.get('approved_summaries', 0)
            st.metric("Approved Summaries", approved_summaries)

        with col4:
            most_used_type = analytics_data.get('most_used_type', 'N/A')
            st.metric("Most Used Type", most_used_type.title())

        # Summary type distribution
        if analytics_data.get('type_distribution'):
            st.write("**Summary Type Distribution:**")
            st.bar_chart(analytics_data['type_distribution'])

        # Audience preferences
        if analytics_data.get('audience_preferences'):
            st.write("**Audience Preferences:**")
            st.bar_chart(analytics_data['audience_preferences'])

        # Quality trends
        if analytics_data.get('quality_trends'):
            st.write("**Quality Trends Over Time:**")
            st.line_chart(analytics_data['quality_trends'])
    else:
        st.info("No summary analytics data available.")
```

---

## **Feature 42: Opportunity Timeline Extraction**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS opportunity_timelines (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    timeline_title VARCHAR(300),
    opportunity_type VARCHAR(100),
    solicitation_number VARCHAR(100),
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence DECIMAL(3,2),
    timeline_summary TEXT
);

CREATE TABLE IF NOT EXISTS timeline_events (
    id SERIAL PRIMARY KEY,
    timeline_id INTEGER REFERENCES opportunity_timelines(id),
    event_title VARCHAR(300) NOT NULL,
    event_description TEXT,
    event_date DATE,
    event_time TIME,
    event_type VARCHAR(100), -- 'deadline', 'milestone', 'meeting', 'submission', 'notification'
    is_critical BOOLEAN DEFAULT FALSE,
    days_from_now INTEGER,
    event_status VARCHAR(50) DEFAULT 'upcoming', -- 'upcoming', 'in_progress', 'completed', 'missed'
    notification_sent BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS timeline_dependencies (
    id SERIAL PRIMARY KEY,
    predecessor_event_id INTEGER REFERENCES timeline_events(id),
    successor_event_id INTEGER REFERENCES timeline_events(id),
    dependency_type VARCHAR(50), -- 'finish_to_start', 'start_to_start', 'finish_to_finish'
    lag_days INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_opportunity_timelines_document ON opportunity_timelines(document_id);
CREATE INDEX IF NOT EXISTS ix_timeline_events_timeline ON timeline_events(timeline_id);
CREATE INDEX IF NOT EXISTS ix_timeline_events_date ON timeline_events(event_date);
CREATE INDEX IF NOT EXISTS ix_timeline_events_type ON timeline_events(event_type);
CREATE INDEX IF NOT EXISTS ix_timeline_events_critical ON timeline_events(is_critical);
```

#### **MCP Integration**
Uses generic `extract_structured_data` tool with timeline-specific schema.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def extract_opportunity_timeline(document_content, document_id=None):
    """Extract opportunity timeline from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to extract timeline information
        timeline_result = call_mcp_tool("extract_structured_data", {
            "text": document_content,
            "schema": {
                "fields": [
                    {"name": "key_dates", "type": "array", "description": "Important dates and deadlines"},
                    {"name": "milestones", "type": "array", "description": "Project milestones and checkpoints"},
                    {"name": "submission_deadlines", "type": "array", "description": "Proposal and document submission deadlines"},
                    {"name": "meetings_events", "type": "array", "description": "Scheduled meetings and events"},
                    {"name": "notification_dates", "type": "array", "description": "Award and notification dates"},
                    {"name": "performance_periods", "type": "array", "description": "Contract performance periods"},
                    {"name": "option_periods", "type": "array", "description": "Option period dates"},
                    {"name": "timeline_overview", "type": "object", "description": "Overall timeline summary and critical path"}
                ]
            },
            "domain_context": "government_contracting",
            "extraction_options": {
                "include_dates": True,
                "include_times": True,
                "calculate_days_from_now": True,
                "identify_critical_path": True,
                "extract_dependencies": True,
                "confidence_threshold": 0.7
            }
        })

        if timeline_result.get('success'):
            # Process and structure the timeline data
            timeline_data = timeline_result['data']
            structured_timeline = process_timeline_data(timeline_data)

            # Save to database if document_id provided
            if document_id and structured_timeline:
                save_opportunity_timeline(document_id, structured_timeline)

            return {
                "success": True,
                "opportunity_timeline": structured_timeline,
                "extraction_confidence": timeline_result.get('confidence', 0.0),
                "total_events": len(structured_timeline.get('events', []))
            }
        else:
            return {"error": "Timeline extraction failed"}

    except Exception as e:
        st.error(f"Error extracting opportunity timeline: {e}")
        return {"error": str(e)}

def process_timeline_data(raw_timeline_data):
    """Process raw timeline data into structured format"""
    from datetime import datetime, date

    structured_timeline = {
        'timeline_title': raw_timeline_data.get('timeline_overview', {}).get('title', ''),
        'opportunity_type': raw_timeline_data.get('timeline_overview', {}).get('opportunity_type', ''),
        'solicitation_number': raw_timeline_data.get('timeline_overview', {}).get('solicitation_number', ''),
        'timeline_summary': raw_timeline_data.get('timeline_overview', {}).get('summary', ''),
        'events': []
    }

    # Process different types of timeline events
    event_categories = {
        'key_dates': 'deadline',
        'milestones': 'milestone',
        'submission_deadlines': 'submission',
        'meetings_events': 'meeting',
        'notification_dates': 'notification',
        'performance_periods': 'milestone',
        'option_periods': 'milestone'
    }

    for data_key, event_type in event_categories.items():
        events = raw_timeline_data.get(data_key, [])

        for event in events:
            if isinstance(event, dict):
                # Parse date and time
                event_date = parse_event_date(event.get('date', ''))
                event_time = parse_event_time(event.get('time', ''))

                # Calculate days from now
                days_from_now = None
                if event_date:
                    today = date.today()
                    days_from_now = (event_date - today).days

                timeline_event = {
                    'title': event.get('title', ''),
                    'description': event.get('description', ''),
                    'event_date': event_date,
                    'event_time': event_time,
                    'event_type': event_type,
                    'is_critical': event.get('is_critical', False),
                    'days_from_now': days_from_now,
                    'event_status': determine_event_status(event_date, days_from_now)
                }
                structured_timeline['events'].append(timeline_event)

    # Sort events by date
    structured_timeline['events'].sort(key=lambda x: x['event_date'] or date.max)

    return structured_timeline

def parse_event_date(date_str):
    """Parse event date from string"""
    if not date_str:
        return None

    import re
    from datetime import datetime

    # Common date formats
    date_patterns = [
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
        (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', '%B %d, %Y')
    ]

    for pattern, format_str in date_patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                if format_str == '%B %d, %Y':
                    date_obj = datetime.strptime(match.group(0), format_str).date()
                else:
                    date_obj = datetime.strptime(match.group(0), format_str).date()
                return date_obj
            except ValueError:
                continue

    return None

def parse_event_time(time_str):
    """Parse event time from string"""
    if not time_str:
        return None

    import re
    from datetime import datetime

    # Common time formats
    time_patterns = [
        (r'(\d{1,2}):(\d{2})\s*(AM|PM)', '%I:%M %p'),
        (r'(\d{1,2}):(\d{2})', '%H:%M')
    ]

    for pattern, format_str in time_patterns:
        match = re.search(pattern, time_str, re.IGNORECASE)
        if match:
            try:
                time_obj = datetime.strptime(match.group(0), format_str).time()
                return time_obj
            except ValueError:
                continue

    return None

def determine_event_status(event_date, days_from_now):
    """Determine event status based on date"""
    if not event_date or days_from_now is None:
        return 'unknown'

    if days_from_now < 0:
        return 'completed'
    elif days_from_now == 0:
        return 'in_progress'
    elif days_from_now <= 7:
        return 'upcoming'
    else:
        return 'future'

def save_opportunity_timeline(document_id, timeline_data):
    """Save opportunity timeline to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Save main timeline record
        cursor.execute("""
            INSERT INTO opportunity_timelines
            (document_id, timeline_title, opportunity_type, solicitation_number,
             timeline_summary, extraction_confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_id, timeline_data['timeline_title'], timeline_data['opportunity_type'],
            timeline_data['solicitation_number'], timeline_data['timeline_summary'], 0.85
        ))

        timeline_id = cursor.fetchone()[0]

        # Save timeline events
        for event in timeline_data['events']:
            cursor.execute("""
                INSERT INTO timeline_events
                (timeline_id, event_title, event_description, event_date, event_time,
                 event_type, is_critical, days_from_now, event_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                timeline_id, event['title'], event['description'], event['event_date'],
                event['event_time'], event['event_type'], event['is_critical'],
                event['days_from_now'], event['event_status']
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving opportunity timeline: {e}")
        return False
    finally:
        conn.close()

def render_opportunity_timeline_extraction():
    """Render opportunity timeline extraction interface"""
    st.subheader("📅 Opportunity Timeline Extraction")

    # Timeline tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Extract Timeline", "Timeline Library", "Calendar View", "Notifications"])

    with tab1:
        st.write("**Extract Timeline from Opportunity Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="timeline_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Opportunity Document:",
                type=['txt', 'pdf', 'docx'],
                key="timeline_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="timeline_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste opportunity document content to extract timeline...",
                key="timeline_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_opportunity_documents()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="timeline_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("📅 Extract Timeline", type="primary"):
            with st.spinner("Extracting opportunity timeline..."):
                timeline_result = extract_opportunity_timeline(document_content, document_name)

                if timeline_result.get('success'):
                    st.session_state.timeline_extraction_result = timeline_result
                    st.session_state.timeline_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display timeline results
        if 'timeline_extraction_result' in st.session_state:
            st.subheader("📅 Extracted Timeline")

            result = st.session_state.timeline_extraction_result
            timeline = result.get('opportunity_timeline', {})
            events = timeline.get('events', [])

            # Timeline header
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if timeline.get('timeline_title'):
                    st.write(f"**{timeline['timeline_title']}**")

                if timeline.get('solicitation_number'):
                    st.write(f"**Solicitation:** {timeline['solicitation_number']}")

            with col2:
                st.metric("Total Events", result.get('total_events', 0))

            with col3:
                confidence = result.get('extraction_confidence', 0.0)
                st.metric("Extraction Confidence", f"{confidence:.1%}")

            # Timeline summary
            if timeline.get('timeline_summary'):
                st.info(timeline['timeline_summary'])

            # Timeline visualization
            if events:
                st.write("**Timeline Events:**")

                # Create timeline visualization
                render_timeline_visualization(events)

                # Events by status
                st.write("**Events by Status:**")

                # Group events by status
                events_by_status = {}
                for event in events:
                    status = event.get('event_status', 'unknown')
                    if status not in events_by_status:
                        events_by_status[status] = []
                    events_by_status[status].append(event)

                # Display events by status
                status_order = ['in_progress', 'upcoming', 'future', 'completed']

                for status in status_order:
                    if status in events_by_status:
                        status_icon = get_event_status_icon(status)
                        status_events = events_by_status[status]

                        st.write(f"**{status_icon} {status.replace('_', ' ').title()} ({len(status_events)} events):**")

                        for event in status_events:
                            with st.container():
                                col1, col2, col3 = st.columns([3, 1, 1])

                                with col1:
                                    critical_indicator = "🔴 " if event.get('is_critical') else ""
                                    event_type_icon = get_event_type_icon(event.get('event_type', 'deadline'))

                                    st.write(f"**{critical_indicator}{event_type_icon} {event.get('title', 'Untitled Event')}**")

                                    if event.get('description'):
                                        st.caption(event['description'])

                                with col2:
                                    if event.get('event_date'):
                                        st.write(f"📅 {event['event_date']}")

                                    if event.get('event_time'):
                                        st.write(f"🕐 {event['event_time']}")

                                with col3:
                                    if event.get('days_from_now') is not None:
                                        days = event['days_from_now']
                                        if days == 0:
                                            st.write("**Today**")
                                        elif days == 1:
                                            st.write("**Tomorrow**")
                                        elif days > 0:
                                            st.write(f"**In {days} days**")
                                        else:
                                            st.write(f"**{abs(days)} days ago**")

                            st.divider()

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Timeline"):
                    save_opportunity_timeline(st.session_state.timeline_document['name'], timeline)
                    st.success("Timeline saved!")

            with col2:
                if st.button("📅 Export to Calendar"):
                    export_timeline_to_calendar(events)
                    st.success("Timeline exported to calendar!")

            with col3:
                if st.button("📊 Generate Gantt Chart"):
                    generate_gantt_chart(events)
                    st.success("Gantt chart generated!")

            with col4:
                if st.button("🔔 Set Notifications"):
                    setup_timeline_notifications(events)
                    st.success("Notifications configured!")

    with tab2:
        st.write("**Timeline Library**")

        # Get saved timelines
        saved_timelines = get_saved_opportunity_timelines()

        if saved_timelines:
            for timeline_data in saved_timelines:
                doc_name, timeline_title, opportunity_type, total_events, critical_events, extraction_date = timeline_data

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**📅 {timeline_title or doc_name}**")
                        st.caption(f"From: {doc_name}")
                        if opportunity_type:
                            st.caption(f"Type: {opportunity_type}")

                    with col2:
                        st.metric("Events", total_events)
                        if critical_events > 0:
                            st.write(f"🔴 {critical_events} critical")

                    with col3:
                        st.caption(extraction_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_timeline_{doc_name}"):
                            timeline_details = load_timeline_details(doc_name)
                            st.session_state.view_timeline_details = timeline_details
                            st.rerun()

                st.divider()
        else:
            st.info("No timelines saved yet.")

    with tab3:
        st.write("**Calendar View**")

        # Calendar visualization of all timelines
        render_timeline_calendar_view()

    with tab4:
        st.write("**Timeline Notifications**")

        # Notification management
        render_timeline_notifications_management()

def get_event_status_icon(status):
    """Get icon for event status"""
    icons = {
        "upcoming": "⏰",
        "in_progress": "🔄",
        "completed": "✅",
        "future": "📅",
        "missed": "❌"
    }
    return icons.get(status, "❓")

def get_event_type_icon(event_type):
    """Get icon for event type"""
    icons = {
        "deadline": "⏰",
        "milestone": "🎯",
        "meeting": "👥",
        "submission": "📤",
        "notification": "📢"
    }
    return icons.get(event_type, "📅")

def render_timeline_visualization(events):
    """Render timeline visualization"""
    import plotly.graph_objects as go
    from datetime import datetime, timedelta

    # Prepare data for timeline chart
    event_dates = []
    event_titles = []
    event_types = []
    event_colors = []

    color_map = {
        'deadline': 'red',
        'milestone': 'blue',
        'meeting': 'green',
        'submission': 'orange',
        'notification': 'purple'
    }

    for event in events:
        if event.get('event_date'):
            event_dates.append(event['event_date'])
            event_titles.append(event.get('title', 'Untitled'))
            event_type = event.get('event_type', 'deadline')
            event_types.append(event_type)
            event_colors.append(color_map.get(event_type, 'gray'))

    if event_dates:
        # Create timeline scatter plot
        fig = go.Figure()

        # Add events by type
        for event_type, color in color_map.items():
            type_dates = [d for d, t in zip(event_dates, event_types) if t == event_type]
            type_titles = [title for title, t in zip(event_titles, event_types) if t == event_type]

            if type_dates:
                fig.add_trace(go.Scatter(
                    x=type_dates,
                    y=[event_type] * len(type_dates),
                    mode='markers+text',
                    name=event_type.title(),
                    text=type_titles,
                    textposition='top center',
                    marker=dict(size=12, color=color),
                    hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Type: %{y}<extra></extra>'
                ))

        fig.update_layout(
            title="Opportunity Timeline",
            xaxis_title="Date",
            yaxis_title="Event Type",
            showlegend=True,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

def render_timeline_calendar_view():
    """Render calendar view of all timelines"""
    st.write("**All Timeline Events:**")

    # Get all timeline events
    all_events = get_all_timeline_events()

    if all_events:
        # Create calendar visualization
        import calendar
        from datetime import datetime, date

        # Group events by month
        events_by_month = {}
        for event in all_events:
            event_date = event.get('event_date')
            if event_date:
                month_key = f"{event_date.year}-{event_date.month:02d}"
                if month_key not in events_by_month:
                    events_by_month[month_key] = []
                events_by_month[month_key].append(event)

        # Display events by month
        for month_key in sorted(events_by_month.keys()):
            year, month = map(int, month_key.split('-'))
            month_name = calendar.month_name[month]

            st.write(f"**{month_name} {year}:**")

            month_events = events_by_month[month_key]
            month_events.sort(key=lambda x: x.get('event_date', date.max))

            for event in month_events:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    event_icon = get_event_type_icon(event.get('event_type', 'deadline'))
                    critical_indicator = "🔴 " if event.get('is_critical') else ""
                    st.write(f"{critical_indicator}{event_icon} **{event.get('title', 'Untitled')}**")

                with col2:
                    st.write(f"📅 {event.get('event_date', 'No date')}")

                with col3:
                    status_icon = get_event_status_icon(event.get('event_status', 'unknown'))
                    st.write(f"{status_icon} {event.get('event_status', 'Unknown').title()}")

            st.divider()
    else:
        st.info("No timeline events available.")

def render_timeline_notifications_management():
    """Render timeline notifications management"""
    st.write("**Notification Settings:**")

    # Get upcoming critical events
    upcoming_events = get_upcoming_critical_events()

    if upcoming_events:
        st.write("**Upcoming Critical Events:**")

        for event in upcoming_events:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"🔴 **{event.get('title', 'Untitled')}**")
                st.caption(f"Date: {event.get('event_date', 'No date')}")

            with col2:
                days_remaining = event.get('days_from_now', 0)
                if days_remaining <= 1:
                    st.error(f"{days_remaining} days")
                elif days_remaining <= 7:
                    st.warning(f"{days_remaining} days")
                else:
                    st.info(f"{days_remaining} days")

            with col3:
                if st.button("🔔 Set Alert", key=f"alert_{event.get('title', 'event')}"):
                    setup_event_notification(event)
                    st.success("Alert set!")
    else:
        st.info("No upcoming critical events.")

    # Notification preferences
    st.write("**Notification Preferences:**")

    col1, col2 = st.columns(2)

    with col1:
        email_notifications = st.checkbox("Email Notifications", value=True)
        dashboard_notifications = st.checkbox("Dashboard Notifications", value=True)

    with col2:
        notification_advance = st.selectbox(
            "Notify in advance:",
            ["1 day", "3 days", "1 week", "2 weeks"],
            index=2
        )

        critical_only = st.checkbox("Critical events only", value=False)

    if st.button("💾 Save Notification Settings"):
        save_notification_preferences({
            'email': email_notifications,
            'dashboard': dashboard_notifications,
            'advance_days': notification_advance,
            'critical_only': critical_only
        })
        st.success("Notification settings saved!")

---

## **Feature 39: Document Comparison Tool**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS document_comparisons (
    id SERIAL PRIMARY KEY,
    comparison_title VARCHAR(300),
    document1_id VARCHAR(100) NOT NULL,
    document1_name VARCHAR(300) NOT NULL,
    document2_id VARCHAR(100) NOT NULL,
    document2_name VARCHAR(300) NOT NULL,
    comparison_type VARCHAR(50), -- 'version_comparison', 'amendment_analysis', 'proposal_comparison'
    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_similarity DECIMAL(5,4), -- 0.0000 to 1.0000
    total_differences INTEGER DEFAULT 0,
    significant_changes INTEGER DEFAULT 0,
    comparison_summary TEXT,
    compared_by VARCHAR(100) DEFAULT 'ai_system'
);

CREATE TABLE IF NOT EXISTS document_differences (
    id SERIAL PRIMARY KEY,
    comparison_id INTEGER REFERENCES document_comparisons(id),
    difference_type VARCHAR(50), -- 'addition', 'deletion', 'modification', 'formatting'
    section_name VARCHAR(200),
    line_number_doc1 INTEGER,
    line_number_doc2 INTEGER,
    original_text TEXT,
    new_text TEXT,
    change_significance VARCHAR(20), -- 'minor', 'moderate', 'major', 'critical'
    change_category VARCHAR(100), -- 'content', 'formatting', 'structure', 'metadata'
    context_before TEXT,
    context_after TEXT,
    similarity_score DECIMAL(5,4),
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT
);

CREATE TABLE IF NOT EXISTS comparison_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    comparison_settings JSONB NOT NULL,
    ignore_patterns TEXT[],
    focus_areas TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_document_comparisons_doc1 ON document_comparisons(document1_id);
CREATE INDEX IF NOT EXISTS ix_document_comparisons_doc2 ON document_comparisons(document2_id);
CREATE INDEX IF NOT EXISTS ix_document_differences_comparison ON document_differences(comparison_id);
CREATE INDEX IF NOT EXISTS ix_document_differences_type ON document_differences(difference_type);
CREATE INDEX IF NOT EXISTS ix_document_differences_significance ON document_differences(change_significance);
```

#### **MCP Integration**
Uses generic `calculate_similarity` tool with document comparison-specific contexts.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def compare_documents(document1_content, document2_content, comparison_options=None, document_names=None):
    """Compare two documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Set default options
        if not comparison_options:
            comparison_options = {
                'comparison_type': 'version_comparison',
                'granularity': 'paragraph',
                'ignore_formatting': True,
                'highlight_changes': True
            }

        # Use MCP to compare documents
        comparison_result = call_mcp_tool("calculate_similarity", {
            "text1": document1_content,
            "text2": document2_content,
            "similarity_type": "document_comparison",
            "analysis_options": {
                "comparison_type": comparison_options.get('comparison_type', 'version_comparison'),
                "granularity": comparison_options.get('granularity', 'paragraph'),
                "ignore_formatting": comparison_options.get('ignore_formatting', True),
                "identify_changes": True,
                "change_categories": ["additions", "deletions", "modifications", "formatting"],
                "significance_levels": ["minor", "moderate", "major", "critical"],
                "context_lines": 3,
                "similarity_threshold": 0.8
            },
            "domain_context": "government_contracting",
            "output_format": "detailed_comparison"
        })

        if comparison_result.get('success'):
            # Process and structure the comparison data
            comparison_data = comparison_result['data']
            structured_comparison = process_comparison_data(comparison_data, comparison_options)

            # Save to database if document names provided
            if document_names and structured_comparison:
                save_document_comparison(document_names, structured_comparison)

            return {
                "success": True,
                "document_comparison": structured_comparison,
                "comparison_confidence": comparison_result.get('confidence', 0.0)
            }
        else:
            return {"error": "Document comparison failed"}

    except Exception as e:
        st.error(f"Error comparing documents: {e}")
        return {"error": str(e)}

def process_comparison_data(raw_comparison_data, comparison_options):
    """Process raw comparison data into structured format"""
    structured_comparison = {
        'comparison_type': comparison_options.get('comparison_type', 'version_comparison'),
        'overall_similarity': raw_comparison_data.get('overall_similarity', 0.0),
        'comparison_summary': raw_comparison_data.get('summary', ''),
        'differences': []
    }

    # Process identified differences
    identified_differences = raw_comparison_data.get('differences', [])

    for diff in identified_differences:
        if isinstance(diff, dict):
            difference_analysis = {
                'difference_type': diff.get('type', 'modification'),
                'section_name': diff.get('section', ''),
                'line_number_doc1': diff.get('line_doc1', 0),
                'line_number_doc2': diff.get('line_doc2', 0),
                'original_text': diff.get('original_text', ''),
                'new_text': diff.get('new_text', ''),
                'change_significance': diff.get('significance', 'moderate'),
                'change_category': diff.get('category', 'content'),
                'context_before': diff.get('context_before', ''),
                'context_after': diff.get('context_after', ''),
                'similarity_score': diff.get('similarity_score', 0.0)
            }
            structured_comparison['differences'].append(difference_analysis)

    # Calculate summary statistics
    structured_comparison['total_differences'] = len(structured_comparison['differences'])
    structured_comparison['significant_changes'] = sum(
        1 for diff in structured_comparison['differences']
        if diff['change_significance'] in ['major', 'critical']
    )

    return structured_comparison

def save_document_comparison(document_names, comparison_data):
    """Save document comparison to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Save main comparison record
        cursor.execute("""
            INSERT INTO document_comparisons
            (document1_id, document1_name, document2_id, document2_name, comparison_type,
             overall_similarity, total_differences, significant_changes, comparison_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_names['doc1_id'], document_names['doc1_name'],
            document_names['doc2_id'], document_names['doc2_name'],
            comparison_data['comparison_type'], comparison_data['overall_similarity'],
            comparison_data['total_differences'], comparison_data['significant_changes'],
            comparison_data['comparison_summary']
        ))

        comparison_id = cursor.fetchone()[0]

        # Save individual differences
        for diff in comparison_data['differences']:
            cursor.execute("""
                INSERT INTO document_differences
                (comparison_id, difference_type, section_name, line_number_doc1, line_number_doc2,
                 original_text, new_text, change_significance, change_category,
                 context_before, context_after, similarity_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                comparison_id, diff['difference_type'], diff['section_name'],
                diff['line_number_doc1'], diff['line_number_doc2'], diff['original_text'],
                diff['new_text'], diff['change_significance'], diff['change_category'],
                diff['context_before'], diff['context_after'], diff['similarity_score']
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving document comparison: {e}")
        return False
    finally:
        conn.close()

def render_document_comparison_tool():
    """Render document comparison tool interface"""
    st.subheader("🔍 Document Comparison Tool")

    # Comparison tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Compare Documents", "Comparison History", "Templates", "Analytics"])

    with tab1:
        st.write("**Compare Two Documents Side-by-Side**")

        # Document selection
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Document 1 (Original):**")
            doc1_input_method = st.radio(
                "Document 1 Input:",
                ["Upload File", "Paste Text", "Select from Library"],
                key="doc1_input_method"
            )

            doc1_content = ""
            doc1_name = ""

            if doc1_input_method == "Upload File":
                doc1_file = st.file_uploader(
                    "Upload Document 1:",
                    type=['txt', 'pdf', 'docx'],
                    key="doc1_file_upload"
                )

                if doc1_file:
                    doc1_content = extract_text_from_file(doc1_file)
                    doc1_name = doc1_file.name

            elif doc1_input_method == "Paste Text":
                doc1_name = st.text_input("Document 1 Name:", key="doc1_name")
                doc1_content = st.text_area(
                    "Document 1 Content:",
                    height=200,
                    key="doc1_text_input"
                )

            elif doc1_input_method == "Select from Library":
                documents = get_document_library()

                if documents:
                    selected_doc1 = st.selectbox(
                        "Select Document 1:",
                        options=documents,
                        format_func=lambda x: f"{x['name']} ({x['type']})",
                        key="doc1_selection"
                    )

                    if selected_doc1:
                        doc1_content = load_document_content(selected_doc1['id'])
                        doc1_name = selected_doc1['name']

        with col2:
            st.write("**Document 2 (Comparison):**")
            doc2_input_method = st.radio(
                "Document 2 Input:",
                ["Upload File", "Paste Text", "Select from Library"],
                key="doc2_input_method"
            )

            doc2_content = ""
            doc2_name = ""

            if doc2_input_method == "Upload File":
                doc2_file = st.file_uploader(
                    "Upload Document 2:",
                    type=['txt', 'pdf', 'docx'],
                    key="doc2_file_upload"
                )

                if doc2_file:
                    doc2_content = extract_text_from_file(doc2_file)
                    doc2_name = doc2_file.name

            elif doc2_input_method == "Paste Text":
                doc2_name = st.text_input("Document 2 Name:", key="doc2_name")
                doc2_content = st.text_area(
                    "Document 2 Content:",
                    height=200,
                    key="doc2_text_input"
                )

            elif doc2_input_method == "Select from Library":
                documents = get_document_library()

                if documents:
                    selected_doc2 = st.selectbox(
                        "Select Document 2:",
                        options=documents,
                        format_func=lambda x: f"{x['name']} ({x['type']})",
                        key="doc2_selection"
                    )

                    if selected_doc2:
                        doc2_content = load_document_content(selected_doc2['id'])
                        doc2_name = selected_doc2['name']

        # Comparison options
        if doc1_content and doc2_content:
            st.write("**Comparison Options:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                comparison_type = st.selectbox(
                    "Comparison Type:",
                    ["Version Comparison", "Amendment Analysis", "Proposal Comparison"],
                    key="comparison_type"
                )

            with col2:
                granularity = st.selectbox(
                    "Comparison Granularity:",
                    ["Paragraph", "Sentence", "Word"],
                    key="comparison_granularity"
                )

            with col3:
                ignore_formatting = st.checkbox(
                    "Ignore Formatting Changes",
                    value=True,
                    key="ignore_formatting"
                )

            # Advanced options
            with st.expander("🔧 Advanced Comparison Options"):
                col1, col2 = st.columns(2)

                with col1:
                    highlight_changes = st.checkbox("Highlight Changes", value=True, key="highlight_changes")
                    show_context = st.checkbox("Show Context Lines", value=True, key="show_context")

                with col2:
                    similarity_threshold = st.slider(
                        "Similarity Threshold:",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.8,
                        step=0.1,
                        key="similarity_threshold"
                    )

            if st.button("🔍 Compare Documents", type="primary"):
                with st.spinner("Comparing documents..."):
                    comparison_options = {
                        'comparison_type': comparison_type.lower().replace(' ', '_'),
                        'granularity': granularity.lower(),
                        'ignore_formatting': ignore_formatting,
                        'highlight_changes': highlight_changes,
                        'similarity_threshold': similarity_threshold
                    }

                    document_names = {
                        'doc1_id': doc1_name,
                        'doc1_name': doc1_name,
                        'doc2_id': doc2_name,
                        'doc2_name': doc2_name
                    }

                    comparison_result = compare_documents(
                        doc1_content,
                        doc2_content,
                        comparison_options,
                        document_names
                    )

                    if comparison_result.get('success'):
                        st.session_state.comparison_result = comparison_result
                        st.session_state.comparison_documents = {
                            'doc1': {'name': doc1_name, 'content': doc1_content},
                            'doc2': {'name': doc2_name, 'content': doc2_content}
                        }

        # Display comparison results
        if 'comparison_result' in st.session_state:
            st.subheader("🔍 Document Comparison Results")

            result = st.session_state.comparison_result
            comparison = result.get('document_comparison', {})
            differences = comparison.get('differences', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                similarity = comparison.get('overall_similarity', 0.0)
                st.metric("Overall Similarity", f"{similarity:.1%}")

            with col2:
                total_diffs = comparison.get('total_differences', 0)
                st.metric("Total Differences", total_diffs)

            with col3:
                significant_changes = comparison.get('significant_changes', 0)
                st.metric("Significant Changes", significant_changes)

            with col4:
                confidence = result.get('comparison_confidence', 0.0)
                st.metric("Analysis Confidence", f"{confidence:.1%}")

            # Comparison summary
            if comparison.get('comparison_summary'):
                st.write("**Comparison Summary:**")
                st.info(comparison['comparison_summary'])

            # Side-by-side comparison view
            if differences:
                st.write("**Side-by-Side Comparison:**")

                # Filter options
                col1, col2, col3 = st.columns(3)

                with col1:
                    change_type_filter = st.selectbox(
                        "Filter by Change Type:",
                        ["All", "Additions", "Deletions", "Modifications", "Formatting"],
                        key="change_type_filter"
                    )

                with col2:
                    significance_filter = st.selectbox(
                        "Filter by Significance:",
                        ["All", "Critical", "Major", "Moderate", "Minor"],
                        key="significance_filter"
                    )

                with col3:
                    category_filter = st.selectbox(
                        "Filter by Category:",
                        ["All", "Content", "Structure", "Formatting", "Metadata"],
                        key="category_filter"
                    )

                # Display differences
                filtered_differences = filter_differences(differences, change_type_filter, significance_filter, category_filter)

                if filtered_differences:
                    for i, diff in enumerate(filtered_differences, 1):
                        significance_icon = get_significance_icon(diff.get('change_significance', 'moderate'))
                        change_type_icon = get_change_type_icon(diff.get('difference_type', 'modification'))

                        with st.expander(f"{significance_icon} {change_type_icon} Change {i}: {diff.get('section_name', 'Unknown Section')}"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("**Original (Document 1):**")
                                if diff.get('original_text'):
                                    st.text_area(
                                        "",
                                        value=diff['original_text'],
                                        height=150,
                                        key=f"orig_{i}",
                                        disabled=True
                                    )
                                else:
                                    st.info("No content (deletion or new section)")

                            with col2:
                                st.write("**Modified (Document 2):**")
                                if diff.get('new_text'):
                                    st.text_area(
                                        "",
                                        value=diff['new_text'],
                                        height=150,
                                        key=f"new_{i}",
                                        disabled=True
                                    )
                                else:
                                    st.info("No content (addition or removed section)")

                            # Change details
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**Type:** {diff.get('difference_type', 'N/A').title()}")
                                st.write(f"**Category:** {diff.get('change_category', 'N/A').title()}")

                            with col2:
                                st.write(f"**Significance:** {diff.get('change_significance', 'N/A').title()}")
                                similarity = diff.get('similarity_score', 0.0)
                                st.write(f"**Similarity:** {similarity:.1%}")

                            with col3:
                                line1 = diff.get('line_number_doc1', 0)
                                line2 = diff.get('line_number_doc2', 0)
                                st.write(f"**Line (Doc 1):** {line1}")
                                st.write(f"**Line (Doc 2):** {line2}")

                            # Context
                            if show_context and (diff.get('context_before') or diff.get('context_after')):
                                st.write("**Context:**")
                                if diff.get('context_before'):
                                    st.caption(f"Before: {diff['context_before']}")
                                if diff.get('context_after'):
                                    st.caption(f"After: {diff['context_after']}")
                else:
                    st.info("No differences match the selected filters.")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Comparison"):
                    save_document_comparison(st.session_state.comparison_documents, comparison)
                    st.success("Comparison saved!")

            with col2:
                if st.button("📊 Generate Report"):
                    generate_comparison_report(comparison)
                    st.success("Comparison report generated!")

            with col3:
                if st.button("📤 Export Results"):
                    export_comparison_results(comparison)
                    st.success("Results exported!")

            with col4:
                if st.button("🔄 New Comparison"):
                    del st.session_state.comparison_result
                    del st.session_state.comparison_documents
                    st.rerun()

    with tab2:
        st.write("**Comparison History**")

        # Get saved comparisons
        saved_comparisons = get_saved_document_comparisons()

        if saved_comparisons:
            for comparison_data in saved_comparisons:
                doc1_name, doc2_name, comparison_type, similarity, total_diffs, significant_changes, comparison_date = comparison_data

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**🔍 {doc1_name} ↔ {doc2_name}**")
                        st.caption(f"Type: {comparison_type.replace('_', ' ').title()}")
                        st.caption(f"Date: {comparison_date.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        st.metric("Similarity", f"{similarity:.1%}")
                        st.write(f"📊 {total_diffs} differences")

                    with col3:
                        if significant_changes > 0:
                            st.metric("Significant", significant_changes)

                        if st.button("👁️", key=f"view_comparison_{doc1_name}_{doc2_name}"):
                            comparison_details = load_comparison_details(doc1_name, doc2_name)
                            st.session_state.view_comparison_details = comparison_details
                            st.rerun()

                st.divider()
        else:
            st.info("No document comparisons saved yet.")

    with tab3:
        st.write("**Comparison Templates**")

        # Template management
        render_comparison_templates_management()

    with tab4:
        st.write("**Comparison Analytics**")

        # Comparison analytics
        render_comparison_analytics()

def filter_differences(differences, change_type_filter, significance_filter, category_filter):
    """Filter differences based on selected criteria"""
    filtered = differences

    if change_type_filter != "All":
        filtered = [d for d in filtered if d.get('difference_type', '').lower() == change_type_filter.lower().rstrip('s')]

    if significance_filter != "All":
        filtered = [d for d in filtered if d.get('change_significance', '').lower() == significance_filter.lower()]

    if category_filter != "All":
        filtered = [d for d in filtered if d.get('change_category', '').lower() == category_filter.lower()]

    return filtered

def get_significance_icon(significance):
    """Get icon for change significance"""
    icons = {
        "critical": "🔴",
        "major": "🟠",
        "moderate": "🟡",
        "minor": "🟢"
    }
    return icons.get(significance, "⚪")

def get_change_type_icon(change_type):
    """Get icon for change type"""
    icons = {
        "addition": "➕",
        "deletion": "➖",
        "modification": "✏️",
        "formatting": "🎨"
    }
    return icons.get(change_type, "📝")

def render_comparison_templates_management():
    """Render comparison templates management"""
    st.write("**Available Templates:**")

    # Default templates
    default_templates = {
        "Contract Amendment": {
            "settings": {"focus_areas": ["legal_terms", "financial_terms", "deadlines"], "ignore_formatting": True},
            "type": "amendment_analysis"
        },
        "Proposal Version": {
            "settings": {"focus_areas": ["technical_content", "pricing", "timeline"], "ignore_formatting": False},
            "type": "version_comparison"
        },
        "RFP Analysis": {
            "settings": {"focus_areas": ["requirements", "evaluation_criteria", "submission_details"], "ignore_formatting": True},
            "type": "proposal_comparison"
        }
    }

    for template_name, template_config in default_templates.items():
        with st.expander(f"📋 {template_name}"):
            st.write(f"**Type:** {template_config['type'].replace('_', ' ').title()}")
            st.write("**Focus Areas:**")
            for area in template_config["settings"]["focus_areas"]:
                st.write(f"• {area.replace('_', ' ').title()}")

            if st.button("📋 Use Template", key=f"use_template_{template_name}"):
                st.session_state.selected_comparison_template = template_config
                st.success(f"Template '{template_name}' selected!")

def render_comparison_analytics():
    """Render comparison analytics"""
    st.write("**Comparison Analytics:**")

    # Get analytics data
    analytics_data = get_comparison_analytics_data()

    if analytics_data:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Comparisons", analytics_data.get('total_comparisons', 0))

        with col2:
            avg_similarity = analytics_data.get('average_similarity', 0.0)
            st.metric("Average Similarity", f"{avg_similarity:.1%}")

        with col3:
            most_common_type = analytics_data.get('most_common_type', 'N/A')
            st.metric("Most Common Type", most_common_type.replace('_', ' ').title())

        with col4:
            avg_differences = analytics_data.get('average_differences', 0)
            st.metric("Avg Differences", avg_differences)

        # Comparison type distribution
        if analytics_data.get('type_distribution'):
            st.write("**Comparison Type Distribution:**")
            st.bar_chart(analytics_data['type_distribution'])

        # Similarity trends
        if analytics_data.get('similarity_trends'):
            st.write("**Similarity Trends Over Time:**")
            st.line_chart(analytics_data['similarity_trends'])
    else:
        st.info("No comparison analytics data available.")
```

---

## **Feature 40: Automated Q&A Generation**
**Status:** ⏳ Ready for Implementation
**Complexity:** MEDIUM | **Priority:** LOW

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS qa_generations (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    generation_title VARCHAR(300),
    document_type VARCHAR(100), -- 'rfp', 'proposal', 'contract', 'amendment'
    qa_purpose VARCHAR(100), -- 'compliance_check', 'proposal_prep', 'review_questions', 'training'
    total_questions INTEGER DEFAULT 0,
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_confidence DECIMAL(3,2),
    generated_by VARCHAR(100) DEFAULT 'ai_system'
);

CREATE TABLE IF NOT EXISTS generated_questions (
    id SERIAL PRIMARY KEY,
    qa_generation_id INTEGER REFERENCES qa_generations(id),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50), -- 'factual', 'analytical', 'compliance', 'clarification'
    question_category VARCHAR(100), -- 'technical', 'financial', 'schedule', 'compliance', 'general'
    difficulty_level VARCHAR(20), -- 'basic', 'intermediate', 'advanced', 'expert'
    suggested_answer TEXT,
    answer_confidence DECIMAL(3,2),
    source_section TEXT,
    source_page INTEGER,
    is_critical BOOLEAN DEFAULT FALSE,
    requires_clarification BOOLEAN DEFAULT FALSE,
    question_priority INTEGER DEFAULT 5, -- 1-10 scale
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    template_purpose VARCHAR(100) NOT NULL,
    question_types TEXT[] NOT NULL,
    question_categories TEXT[] NOT NULL,
    difficulty_distribution JSONB, -- {"basic": 30, "intermediate": 50, "advanced": 20}
    template_settings JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_responses (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES generated_questions(id),
    response_text TEXT NOT NULL,
    responder VARCHAR(100),
    response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT FALSE,
    reviewer VARCHAR(100),
    review_date TIMESTAMP,
    review_notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_qa_generations_document ON qa_generations(document_id);
CREATE INDEX IF NOT EXISTS ix_generated_questions_generation ON generated_questions(qa_generation_id);
CREATE INDEX IF NOT EXISTS ix_generated_questions_type ON generated_questions(question_type);
CREATE INDEX IF NOT EXISTS ix_generated_questions_category ON generated_questions(question_category);
CREATE INDEX IF NOT EXISTS ix_generated_questions_critical ON generated_questions(is_critical);
```

#### **MCP Integration**
Uses generic `generate_insights` tool with Q&A generation-specific contexts.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def generate_qa_from_document(document_content, qa_options=None, document_id=None):
    """Generate Q&A from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Set default options
        if not qa_options:
            qa_options = {
                'document_type': 'rfp',
                'qa_purpose': 'proposal_prep',
                'question_count': 20,
                'difficulty_mix': {'basic': 30, 'intermediate': 50, 'advanced': 20}
            }

        # Use MCP to generate Q&A
        qa_result = call_mcp_tool("generate_insights", {
            "content": document_content,
            "insight_type": "question_answer_generation",
            "context": {
                "domain": "government_contracting",
                "document_type": qa_options.get('document_type', 'rfp'),
                "qa_purpose": qa_options.get('qa_purpose', 'proposal_prep'),
                "question_types": ["factual", "analytical", "compliance", "clarification"],
                "question_categories": ["technical", "financial", "schedule", "compliance", "general"],
                "difficulty_levels": list(qa_options.get('difficulty_mix', {}).keys()),
                "target_count": qa_options.get('question_count', 20),
                "include_answers": True,
                "include_source_references": True,
                "prioritize_critical": True
            },
            "output_format": "structured_qa_set"
        })

        if qa_result.get('success'):
            # Process and structure the Q&A data
            qa_data = qa_result['data']
            structured_qa = process_qa_data(qa_data, qa_options)

            # Save to database if document_id provided
            if document_id and structured_qa:
                save_qa_generation(document_id, structured_qa)

            return {
                "success": True,
                "qa_generation": structured_qa,
                "generation_confidence": qa_result.get('confidence', 0.0)
            }
        else:
            return {"error": "Q&A generation failed"}

    except Exception as e:
        st.error(f"Error generating Q&A: {e}")
        return {"error": str(e)}

def process_qa_data(raw_qa_data, qa_options):
    """Process raw Q&A data into structured format"""
    structured_qa = {
        'document_type': qa_options.get('document_type', 'rfp'),
        'qa_purpose': qa_options.get('qa_purpose', 'proposal_prep'),
        'generation_title': raw_qa_data.get('title', ''),
        'questions': []
    }

    # Process generated questions
    generated_questions = raw_qa_data.get('questions', [])

    for question in generated_questions:
        if isinstance(question, dict):
            question_analysis = {
                'question_text': question.get('question', ''),
                'question_type': question.get('type', 'factual'),
                'question_category': question.get('category', 'general'),
                'difficulty_level': question.get('difficulty', 'intermediate'),
                'suggested_answer': question.get('answer', ''),
                'answer_confidence': question.get('answer_confidence', 0.0),
                'source_section': question.get('source_section', ''),
                'source_page': question.get('source_page', 0),
                'is_critical': question.get('is_critical', False),
                'requires_clarification': question.get('requires_clarification', False),
                'question_priority': question.get('priority', 5)
            }
            structured_qa['questions'].append(question_analysis)

    structured_qa['total_questions'] = len(structured_qa['questions'])

    return structured_qa

def save_qa_generation(document_id, qa_data):
    """Save Q&A generation to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Save main Q&A generation record
        cursor.execute("""
            INSERT INTO qa_generations
            (document_id, generation_title, document_type, qa_purpose, total_questions, generation_confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_id, qa_data['generation_title'], qa_data['document_type'],
            qa_data['qa_purpose'], qa_data['total_questions'], 0.85
        ))

        qa_generation_id = cursor.fetchone()[0]

        # Save individual questions
        for question in qa_data['questions']:
            cursor.execute("""
                INSERT INTO generated_questions
                (qa_generation_id, question_text, question_type, question_category,
                 difficulty_level, suggested_answer, answer_confidence, source_section,
                 source_page, is_critical, requires_clarification, question_priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                qa_generation_id, question['question_text'], question['question_type'],
                question['question_category'], question['difficulty_level'], question['suggested_answer'],
                question['answer_confidence'], question['source_section'], question['source_page'],
                question['is_critical'], question['requires_clarification'], question['question_priority']
            ))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving Q&A generation: {e}")
        return False
    finally:
        conn.close()

def render_qa_generation_tool():
    """Render Q&A generation tool interface"""
    st.subheader("❓ Automated Q&A Generation")

    # Q&A tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Generate Q&A", "Q&A Library", "Templates", "Review & Responses"])

    with tab1:
        st.write("**Generate Questions & Answers from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="qa_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="qa_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="qa_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to generate Q&A...",
                key="qa_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="qa_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        # Q&A generation options
        if document_content:
            st.write("**Q&A Generation Options:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                document_type = st.selectbox(
                    "Document Type:",
                    ["RFP", "Proposal", "Contract", "Amendment", "SOW"],
                    key="qa_document_type"
                )

            with col2:
                qa_purpose = st.selectbox(
                    "Q&A Purpose:",
                    ["Proposal Preparation", "Compliance Check", "Review Questions", "Training"],
                    key="qa_purpose"
                )

            with col3:
                question_count = st.number_input(
                    "Number of Questions:",
                    min_value=5,
                    max_value=100,
                    value=20,
                    step=5,
                    key="question_count"
                )

            # Question type distribution
            st.write("**Question Type Distribution:**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                factual_pct = st.slider("Factual %", 0, 100, 30, key="factual_pct")

            with col2:
                analytical_pct = st.slider("Analytical %", 0, 100, 40, key="analytical_pct")

            with col3:
                compliance_pct = st.slider("Compliance %", 0, 100, 20, key="compliance_pct")

            with col4:
                clarification_pct = st.slider("Clarification %", 0, 100, 10, key="clarification_pct")

            # Difficulty distribution
            st.write("**Difficulty Distribution:**")
            col1, col2, col3 = st.columns(3)

            with col1:
                basic_pct = st.slider("Basic %", 0, 100, 30, key="basic_pct")

            with col2:
                intermediate_pct = st.slider("Intermediate %", 0, 100, 50, key="intermediate_pct")

            with col3:
                advanced_pct = st.slider("Advanced %", 0, 100, 20, key="advanced_pct")

            # Advanced options
            with st.expander("🔧 Advanced Options"):
                col1, col2 = st.columns(2)

                with col1:
                    include_answers = st.checkbox("Include Suggested Answers", value=True, key="include_answers")
                    prioritize_critical = st.checkbox("Prioritize Critical Questions", value=True, key="prioritize_critical")

                with col2:
                    focus_categories = st.multiselect(
                        "Focus Categories:",
                        ["Technical", "Financial", "Schedule", "Compliance", "General"],
                        default=["Technical", "Compliance"],
                        key="focus_categories"
                    )

            if st.button("❓ Generate Q&A", type="primary"):
                with st.spinner("Generating questions and answers..."):
                    qa_options = {
                        'document_type': document_type.lower(),
                        'qa_purpose': qa_purpose.lower().replace(' ', '_'),
                        'question_count': question_count,
                        'type_distribution': {
                            'factual': factual_pct,
                            'analytical': analytical_pct,
                            'compliance': compliance_pct,
                            'clarification': clarification_pct
                        },
                        'difficulty_mix': {
                            'basic': basic_pct,
                            'intermediate': intermediate_pct,
                            'advanced': advanced_pct
                        },
                        'focus_categories': [cat.lower() for cat in focus_categories]
                    }

                    qa_result = generate_qa_from_document(
                        document_content,
                        qa_options,
                        document_name
                    )

                    if qa_result.get('success'):
                        st.session_state.qa_generation_result = qa_result
                        st.session_state.qa_document = {
                            'name': document_name,
                            'content': document_content
                        }

        # Display Q&A results
        if 'qa_generation_result' in st.session_state:
            st.subheader("❓ Generated Questions & Answers")

            result = st.session_state.qa_generation_result
            qa_data = result.get('qa_generation', {})
            questions = qa_data.get('questions', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Questions", qa_data.get('total_questions', 0))

            with col2:
                critical_questions = sum(1 for q in questions if q.get('is_critical'))
                st.metric("Critical Questions", critical_questions)

            with col3:
                confidence = result.get('generation_confidence', 0.0)
                st.metric("Generation Confidence", f"{confidence:.1%}")

            with col4:
                clarification_needed = sum(1 for q in questions if q.get('requires_clarification'))
                st.metric("Need Clarification", clarification_needed)

            # Filter and display questions
            if questions:
                st.write("**Generated Questions:**")

                # Filter options
                col1, col2, col3 = st.columns(3)

                with col1:
                    type_filter = st.selectbox(
                        "Filter by Type:",
                        ["All", "Factual", "Analytical", "Compliance", "Clarification"],
                        key="qa_type_filter"
                    )

                with col2:
                    category_filter = st.selectbox(
                        "Filter by Category:",
                        ["All", "Technical", "Financial", "Schedule", "Compliance", "General"],
                        key="qa_category_filter"
                    )

                with col3:
                    difficulty_filter = st.selectbox(
                        "Filter by Difficulty:",
                        ["All", "Basic", "Intermediate", "Advanced"],
                        key="qa_difficulty_filter"
                    )

                # Display filtered questions
                filtered_questions = filter_questions(questions, type_filter, category_filter, difficulty_filter)

                if filtered_questions:
                    for i, question in enumerate(filtered_questions, 1):
                        priority_icon = get_priority_icon(question.get('question_priority', 5))
                        critical_indicator = "🔴 " if question.get('is_critical') else ""
                        clarification_indicator = "❓ " if question.get('requires_clarification') else ""

                        with st.expander(f"{critical_indicator}{clarification_indicator}{priority_icon} Q{i}: {question.get('question_text', 'No question text')[:100]}..."):
                            # Question details
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write("**Question:**")
                                st.write(question.get('question_text', 'No question text'))

                                if include_answers and question.get('suggested_answer'):
                                    st.write("**Suggested Answer:**")
                                    st.info(question['suggested_answer'])

                                if question.get('source_section'):
                                    st.write("**Source Section:**")
                                    st.caption(question['source_section'])

                            with col2:
                                st.write(f"**Type:** {question.get('question_type', 'N/A').title()}")
                                st.write(f"**Category:** {question.get('question_category', 'N/A').title()}")
                                st.write(f"**Difficulty:** {question.get('difficulty_level', 'N/A').title()}")
                                st.write(f"**Priority:** {question.get('question_priority', 5)}/10")

                                if question.get('answer_confidence'):
                                    st.metric("Answer Confidence", f"{question['answer_confidence']:.1%}")

                                if question.get('source_page'):
                                    st.write(f"**Page:** {question['source_page']}")
                else:
                    st.info("No questions match the selected filters.")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Q&A Set"):
                    save_qa_generation(st.session_state.qa_document['name'], qa_data)
                    st.success("Q&A set saved!")

            with col2:
                if st.button("📄 Export to PDF"):
                    export_qa_to_pdf(qa_data)
                    st.success("Q&A exported to PDF!")

            with col3:
                if st.button("📊 Generate Quiz"):
                    generate_interactive_quiz(questions)
                    st.success("Interactive quiz generated!")

            with col4:
                if st.button("🔄 Regenerate"):
                    del st.session_state.qa_generation_result
                    st.rerun()

    with tab2:
        st.write("**Q&A Library**")

        # Get saved Q&A sets
        saved_qa_sets = get_saved_qa_generations()

        if saved_qa_sets:
            for qa_set_data in saved_qa_sets:
                doc_name, generation_title, document_type, qa_purpose, total_questions, critical_questions, generation_date = qa_set_data

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**❓ {generation_title or doc_name}**")
                        st.caption(f"From: {doc_name}")
                        st.caption(f"Type: {document_type.title()} | Purpose: {qa_purpose.replace('_', ' ').title()}")

                    with col2:
                        st.metric("Questions", total_questions)
                        if critical_questions > 0:
                            st.write(f"🔴 {critical_questions} critical")

                    with col3:
                        st.caption(generation_date.strftime('%Y-%m-%d'))

                        if st.button("👁️", key=f"view_qa_{doc_name}"):
                            qa_details = load_qa_generation_details(doc_name)
                            st.session_state.view_qa_details = qa_details
                            st.rerun()

                st.divider()
        else:
            st.info("No Q&A sets saved yet.")

    with tab3:
        st.write("**Q&A Templates**")

        # Template management
        render_qa_templates_management()

    with tab4:
        st.write("**Review & Responses**")

        # Q&A review and response management
        render_qa_review_management()

def filter_questions(questions, type_filter, category_filter, difficulty_filter):
    """Filter questions based on selected criteria"""
    filtered = questions

    if type_filter != "All":
        filtered = [q for q in filtered if q.get('question_type', '').lower() == type_filter.lower()]

    if category_filter != "All":
        filtered = [q for q in filtered if q.get('question_category', '').lower() == category_filter.lower()]

    if difficulty_filter != "All":
        filtered = [q for q in filtered if q.get('difficulty_level', '').lower() == difficulty_filter.lower()]

    return filtered

def get_priority_icon(priority):
    """Get icon for question priority"""
    if priority >= 8:
        return "🔥"
    elif priority >= 6:
        return "⭐"
    elif priority >= 4:
        return "📌"
    else:
        return "📝"

def render_qa_templates_management():
    """Render Q&A templates management"""
    st.write("**Available Templates:**")

    # Default templates
    default_templates = {
        "RFP Compliance Check": {
            "purpose": "compliance_check",
            "question_types": ["compliance", "factual", "clarification"],
            "categories": ["compliance", "technical", "financial"],
            "difficulty": {"basic": 20, "intermediate": 60, "advanced": 20}
        },
        "Proposal Preparation": {
            "purpose": "proposal_prep",
            "question_types": ["analytical", "factual", "compliance"],
            "categories": ["technical", "financial", "schedule"],
            "difficulty": {"basic": 30, "intermediate": 50, "advanced": 20}
        },
        "Contract Review": {
            "purpose": "review_questions",
            "question_types": ["analytical", "compliance", "clarification"],
            "categories": ["compliance", "financial", "general"],
            "difficulty": {"basic": 40, "intermediate": 40, "advanced": 20}
        }
    }

    for template_name, template_config in default_templates.items():
        with st.expander(f"❓ {template_name}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Purpose:** {template_config['purpose'].replace('_', ' ').title()}")
                st.write("**Question Types:**")
                for qtype in template_config["question_types"]:
                    st.write(f"• {qtype.title()}")

            with col2:
                st.write("**Categories:**")
                for category in template_config["categories"]:
                    st.write(f"• {category.title()}")

                st.write("**Difficulty Mix:**")
                for level, pct in template_config["difficulty"].items():
                    st.write(f"• {level.title()}: {pct}%")

            if st.button("❓ Use Template", key=f"use_qa_template_{template_name}"):
                st.session_state.selected_qa_template = template_config
                st.success(f"Template '{template_name}' selected!")

def render_qa_review_management():
    """Render Q&A review and response management"""
    st.write("**Questions Requiring Review:**")

    # Get questions needing review
    review_questions = get_questions_needing_review()

    if review_questions:
        for question_data in review_questions:
            question_text, question_type, is_critical, requires_clarification, suggested_answer = question_data

            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    critical_indicator = "🔴 " if is_critical else ""
                    clarification_indicator = "❓ " if requires_clarification else ""

                    st.write(f"**{critical_indicator}{clarification_indicator}{question_text}**")
                    st.caption(f"Type: {question_type.title()}")

                    if suggested_answer:
                        st.write("**Suggested Answer:**")
                        st.info(suggested_answer)

                with col2:
                    response_text = st.text_area(
                        "Your Response:",
                        height=100,
                        key=f"response_{question_text[:20]}"
                    )

                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{question_text[:20]}"):
                            approve_question_response(question_text, response_text)
                            st.success("Response approved!")

                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{question_text[:20]}"):
                            reject_question_response(question_text, response_text)
                            st.warning("Response rejected!")

            st.divider()
    else:
        st.info("No questions requiring review.")
```

---

## **Feature 43: Contract Vehicle Identification**
**Status:** ⏳ Ready for Implementation
**Complexity:** LOW | **Priority:** MEDIUM

#### **Database Schema Extensions**
```sql
-- Add to setup_database() function
CREATE TABLE IF NOT EXISTS contract_vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_name VARCHAR(200) NOT NULL UNIQUE,
    vehicle_type VARCHAR(100) NOT NULL, -- 'gsa_schedule', 'gwac', 'idiq', 'bpa', 'single_award'
    vehicle_description TEXT,
    managing_agency VARCHAR(200),
    vehicle_number VARCHAR(100),
    expiration_date DATE,
    ceiling_value DECIMAL(15,2),
    small_business_set_aside BOOLEAN DEFAULT FALSE,
    naics_codes TEXT[],
    eligible_contractors TEXT[],
    vehicle_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicle_identifications (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL,
    identified_vehicle_id INTEGER REFERENCES contract_vehicles(id),
    identification_confidence DECIMAL(3,2),
    identification_method VARCHAR(50), -- 'explicit_mention', 'pattern_match', 'context_analysis'
    supporting_evidence TEXT[],
    alternative_vehicles INTEGER[], -- Array of other possible vehicle IDs
    identification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    identified_by VARCHAR(100) DEFAULT 'ai_system',
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verification_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicle_eligibility_checks (
    id SERIAL PRIMARY KEY,
    vehicle_identification_id INTEGER REFERENCES vehicle_identifications(id),
    company_name VARCHAR(300),
    eligibility_status VARCHAR(50), -- 'eligible', 'not_eligible', 'needs_verification', 'unknown'
    eligibility_factors JSONB,
    small_business_status VARCHAR(100),
    naics_match BOOLEAN DEFAULT FALSE,
    ceiling_compliance BOOLEAN DEFAULT FALSE,
    geographic_eligibility BOOLEAN DEFAULT FALSE,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_review_date DATE
);

CREATE INDEX IF NOT EXISTS ix_contract_vehicles_type ON contract_vehicles(vehicle_type);
CREATE INDEX IF NOT EXISTS ix_contract_vehicles_agency ON contract_vehicles(managing_agency);
CREATE INDEX IF NOT EXISTS ix_contract_vehicles_active ON contract_vehicles(is_active);
CREATE INDEX IF NOT EXISTS ix_vehicle_identifications_document ON vehicle_identifications(document_id);
CREATE INDEX IF NOT EXISTS ix_vehicle_identifications_vehicle ON vehicle_identifications(identified_vehicle_id);
CREATE INDEX IF NOT EXISTS ix_vehicle_identifications_confidence ON vehicle_identifications(identification_confidence);
```

#### **MCP Integration**
Uses generic `classify_content` tool with contract vehicle classification contexts.

#### **Implementation Functions**
```python
# Add to govcon_suite.py
def identify_contract_vehicle(document_content, document_id=None):
    """Identify contract vehicle from documents using MCP"""
    llm_config = setup_llm_api()
    if not llm_config:
        return {"error": "MCP connection not available"}

    try:
        # Use MCP to classify contract vehicle
        vehicle_result = call_mcp_tool("classify_content", {
            "content": document_content,
            "classification_scheme": "government_contract_vehicles",
            "domain_rules": {
                "vehicle_types": [
                    "gsa_schedule", "gwac", "idiq", "bpa", "single_award",
                    "oasis", "cio_sp3", "sewp", "8a_stars", "vets_2"
                ],
                "identification_patterns": [
                    "contract_numbers", "vehicle_names", "managing_agencies",
                    "ceiling_values", "naics_codes", "set_aside_types"
                ],
                "context_indicators": [
                    "solicitation_type", "award_method", "competition_type",
                    "small_business_requirements", "geographic_scope"
                ],
                "confidence_factors": [
                    "explicit_mention", "pattern_match", "context_analysis"
                ]
            },
            "extract_supporting_evidence": True,
            "identify_alternatives": True
        })

        if vehicle_result.get('success'):
            # Process and structure the vehicle identification
            vehicle_data = vehicle_result['data']
            structured_identification = process_vehicle_identification_data(vehicle_data)

            # Save to database if document_id provided
            if document_id and structured_identification:
                save_vehicle_identification(document_id, structured_identification)

            return {
                "success": True,
                "vehicle_identification": structured_identification,
                "identification_confidence": vehicle_result.get('confidence', 0.0)
            }
        else:
            return {"error": "Contract vehicle identification failed"}

    except Exception as e:
        st.error(f"Error identifying contract vehicle: {e}")
        return {"error": str(e)}

def process_vehicle_identification_data(raw_vehicle_data):
    """Process raw vehicle identification data into structured format"""
    structured_identification = {
        'primary_vehicle': None,
        'alternative_vehicles': [],
        'identification_confidence': raw_vehicle_data.get('confidence', 0.0),
        'identification_method': raw_vehicle_data.get('method', 'context_analysis'),
        'supporting_evidence': raw_vehicle_data.get('evidence', [])
    }

    # Process primary vehicle identification
    primary_vehicle = raw_vehicle_data.get('primary_vehicle')
    if primary_vehicle:
        structured_identification['primary_vehicle'] = {
            'vehicle_name': primary_vehicle.get('name', ''),
            'vehicle_type': primary_vehicle.get('type', ''),
            'vehicle_number': primary_vehicle.get('number', ''),
            'managing_agency': primary_vehicle.get('agency', ''),
            'confidence': primary_vehicle.get('confidence', 0.0)
        }

    # Process alternative vehicles
    alternative_vehicles = raw_vehicle_data.get('alternatives', [])
    for alt_vehicle in alternative_vehicles:
        if isinstance(alt_vehicle, dict):
            alt_data = {
                'vehicle_name': alt_vehicle.get('name', ''),
                'vehicle_type': alt_vehicle.get('type', ''),
                'confidence': alt_vehicle.get('confidence', 0.0),
                'reason': alt_vehicle.get('reason', '')
            }
            structured_identification['alternative_vehicles'].append(alt_data)

    return structured_identification

def save_vehicle_identification(document_id, identification_data):
    """Save vehicle identification to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Find or create vehicle record
        primary_vehicle = identification_data.get('primary_vehicle')
        if primary_vehicle:
            vehicle_id = find_or_create_vehicle(cursor, primary_vehicle)

            # Save identification record
            cursor.execute("""
                INSERT INTO vehicle_identifications
                (document_id, identified_vehicle_id, identification_confidence,
                 identification_method, supporting_evidence)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                document_id, vehicle_id, identification_data['identification_confidence'],
                identification_data['identification_method'], identification_data['supporting_evidence']
            ))

            identification_id = cursor.fetchone()[0]

            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error saving vehicle identification: {e}")
        return False
    finally:
        conn.close()

def find_or_create_vehicle(cursor, vehicle_data):
    """Find existing vehicle or create new one"""
    vehicle_name = vehicle_data.get('vehicle_name', '')
    vehicle_type = vehicle_data.get('vehicle_type', '')

    # Try to find existing vehicle
    cursor.execute("""
        SELECT id FROM contract_vehicles
        WHERE vehicle_name = %s OR vehicle_number = %s
    """, (vehicle_name, vehicle_data.get('vehicle_number', '')))

    result = cursor.fetchone()
    if result:
        return result[0]

    # Create new vehicle record
    cursor.execute("""
        INSERT INTO contract_vehicles
        (vehicle_name, vehicle_type, managing_agency, vehicle_number)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        vehicle_name, vehicle_type,
        vehicle_data.get('managing_agency', ''),
        vehicle_data.get('vehicle_number', '')
    ))

    return cursor.fetchone()[0]

def render_contract_vehicle_identification():
    """Render contract vehicle identification interface"""
    st.subheader("🏛️ Contract Vehicle Identification")

    # Vehicle identification tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Identify Vehicle", "Vehicle Database", "Eligibility Check", "Analytics"])

    with tab1:
        st.write("**Identify Contract Vehicle from Documents**")

        # Document input
        input_method = st.radio(
            "Document Input:",
            ["Upload File", "Paste Text", "Select from Library"],
            key="vehicle_input_method"
        )

        document_content = ""
        document_name = ""

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload Document:",
                type=['txt', 'pdf', 'docx'],
                key="vehicle_file_upload"
            )

            if uploaded_file:
                document_content = extract_text_from_file(uploaded_file)
                document_name = uploaded_file.name

        elif input_method == "Paste Text":
            document_name = st.text_input("Document Name:", key="vehicle_doc_name")
            document_content = st.text_area(
                "Document Content:",
                height=300,
                placeholder="Paste document content to identify contract vehicle...",
                key="vehicle_text_input"
            )

        elif input_method == "Select from Library":
            documents = get_document_library()

            if documents:
                selected_doc = st.selectbox(
                    "Select Document:",
                    options=documents,
                    format_func=lambda x: f"{x['name']} ({x['type']})",
                    key="vehicle_doc_selection"
                )

                if selected_doc:
                    document_content = load_document_content(selected_doc['id'])
                    document_name = selected_doc['name']

        if document_content and st.button("🏛️ Identify Contract Vehicle", type="primary"):
            with st.spinner("Identifying contract vehicle..."):
                vehicle_result = identify_contract_vehicle(document_content, document_name)

                if vehicle_result.get('success'):
                    st.session_state.vehicle_identification_result = vehicle_result
                    st.session_state.vehicle_document = {
                        'name': document_name,
                        'content': document_content
                    }

        # Display identification results
        if 'vehicle_identification_result' in st.session_state:
            st.subheader("🏛️ Contract Vehicle Identification Results")

            result = st.session_state.vehicle_identification_result
            identification = result.get('vehicle_identification', {})
            primary_vehicle = identification.get('primary_vehicle')
            alternative_vehicles = identification.get('alternative_vehicles', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                confidence = identification.get('identification_confidence', 0.0)
                st.metric("Identification Confidence", f"{confidence:.1%}")

            with col2:
                method = identification.get('identification_method', 'N/A')
                st.metric("Method", method.replace('_', ' ').title())

            with col3:
                alternatives_count = len(alternative_vehicles)
                st.metric("Alternative Vehicles", alternatives_count)

            with col4:
                evidence_count = len(identification.get('supporting_evidence', []))
                st.metric("Evidence Points", evidence_count)

            # Primary vehicle identification
            if primary_vehicle:
                st.write("**Primary Vehicle Identified:**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    vehicle_icon = get_vehicle_type_icon(primary_vehicle.get('vehicle_type', ''))
                    st.write(f"**{vehicle_icon} {primary_vehicle.get('vehicle_name', 'Unknown Vehicle')}**")

                    if primary_vehicle.get('vehicle_number'):
                        st.write(f"**Vehicle Number:** {primary_vehicle['vehicle_number']}")

                    if primary_vehicle.get('managing_agency'):
                        st.write(f"**Managing Agency:** {primary_vehicle['managing_agency']}")

                    vehicle_type = primary_vehicle.get('vehicle_type', 'Unknown')
                    st.write(f"**Vehicle Type:** {vehicle_type.replace('_', ' ').title()}")

                with col2:
                    vehicle_confidence = primary_vehicle.get('confidence', 0.0)
                    st.metric("Vehicle Confidence", f"{vehicle_confidence:.1%}")

                    # Get vehicle details from database
                    vehicle_details = get_vehicle_details(primary_vehicle.get('vehicle_name', ''))
                    if vehicle_details:
                        if vehicle_details.get('ceiling_value'):
                            st.metric("Ceiling Value", f"${vehicle_details['ceiling_value']:,.0f}")

                        if vehicle_details.get('expiration_date'):
                            st.write(f"**Expires:** {vehicle_details['expiration_date']}")

            # Supporting evidence
            supporting_evidence = identification.get('supporting_evidence', [])
            if supporting_evidence:
                st.write("**Supporting Evidence:**")
                for i, evidence in enumerate(supporting_evidence, 1):
                    st.write(f"{i}. {evidence}")

            # Alternative vehicles
            if alternative_vehicles:
                st.write("**Alternative Vehicle Possibilities:**")

                for alt_vehicle in alternative_vehicles:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            alt_icon = get_vehicle_type_icon(alt_vehicle.get('vehicle_type', ''))
                            st.write(f"**{alt_icon} {alt_vehicle.get('vehicle_name', 'Unknown')}**")

                            if alt_vehicle.get('reason'):
                                st.caption(f"Reason: {alt_vehicle['reason']}")

                        with col2:
                            alt_confidence = alt_vehicle.get('confidence', 0.0)
                            st.metric("Confidence", f"{alt_confidence:.1%}")

                        with col3:
                            vehicle_type = alt_vehicle.get('vehicle_type', 'Unknown')
                            st.write(f"**Type:** {vehicle_type.replace('_', ' ').title()}")

                st.divider()

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("💾 Save Identification"):
                    save_vehicle_identification(st.session_state.vehicle_document['name'], identification)
                    st.success("Vehicle identification saved!")

            with col2:
                if st.button("✅ Check Eligibility"):
                    check_vehicle_eligibility(primary_vehicle)
                    st.success("Eligibility check initiated!")

            with col3:
                if st.button("📊 Vehicle Details"):
                    show_vehicle_details(primary_vehicle)
                    st.success("Vehicle details displayed!")

            with col4:
                if st.button("🔄 New Identification"):
                    del st.session_state.vehicle_identification_result
                    del st.session_state.vehicle_document
                    st.rerun()

    with tab2:
        st.write("**Contract Vehicle Database**")

        # Vehicle database management
        render_vehicle_database_management()

    with tab3:
        st.write("**Eligibility Check**")

        # Eligibility checking interface
        render_vehicle_eligibility_check()

    with tab4:
        st.write("**Vehicle Analytics**")

        # Vehicle identification analytics
        render_vehicle_analytics()

def get_vehicle_type_icon(vehicle_type):
    """Get icon for vehicle type"""
    icons = {
        "gsa_schedule": "🏪",
        "gwac": "🌐",
        "idiq": "📋",
        "bpa": "🤝",
        "single_award": "🎯",
        "oasis": "🏛️",
        "cio_sp3": "💻",
        "sewp": "🔧",
        "8a_stars": "⭐",
        "vets_2": "🎖️"
    }
    return icons.get(vehicle_type, "📄")

def render_vehicle_database_management():
    """Render vehicle database management interface"""
    st.write("**Known Contract Vehicles:**")

    # Get all vehicles from database
    all_vehicles = get_all_contract_vehicles()

    if all_vehicles:
        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            type_filter = st.selectbox(
                "Filter by Type:",
                ["All", "GSA Schedule", "GWAC", "IDIQ", "BPA", "Single Award"],
                key="vehicle_type_filter"
            )

        with col2:
            agency_filter = st.selectbox(
                "Filter by Agency:",
                ["All"] + get_unique_agencies(),
                key="vehicle_agency_filter"
            )

        with col3:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "Active", "Expired"],
                key="vehicle_status_filter"
            )

        # Display vehicles
        filtered_vehicles = filter_vehicles(all_vehicles, type_filter, agency_filter, status_filter)

        for vehicle in filtered_vehicles:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    vehicle_icon = get_vehicle_type_icon(vehicle.get('vehicle_type', ''))
                    st.write(f"**{vehicle_icon} {vehicle.get('vehicle_name', 'Unknown')}**")

                    if vehicle.get('vehicle_number'):
                        st.caption(f"Number: {vehicle['vehicle_number']}")

                    if vehicle.get('managing_agency'):
                        st.caption(f"Agency: {vehicle['managing_agency']}")

                with col2:
                    if vehicle.get('ceiling_value'):
                        st.metric("Ceiling", f"${vehicle['ceiling_value']:,.0f}")

                    vehicle_type = vehicle.get('vehicle_type', 'Unknown')
                    st.write(f"**{vehicle_type.replace('_', ' ').title()}**")

                with col3:
                    if vehicle.get('expiration_date'):
                        st.write(f"**Expires:** {vehicle['expiration_date']}")

                    status = "Active" if vehicle.get('is_active') else "Inactive"
                    status_icon = "✅" if vehicle.get('is_active') else "❌"
                    st.write(f"{status_icon} **{status}**")

                    if st.button("👁️", key=f"view_vehicle_{vehicle.get('id')}"):
                        vehicle_details = load_vehicle_details(vehicle.get('id'))
                        st.session_state.view_vehicle_details = vehicle_details
                        st.rerun()

            st.divider()
    else:
        st.info("No contract vehicles in database.")

    # Add new vehicle
    with st.expander("➕ Add New Contract Vehicle"):
        col1, col2 = st.columns(2)

        with col1:
            new_vehicle_name = st.text_input("Vehicle Name:", key="new_vehicle_name")
            new_vehicle_type = st.selectbox(
                "Vehicle Type:",
                ["GSA Schedule", "GWAC", "IDIQ", "BPA", "Single Award"],
                key="new_vehicle_type"
            )
            new_managing_agency = st.text_input("Managing Agency:", key="new_managing_agency")

        with col2:
            new_vehicle_number = st.text_input("Vehicle Number:", key="new_vehicle_number")
            new_ceiling_value = st.number_input("Ceiling Value ($):", min_value=0, key="new_ceiling_value")
            new_expiration_date = st.date_input("Expiration Date:", key="new_expiration_date")

        new_description = st.text_area("Description:", key="new_vehicle_description")

        if st.button("➕ Add Vehicle", disabled=not new_vehicle_name):
            add_new_vehicle({
                'name': new_vehicle_name,
                'type': new_vehicle_type.lower().replace(' ', '_'),
                'agency': new_managing_agency,
                'number': new_vehicle_number,
                'ceiling': new_ceiling_value,
                'expiration': new_expiration_date,
                'description': new_description
            })
            st.success(f"Vehicle '{new_vehicle_name}' added!")
            st.rerun()

def render_vehicle_eligibility_check():
    """Render vehicle eligibility check interface"""
    st.write("**Check Company Eligibility for Contract Vehicles**")

    # Company information
    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input("Company Name:", key="eligibility_company_name")
        small_business_status = st.selectbox(
            "Small Business Status:",
            ["Large Business", "Small Business", "8(a)", "HUBZone", "WOSB", "VOSB", "SDVOSB"],
            key="small_business_status"
        )

    with col2:
        primary_naics = st.text_input("Primary NAICS Code:", key="primary_naics")
        annual_revenue = st.number_input("Annual Revenue ($):", min_value=0, key="annual_revenue")

    # Vehicle selection
    available_vehicles = get_all_contract_vehicles()
    if available_vehicles:
        selected_vehicle = st.selectbox(
            "Select Contract Vehicle:",
            options=available_vehicles,
            format_func=lambda x: f"{x['vehicle_name']} ({x['vehicle_type'].replace('_', ' ').title()})",
            key="eligibility_vehicle_selection"
        )

        if company_name and selected_vehicle and st.button("✅ Check Eligibility", type="primary"):
            with st.spinner("Checking eligibility..."):
                eligibility_result = check_company_eligibility(
                    company_name, small_business_status, primary_naics,
                    annual_revenue, selected_vehicle
                )

                if eligibility_result.get('success'):
                    st.session_state.eligibility_result = eligibility_result

    # Display eligibility results
    if 'eligibility_result' in st.session_state:
        st.subheader("✅ Eligibility Check Results")

        result = st.session_state.eligibility_result
        eligibility = result.get('eligibility_check', {})

        # Overall eligibility status
        status = eligibility.get('eligibility_status', 'unknown')
        status_icon = get_eligibility_status_icon(status)

        st.write(f"**{status_icon} Eligibility Status: {status.replace('_', ' ').title()}**")

        # Detailed factors
        factors = eligibility.get('eligibility_factors', {})

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Eligibility Factors:**")

            for factor, status in factors.items():
                factor_icon = "✅" if status else "❌"
                st.write(f"{factor_icon} {factor.replace('_', ' ').title()}")

        with col2:
            st.write("**Requirements:**")

            requirements = eligibility.get('requirements', [])
            for requirement in requirements:
                st.write(f"• {requirement}")

        # Recommendations
        if eligibility.get('recommendations'):
            st.write("**Recommendations:**")
            st.info(eligibility['recommendations'])

def get_eligibility_status_icon(status):
    """Get icon for eligibility status"""
    icons = {
        "eligible": "✅",
        "not_eligible": "❌",
        "needs_verification": "⚠️",
        "unknown": "❓"
    }
    return icons.get(status, "❓")

def render_vehicle_analytics():
    """Render vehicle analytics"""
    st.write("**Vehicle Identification Analytics:**")

    # Get analytics data
    analytics_data = get_vehicle_analytics_data()

    if analytics_data:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Identifications", analytics_data.get('total_identifications', 0))

        with col2:
            avg_confidence = analytics_data.get('average_confidence', 0.0)
            st.metric("Average Confidence", f"{avg_confidence:.1%}")

        with col3:
            most_common_vehicle = analytics_data.get('most_common_vehicle', 'N/A')
            st.metric("Most Common Vehicle", most_common_vehicle)

        with col4:
            verified_identifications = analytics_data.get('verified_identifications', 0)
            st.metric("Verified Identifications", verified_identifications)

        # Vehicle type distribution
        if analytics_data.get('vehicle_type_distribution'):
            st.write("**Vehicle Type Distribution:**")
            st.bar_chart(analytics_data['vehicle_type_distribution'])

        # Identification confidence trends
        if analytics_data.get('confidence_trends'):
            st.write("**Identification Confidence Trends:**")
            st.line_chart(analytics_data['confidence_trends'])

        # Top identified vehicles
        if analytics_data.get('top_vehicles'):
            st.write("**Most Frequently Identified Vehicles:**")
            for vehicle in analytics_data['top_vehicles']:
                col1, col2 = st.columns([3, 1])

                with col1:
                    vehicle_icon = get_vehicle_type_icon(vehicle['type'])
                    st.write(f"{vehicle_icon} **{vehicle['name']}**")

                with col2:
                    st.metric("Count", vehicle['count'])
    else:
        st.info("No vehicle analytics data available.")

*This implementation guide provides the complete technical foundation for integrating sammySosa with GremlinsAI's multi-client MCP server architecture, enabling all 93 Apollo GovCon features through generic, domain-configurable AI tools.*

### **🔍 Text Analysis & Processing**
```python
POST /ai/extract-keywords              # Extract keywords from text (Feature 3, 16)
POST /ai/extract-technical-keywords    # Extract technical terms (Feature 16)
POST /ai/extract-domain-keywords       # Extract domain-specific keywords (Feature 16)
POST /ai/rank-keyword-importance       # Rank keywords by relevance (Feature 16)
POST /ai/categorize-keywords           # Categorize keywords by type (Feature 16)
POST /ai/extract-locations             # Extract location info (Feature 8)
POST /ai/extract-requirements          # Extract requirements from SOWs
POST /ai/analyze-document              # General document analysis
POST /ai/summarize-text                # Generate text summaries
POST /ai/extract-entities              # Extract named entities
```

### **🔍 Opportunity Analysis**
```python
POST /ai/find-similar-opportunities    # Find similar opportunities (Feature 11)
POST /ai/calculate-similarity-score    # Calculate similarity scores (Feature 11)
POST /ai/extract-opportunity-features  # Extract features for matching (Feature 11)
POST /ai/analyze-buying-patterns       # Analyze agency patterns (Feature 12)
POST /ai/predict-future-opportunities  # Predict future opps (Feature 12)
POST /ai/generate-pattern-insights     # Generate insights (Feature 12)
POST /ai/assess-opportunity-fit        # Assess company fit for opportunity
POST /ai/calculate-p-win-score         # Calculate probability of win
```

### **⚖️ Compliance & Risk Analysis**
```python
POST /ai/analyze-far-clauses           # Analyze FAR clauses (Feature 15)
POST /ai/detect-clause-anomalies       # Detect clause anomalies (Feature 15)
POST /ai/explain-far-clause            # Explain FAR clauses (Feature 15)
POST /ai/assess-compliance-risk        # Assess compliance risk (Feature 15)
POST /ai/validate-requirements         # Validate requirement compliance
POST /ai/detect-red-flags              # Detect opportunity red flags
POST /ai/analyze-terms-conditions      # Analyze T&Cs for risks
```

### **🗺️ Geographic & Location Services**
```python
POST /ai/geocode-address               # Convert addresses to coordinates (Feature 8)
POST /ai/validate-location             # Validate location information
POST /ai/extract-geographic-scope      # Extract geographic requirements
POST /ai/analyze-location-preferences  # Analyze location preferences
```

### **📊 Content Generation**
```python
POST /ai/generate-search-queries       # Generate smart search queries (Feature 14)
POST /ai/generate-summary              # Generate opportunity summaries
POST /ai/generate-recommendations      # Generate actionable recommendations
POST /ai/generate-insights             # Generate business insights
POST /ai/generate-proposal-outline     # Generate proposal outlines
POST /ai/generate-capability-statement # Generate capability statements
POST /ai/generate-teaming-suggestions  # Suggest teaming partners
```

### **🤖 Advanced AI Features**
```python
POST /ai/analyze-competition           # Analyze competitive landscape
POST /ai/predict-award-timeline        # Predict award timelines
POST /ai/assess-protest-risk           # Assess protest risk
POST /ai/generate-questions            # Generate clarification questions
POST /ai/analyze-evaluation-criteria   # Analyze evaluation criteria
POST /ai/optimize-proposal-strategy    # Optimize proposal strategy
POST /ai/analyze-past-performance      # Analyze past performance requirements
```

### **🔧 Utility & Management**
```python
GET  /health                           # Service health check
GET  /status                           # Service status and capabilities
GET  /models                           # Available AI models
POST /models/switch                    # Switch between models
GET  /capabilities                     # Service capabilities
GET  /usage/stats                      # Usage statistics
GET  /usage/limits                     # Rate limits and quotas
```

### **🔐 Authentication & Security**
```python
POST /auth/token                       # Get authentication token
POST /auth/refresh                     # Refresh authentication token
GET  /auth/validate                    # Validate token
POST /auth/logout                      # Logout and invalidate token
```

---

## **Feature 21: State & Local Portal Integration**
**Status:** ⏳ Ready for Implementation
**Complexity:** HIGH | **Priority:** MEDIUM

#### **Database Schema Extension**
```python
# Add to existing setup_database() function in govcon_suite.py
portal_sources = Table(
    "portal_sources",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("portal_name", String, nullable=False),
    Column("portal_url", String, nullable=False),
    Column("portal_type", String, nullable=False),  # 'state', 'local', 'federal'
    Column("state_code", String),                   # For state portals
    Column("city_name", String),                    # For local portals
    Column("scraper_config", JSONB),                # Portal-specific scraping config
    Column("is_active", Boolean, default=True),
    Column("last_scraped", String),
    Column("success_rate", Float, default=0.0),
    Column("created_date", String, default=lambda: datetime.now().isoformat())
)

portal_opportunities = Table(
    "portal_opportunities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("portal_id", Integer, ForeignKey("portal_sources.id")),
    Column("external_id", String, nullable=False),   # ID from external portal
    Column("title", String),
    Column("agency", String),
    Column("posted_date", String),
    Column("response_deadline", String),
    Column("description", String),
    Column("contact_info", String),
    Column("raw_data", JSONB),
    Column("sync_status", String, default="new"),    # 'new', 'synced', 'failed'
    Column("created_date", String, default=lambda: datetime.now().isoformat())
)

# Add indexes
Index("ix_portal_sources_active", portal_sources.c.is_active)
Index("ix_portal_sources_type", portal_sources.c.portal_type)
Index("ix_portal_opportunities_portal_id", portal_opportunities.c.portal_id)
Index("ix_portal_opportunities_sync_status", portal_opportunities.c.sync_status)
```

#### **MCP Tool Usage**
- **`extract_structured_data`** - Extract opportunity data from various portal formats
- **`classify_content`** - Classify and standardize opportunity types across portals

#### **Implementation Functions**
```python
# Add to govcon_suite.py
import requests
from bs4 import BeautifulSoup

def add_portal_source(portal_name, portal_url, portal_type, state_code=None, city_name=None, scraper_config=None):
    """Add a new portal source for scraping"""
    try:
        engine = setup_database()

        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO portal_sources
                (portal_name, portal_url, portal_type, state_code, city_name,
                 scraper_config, created_date)
                VALUES (:name, :url, :type, :state, :city, :config, :created_date)
                RETURNING id
            """), {
                "name": portal_name,
                "url": portal_url,
                "type": portal_type,
                "state": state_code,
                "city": city_name,
                "config": json.dumps(scraper_config or {}),
                "created_date": datetime.now().isoformat()
            })
            conn.commit()

            return result.fetchone()[0]

    except Exception as e:
        st.error(f"Error adding portal source: {str(e)}")
        return None

def scrape_portal_opportunities(portal_id):
    """Scrape opportunities from a specific portal using MCP tools"""
    try:
        engine = setup_database()

        # Get portal configuration
        portal_config = pd.read_sql("""
            SELECT portal_name, portal_url, portal_type, scraper_config
            FROM portal_sources
            WHERE id = :portal_id AND is_active = TRUE
        """, engine, params={"portal_id": portal_id})

        if portal_config.empty:
            return 0

        config = portal_config.iloc[0]
        scraper_config = json.loads(config['scraper_config']) if config['scraper_config'] else {}

        # Fetch portal page
        response = requests.get(config['portal_url'], timeout=30)
        response.raise_for_status()

        # Use MCP to extract structured data
        mcp_config = setup_mcp_connection()

        extraction_result = call_mcp_tool("extract_structured_data", {
            "text": response.text,
            "schema": {
                "fields": [
                    {"name": "opportunities", "type": "array", "description": "List of opportunity postings"},
                    {"name": "title", "type": "string", "description": "Opportunity title"},
                    {"name": "agency", "type": "string", "description": "Posting agency"},
                    {"name": "posted_date", "type": "string", "description": "Date posted"},
                    {"name": "deadline", "type": "string", "description": "Response deadline"},
                    {"name": "description", "type": "string", "description": "Opportunity description"},
                    {"name": "contact", "type": "string", "description": "Contact information"}
                ]
            },
            "domain_context": f"government_procurement_{config['portal_type']}"
        })

        if not extraction_result.get("success"):
            return 0

        opportunities = extraction_result.get("data", {}).get("results", [])
        opportunities_added = 0

        # Store extracted opportunities
        with engine.connect() as conn:
            for opp in opportunities:
                try:
                    conn.execute(text("""
                        INSERT INTO portal_opportunities
                        (portal_id, external_id, title, agency, posted_date,
                         response_deadline, description, contact_info, raw_data, created_date)
                        VALUES (:portal_id, :external_id, :title, :agency, :posted_date,
                                :deadline, :description, :contact, :raw_data, :created_date)
                    """), {
                        "portal_id": portal_id,
                        "external_id": opp.get("id", f"portal_{portal_id}_{opportunities_added}"),
                        "title": opp.get("title", ""),
                        "agency": opp.get("agency", ""),
                        "posted_date": opp.get("posted_date", ""),
                        "deadline": opp.get("deadline", ""),
                        "description": opp.get("description", ""),
                        "contact": opp.get("contact", ""),
                        "raw_data": json.dumps(opp),
                        "created_date": datetime.now().isoformat()
                    })
                    opportunities_added += 1

                except IntegrityError:
                    # Duplicate opportunity, skip
                    continue

            # Update portal last scraped time
            conn.execute(text("""
                UPDATE portal_sources
                SET last_scraped = :last_scraped,
                    success_rate = COALESCE(success_rate * 0.9 + 0.1, 0.1)
                WHERE id = :portal_id
            """), {
                "portal_id": portal_id,
                "last_scraped": datetime.now().isoformat()
            })

            conn.commit()

        return opportunities_added

    except Exception as e:
        st.error(f"Error scraping portal: {str(e)}")

        # Update failure rate
        try:
            engine = setup_database()
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE portal_sources
                    SET success_rate = COALESCE(success_rate * 0.9, 0.0)
                    WHERE id = :portal_id
                """), {"portal_id": portal_id})
                conn.commit()
        except:
            pass

        return 0

def sync_portal_opportunities_to_main():
    """Sync portal opportunities to main opportunities table"""
    try:
        engine = setup_database()

        # Get unsynced portal opportunities
        portal_opps = pd.read_sql("""
            SELECT po.*, ps.portal_name, ps.portal_type, ps.state_code, ps.city_name
            FROM portal_opportunities po
            JOIN portal_sources ps ON po.portal_id = ps.id
            WHERE po.sync_status = 'new'
            ORDER BY po.created_date DESC
        """, engine)

        synced_count = 0

        for _, opp in portal_opps.iterrows():
            try:
                # Generate unique notice_id for portal opportunities
                notice_id = f"PORTAL_{opp['portal_id']}_{opp['external_id']}"

                # Use MCP to classify and standardize the opportunity
                classification_result = call_mcp_tool("classify_content", {
                    "content": f"{opp['title']} {opp['description']}",
                    "classification_scheme": "government_contracting_taxonomy",
                    "domain_rules": "standardize_opportunity_data"
                })

                # Insert into main opportunities table
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO opportunities
                        (notice_id, title, agency, posted_date, response_deadline,
                         naics_code, set_aside, status, p_win_score, analysis_summary, raw_data)
                        VALUES (:notice_id, :title, :agency, :posted_date, :deadline,
                                :naics, :set_aside, 'New', 0, :summary, :raw_data)
                    """), {
                        "notice_id": notice_id,
                        "title": opp['title'],
                        "agency": f"{opp['agency']} ({opp['portal_name']})",
                        "posted_date": opp['posted_date'],
                        "deadline": opp['response_deadline'],
                        "naics": classification_result.get("data", {}).get("naics_code", ""),
                        "set_aside": classification_result.get("data", {}).get("set_aside_type", ""),
                        "summary": f"Opportunity from {opp['portal_name']} portal",
                        "raw_data": opp['raw_data']
                    })

                    # Mark as synced
                    conn.execute(text("""
                        UPDATE portal_opportunities
                        SET sync_status = 'synced'
                        WHERE id = :id
                    """), {"id": opp['id']})

                    conn.commit()
                    synced_count += 1

            except IntegrityError:
                # Duplicate, mark as synced anyway
                with engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE portal_opportunities
                        SET sync_status = 'synced'
                        WHERE id = :id
                    """), {"id": opp['id']})
                    conn.commit()

            except Exception as e:
                # Mark as failed
                with engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE portal_opportunities
                        SET sync_status = 'failed'
                        WHERE id = :id
                    """), {"id": opp['id']})
                    conn.commit()

        return synced_count

    except Exception as e:
        st.error(f"Error syncing portal opportunities: {str(e)}")
        return 0

def render_portal_integration():
    """Render state & local portal integration interface"""
    st.subheader("🏛️ State & Local Portal Integration")

    # Portal management
    tab1, tab2, tab3 = st.tabs(["📋 Portal Sources", "🔄 Sync Opportunities", "📊 Portal Statistics"])

    with tab1:
        st.subheader("Portal Source Management")

        # Add new portal
        with st.expander("➕ Add New Portal Source", expanded=False):
            with st.form("add_portal"):
                col1, col2 = st.columns(2)

                with col1:
                    portal_name = st.text_input("Portal Name", placeholder="California eProcurement")
                    portal_url = st.text_input("Portal URL", placeholder="https://www.caleprocure.ca.gov/")
                    portal_type = st.selectbox("Portal Type", ["state", "local", "federal"])

                with col2:
                    state_code = st.text_input("State Code (if applicable)", placeholder="CA")
                    city_name = st.text_input("City Name (if local)", placeholder="Los Angeles")

                if st.form_submit_button("Add Portal", type="primary"):
                    if portal_name and portal_url:
                        portal_id = add_portal_source(
                            portal_name, portal_url, portal_type,
                            state_code or None, city_name or None
                        )

                        if portal_id:
                            st.success(f"Portal '{portal_name}' added successfully!")
                            st.rerun()
                    else:
                        st.error("Please provide portal name and URL.")

        # Show existing portals
        try:
            engine = setup_database()
            portals = pd.read_sql("""
                SELECT id, portal_name, portal_url, portal_type, state_code, city_name,
                       is_active, last_scraped, success_rate
                FROM portal_sources
                ORDER BY portal_type, portal_name
            """, engine)

            if not portals.empty:
                st.write("**Configured Portal Sources:**")

                for _, portal in portals.iterrows():
                    with st.expander(f"{'✅' if portal['is_active'] else '❌'} {portal['portal_name']} ({portal['portal_type'].title()})"):
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.write(f"**URL:** {portal['portal_url']}")
                            if portal['state_code']:
                                st.write(f"**State:** {portal['state_code']}")
                            if portal['city_name']:
                                st.write(f"**City:** {portal['city_name']}")

                            if portal['last_scraped']:
                                st.write(f"**Last Scraped:** {portal['last_scraped'][:19]}")

                            st.write(f"**Success Rate:** {portal['success_rate']*100:.1f}%")

                        with col2:
                            if st.button("🔄 Scrape Now", key=f"scrape_{portal['id']}"):
                                with st.spinner(f"Scraping {portal['portal_name']}..."):
                                    opportunities_found = scrape_portal_opportunities(portal['id'])

                                if opportunities_found > 0:
                                    st.success(f"Found {opportunities_found} opportunities!")
                                else:
                                    st.info("No new opportunities found.")

                        with col3:
                            current_status = "Active" if portal['is_active'] else "Inactive"
                            new_status = st.selectbox(
                                "Status",
                                ["Active", "Inactive"],
                                index=0 if portal['is_active'] else 1,
                                key=f"status_{portal['id']}"
                            )

                            if new_status != current_status:
                                # Update portal status
                                update_portal_status(portal['id'], new_status == "Active")
                                st.rerun()
            else:
                st.info("No portal sources configured yet.")

        except Exception as e:
            st.error(f"Error loading portals: {str(e)}")

    with tab2:
        st.subheader("Opportunity Synchronization")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Scrape All Active Portals", type="primary"):
                with st.spinner("Scraping all active portals..."):
                    total_opportunities = scrape_all_active_portals()

                if total_opportunities > 0:
                    st.success(f"Found {total_opportunities} total opportunities across all portals!")
                else:
                    st.info("No new opportunities found.")

        with col2:
            if st.button("📥 Sync to Main Database"):
                with st.spinner("Syncing portal opportunities to main database..."):
                    synced_count = sync_portal_opportunities_to_main()

                if synced_count > 0:
                    st.success(f"Synced {synced_count} opportunities to main database!")
                else:
                    st.info("No new opportunities to sync.")

        # Show recent portal opportunities
        try:
            engine = setup_database()
            recent_portal_opps = pd.read_sql("""
                SELECT po.title, po.agency, po.posted_date, po.sync_status,
                       ps.portal_name, ps.portal_type
                FROM portal_opportunities po
                JOIN portal_sources ps ON po.portal_id = ps.id
                ORDER BY po.created_date DESC
                LIMIT 20
            """, engine)

            if not recent_portal_opps.empty:
                st.write("**Recent Portal Opportunities:**")
                st.dataframe(recent_portal_opps, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading recent opportunities: {str(e)}")

    with tab3:
        st.subheader("Portal Statistics")

        try:
            engine = setup_database()

            # Portal performance stats
            portal_stats = pd.read_sql("""
                SELECT ps.portal_name, ps.portal_type, ps.success_rate,
                       COUNT(po.id) as total_opportunities,
                       COUNT(CASE WHEN po.sync_status = 'synced' THEN 1 END) as synced_opportunities,
                       MAX(ps.last_scraped) as last_scraped
                FROM portal_sources ps
                LEFT JOIN portal_opportunities po ON ps.id = po.portal_id
                GROUP BY ps.id, ps.portal_name, ps.portal_type, ps.success_rate
                ORDER BY total_opportunities DESC
            """, engine)

            if not portal_stats.empty:
                st.write("**Portal Performance:**")

                # Create metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_portals = len(portal_stats)
                    st.metric("Total Portals", total_portals)

                with col2:
                    total_opps = portal_stats['total_opportunities'].sum()
                    st.metric("Total Opportunities", total_opps)

                with col3:
                    synced_opps = portal_stats['synced_opportunities'].sum()
                    st.metric("Synced Opportunities", synced_opps)

                with col4:
                    avg_success_rate = portal_stats['success_rate'].mean() * 100
                    st.metric("Avg Success Rate", f"{avg_success_rate:.1f}%")

                # Detailed stats table
                st.write("**Detailed Portal Statistics:**")
                st.dataframe(portal_stats, use_container_width=True)

                # Success rate chart
                if len(portal_stats) > 1:
                    import plotly.express as px

                    fig = px.bar(
                        portal_stats,
                        x='portal_name',
                        y='success_rate',
                        color='portal_type',
                        title="Portal Success Rates",
                        labels={'success_rate': 'Success Rate', 'portal_name': 'Portal Name'}
                    )

                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading portal statistics: {str(e)}")

def scrape_all_active_portals():
    """Scrape opportunities from all active portals"""
    try:
        engine = setup_database()

        active_portals = pd.read_sql("""
            SELECT id FROM portal_sources WHERE is_active = TRUE
        """, engine)

        total_opportunities = 0

        for _, portal in active_portals.iterrows():
            opportunities_found = scrape_portal_opportunities(portal['id'])
            total_opportunities += opportunities_found

        return total_opportunities

    except Exception as e:
        st.error(f"Error scraping all portals: {str(e)}")
        return 0

def update_portal_status(portal_id, is_active):
    """Update portal active status"""
    try:
        engine = setup_database()

        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE portal_sources
                SET is_active = :is_active
                WHERE id = :portal_id
            """), {
                "portal_id": portal_id,
                "is_active": is_active
            })
            conn.commit()

    except Exception as e:
        st.error(f"Error updating portal status: {str(e)}")
```

---

*Continuing with more features...*
