"""
Resume builder functionality tests
"""
import pytest
import json


class TestResumeBuilder:
    """Test resume builder functionality"""
    
    def test_resume_builder_page_loads(self, authenticated_coach_client):
        """Test resume builder page loads correctly"""
        response = authenticated_coach_client.get('/resume-builder')
        assert response.status_code == 200
        assert b'Resume Builder' in response.data
        assert b'AI Resume' in response.data
    
    def test_resume_builder_form_present(self, authenticated_coach_client):
        """Test resume builder form elements are present"""
        response = authenticated_coach_client.get('/resume-builder')
        assert response.status_code == 200
        assert b'textarea' in response.data
        assert b'Generate Resume' in response.data
    
    def test_resume_builder_instructions(self, authenticated_coach_client):
        """Test resume builder shows instructions"""
        response = authenticated_coach_client.get('/resume-builder')
        assert response.status_code == 200
        assert b'Hindi' in response.data or b'English' in response.data
        assert b'experience' in response.data.lower()


class TestResumeGeneration:
    """Test resume generation API"""
    
    def test_text_to_resume_api_english(self, authenticated_coach_client):
        """Test resume generation with English text"""
        test_text = """
        My name is John Smith.
        I am a football coach.
        I have 5 years of experience.
        I train under 16 players.
        I am AIFF Level One certified.
        """
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'full_name' in data
        assert 'headline' in data
        assert 'summary' in data
        assert 'skills' in data
        assert 'experience' in data
        assert 'certifications' in data
        assert 'achievements' in data
    
    def test_text_to_resume_api_hindi(self, authenticated_coach_client):
        """Test resume generation with Hindi text"""
        test_text = """
        मेरा नाम अमित वर्मा है।
        मैं फुटबॉल कोच हूँ।
        मुझे 5 साल का अनुभव है।
        मैं अंडर 14 खिलाड़ियों को प्रशिक्षण देता हूँ।
        मैं AIFF Level One certified हूँ।
        """
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'full_name' in data
        assert 'certifications' in data
        # Should extract AIFF certification
        assert len(data['certifications']) > 0
    
    def test_text_to_resume_empty_input(self, authenticated_coach_client):
        """Test resume generation with empty input"""
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': ''}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should return default structure
        assert 'full_name' in data
        assert data['full_name'] == 'Professional Coach'
    
    def test_text_to_resume_name_extraction(self, authenticated_coach_client):
        """Test name extraction from text"""
        test_text = "मेरा नाम राहुल शर्मा है। मैं क्रिकेट कोच हूँ।"
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should extract name (basic extraction logic)
        assert data['full_name'] != 'Professional Coach'
    
    def test_text_to_resume_experience_extraction(self, authenticated_coach_client):
        """Test experience extraction from text"""
        test_text = "I have 7 years of coaching experience in basketball."
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should extract experience information
        assert len(data['experience']) > 0
        assert 'experience' in data['experience'][0]['description'].lower()
    
    def test_text_to_resume_certification_extraction(self, authenticated_coach_client):
        """Test certification extraction from text"""
        test_text = """
        I am certified coach.
        I have AIFF Level One certification.
        I also have BCCI Level Two certificate.
        """
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should extract certifications
        assert len(data['certifications']) > 0
        cert_text = ' '.join(data['certifications']).lower()
        assert 'aiff' in cert_text or 'level' in cert_text


class TestResumeOutput:
    """Test resume output formatting"""
    
    def test_resume_data_structure(self, authenticated_coach_client):
        """Test resume data has correct structure"""
        test_text = "Test coach with experience"
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check required fields
        required_fields = ['full_name', 'headline', 'summary', 'skills', 'experience', 'certifications', 'achievements']
        for field in required_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data['skills'], list)
        assert isinstance(data['experience'], list)
        assert isinstance(data['certifications'], list)
        assert isinstance(data['achievements'], list)
    
    def test_resume_skills_generation(self, authenticated_coach_client):
        """Test resume skills generation"""
        test_text = "Football coach with fitness training experience"
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have default skills
        assert len(data['skills']) > 0
        skills_text = ' '.join(data['skills']).lower()
        assert 'coaching' in skills_text
    
    def test_resume_experience_structure(self, authenticated_coach_client):
        """Test resume experience structure"""
        test_text = "Senior football coach with team management experience"
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': test_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check experience structure
        assert len(data['experience']) > 0
        exp = data['experience'][0]
        assert 'role' in exp
        assert 'description' in exp


class TestResumeValidation:
    """Test resume input validation"""
    
    def test_invalid_json_input(self, authenticated_coach_client):
        """Test handling of invalid JSON input"""
        response = authenticated_coach_client.post('/text-to-resume',
            data='invalid json',
            content_type='application/json'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_missing_text_field(self, authenticated_coach_client):
        """Test handling of missing text field"""
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'other_field': 'value'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should return default structure
        assert 'full_name' in data
    
    def test_very_long_text_input(self, authenticated_coach_client):
        """Test handling of very long text input"""
        long_text = "I am a coach. " * 1000  # Very long text
        
        response = authenticated_coach_client.post('/text-to-resume',
            data=json.dumps({'text': long_text}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should handle without errors
        assert 'full_name' in data


class TestResumeAccessControl:
    """Test resume builder access control"""
    
    def test_resume_builder_requires_login(self, client):
        """Test resume builder requires authentication"""
        response = client.get('/resume-builder')
        assert response.status_code == 302  # Redirect to login
    
    def test_text_to_resume_requires_login(self, client):
        """Test text-to-resume API requires authentication"""
        response = client.post('/text-to-resume',
            data=json.dumps({'text': 'test'}),
            content_type='application/json'
        )
        assert response.status_code == 302  # Redirect to login
    
    def test_employer_cannot_access_resume_builder(self, authenticated_employer_client):
        """Test employer cannot access resume builder"""
        response = authenticated_employer_client.get('/resume-builder')
        # Should redirect or show error
        assert response.status_code in [302, 403]