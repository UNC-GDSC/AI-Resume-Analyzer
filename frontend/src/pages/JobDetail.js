import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import {
  FiArrowLeft,
  FiUpload,
  FiFileText,
  FiCheckCircle,
  FiXCircle,
  FiTrendingUp,
  FiRefreshCw,
} from 'react-icons/fi';

const JobDetail = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJobDetails();
    fetchRankings();
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/jobs/${jobId}`
      );
      setJob(response.data);
    } catch (err) {
      setError('Failed to fetch job details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRankings = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/rankings/job/${jobId}`
      );
      setRankings(response.data);
    } catch (err) {
      console.error('Failed to fetch rankings:', err);
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    setError('');

    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('job_id', jobId);

      try {
        await axios.post(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/resumes/upload`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
      } catch (err) {
        setError(`Failed to upload ${file.name}: ${err.response?.data?.detail || 'Unknown error'}`);
        console.error(err);
      }
    }

    setUploading(false);
    fetchRankings();
  }, [jobId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: true,
  });

  const handleRerank = async () => {
    try {
      setLoading(true);
      await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/rankings/job/${jobId}/rerank`
      );
      fetchRankings();
    } catch (err) {
      setError('Failed to re-rank resumes');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 65) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 65) return 'bg-blue-100';
    if (score >= 50) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Job not found</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <FiArrowLeft />
        <span>Back to Dashboard</span>
      </button>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job Details */}
        <div className="lg:col-span-1">
          <div className="card sticky top-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {job.title}
            </h1>
            {job.company && (
              <p className="text-lg text-gray-700 mb-1">{job.company}</p>
            )}
            {job.location && (
              <p className="text-sm text-gray-600 mb-4">{job.location}</p>
            )}

            <div className="mb-4">
              <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
              <p className="text-gray-700 text-sm whitespace-pre-wrap">
                {job.description}
              </p>
            </div>

            {job.required_skills && job.required_skills.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold text-gray-900 mb-2">
                  Required Skills
                </h3>
                <div className="flex flex-wrap gap-2">
                  {job.required_skills.map((skill, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {job.preferred_skills && job.preferred_skills.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold text-gray-900 mb-2">
                  Preferred Skills
                </h3>
                <div className="flex flex-wrap gap-2">
                  {job.preferred_skills.map((skill, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {(job.experience_years || job.education_level) && (
              <div className="border-t pt-4">
                {job.experience_years && (
                  <p className="text-sm text-gray-700 mb-2">
                    <strong>Experience:</strong> {job.experience_years}+ years
                  </p>
                )}
                {job.education_level && (
                  <p className="text-sm text-gray-700">
                    <strong>Education:</strong> {job.education_level}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Resume Upload and Rankings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Area */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Upload Resumes
            </h2>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400'
              }`}
            >
              <input {...getInputProps()} />
              <FiUpload className="mx-auto text-4xl text-gray-400 mb-4" />
              {uploading ? (
                <p className="text-gray-600">Uploading and processing...</p>
              ) : isDragActive ? (
                <p className="text-primary-600 font-medium">
                  Drop the files here...
                </p>
              ) : (
                <div>
                  <p className="text-gray-700 font-medium mb-2">
                    Drag & drop resumes here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports PDF, DOCX, and TXT files
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Rankings */}
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">
                Candidate Rankings ({rankings.length})
              </h2>
              {rankings.length > 0 && (
                <button
                  onClick={handleRerank}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <FiRefreshCw />
                  <span>Re-rank All</span>
                </button>
              )}
            </div>

            {rankings.length === 0 ? (
              <div className="text-center py-8">
                <FiFileText className="mx-auto text-5xl text-gray-400 mb-4" />
                <p className="text-gray-600">
                  No resumes uploaded yet. Upload resumes to see rankings.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {rankings.map((ranking, index) => (
                  <div
                    key={ranking.id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl font-bold text-gray-400">
                            #{index + 1}
                          </span>
                          <div>
                            <h3 className="font-semibold text-gray-900">
                              {ranking.candidate_name || 'Unknown Candidate'}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {ranking.filename}
                            </p>
                            {ranking.candidate_email && (
                              <p className="text-sm text-gray-500">
                                {ranking.candidate_email}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`text-3xl font-bold ${getScoreColor(
                            ranking.overall_score
                          )}`}
                        >
                          {ranking.overall_score.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-500">Overall Score</div>
                      </div>
                    </div>

                    {/* Score Breakdown */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                      <div className={`p-2 rounded ${getScoreBgColor(ranking.semantic_similarity_score)}`}>
                        <div className={`text-sm font-semibold ${getScoreColor(ranking.semantic_similarity_score)}`}>
                          {ranking.semantic_similarity_score.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-600">Semantic</div>
                      </div>
                      <div className={`p-2 rounded ${getScoreBgColor(ranking.skill_match_score)}`}>
                        <div className={`text-sm font-semibold ${getScoreColor(ranking.skill_match_score)}`}>
                          {ranking.skill_match_score.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-600">Skills</div>
                      </div>
                      <div className={`p-2 rounded ${getScoreBgColor(ranking.experience_score)}`}>
                        <div className={`text-sm font-semibold ${getScoreColor(ranking.experience_score)}`}>
                          {ranking.experience_score.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-600">Experience</div>
                      </div>
                      <div className={`p-2 rounded ${getScoreBgColor(ranking.education_score)}`}>
                        <div className={`text-sm font-semibold ${getScoreColor(ranking.education_score)}`}>
                          {ranking.education_score.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-600">Education</div>
                      </div>
                    </div>

                    {/* Summary */}
                    <p className="text-sm text-gray-700 mb-3">
                      {ranking.summary}
                    </p>

                    {/* Skills */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {ranking.matched_skills && ranking.matched_skills.length > 0 && (
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <FiCheckCircle className="text-green-600" />
                            <span className="text-xs font-semibold text-gray-700">
                              Matched Skills ({ranking.matched_skills.length})
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {ranking.matched_skills.slice(0, 5).map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded"
                              >
                                {skill}
                              </span>
                            ))}
                            {ranking.matched_skills.length > 5 && (
                              <span className="px-2 py-1 text-xs text-gray-600">
                                +{ranking.matched_skills.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {ranking.missing_skills && ranking.missing_skills.length > 0 && (
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <FiXCircle className="text-red-600" />
                            <span className="text-xs font-semibold text-gray-700">
                              Missing Skills ({ranking.missing_skills.length})
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {ranking.missing_skills.slice(0, 5).map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded"
                              >
                                {skill}
                              </span>
                            ))}
                            {ranking.missing_skills.length > 5 && (
                              <span className="px-2 py-1 text-xs text-gray-600">
                                +{ranking.missing_skills.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetail;
