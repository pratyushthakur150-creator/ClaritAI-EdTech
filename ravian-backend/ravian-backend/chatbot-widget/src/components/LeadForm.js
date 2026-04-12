import { h } from 'preact';
import { useState } from 'preact/hooks';
import { validateEmail, validatePhone } from '../utils/helpers.js';

const LeadForm = ({ onSubmit, onCancel, isSubmitting }) => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: ''
  });
  
  const [errors, setErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required';
    } else if (!validatePhone(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }
    
    if (formData.email && !validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return h('div', { className: 'lead-form' }, [
    h('h3', { className: 'form-title' }, 'Get Started Today'),
    h('form', { onSubmit: handleSubmit }, [
      h('div', { className: 'form-group' }, [
        h('input', {
          type: 'text',
          className: `form-input ${errors.name ? 'error' : ''}`,
          placeholder: 'Your Name *',
          value: formData.name,
          onInput: (e) => handleChange('name', e.target.value),
          'aria-label': 'Your name',
          'aria-required': 'true',
          'aria-invalid': !!errors.name
        }),
        errors.name && h('div', { className: 'error-text' }, errors.name)
      ]),
      h('div', { className: 'form-group' }, [
        h('input', {
          type: 'tel',
          className: `form-input ${errors.phone ? 'error' : ''}`,
          placeholder: 'Phone Number *',
          value: formData.phone,
          onInput: (e) => handleChange('phone', e.target.value),
          'aria-label': 'Phone number',
          'aria-required': 'true',
          'aria-invalid': !!errors.phone
        }),
        errors.phone && h('div', { className: 'error-text' }, errors.phone)
      ]),
      h('div', { className: 'form-group' }, [
        h('input', {
          type: 'email',
          className: `form-input ${errors.email ? 'error' : ''}`,
          placeholder: 'Email (Optional)',
          value: formData.email,
          onInput: (e) => handleChange('email', e.target.value),
          'aria-label': 'Email address',
          'aria-invalid': !!errors.email
        }),
        errors.email && h('div', { className: 'error-text' }, errors.email)
      ]),
      h('div', { className: 'form-buttons' }, [
        h('button', {
          type: 'submit',
          className: 'submit-button',
          disabled: isSubmitting
        }, isSubmitting ? 'Submitting...' : 'Submit'),
        h('button', {
          type: 'button',
          className: 'cancel-button',
          onClick: onCancel
        }, 'Cancel')
      ])
    ])
  ]);
};

export default LeadForm;