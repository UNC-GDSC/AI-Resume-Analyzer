import React from 'react';
import { FiTrendingUp, FiUsers, FiAward, FiAlertCircle } from 'react-icons/fi';

const Analytics = ({ analytics }) => {
  if (!analytics) return null;

  const { score_distribution, top_skills, common_missing_skills, average_score } = analytics;

  const getScoreColor = (range) => {
    if (range === '80-100') return 'bg-green-500';
    if (range === '65-79') return 'bg-blue-500';
    if (range === '50-64') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Score Distribution */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
          <FiTrendingUp className="text-primary-600" />
          <span>Score Distribution</span>
        </h3>
        <div className="space-y-3">
          {Object.entries(score_distribution || {}).map(([range, count]) => {
            const total = Object.values(score_distribution).reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? (count / total) * 100 : 0;

            return (
              <div key={range}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{range}</span>
                  <span className="text-gray-600">
                    {count} ({percentage.toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getScoreColor(range)}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Skills */}
      {top_skills && top_skills.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <FiAward className="text-primary-600" />
            <span>Most Common Skills</span>
          </h3>
          <div className="space-y-2">
            {top_skills.slice(0, 5).map((item, index) => (
              <div key={index} className="flex items-center space-x-3">
                <span className="text-2xl font-bold text-gray-300">
                  {index + 1}
                </span>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium">{item.skill}</span>
                    <span className="text-sm text-gray-600">{item.count} candidates</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-primary-500 h-1.5 rounded-full"
                      style={{
                        width: `${(item.count / top_skills[0].count) * 100}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Common Missing Skills */}
      {common_missing_skills && common_missing_skills.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <FiAlertCircle className="text-red-600" />
            <span>Commonly Missing Skills</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {common_missing_skills.slice(0, 10).map((item, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
              >
                {item.skill} ({item.count})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center">
          <FiUsers className="mx-auto text-4xl text-primary-600 mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {analytics.total_candidates}
          </div>
          <div className="text-sm text-gray-600">Total Candidates</div>
        </div>
        <div className="card text-center">
          <FiTrendingUp className="mx-auto text-4xl text-green-600 mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {average_score?.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Average Score</div>
        </div>
        <div className="card text-center">
          <FiAward className="mx-auto text-4xl text-yellow-600 mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {analytics.top_candidate_score?.toFixed(1) || 'N/A'}
          </div>
          <div className="text-sm text-gray-600">Top Score</div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
