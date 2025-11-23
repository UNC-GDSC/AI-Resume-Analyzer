import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { FiPlus, FiFileText, FiUsers, FiTrendingUp } from 'react-icons/fi';

const Dashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/jobs`
      );
      setJobs(response.data);
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job?')) {
      return;
    }

    try {
      await axios.delete(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/jobs/${jobId}`
      );
      setJobs(jobs.filter((job) => job.id !== jobId));
    } catch (err) {
      alert('Failed to delete job');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Job Postings</h1>
          <p className="mt-2 text-gray-600">
            Manage your job postings and review candidate rankings
          </p>
        </div>
        <Link to="/jobs/create" className="btn-primary flex items-center space-x-2">
          <FiPlus />
          <span>Create New Job</span>
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="text-center py-12">
          <FiFileText className="mx-auto text-6xl text-gray-400 mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            No job postings yet
          </h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first job posting
          </p>
          <Link to="/jobs/create" className="btn-primary inline-flex items-center space-x-2">
            <FiPlus />
            <span>Create Job Posting</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div key={job.id} className="card">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    {job.title}
                  </h3>
                  {job.company && (
                    <p className="text-sm text-gray-600">{job.company}</p>
                  )}
                  {job.location && (
                    <p className="text-sm text-gray-500">{job.location}</p>
                  )}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-gray-700 line-clamp-3">
                  {job.description}
                </p>
              </div>

              <div className="flex items-center space-x-4 mb-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <FiUsers />
                  <span>{job.resume_count || 0} resumes</span>
                </div>
                {job.required_skills && job.required_skills.length > 0 && (
                  <div className="flex items-center space-x-1">
                    <FiTrendingUp />
                    <span>{job.required_skills.length} skills</span>
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                <Link
                  to={`/jobs/${job.id}`}
                  className="flex-1 btn-primary text-center"
                >
                  View Details
                </Link>
                <button
                  onClick={() => handleDelete(job.id)}
                  className="btn-danger"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
