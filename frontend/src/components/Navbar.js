import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiUser, FiLogOut, FiFileText } from 'react-icons/fi';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <FiFileText className="text-primary-600 text-3xl" />
              <span className="text-xl font-bold text-gray-900">
                AI Resume Analyzer
              </span>
            </Link>
          </div>

          {isAuthenticated && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-gray-700">
                <FiUser />
                <span className="text-sm font-medium">
                  {user?.username || 'User'}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
              >
                <FiLogOut />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
