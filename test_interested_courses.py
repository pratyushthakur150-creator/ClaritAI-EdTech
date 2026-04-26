import sys, os
sys.path.append(os.path.abspath('ravian-backend/ravian-backend/ravian-backend'))
from app.schemas.lead import LeadCreate

# Nested list example that previously caused validation errors
nested_courses = [['English'], 'Math', ['Physics', 'Chemistry'], 123]

lead = LeadCreate(
    name='Test User',
    phone='+1-555-123-4567',
    email='test@example.com',
    source='CHATBOT',
    intent='Testing interested courses flattening',
    interested_courses=nested_courses,
    urgency='MEDIUM'
)
print('Validated interested_courses:', lead.interested_courses)
