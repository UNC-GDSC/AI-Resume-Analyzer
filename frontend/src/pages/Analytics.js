import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiArrowLeft, FiDownload } from 'react-icons/fi';
import AnalyticsComponent from '../components/Analytics';

const AnalyticsPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalytics();
  }, [jobId]);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/analytics/job/${jobId}/stats`
      );
      setJob({ id: jobId, title: response.data.job_title });
      setAnalytics(response.data.analytics);
    } catch (err) {
      setError('Failed to fetch analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/analytics/job/${jobId}/export/csv`,
        {
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `rankings_${jobId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to export CSV');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={() => navigate(`/jobs/${jobId}`)}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
        >
          <FiArrowLeft />
          <span>Back to Job</span>
        </button>

        <button
          onClick={handleExportCSV}
          className="btn-primary flex items-center space-x-2"
        >
          <FiDownload />
          <span>Export CSV</span>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Analytics: {job?.title}
        </h1>
        <p className="mt-2 text-gray-600">
          Detailed insights and statistics for this job posting
        </p>
      </div>

      <AnalyticsComponent analytics={analytics} />
    </div>
  );
};

export default AnalyticsPage;
