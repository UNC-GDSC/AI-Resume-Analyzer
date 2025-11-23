import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiArrowLeft } from 'react-icons/fi';

const CreateJob = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requirements: '',
    company: '',
    location: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/jobs`,
        formData
      );
      navigate(`/jobs/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create job');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <FiArrowLeft />
        <span>Back to Dashboard</span>
      </button>

      <div className="card">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Create New Job Posting
        </h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="label">
              Job Title *
            </label>
            <input
              id="title"
              name="title"
              type="text"
              required
              className="input"
              placeholder="e.g., Senior Python Developer"
              value={formData.title}
              onChange={handleChange}
            />
          </div>

          <div>
            <label htmlFor="company" className="label">
              Company
            </label>
            <input
              id="company"
              name="company"
              type="text"
              className="input"
              placeholder="e.g., Tech Corp"
              value={formData.company}
              onChange={handleChange}
            />
          </div>

          <div>
            <label htmlFor="location" className="label">
              Location
            </label>
            <input
              id="location"
              name="location"
              type="text"
              className="input"
              placeholder="e.g., San Francisco, CA (Remote)"
              value={formData.location}
              onChange={handleChange}
            />
          </div>

          <div>
            <label htmlFor="description" className="label">
              Job Description *
            </label>
            <textarea
              id="description"
              name="description"
              required
              rows="8"
              className="input"
              placeholder="Describe the role, responsibilities, and what makes this position exciting..."
              value={formData.description}
              onChange={handleChange}
            />
            <p className="mt-2 text-sm text-gray-500">
              The AI will automatically extract required skills, experience level, and education requirements from your description.
            </p>
          </div>

          <div>
            <label htmlFor="requirements" className="label">
              Additional Requirements
            </label>
            <textarea
              id="requirements"
              name="requirements"
              rows="4"
              className="input"
              placeholder="List any specific requirements, qualifications, or nice-to-haves..."
              value={formData.requirements}
              onChange={handleChange}
            />
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary"
            >
              {loading ? 'Creating...' : 'Create Job Posting'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateJob;
