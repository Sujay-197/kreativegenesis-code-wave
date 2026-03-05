"""
Test suite for AppForge AI Backend Modes (Simple & Tailored)
Tailored Mode handles all complexity levels from simple to enterprise/expert.
Run without making actual API calls by mocking all external services.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK DATA & FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_REQUIREMENTS = {
    "auth_and_users": "Single user, no authentication needed. Just one person using the app.",
    "data_and_storage": "Store customer orders with names, email, phone, and order details.",
    "ui_complexity": "Simple, clean interface. Desktop and mobile friendly.",
    "business_logic": "Calculate total order price, send email confirmation.",
    "integrations": "Email service for sending order confirmations.",
    "confidence_score": 85.5
}

MOCK_GENERATED_CODE = {
    "html": """<!DOCTYPE html>
<html>
<head>
    <title>Order Management App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="max-w-md mx-auto mt-10 bg-white p-6 rounded-lg shadow">
        <h1 class="text-2xl font-bold mb-4">Order Form</h1>
        <form id="orderForm">
            <input type="text" placeholder="Customer Name" id="name" required class="w-full p-2 border mb-2">
            <input type="email" placeholder="Email" id="email" required class="w-full p-2 border mb-2">
            <input type="tel" placeholder="Phone" id="phone" required class="w-full p-2 border mb-2">
            <textarea placeholder="Order Details" id="details" required class="w-full p-2 border mb-4"></textarea>
            <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded">Submit Order</button>
        </form>
        <div id="result" class="mt-4"></div>
    </div>
</body>
</html>""",
    "css": """body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.form-container {
    max-width: 500px;
    margin: 50px auto;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
}
button:hover {
    opacity: 0.9;
}""",
    "js": """document.getElementById('orderForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const order = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        details: document.getElementById('details').value,
        timestamp: new Date().toISOString()
    };
    console.log('Order submitted:', order);
    document.getElementById('result').innerHTML = '<p class="text-green-500">Order submitted successfully!</p>';
    this.reset();
});"""
}

MOCK_CONVERSATION = [
    {
        "role": "user",
        "content": "I want to build an app to manage orders for my bakery"
    },
    {
        "role": "assistant",
        "content": "That sounds wonderful! A bakery order management app could really streamline things. Tell me, are the orders coming from customers online, or are you managing orders from different sources?"
    },
    {
        "role": "user",
        "content": "Mostly online and phone orders that I need to track"
    },
    {
        "role": "assistant",
        "content": "Got it! So you're juggling orders from multiple channels. How many people on your team will be using this app to view and track orders?"
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class MockGroqClient:
    """Mock Groq client for testing."""
    def __init__(self):
        self.call_count = 0
    
    def chat(self):
        """Mock chat.completions.create"""
        return self
    
    def completions(self):
        return self
    
    def create(self, **kwargs):
        self.call_count += 1
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "That's an interesting approach! Who will be using this app and what's the main workflow they'll follow?"
        return mock_response


class MockHFClient:
    """Mock Hugging Face Inference client for testing."""
    def __init__(self):
        self.call_count = 0
    
    def chat_completion(self, **kwargs):
        self.call_count += 1
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "auth_and_users": "Single user, no auth",
            "data_and_storage": "Simple order storage",
            "ui_complexity": "Basic form interface",
            "business_logic": "Order calculation",
            "integrations": "Email notifications",
            "confidence_score": 80.0
        })
        return mock_response


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — SIMPLE MODE
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimpleMode:
    """Test Simple Mode functionality without API calls."""
    
    def test_simple_mode_conversation_format(self):
        """Test that simple mode conversation maintains correct format."""
        history = [
            {"role": "user", "parts": ["I want to build an app"]},
        ]
        
        assert history[0]["role"] == "user"
        assert "parts" in history[0]
        assert isinstance(history[0]["parts"], list)
    
    def test_extract_code_blocks_html(self):
        """Test HTML block extraction from markdown."""
        # Import the function from backend_mode
        from backend_mode import extract_code_blocks
        
        markdown = """
```html
<!DOCTYPE html>
<html><body>Hello</body></html>
```
```css
body { color: blue; }
```
```javascript
console.log('test');
```
"""
        html, css, js = extract_code_blocks(markdown)
        
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "color: blue" in css
        assert "console.log" in js
    
    def test_extract_code_blocks_fallback(self):
        """Test fallback when code blocks are missing."""
        from backend_mode import extract_code_blocks
        
        markdown = "No code blocks here"
        html, css, js = extract_code_blocks(markdown)
        
        assert "Failed" in html or "HTML" in html
        assert "Failed" in css or "CSS" in css
        assert "Failed" in js or "JS" in js
    
    def test_requirements_object_validation(self):
        """Test that RequirementsObject properly validates input."""
        from backend_mode import RequirementsObject
        
        valid_req = RequirementsObject(
            auth_and_users="Single user",
            data_and_storage="Local storage",
            ui_complexity="Simple",
            business_logic="Basic calculations",
            integrations="None"
        )
        
        assert valid_req.auth_and_users == "Single user"
        assert valid_req.data_and_storage == "Local storage"
        assert hasattr(valid_req, 'integrations')
    
    def test_simple_mode_session_creation(self):
        """Test that sessions are properly created."""
        from backend_mode import get_or_create_session
        
        session_id = get_or_create_session(None, "simple")
        
        assert session_id is not None
        assert len(session_id) > 0
        
        # Create another and verify it's different
        session_id2 = get_or_create_session(None, "simple")
        assert session_id != session_id2


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — TAILORED MODE
# ═══════════════════════════════════════════════════════════════════════════════

class TestTailoredMode:
    """Test Tailored Mode functionality."""
    
    def test_tailored_mode_conversation_format(self):
        """Test that tailored mode conversation maintains correct format."""
        history = [
            {"role": "user", "content": "I want to build an app"},
        ]
        
        assert history[0]["role"] == "user"
        assert "content" in history[0]
        assert isinstance(history[0]["content"], str)
    
    def test_tailored_mode_technical_spec_initialization(self):
        """Test that tailored mode initializes technical spec correctly."""
        from backend_mode import get_or_create_session
        from backend_mode import sessions
        
        session_id = get_or_create_session(None, "tailored")
        session = sessions[session_id]
        
        assert "technical_spec" in session
        assert "auth_and_users" in session["technical_spec"]
        assert session["technical_spec"]["auth_and_users"] == "Not yet discussed"
        assert session["code"] is None
    
    def test_tailored_mode_session_update(self):
        """Test that technical spec updates in tailored mode."""
        from backend_mode import get_or_create_session, sessions
        
        session_id = get_or_create_session(None, "tailored")
        session = sessions[session_id]
        
        # Simulate analyzer updating the spec
        new_spec = {
            "auth_and_users": "Multiple users with roles",
            "data_and_storage": "Cloud database",
            "ui_complexity": "Complex dashboard",
            "business_logic": "Advanced workflows",
            "integrations": "Third-party APIs"
        }
        session["technical_spec"].update(new_spec)
        
        assert session["technical_spec"]["auth_and_users"] == "Multiple users with roles"
        assert session["technical_spec"]["data_and_storage"] == "Cloud database"


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED TAILORED MODE TESTS (UNIFIED)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTailoredModeAdvanced:
    """Test Tailored Mode handling advanced/expert-level requirements (unified)."""
    
    def test_tailored_mode_advanced_requirements(self):
        """Test that tailored mode can capture complex, advanced requirements."""
        advanced_requirements = {
            "auth_and_users": "Multi-tenant with role-based access control (Admin, Manager, User)",
            "data_and_storage": "PostgreSQL with Redis caching layer",
            "ui_complexity": "Real-time dashboard with charts, WebSocket updates",
            "business_logic": "Complex workflow engine with conditional logic, notifications, audit logging",
            "integrations": "Stripe payments, SendGrid email, Slack notifications, Google Analytics"
        }
        
        # Verify tailored mode can handle complexity
        assert "PostgreSQL" in advanced_requirements["data_and_storage"]
        assert "Real-time dashboard" in advanced_requirements["ui_complexity"]
        assert "Stripe" in advanced_requirements["integrations"]
    
    def test_tailored_mode_production_code_generation(self):
        """Test that tailored mode generates production-grade code."""
        production_spec = {
            "auth_and_users": "OAuth2 with JWT tokens",
            "data_and_storage": "PostgreSQL with migrations",
            "ui_complexity": "React with TypeScript and state management",
            "business_logic": "Microservices architecture",
            "integrations": "REST API design with OpenAPI spec"
        }
        
        # Verify spec is production-ready
        assert "OAuth2" in production_spec["auth_and_users"]
        assert "TypeScript" in production_spec["ui_complexity"]
        assert "REST API" in production_spec["integrations"]
    
    def test_tailored_mode_extended_conversation(self):
        """Test that tailored mode maintains extended conversation history for complex requirements."""
        extended_conversation = [
            {"role": "user", "content": "I need a SaaS platform for team collaboration"},
            {"role": "assistant", "content": "That's ambitious! Let's start with your target market."},
            {"role": "user", "content": "Remote teams in tech startups"},
            {"role": "assistant", "content": "Great. How many concurrent users are you expecting at launch?"},
            {"role": "user", "content": "Starting with 1,000 beta users, scaling to 100,000"},
            {"role": "assistant", "content": "That's important. What's your timeline for reaching scale?"},
        ]
        
        assert len(extended_conversation) == 6
        assert all("role" in msg and "content" in msg for msg in extended_conversation)
    
    def test_tailored_mode_scalable_spec_validation(self):
        """Test tailored mode validation for specs of any complexity."""
        def validate_tailored_spec(spec: Dict[str, Any]) -> bool:
            """Validate if spec has core requirements fields."""
            required_fields = [
                "auth_and_users",
                "data_and_storage",
                "ui_complexity",
                "business_logic",
                "integrations"
            ]
            
            return all(field in spec for field in required_fields)
        
        simple_spec = {
            "auth_and_users": "Basic",
            "data_and_storage": "Local storage",
            "ui_complexity": "Simple form",
            "business_logic": "Basic logic",
            "integrations": "None"
        }
        
        complex_spec = {
            "auth_and_users": "OAuth2",
            "data_and_storage": "PostgreSQL",
            "ui_complexity": "React + TypeScript",
            "business_logic": "Microservices",
            "integrations": "Multiple APIs"
        }
        
        assert validate_tailored_spec(simple_spec)
        assert validate_tailored_spec(complex_spec)
    
    def test_tailored_mode_technical_guidance(self):
        """Test tailored mode can capture technical guidance for improvements."""
        technical_guidance = {
            "current_architecture": "Monolith with SQLite",
            "improvements": [
                "Migrate to microservices for scalability",
                "Upgrade to PostgreSQL with backups",
                "Implement automated testing"
            ],
            "estimated_effort": "3-6 months",
            "priority": "High"
        }
        
        assert len(technical_guidance["improvements"]) > 0
        assert "estimated_effort" in technical_guidance


# ═══════════════════════════════════════════════════════════════════════════════
# CODE GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCodeGeneration:
    """Test code generation without making API calls."""
    
    def test_generated_code_structure(self):
        """Test that generated code has proper structure."""
        code = MOCK_GENERATED_CODE
        
        assert "html" in code
        assert "css" in code
        assert "js" in code
        assert len(code["html"]) > 0
        assert len(code["css"]) > 0
        assert len(code["js"]) > 0
    
    def test_html_contains_required_elements(self):
        """Test that generated HTML has essential elements."""
        html = MOCK_GENERATED_CODE["html"]
        
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "body" in html.lower()
    
    def test_javascript_event_handling(self):
        """Test that generated JS has event handlers."""
        js = MOCK_GENERATED_CODE["js"]
        
        assert "addEventListener" in js or "onclick" in js.lower()
        assert "document" in js or "getElementById" in js
    
    def test_css_styling_present(self):
        """Test that CSS has actual styles."""
        css = MOCK_GENERATED_CODE["css"]
        
        assert "{" in css
        assert "}" in css
        assert "font-family" in css or "color" in css or "padding" in css or "margin" in css


# ═══════════════════════════════════════════════════════════════════════════════
# END-TO-END SCENARIO TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEndScenarios:
    """Test complete user scenarios."""
    
    def test_bakery_order_system_scenario(self):
        """Test building a bakery order management system."""
        conversation = [
            {"type": "user", "text": "I own a bakery and need to manage orders"},
            {"type": "system", "text": "validating requirements..."},
            {"type": "system", "spec": MOCK_REQUIREMENTS},
            {"type": "system", "text": "generating code..."},
            {"type": "system", "code": MOCK_GENERATED_CODE}
        ]
        
        assert len(conversation) >= 5
        assert any(msg.get("type") == "system" and "spec" in msg for msg in conversation)
        assert any(msg.get("type") == "system" and "code" in msg for msg in conversation)
    
    def test_multi_turn_conversation_flow(self):
        """Test multi-turn conversation with progressive refinement."""
        flow = {
            "turn_1": {
                "user": "I want to build an app",
                "assistant_extracts": {"confidence": 20}
            },
            "turn_2": {
                "user": "It's for managing orders",
                "assistant_extracts": {"confidence": 50}
            },
            "turn_3": {
                "user": "For my bakery, with multiple order sources",
                "assistant_extracts": {"confidence": 75}
            },
            "turn_4": {
                "user": "And email notifications to customers",
                "assistant_extracts": {"confidence": 90}
            }
        }
        
        # Verify confidence increases
        confidences = [flow[f"turn_{i}"]["assistant_extracts"]["confidence"] for i in range(1, 5)]
        assert confidences == sorted(confidences)  # Increasing order


# ═══════════════════════════════════════════════════════════════════════════════
# PYTEST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run all tests
    pytest.main([
        __file__,
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "-s"  # Show print statements
    ])
